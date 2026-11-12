# Call a service you don't own

The layers and the adapter's contract are in `SKILL.md` (Write an adapter); this is the HTTP mechanics an adapter shares across its sources.
`adapt/httpx_.py` holds two builders: the client the composition root opens once per run and closes, and the getter each source module composes with its parse:

```python
def _retryable(failure: BaseException) -> bool:
    """Retry a transport fault, a throttle or a server fault, never a client error."""
    if isinstance(failure, httpx.TransportError):
        return True
    return isinstance(failure, httpx.HTTPStatusError) and (
        failure.response.status_code == 429 or failure.response.status_code >= 500
    )


def _wait(state: tenacity.RetryCallState) -> float:
    """Wait as long as the service asked, else back off with jitter."""
    failure = state.outcome.exception() if state.outcome else None
    header = (
        failure.response.headers.get("Retry-After")
        if isinstance(failure, httpx.HTTPStatusError)
        else None
    )
    if header is not None and header.isdigit():
        return float(header)
    return tenacity.wait_exponential_jitter(initial=1, max=60)(state)


def build_client(
    api_key: str,
    *,
    timeout: float,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Client:
    """Return the one client a run shares; the composition root closes it."""
    return httpx.Client(
        headers={
            "User-Agent": f"mypackage/{importlib.metadata.version('mypackage')}",
            "X-API-Key": api_key,
        },
        timeout=timeout,
        transport=transport,
    )


def build_get_document(
    client: httpx.Client,
    *,
    budget: int,
    rates: list[pyrate_limiter.Rate],
    sleep: collections.abc.Callable[[float], None] = time.sleep,
) -> collections.abc.Callable[[str], str]:
    """Return a getter over the client, paced at every rate, capped and retried."""
    limiter = pyrate_limiter.Limiter(rates)
    sent = itertools.count(1)
    retrying = tenacity.Retrying(
        reraise=True,
        retry=tenacity.retry_if_exception(_retryable),
        sleep=sleep,
        stop=tenacity.stop_after_attempt(5),
        wait=_wait,
    )

    def attempt(url: str) -> str:
        if next(sent) > budget or not limiter.try_acquire("source", timeout=60):
            raise error.QuotaError(f"The day's requests ran out before {url}")
        return client.get(url).raise_for_status().text

    def get_document(url: str) -> str:
        return retrying(attempt, url)

    return get_document
```

- **The composition root builds one client per run and passes it in** — `with httpx_.build_client(key, timeout=...) as client:` — binding the key from settings (`SKILL.md`, Configuration); a `functools.cache`d module-level client has no owner to close it and no seam for a test transport.
`timeout` and `rates` come from the source's package YAML, so a second source over the same module states its own.
- **`transport` and `sleep` are the test seams `write-tests` uses**, with the one patch of `pyrate-limiter`'s own sleep in its Python reference.
- **Send your own user agent**: a library's default gets refused unevenly by whatever fronts the service, so the same code works on two hosts and 403s on a third.
A service that accepts only a browser string is a fact found by trying it, not a default.
- **The key goes in a header, never the query string**, which every proxy, access log and shared link records.
- **Pace every window the service states.** The source's YAML lists one `Rate` per window — `Rate(2, Duration.SECOND)`, `Rate(5000, Duration.DAY)` — and `Limiter` takes the list.
A day's cap is shared by every process that runs that day — the scheduled run, a backfill, a manual fetch — and a limiter counts only its own, so the composition root also passes `budget`, the day's limit less the `requests` the manifest records for today (`store-data`), and the getter raises `QuotaError` past it.
`try_acquire(..., timeout=60)` caps a wait at a minute, so the limiter's own day window refuses rather than sleeping until it rolls over; either refusal fails the item and every one after it without asking, since each would get the same answer.
`Limiter` (`pyrate-limiter` 4.5.1) rejects a list whose limits don't rise with the interval, so the list holds the windows as the service states them, never a day's limit cut below a shorter window's.
- **`tenacity` retries** only a transport fault, a `429` or a `5xx`, honouring `Retry-After`, with `reraise=True` so the caller sees the real exception; a `4xx` is your bug and retrying it only hides which request was wrong (`write-python`, Classify outcomes).
Pacing sits inside the attempt, so a retry takes a slot too.
- **Page to exhaustion and assert the count**: follow the next-page link until the service sends none, then compare the rows against the total the first page states, since a loop stopping at a fixed page count caps the data silently.

**Recognise a publisher's unstated terms**, since all three look like your bug and none appears in a test:

- **A burst is throttled, not refused**: after enough requests the service answers `200` with an HTML page instead of the file.
The tell is a failure that follows the request count; retry the same call after a pause.
- **A rate is stated somewhere you haven't read**: a `Crawl-delay` in `robots.txt`, or a `429` past an API's per-minute cap.
Back off long enough to outlast the window; pace a walk you chose (paging through results) and leave a single requested fetch alone.
- **Some documents need cookies first**: the first request redirects to a consent page whose cookies the second needs.
Give the HTTP module an optional page to visit first, beside the timeout and user agent.
