# Write tests in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python with `pytest`.
Installing `pytest` lives in `setup-python`; the `tests/` layout in `structure-python`.

## Pick a layout

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
      test_core.py
    packages/
      test_httpx.py
```

`structure-python` owns this tree and the `pytest` settings that serve it; what follows is only what writing the tests adds to it.

- `reference.py` is the addition to the `pytest_` package — the oracle a property test agrees with (see `SKILL.md`), a starting state like any other and so reached through a fixture.
- `-p` must name the module the fixtures are *defined* in, `pytest_.given`; `-p pytest_` loads the empty `__init__` and registers nothing.
The zero-config alternative is a `conftest.py`, which `pytest` auto-discovers — and the `pytest_plugins` variable works only there, never in `pyproject.toml`.
- `pythonpath` only applies while `pytest` runs, so static tools resolve `from pytest_ import then` their own way — `pyright` finds it, but an IDE like PyCharm needs `tests/` marked as a source root, an uncommitted setting that can't live in `pyproject.toml`.

## Tests are code

- Tests obey `write-python` in full: docstring and annotate every test — return `-> None`, and type every fixture parameter (`tmp_path: pathlib.Path`, `capsys: pytest.CaptureFixture[str]`).
There is no `per-file-ignores` exemption for `tests/`.
- Fixture docstrings are imperative too (`ruff`'s `D401`): "Load the sample dataset", not "The sample dataset".

## Given, when, then

The three beats become the `pytest_` package's `given`, `when` and `then` modules (above): fixtures, action helpers, and custom assertions.
Supply the *given* through fixtures:

- Take each *given* as a `@pytest.fixture` argument; the fixture names and builds the scenario so the body doesn't set it up inline.
- Put shared fixtures in the `pytest_` package's `given.py`, registered as a plugin with `addopts = "-p pytest_.given"` (see Pick a layout).
- Use the narrowest correct **scope**: per-function (the default) keeps tests independent; widen to `module`/`session` only for expensive, read-only setup.
- Build files under the `tmp_path` fixture; never read or write the repo tree or a real home directory.
- Inject a fake at the seam you designed; reach for `monkeypatch` or `pytest-mock` only at a genuine external boundary you can't inject.

A fixture sources each input, and — harder — each expected value:

- A canonical dataset → a file under `tests/data/` a fixture loads (`polars.scan_csv(path, try_parse_dates=True)`).
- A tailored input → a fixture returning a builder function, or a fixture derived from another and narrowed.
- Expected values → a fixture that derives them in plain Python (not by re-running the pipeline), passed into a `then` assertion; where that would just reimplement the code, assert invariants instead (`then.conserves`, `then.column_sorted`).

The *when* helpers name compound actions where they earn it; the *then* helpers are the custom assertions below.

## Many inputs

For independent scalar cases — not for splitting one whole-frame operation into a case per row (assert that whole under Assertions) — parametrize:

```python
@pytest.mark.parametrize(
    ("quantity", "unit_price", "expected"),
    [(2, 10.0, 20.0), (0, 10.0, 0.0), (3, 4.5, 13.5)],
)
def test_when_revenue_then_quantity_times_price(
    quantity: int, unit_price: float, expected: float
) -> None:
    """Revenue is quantity times unit price."""
    assert revenue(quantity, unit_price) == expected
```

Give cases `ids` when the values don't read clearly in the output.

For a property that should hold across an input space, let `hypothesis` generate and shrink the inputs:

```python
@hypothesis.given(xs=hypothesis.strategies.lists(hypothesis.strategies.integers()))
def test_when_sorted_twice_then_unchanged(xs: list[int]) -> None:
    """Sorting an already-sorted list changes nothing."""
    assert sorted(sorted(xs)) == sorted(xs)
```

Bind the strategy to a module-level name when several properties share it, rather than repeating the `@hypothesis.given` argument, and set `@hypothesis.settings(deadline=None)` for anything doing real work per example.

Where the property only means something once the input reaches a particular state, **build the state into the strategy and then check it arrives**.
Draw the increments and accumulate them (`itertools.accumulate` over a drifting step) so runs and trends actually occur, since independent draws almost never produce one.
Then run a throwaway loop over a few hundred generated inputs counting how many land in each state you care about, and only keep the property once that count is high.
A `hypothesis.event(...)` call in the test body records the same thing in the run statistics if you would rather keep the check.

## Assertions

Prefer a `then_` custom assertion to a bare `assert` in the test body — even for a simple equality.
Collect them in the `pytest_` package's `then` module, imported as `from pytest_ import then`, so every test reads the same way and each check is defined once:

```python
# tests/pytest_/then.py
def equals(actual: object, *, expected: object) -> None:
    """Assert two values are equal."""
    assert actual == expected, f"expected {expected!r}, got {actual!r}"


def column_equals(
    frame: polars.DataFrame, *, column: str, values: collections.abc.Sequence[object]
) -> None:
    """Assert the frame's column holds exactly these values, in order."""
    equals(frame.get_column(column).to_list(), expected=list(values))
```

A test body then reads `then.equals(code, expected=0)` or `then.column_equals(priced, column="revenue", values=expected_revenue)`.
Naming the expected side is what stops the classic transposition, where a swapped pair still passes but reports the failure backwards.

- Give each helper a failure message, since `pytest` only rewrites asserts in test modules, not an imported one (or call `pytest.register_assert_rewrite("pytest_.then")`).
- Assert an expected exception with `with pytest.raises(SomeError):`, checking the type or message.
- Compare floats with `pytest.approx`, never `==`.

Assert a dataframe transform on the **whole frame** in one test, with the `then` assertions above and the expected values from a fixture — never a literal.
Here `expected_revenue` is a fixture that derives `quantity * unit_price` from the raw data in plain Python:

```python
def test_when_add_revenue_then_revenue_is_quantity_times_price(
    sales: polars.LazyFrame, expected_revenue: list[float]
) -> None:
    """Revenue is quantity times unit price for every row."""
    priced = pipeline.map_add_revenue(sales).collect()
    then.column_equals(priced, column="revenue", values=expected_revenue)
```

Where deriving the expected would just reimplement the code — a group-by, a ranking — assert an invariant instead (`then.conserves`, `then.column_sorted`).
For an exact whole-frame match including dtypes, use `polars.testing.assert_frame_equal(result, expected)` — which needs its own `import polars.testing`, since importing `polars` alone does not bind the submodule (see `write-python`).

## Dependency tests

Pin a network-backed dependency through `httpx.MockTransport`, which answers from a handler you supply while leaving status handling, decoding and redirects to `httpx` itself:

```python
def test_when_raise_for_status_then_a_not_found_raises() -> None:
    """A 404 raises rather than handing back an empty body."""

    def refuse(request: httpx.Request) -> httpx.Response:
        """Answer every request the way a missing document does."""
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(refuse))
    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.test/holdings.csv").raise_for_status()
```

Keep the recorded response in `tests/data/` and load it through a fixture, the same as any other given.
`respx` is the alternative where you want to assert on the request as well, but the transport is enough to pin behaviour and carries no extra dependency.

## Coverage and speed

- `pytest-cov` reports coverage (`uv run pytest --cov`).
- Mark slow or external tests with a custom marker (`@pytest.mark.slow`) so the default run stays quick.

## Logging

To show logs from both the code under test and the tests during a run, `rich`-rendered to match the application's own handler, put a `RichHandler` on the root logger for the session and switch capture to `tee-sys`.
Nothing goes in the test files — `pytest` attaches to the root logger, so any `logging.getLogger(__name__)` call flows through.

Configure it in the `pytest_` package.
A session fixture wires the handler; a `RichHandler` subclass opens each test's first log on a fresh line so it doesn't jam `pytest`'s progress line, reset per test by an autouse fixture:

```python
# tests/pytest_/given.py
class _TestRichHandler(rich.logging.RichHandler):
    """Rich handler that opens each test's first log line on a fresh row."""

    def __init__(self) -> None:
        super().__init__(rich_tracebacks=True)
        self.new_test = True

    def emit(self, record: logging.LogRecord) -> None:
        """Break onto a new line before a test's first record, then render it."""
        if self.new_test:
            self.console.print()
            self.new_test = False
        super().emit(record)


_log_handler = _TestRichHandler()


@pytest.fixture(autouse=True)
def _reset_log_newline() -> None:
    """Arm a fresh leading newline for each test's logs."""
    _log_handler.new_test = True


@pytest.fixture(scope="session", autouse=True)
def _rich_logging() -> None:
    """Route session logs through Rich, matching the app's handler."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[_log_handler],
        force=True,
    )
```

```toml
[tool.pytest.ini_options]
addopts = "... --capture tee-sys"
```

- Use `--capture tee-sys`, not `--capture no`: it shows output live *and* keeps capturing, so `capsys` assertions and the captured-output report on a failing test still work.
Never `log_cli` — `pytest`'s live logging installs its own handler that bypasses the `RichHandler`.
- The cost: `tee-sys` streams **all** output live, so a chatty suite is noisier than the default capture-and-hide.
A test that consumes its own output through `capsys` won't display its logs — correct, since it is asserting on that output.

If you don't need `rich` specifically, the zero-code alternative is `pytest`'s native live logging (`log_cli = true` with `log_cli_level` and `log_cli_format`): logs stream live in `pytest`'s own format with capture left on.

## Run

`pytest` is the entry point — a test file never has an `if __name__ == "__main__"`.
Run the whole suite, or select a slice by directory, name, or marker:

```bash
uv run pytest
uv run pytest tests/suite/packages
uv run pytest -k revenue
uv run pytest -m slow
```

- `uv run pytest` runs everything under `testpaths`.
- `uv run pytest tests/suite/packages` runs one directory.
- `uv run pytest -k revenue` runs tests whose name matches.
- `uv run pytest -m slow` runs tests carrying a marker.
