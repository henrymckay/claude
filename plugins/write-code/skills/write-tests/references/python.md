# Write tests in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python with `pytest`.

## Pick a layout

`structure-python` owns the `tests/` tree and `setup-python` the `pytest` settings that serve it; writing the tests adds only this:

- `pytest_/reference.py` holds the oracle a property test agrees with, imported by the test (see Many inputs).
- `-p` must name the module the fixtures are *defined* in, `pytest_.given`; `-p pytest_` loads the empty `__init__` and registers nothing.
The zero-config alternative is a `conftest.py`, which `pytest` auto-discovers — and the `pytest_plugins` variable works only there, never in `pyproject.toml`.
- `pythonpath` only applies while `pytest` runs, so static tools resolve `from pytest_ import then` their own way — `pyright` finds it, but an IDE like PyCharm needs `tests/` marked as a source root, an uncommitted setting that can't live in `pyproject.toml`.

## Tests are code

Type every fixture parameter (`tmp_path: pathlib.Path`, `capsys: pytest.CaptureFixture[str]`), so a misnamed fixture fails type-checking before it fails at collection.
Test async code through the `anyio` pytest plugin, `setup-python`'s pick, not `pytest-asyncio`.

## Given, when, then

The three beats become the `pytest_` package's `given`, `when` and `then` modules: fixtures, action helpers, and custom assertions.

Wrong — the given is built in the body, so the scenario has no name:

```python
def test_when_keep_valid_then_non_positive_rows_dropped() -> None:
    raw_sales = polars.DataFrame({"quantity": [2, 0, -1, 5]})
    kept = keep_valid(raw_sales)
    assert kept.get_column("quantity").to_list() == [2, 5]
```

Right — the given is a fixture parameter and the then a named, reusable claim:

```python
def test_when_keep_valid_then_non_positive_rows_dropped(
    raw_sales: polars.DataFrame,
) -> None:
    kept = keep_valid(raw_sales)
    then.every_row_positive(kept, column="quantity")
```

Fixtures:

- Shared fixtures live in `given.py`, registered as Pick a layout says.
- Build files under `tmp_path`, with the app's data directory pointed at it as `store-data` says.
- At a boundary you can't inject, patch with `monkeypatch`; for the clock, `time-machine` freezes `datetime.now` and friends in C, where `monkeypatch` can only replace the module attribute the code happened to import.
- A canonical dataset is a file under `tests/data/` a fixture loads; a recorded response sits under `tests/data/<source>/` beside its recording script.
- A tailored input is a fixture returning a builder function, or a fixture derived from another and narrowed.
- Expected values come from a fixture that derives them in plain Python, passed into a `then` assertion.

## Many inputs

Parametrize independent scalar cases — never one whole-frame operation split into a case per row:

```python
@pytest.mark.parametrize(
    ("quantity", "unit_mass", "expected"),
    argvalues=[(2, 10.0, 20.0), (0, 10.0, 0.0), (3, 4.5, 13.5)],
)
def test_when_total_mass_then_quantity_times_unit_mass(
    quantity: int, unit_mass: float, expected: float
) -> None:
    assert total_mass(quantity, unit_mass) == expected
```

For a property that should hold across an input space, let `hypothesis` generate and shrink the inputs:

```python
import hypothesis
import hypothesis.strategies


@hypothesis.given(xs=hypothesis.strategies.lists(hypothesis.strategies.integers()))
def test_when_sorted_descending_then_reverse_of_ascending(xs: list[int]) -> None:
    assert sorted(xs, reverse=True) == sorted(xs)[::-1]
```

Bind the strategy to a module-level name when several properties share it, rather than repeating the `@hypothesis.given` argument, and set `@hypothesis.settings(deadline=None)` for anything doing real work per example.
A property test takes no function-scoped fixture: `hypothesis` runs the body once per example but the fixture once per test, and fails the run with `HealthCheck.function_scoped_fixture` rather than let the examples share state; import the oracle from `pytest_.reference`, and widen any fixture it needs to `module` scope.

To reach a state independent draws rarely produce, draw increments and accumulate them (`itertools.accumulate` over a drifting step), then count how many generated inputs reach the state — a throwaway loop, or `hypothesis.event(...)` in the test to keep the count in the run statistics.

## Assertions

The `then` assertions (see `SKILL.md`) live in the `pytest_` package's `then` module, imported as `from pytest_ import then`, and the package registers it for assert rewriting so a failure inside it shows `pytest`'s diff rather than a hand-written message:

```python
# tests/pytest_/__init__.py
import pytest

pytest.register_assert_rewrite("pytest_.then")
```

```python
# tests/pytest_/then.py
def column_equals(
    frame: polars.DataFrame, *, column: str, values: collections.abc.Sequence[object]
) -> None:
    """Assert the frame's column holds exactly these values, in order."""
    assert frame.get_column(column).to_list() == list(values)


def conserves(parts: polars.DataFrame, *, column: str, whole: polars.DataFrame) -> None:
    """Assert the parts' column sums to the whole's."""
    assert parts.get_column(column).sum() == whole.get_column(column).sum()


def every_row_positive(frame: polars.DataFrame, *, column: str) -> None:
    """Assert every value in the column is above zero."""
    assert frame.get_column(column).gt(0).all()
```

A test body then reads `then.column_equals(priced, column="revenue", values=expected_revenue)`, and the keyword `values=` names the expected side so a swapped pair reports the failure the right way round.
`pytest` rewrites asserts in test modules, `conftest.py` and plugins named by `-p` (so `pytest_.given`), but not in a sibling it merely imports; without the registration the `then` helpers fail with a bare `AssertionError`.

Assert a frame transform on the **whole frame**, with expected values from a fixture — here `expected_mass` restates the spec's rule, quantity times unit mass, in plain Python over the raw rows:

```python
def test_when_add_mass_then_mass_is_quantity_times_unit_mass(
    shipments: polars.LazyFrame, expected_mass: list[float]
) -> None:
    weighed = pipeline.map_add_mass(shipments).collect()
    then.column_equals(weighed, column="mass", values=expected_mass)
```

For an exact whole-frame match including dtypes, use `polars.testing.assert_frame_equal(result, expected)`, with its own `import polars.testing` (`write-python`, Imports).

## Dependency tests

Pin a network-backed dependency through `httpx.MockTransport`, which answers from a handler you supply while leaving status handling, decoding and redirects to `httpx` itself:

```python
@pytest.fixture
def missing_document() -> collections.abc.Iterator[httpx.Client]:
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(refuse)) as client:
        yield client


def test_when_raise_for_status_then_a_not_found_raises(
    missing_document: httpx.Client,
) -> None:
    with pytest.raises(httpx.HTTPStatusError):
        missing_document.get("https://example.test/report.csv").raise_for_status()
```

`respx` is the alternative where you want to assert on the request as well, but the transport is enough to pin behaviour and carries no extra dependency.

**Record the response with `tests/data/<source>/record.py`**, a PEP 723 script (see `setup-python`) that strips the key from the saved request and response and writes the file the fixture loads.

**Pace and retry through the adapter's seams** (`structure-python`'s `references/http.md` has the adapter):

```python
def build_client(
    api_key: str,
    *,
    timeout: float,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Client: ...


def build_get_document(
    client: httpx.Client,
    *,
    budget: int,
    rates: list[pyrate_limiter.Rate],
    sleep: collections.abc.Callable[[float], None] = time.sleep,
) -> collections.abc.Callable[[str], str]: ...
```

The test builds the client on an `httpx.MockTransport` whose handler answers from a sequence (a `503` with `Retry-After`, then the recorded `200`) and passes `sleep=waits.append`, then asserts the document came back and `waits == [3.0]`.
`pyrate-limiter` 4.5.1 sleeps through its own `pyrate_limiter.limiter.sleep`, so a pacing test adds `monkeypatch.setattr(pyrate_limiter.limiter, "sleep", paced.append)` and asserts on `paced`; the limiter advances as if it had slept, so five calls at two a second finish at once with three waits recorded.
A budget test passes `budget=2` and asserts the third call raises `QuotaError` with the transport's handler called twice.

**Drive a `typer` command through `typer.testing.CliRunner`**, invoking the role package's `app` with the arguments a user would type and asserting on `result.exit_code` and `result.stdout`; the composition root runs for real, with the store at `tmp_path` through the environment and the source on a `MockTransport`, so a CLI test proves the wiring, not only the operation.

## Coverage, speed and logs

- Mark slow or external tests `@pytest.mark.slow`, registered in `setup-python`'s `pytest` block.
- Leave `pytest`'s log capture to show a failing test's logs, with `--log-cli-level INFO` to stream them live; don't wire a `RichHandler` into the suite to match the application's output, since the fixture it needs is longer than any test and `tee-sys` then streams every test's output on every run.

## Run

Run through the project's runner, `uv run` under `setup-python`:

```bash
uv run pytest
uv run pytest tests/suite/packages
uv run pytest -k revenue
uv run pytest -m slow
```
