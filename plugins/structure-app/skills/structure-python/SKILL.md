---
name: structure-python
description: >-
  How to structure a non-trivial Python application — the hexagonal
  (ports-and-adapters) layers of a pure core (domain types, logic, and use
  cases behind ports) and an outer edge (driven adapters for IO, entry-point
  drivers at a composition root), how to declare a port as a noun satisfied by
  a verb and split one whose halves differ, how to write an adapter that maps
  into the port's shared schema, fetches one source for one day politely
  through one httpx client the composition root opens with the key bound in,
  paced by pyrate-limiter at every window the service states within the day's
  budget and retried by tenacity with a transport and a sleep as test seams,
  pages to exhaustion, and returns what it got — records, rejected rows, raw
  pages and failed items — for the store to write, failing an item rather than
  the source and treating an empty answer as an empty day, how it absorbs a
  source's schema changes, malformed rows and a publisher's unstated terms,
  the error package, the three homes of a configuration value (settings for
  deployment values and every secret, package YAML for a source's constants
  and its tolerance, a user-editable CSV of active items), the log level per
  event, and where logging, runtime data assets and the test suite sit. Use
  when organising an app into layers, deciding where configuration, a module,
  entry point, IO adapter, data asset, constant, secret or test belongs,
  naming adapter modules for several sources, designing a port or an adapter's
  output, deciding what happens when one item of a fetch fails or the day's
  requests run out, choosing whether a data file should be CSV, YAML or TOML,
  deciding whether a lookup is a file or an enum, packaging data through
  importlib.resources, applying dependency injection, or laying out the
  code/data/tests directories — even if the user just says "structure this
  app", "where does this go", or "clean/hexagonal architecture". Layers on
  write-python and be-functional; for building the entry points themselves,
  see write-entry-points; for where the data lives, store-data; for
  scaffolding, packaging and tooling, setup-python. A PLAN.md decision
  overrides any rule here.
---

# Structure a Python application

How to organise a non-trivial application — its layers, the boundaries between them, and where each module, adapter and asset belongs.
It sits above `write-python`'s in-code conventions and `be-functional`'s core/shell split; the drivers are built out in `write-entry-points`, storage in `store-data`, and scaffolding and tooling live in `setup-python`.
Three mistakes account for most of what goes wrong: an import that points from the core outward, an adapter that hands on the library's own type instead of yours, and a lookup table left in code because it looked too small for a file.
Every rule here is a default a decision in the project's `PLAN.md` overrides.

**In an existing project, ask first.** Where a repo already has an established layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Code

All the Python lives in a `code/` package under the package root, split into layers, so that the assets in `data/` beside it can mirror those layers and each asset's path names its owner (see [Data](#data)).
The cost is one more segment in every import and console-script path, and a name shared with the stdlib's `code` module, which bites only if `src/mypackage` itself lands on `sys.path`; an app with no `data/` has no reason for `code/`, so its layers sit at the package root.

```text
mypackage/
  __init__.py
  code/
    __init__.py
    adapt/
    drive/
    operate/
    port/
    transform/
  data/
```

`code/` has two groups — a pure **core** holding the logic and an **edge** doing all the IO — in five standard packages, each a regular package with an `__init__.py` (`data/` is a plain resource tree):

- **`transform`** (core) — the problem's types and rules, and the pure functions over them; the domain's records and enums live here, moving to a `domain/` package once they multiply.
- **`port`** (core) — the *behavioural* interfaces the core needs the outside world to satisfy, as `typing.Protocol`s or callable aliases (`Records = collections.abc.Callable[[list[str], datetime.date], Fetched]`, since a fetch's unit of work is one source for one day; a source whose endpoint serves a range per request takes a first and a last day instead, as `run-unattended`'s Make a run rerunnable says), with the records they move (`port.Fetched`) and the schema those records share (`port.RECORDS`) beside them.
A port is a noun naming *what* the core needs, not how, and the function satisfying it is the verb (`port.Records`, `noaa.fetch_records`; see `write-python`); see [Declare a port](#declare-a-port).
- **`operate`** (core) — one function per use case, orchestrating it: calling `transform` for logic and a port for IO, staying pure because the adapter is injected (`operate.report(stations, fetch=...)`).
Imports only `transform` and `port`; a use case is a module named by its verb (`report.py`) and re-exported, so callers write `operate.report(...)` and the module is shadowed (see below) — accept that here, since a use case holds no helper worth reaching behind it, and one that does belongs in `transform`.
- **`adapt`** (edge) — concrete implementations of the ports, one module per source named for it (`noaa.py`, `metoffice.py`), with what every source shares — the client, pacing, retry — in `httpx_.py`, named for the library; the store is `parquet.py`, with `motherduck.py` beside it once the data is hosted, and the overlap lock `lock.py` (see `store-data` and `run-unattended`).
A library-coupled module becomes a package of the same name when it needs a second file (`write-python`, Imports), so `httpx_.py` splits when the second source arrives.
Imports `transform` and `port`, never `operate` or `drive`; see [Write an adapter](#write-an-adapter).
- **`drive`** (edge) — the entry points and the composition root, built out in `write-entry-points`.

Two rules hold it together:

- **IO lives only at the edge.** Network, filesystem, clock, randomness and external services are touched only by `adapt` and `drive`; the core is deterministic and side-effect-free.
Purity is about effects, not dependencies: the core uses computation libraries (`polars`, `numpy`) freely and avoids only the IO frameworks (`httpx`, `typer`, `fastapi`) — even in `polars`, `scan_csv` and `write_*` are edge.
- **Imports point inward.** The edge imports the core and never the reverse; the one place importing both an operation and an adapter is the composition root (see `write-entry-points`).
Control flows outward through the injected port, so the operation *calls* the adapter without *importing* it (see `be-functional`).

**The names are a standard, not a fixed set.** What places a package is its group: add pure packages beside `transform` as the core grows (`domain`, `pricing`), and edge packages beside `adapt` as the IO grows (an `extract` and a `load`), each obeying its group's rules.

**Errors are a core package of their own, `error/`, importing nothing.** Every layer raises the app's exceptions, an adapter converts a library's failure into them and a driver decides what the user sees (`write-python`, Error handling), so they can't live in `adapt`, which nothing inward may import.
The `handle` decorator that converts a library's failures into them (see `write-python`) sits in the same package, since its `report` is usually one of the classes beside it.

**Let it grow into the app.** A tiny tool is a module or two at the package root — no `code/`, no `data/`, no layers.
Introduce them once there is a real boundary to name: an external service, a second entry point, a second operation, assets to separate.

**Design the core's shape before the edge's.** A CLI's flags invite a design pass; the core's data shape rarely does, yet every adapter, operation and test is built on it and a second driver inherits it.
Settle it first, deriving it from the data flow (see `be-functional`).

**A module separates what is read separately.** Split a layer when a module would be worth opening on its own, never one module per function: following one call through three dozen-line files, re-exported by an `__init__.py` that exists to undo the split, is the tell.

**Reach each package through one qualified name.** A package with one cohesive API re-exports it, so callers write `transform.averages(...)` or `port.Records`; a package of independent peers (adapters, `typer` modules) is reached module by module, `noaa.fetch_records`.

**A re-export shadows its module.** Re-exporting `count` from `transform/count.py` binds `transform.count` to the function, so the module — and its private helpers, for a test — is no longer reachable by that name.
In `operate` accept it, as above; elsewhere name the module for the shape it holds (`sequence.py` re-exporting `count`), which also keeps it from holding just one function.

### Declare a port

**Where two calls must come from the same place, make the port a `Protocol` and pass the adapter module to satisfy it.**
The test is whether the calls are **tied** — whether the answer to one decides who answers the next: a registry that lists stations and then fetches one of them.
Pass `{"noaa": noaa}`, not `Source(list=noaa.list_stations, fetch=other.fetch)` — a record of callables type-checks as a chimera of two sources, where a module cannot be mixed with itself.
`pyright` accepts a module as satisfying a protocol, so nothing needs to be a class or inherit anything.

- **Know the cost.** PyCharm's checker and some others reject a module as a protocol, leaving a warning nothing clears; a port declaring `__call__`, or a callable alias, is satisfied by a plain function in every checker.
- **A shared library is not a tie.** A client answering three unrelated questions is one import and three ports; bundling them forces every test fake to implement all three.
Count the ties, not the imports — one adapter module still satisfies all three ports.
- **A protocol's member name is the contract**, so every adapter spells it the same; put what distinguishes implementations (cost, source) in the module name.
- **An adapter whose every call needs one deployment value is a frozen dataclass holding it**, built by the composition root — `parquet.Store(settings.data_dir)` — since a module can't be bound to a value; an adapter with no such state stays a module.

**A port's parameters are the domain's values, not the computation's container.**
A caller should *state* a request — `fetch(stations, *, end, start)` — not assemble one; typing a parameter `polars.DataFrame` makes every adapter and fake speak the frame library.
An axis of the answer, such as a timeframe, belongs as a column of what comes back, not a frame going in.
The tell is a signature that no longer reads as a sentence about the problem.

**Split the port the moment its halves differ** — one adapter can only answer half of it, or a consumer needs only half.
A source answering any query can't enumerate what it offers; a store is written by the nightly and only read by the API and the dashboard, so given a write port and a read port (`store-data`) those two take the read port and a stray write is a type error.
Forced to satisfy the whole port, the adapter returns an empty frame, `None` or `NotImplementedError` — a lie that gets consumed, as when an empty catalogue concatenates into the real one and reads as "offers none".
Two ports let the composition root hand each operation only what it needs, and the type checker enforces the difference.

**An open source is a fallback, not a member of the set.** An adapter answering for any input either claims every name before the real sources are asked, or is consulted last anyway.
Make the order explicit: resolve against sources that state their names, and fall back to the open one only where none claimed it — which also makes it the only one able to call a name unknown.

**Route on a name the source states, not a position.** Where the core picks among adapters at runtime, carry the adapter's key in the data; an index into whatever sequence a driver built means nothing outside that call and can't be type-checked.

### Write an adapter

**An adapter checks every return against a declared schema** — the same columns and types on a full response, an empty one, and absent values alike.
Every source satisfying one port maps its fields into the port's schema (`port.RECORDS`), so one scan reads them all and the core never branches on who sent a row; a port one adapter satisfies keeps the schema as that adapter's module constant:

```python
RECORDS = polars.Schema({"item": polars.String, "value": polars.Float64})
```

`match_to_schema` raises `SchemaError` on a missing column or a wrong dtype and casts nothing wider than `Float32` to `Float64`, so the parse builds the frame with `schema=port.RECORDS` and `.match_to_schema(port.RECORDS)` at the return is the check, on a `LazyFrame` too; it is marked unstable in `polars` 2.1, so pin it with a dependency test (see `write-tests`).
Normalise the library's quirks (`None` for a bad key, columns that vary with row count) once at the boundary, so nothing downstream branches on them; a branch on the upstream's shape past the adapter means it didn't finish its job.

**An adapter returns what it got and writes nothing.** A fetch's unit of work is one source for one day, but it asks for many items, so its port returns a record of all four things the night needs, and the store's write port (`store-data`) writes them where they belong, which is why the fetch adapter never sees the data directory and a test reads its result as values:

```python
@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Fetched:
    """What one source sent for one day, as it arrived."""

    failed: tuple[str, ...]
    raw: tuple[bytes, ...]
    records: polars.DataFrame
    rejected: polars.DataFrame
```

`records` is matched to `port.RECORDS`, `rejected` holds `store-data`'s quarantine row (the raw record as text and its `reason`), `raw` is the bytes of each page as sent, and `failed` names the items that answered nothing usable.

**Fail an item, not the source.** An item that 404s, exhausts its retries or won't parse goes into `rejected` with its reason and its name into `failed`, and the items that arrived go into `records`, so one dead item costs a count in the manifest, not the night; a source whose every item failed **raises**, since storing an empty partition would make an outage read as a quiet day.
An empty answer is different from no answer: an item the source answers with nothing normalises into the declared empty shape, and a day on which every item did so is a stored empty partition with `rows=0` (`store-data`), because that is what the source said.

**Split getting from making sense of.** Give retrieval and parsing a function each and let the port's function compose them: `_parse(get(_url(item, day)))` per item, with `get` the paced getter the composition root built (below).
Retrieval is a few lines that never change; the parse is where the source's quirks accumulate, and kept separate it takes a saved response in a test with no stubbed fetch.

**Declare the columns from the source, not today's caller.** Carry every field the source publishes that the domain has a name for — dropping a column later is one line in the core, widening it means revisiting every adapter and test — but not fields the domain can't name.

**Absorb the source's changes at the edge.** A field the source adds that the domain can't name is logged once per run and dropped, not carried in case; a row that won't parse goes into `rejected` with its reason, never silently dropped, so the rows returned plus the rows quarantined equal the rows the source sent; a batch where rows arrived but none validated raises, since an empty frame says "nothing happened" when the truth is that the source changed shape (a batch with no rows at all is the empty answer above).
The core's own rules take the same shape: a domain validation returns `(valid, rejected)` frames and the operation hands both rejections to the store, and a row the source restated is deduplicated in the core, counted and logged — never in the adapter, whose conservation count would then stop holding.

**Return the narrowest type callers use.** Returning `httpx.Response` makes that library your internal API: callers reach for `.headers`, and swapping the library touches them all.
Return the text, rows or values, and a test fake becomes a function instead of a mock of someone else's class.

**Close the seam on every library the adapter uses.** A response that arrives and won't parse is the same event to the caller as one that never arrived, so catch the parser's exceptions at the same seam as the client's.
Ask what escapes when the service answers `200` with the wrong content — a login page, an error document — and if the answer names a third-party exception, the seam is open.

**Don't refilter what the core already rejects.** A filter in the adapter that duplicates a core rule is a second home for one judgement, and they drift; the tell is an adapter branch asking whether the filtering column is even present.
Filter at the edge only on what the source states and the value can't show.

**Move pure frame operations into the core.** A frame in, a frame out with no IO belongs in `transform`, whichever adapter first needed it; written generically ("take this column as the key"), it is shared and tested once rather than reimplemented per adapter.
The adapter keeps the *decision* — that this source spells a key its own way is knowledge about the source.
A `try` wrapped round the chain hides the pure part by making the reshape read as IO; lift the handling into a decorator and the frame-in, frame-out steps show.

Purity is a proxy, though: columns computed only for a renderer are presentation and stay with the driver (see `write-entry-points`, Driver shell).

**Share one reader per wire format**, with each adapter passing only what differs (columns, header rows to skip).
Wait for the second caller, and count what's really shared — where the library reads the format natively, two adapters may share one line, not worth a module.

**Give a convention several sources share its own edge member**, named for the convention (an identifier scheme, a country-code prefix), holding the rule and its table.
The core still mustn't know it exists, and it isn't a source, so it stays out of the mapping of adapters a driver can fetch from.

**Call services you don't own through one `httpx.Client`, sync as `write-python`'s Sync and async says, with a timeout, a user agent and the key in a header, paced by `pyrate-limiter` and retried by `tenacity`.** `httpx_.py` holds two builders: the client the composition root opens once per run and closes, and the getter each source module composes with its parse:

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

- **The composition root builds one client per run and passes it in** — `with httpx_.build_client(key, timeout=...) as client:` — binding the key from settings as it does (see Configuration); a `functools.cache`d module-level client has no owner to close it and no seam for a test transport.
`timeout` and `rates` are the source's constants from its package YAML, not literals here, so a second source over the same module states its own.
- **`transport` and `sleep` are the test seams** (`write-tests`): `httpx.MockTransport` answers in-process and a spy `sleep` records what the retry would have waited, so "backs off three times" runs in milliseconds.
`pyrate-limiter` takes no sleep of its own, so a pacing test patches its module's, the one patch the seam rule allows (`write-tests`' Python reference).
- **Send your own user agent**: a library's default gets refused unevenly by whatever fronts the service, so the same code works on two hosts and 403s on a third.
`importlib.metadata.version` names the tool and release; a service that accepts only a browser string is a fact found by trying it, not a default.
- **The key goes in a header, never the query string**, which every proxy, access log and shared link records.
- **Pace every window the service states.** The source's YAML lists one `Rate` per window — `Rate(2, Duration.SECOND)`, `Rate(5000, Duration.DAY)` — and `Limiter` takes the list (hand-rolled pacing is `setup-python`'s Libraries).
The day's cap is shared by every process that runs that day — the nightly, a backfill, a manual `fetch` — and a limiter counts only its own, so the composition root also passes `budget`, the day's limit less the `requests` the manifest records for today (`store-data`), and the getter raises `QuotaError` past it.
`try_acquire(..., timeout=60)` caps a wait at a minute, so the limiter's own day window refuses rather than sleeping until it rolls over; either refusal fails the item and every one after it without asking, since each would get the same answer.
`Limiter` (`pyrate-limiter` 4.5.1) rejects a list whose limits don't rise with the interval, so the list holds the windows as the service states them, never a day's limit cut below a shorter window's.
- **`tenacity` retries** only the outcomes the predicate names — a dropped connection or timeout (`httpx.TransportError`), a `429` or a `5xx` — honouring `Retry-After`, with `reraise=True` so the caller sees the real exception; a `4xx` is your bug and retrying it only hides which request was wrong (see `write-python` on classifying outcomes).
Pacing sits inside the attempt, so a retry takes a slot too.
- **Page to exhaustion and assert the count**: follow the next-page link until the service sends none, then compare the rows against the total the first page states, since a loop stopping at a fixed page count caps the data silently (see `write-tests`).

**Recognise a publisher's unstated terms**, since all three look like your bug and none appears in a test:

- **A burst is throttled, not refused**: after enough requests the service answers `200` with an HTML page instead of the file.
The tell is a failure that follows the request count; retry the same call after a pause.
- **A rate is stated somewhere you haven't read**: a `Crawl-delay` in `robots.txt`, or a `429` past an API's per-minute cap.
Back off long enough to outlast the window; pace a walk you chose (paging through results) and leave a single requested fetch alone.
- **Some documents need cookies first**: the first request redirects to a consent page whose cookies the second needs.
Give the HTTP module an optional page to visit first, beside the timeout and user agent.

## Configuration

Configuration is input crossing the boundary, so it takes the same path as any IO.

- **Read and validate at the edge** into typed values.
- **Inject inward.** An operation takes the values it needs as arguments, never a global `Settings` or `os.environ` — reading ambient config is IO.
- **Wire it at the composition root** and inject it beside the adapters; `write-entry-points` has when to validate, where the `.env` is found and when one value outgrows a function.
- **A secret is bound at the composition root, never read by an adapter or carried by a port.** The root reads settings once and binds the key into the adapter as it builds it — `httpx_.build_client(settings.api_key.get_secret_value(), ...)`, then `functools.partial(noaa.fetch_records, get=get)` to make the port's callable — so the port's signature stays the domain's and an adapter test needs no environment.
An adapter reading `os.environ` works on the laptop and fails under a scheduler, whose environment is not the shell's.

**A value has one of three homes, by who changes it:**

- **Settings** — per-deployment values and every secret, which differ between the laptop and the server: the data directory, the API key.
`pydantic-settings` reads them from the environment and a `.env` (see `write-entry-points`); a secret is never committed (see `use-git`).
- **Package YAML in `data/adapt/<source>.yaml`** — per-source constants the code was written against: the base URL, the rates, the page size, the timeout, a field map, and `tolerance`, the number of failed items a night absorbs before the source counts as partial (default 0; `run-unattended`, Report the outcome).
Changing one is a code change and ships with the package; the source module reads its own file through `importlib.resources` into a frozen dataclass (`noaa.read_constants()`), and the root hands the values to the builders.
- **A user-editable CSV in the app's data directory** (`items.csv`, see `store-data`) — a list the user maintains between runs: the items to follow, as `source,item,active`, where an inactive row is skipped, so pausing an item keeps its history and its line.
In package data it would force a reinstall per edit, and a setting can't hold a table.

The tell for the wrong home is a reinstall to add a row, a key in a committed file, or a rate in a `Settings` field that no deployment ever changes.

## Logging

Logging is output, configured at the edge but carried by convention rather than a port.

- **Configure once, at the composition root** — `write-entry-points` has the handler setup.
A library or core module calling `logging.basicConfig` hijacks its host; a module logger in the core costs it nothing, since with no handler installed a record vanishes.
- **Configuring the root adopts every dependency's narration.** A library logging failures your adapter already handled now writes them to standard error above your one line.
Where that happens, set that library's logger level at the composition root, by name — adopting its records is then a decision; `httpx` and `httpcore` narrate every request at INFO, so the root sets both to WARNING.
- **The edge narrates; the core stays quiet.** Log at the edge; the core returns its results and is pinned by tests.
- **One level per event**: a request is DEBUG, an adapter call INFO, a failure caught and handled (a rejected row, a failed item) WARNING, a failed source ERROR.
A level picked per line makes `--log-level INFO` show a different story in each module; `write-entry-points` sets the level an interactive and a scheduled command run at.

## Data

Load runtime assets — SQL files, templates, reference tables — through `importlib.resources`, never a path built from `__file__`.
Keep them in one `data/` directory **mirroring the code layers**, so each path names its owner:

```text
mypackage/
  code/
  data/
    adapt/
      orders.sql
    drive/
      report.html
    transform/
      regions.csv
```

- `data/adapt/` holds what an adapter runs or reads about the outside world (queries, where each source publishes).
- `data/drive/` holds templates and static files a driver renders.
- `data/transform/` holds reference data the core computes over — loaded by the edge and passed in, since reading a file is IO.

**Reference data goes in `data/` once it is a table someone will correct** — rows the code looks up, a station's region or a source's field names — since a file lets someone see all of it, diff one row and fix it without opening a module, and six rows today is thirty next year.
A closed set the code *branches on* (three scenarios, a handful of modes) is an `enum.StrEnum` or a dict literal in `transform` (see `write-python`): a file escapes the type checker, so a misspelt member is found at runtime instead of by `pyright`.

- **Normalise it**: a prefix every row repeats (a base URL) is one value, held once.
- **A translation between your vocabulary and a library's is a table too** — your word against their spelling — so it goes in `data/adapt/`, keeping the library's spelling from leaking into output.
- **A lookup's table is data, including method names it selects.** A name in a file escapes the type checker, so add one test asserting every name in the table resolves.

**Use CSV only for a genuine table, YAML or TOML for everything else.** A table has the same fields on every row and enough rows for a header to pay off.
Configuration sets scalars beside collections and nests, which CSV can't hold — the tell is a value that belongs with the data (a shared base URL) ending up in code:

```yaml
base-url: https://data.example.com/stations/
stations:
  LHR: heathrow.csv
  MAN: manchester.csv
```

Load YAML with `yaml.safe_load` (never `yaml.load`, which builds arbitrary objects) and TOML with `tomllib`, which reads and cannot write — no cost for a file only read.
YAML is the default for nested per-source constants; TOML where a tool already reads the file or the user edits it beside `pyproject.toml`.
Both take comments, so the reason for a row survives beside it.

**Package data lives inside the package** (`src/mypackage/data/`), since only the package under `src/` ships; a repo-root `data/` beside `src/` and `tests/` is for data deliberately kept out of the wheel, and the runtime data directory the app writes is `store-data`'s.
`uv_build` ships every file under the package, non-`.py` included.
**An app with no runtime assets has no `data/`** — don't scaffold an empty tree.

```python
from importlib import resources

query = resources.files("mypackage").joinpath("data/adapt/orders.sql").read_text()
```

## Tests

Tests live in `tests/`, never beside the source:

```text
tests/
  data/
  pytest_/
    __init__.py
    given.py
    reference.py
    then.py
    when.py
  suite/
    mypackage/
    packages/
```

- **`data/`** — files the tests load, a recorded response under `data/<source>/` (see `write-tests`); never shipped.
- **`pytest_/`** — imported helpers, a package named for its coupling to `pytest`: fixtures in `given.py`, assertions in `then.py`, named actions in `when.py`; tests import `from pytest_ import then`.
- **`suite/`** — the cases: your code mirrored in `suite/mypackage/`, dependency-behaviour tests in `suite/packages/`.
It is not a package: `--import-mode importlib` collects files by path, so same-named test files in different directories coexist.

`setup-python`'s `pytest` settings serve this layout (`testpaths`, `pythonpath = ["tests"]`, `-p pytest_.given`); scaffold `given.py` up front, since `-p` fails without it.
How to write the tests is `write-tests`.
