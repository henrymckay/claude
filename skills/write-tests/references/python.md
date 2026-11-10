# Write tests in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python with `pytest`.
Installing `pytest` lives in `setup-python`; the `tests/` layout in `structure-python`.

## Pick a layout

`structure-python` owns the `tests/` tree and the `pytest` settings that serve it; writing the tests adds only this:

- `pytest_/reference.py` holds the oracle a property test agrees with (see `SKILL.md`), a starting state like any other and so reached through a fixture.
- `-p` must name the module the fixtures are *defined* in, `pytest_.given`; `-p pytest_` loads the empty `__init__` and registers nothing.
The zero-config alternative is a `conftest.py`, which `pytest` auto-discovers — and the `pytest_plugins` variable works only there, never in `pyproject.toml`.
- `pythonpath` only applies while `pytest` runs, so static tools resolve `from pytest_ import then` their own way — `pyright` finds it, but an IDE like PyCharm needs `tests/` marked as a source root, an uncommitted setting that can't live in `pyproject.toml`.

## Tests are code

- Annotate every test `-> None` and type every fixture parameter (`tmp_path: pathlib.Path`, `capsys: pytest.CaptureFixture[str]`).
- No docstrings on tests or fixtures: `setup-python` ignores the `D` rules under `tests/`, since the name is the claim.

## Given, when, then

The three beats become the `pytest_` package's `given`, `when` and `then` modules: fixtures, action helpers, and custom assertions.

```python
# Wrong: the given is built in the body, so the scenario has no name.
def test_when_keep_valid_then_non_positive_rows_dropped() -> None:
    raw_sales = polars.DataFrame({"quantity": [2, 0, -1, 5]})
    kept = keep_valid(raw_sales)
    assert kept.get_column("quantity").to_list() == [2, 5]


# Right: the given is a fixture parameter and the then a named, reusable claim.
def test_when_keep_valid_then_non_positive_rows_dropped(
    raw_sales: polars.DataFrame,
) -> None:
    kept = keep_valid(raw_sales)
    then.every_row_positive(kept, column="quantity")
```

Supply the *given* through fixtures:

- Take each *given* as a `@pytest.fixture` argument; the fixture names and builds the scenario so the body doesn't set it up inline.
- Put shared fixtures in `given.py`, registered with `addopts = "-p pytest_.given"` (see Pick a layout).
- Widen a fixture's `scope` to `"module"` or `"session"` for expensive read-only setup.
- Build files under the `tmp_path` fixture; never read or write the repo tree or a real home directory.
- At a boundary you can't inject, patch with `monkeypatch`; for the clock, `time-machine` freezes `datetime.now` and friends in C, where `monkeypatch` can only replace the module attribute the code happened to import.

A fixture sources each input, and — harder — each expected value:

- A canonical dataset → a file under `tests/data/` a fixture loads (`polars.scan_csv(path, try_parse_dates=True)`).
- A tailored input → a fixture returning a builder function, or a fixture derived from another and narrowed.
- Expected values → a fixture that derives them in plain Python (not by re-running the pipeline), passed into a `then` assertion; where that would just reimplement the code, assert invariants instead (`then.conserves`, `then.column_sorted`).

The *when* helpers name compound actions where they earn it; the *then* helpers are the custom assertions below.

## Many inputs

Parametrize independent scalar cases — never one whole-frame operation split into a case per row:

```python
@pytest.mark.parametrize(
    ("quantity", "unit_price", "expected"),
    [(2, 10.0, 20.0), (0, 10.0, 0.0), (3, 4.5, 13.5)],
)
def test_when_revenue_then_quantity_times_price(
    quantity: int, unit_price: float, expected: float
) -> None:
    assert revenue(quantity, unit_price) == expected
```

Give cases `ids` when the values don't read clearly in the output.

For a property that should hold across an input space, let `hypothesis` generate and shrink the inputs:

```python
@hypothesis.given(xs=hypothesis.strategies.lists(hypothesis.strategies.integers()))
def test_when_sorted_twice_then_unchanged(xs: list[int]) -> None:
    assert sorted(sorted(xs)) == sorted(xs)
```

Bind the strategy to a module-level name when several properties share it, rather than repeating the `@hypothesis.given` argument, and set `@hypothesis.settings(deadline=None)` for anything doing real work per example.
A property test takes no function-scoped fixture: `hypothesis` runs the body once per example but the fixture once per test, and fails the run with `HealthCheck.function_scoped_fixture` rather than let the examples share state; import the oracle from `pytest_.reference`, and widen any fixture it needs to `module` scope.

To reach a state independent draws rarely produce, draw increments and accumulate them (`itertools.accumulate` over a drifting step), then count how many generated inputs reach the state — a throwaway loop, or `hypothesis.event(...)` in the test to keep the count in the run statistics.

## Assertions

A bare `assert actual == expected` for an equality; a `then` assertion for a domain claim several tests share.
Collect those in the `pytest_` package's `then` module, imported as `from pytest_ import then`, and register it for assert rewriting so a failure inside it shows `pytest`'s diff rather than a hand-written message:

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


def conserves(parts: polars.DataFrame, *, whole: polars.DataFrame, column: str) -> None:
    """Assert the parts' column sums to the whole's."""
    assert parts.get_column(column).sum() == whole.get_column(column).sum()
```

A test body then reads `then.column_equals(priced, column="revenue", values=expected_revenue)`, and the keyword `values=` names the expected side so a swapped pair reports the failure the right way round.
`pytest` rewrites asserts in test modules, `conftest.py` and plugins named by `-p` (so `pytest_.given`), but not in a sibling it merely imports; without the registration the `then` helpers fail with a bare `AssertionError`.

Assert a frame transform on the **whole frame**, with expected values from a fixture — here `expected_revenue` derives `quantity * unit_price` from the raw data in plain Python:

```python
def test_when_add_revenue_then_revenue_is_quantity_times_price(
    sales: polars.LazyFrame, expected_revenue: list[float]
) -> None:
    priced = pipeline.map_add_revenue(sales).collect()
    then.column_equals(priced, column="revenue", values=expected_revenue)
```

For an exact whole-frame match including dtypes, use `polars.testing.assert_frame_equal(result, expected)` — which needs its own `import polars.testing`, since importing `polars` alone does not bind the submodule (see `write-python`).

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

Keep the recorded response in `tests/data/` and load it through a fixture, the same as any other given.
`respx` is the alternative where you want to assert on the request as well, but the transport is enough to pin behaviour and carries no extra dependency.

**Record it with `tests/data/record.py`**, a PEP 723 script (see `setup-python`) that calls the real source with the key from the environment, strips the key from the saved request and response, and writes the file the fixture loads; re-run it when the source changes shape, so the fixture is always something the source actually sent.

**Pace and retry through a seam.** The client builder takes `sleep: collections.abc.Callable[[float], None] = time.sleep`, passed on to the retry and rate-limit policy; the test passes a spy that records the waits, so a test of "backs off three times" runs in milliseconds.

## Coverage, speed and logs

- Mark slow or external tests `@pytest.mark.slow`; the marker is registered in `setup-python`'s `pytest` block, whose `--strict-markers` turns a misspelt marker into an error instead of a silently unselected test.
- Leave `pytest`'s log capture on: a failing test's report shows its logs, and `uv run pytest --log-cli-level INFO` streams them live for a debugging run.
Don't wire a `RichHandler` into the suite to match the application's output; the fixture it needs is longer than any test and `tee-sys` then streams every test's output on every run.

## Run

Run everything under `testpaths`, or a slice by directory, name (`-k`) or marker (`-m`):

```bash
uv run pytest
uv run pytest tests/suite/packages
uv run pytest -k revenue
uv run pytest -m slow
```
