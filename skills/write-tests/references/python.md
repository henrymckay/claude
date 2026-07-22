# Python testing idioms (pytest)

The language-agnostic principles are in `SKILL.md`; this is how they land in Python with `pytest`.
Installing pytest and the `tests/` layout live in `setup-python`.

## Tests are code

- Tests obey `write-python` in full: docstring and annotate every test — return `-> None`, and type every fixture parameter (`tmp_path: pathlib.Path`, `capsys: pytest.CaptureFixture[str]`). There is no `per-file-ignores` exemption for `tests/`.
- Fixture docstrings are imperative too (ruff `D401`): "Load the sample dataset", not "The sample dataset".

## Given via fixtures

- Supply the *given* as `@pytest.fixture` arguments; the fixture names and builds the scenario so the body doesn't set it up inline.
- Put fixtures shared across files in a `conftest.py`; pytest discovers it automatically.
- Use the narrowest correct **scope**: per-function (the default) keeps tests independent; widen to `module`/`session` only for expensive, read-only setup.
- Build files under the `tmp_path` fixture; never read or write the repo tree or a real home directory.

## Table-driven: parametrize

For independent scalar cases — not for splitting one whole-frame operation into a case per row (assert that whole, below).

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

## Whole-frame assertions

Assert a dataframe transform on the whole frame in one test, with the `then` assertions above and the expected values from a fixture — never a literal. Here `expected_revenue` is a fixture that derives `quantity * unit_price` from the raw data in plain Python:

```python
def test_when_add_revenue_then_revenue_is_quantity_times_price(
    sales: polars.LazyFrame, expected_revenue: list[float]
) -> None:
    """Revenue is quantity times unit price for every row."""
    priced = pipeline.map_add_revenue(sales).collect()

    then.column_equals(priced, "revenue", expected_revenue)
```

Where deriving the expected would just reimplement the code — a group-by, a ranking — assert an invariant instead (`then.conserves`, `then.column_sorted`).

For an exact whole-frame match including dtypes, use `polars.testing.assert_frame_equal(result, expected)`.

## Property-based: Hypothesis

```python
@hypothesis.given(xs=hypothesis.strategies.lists(hypothesis.strategies.integers()))
def test_when_sorted_twice_then_unchanged(xs: list[int]) -> None:
    """Sorting an already-sorted list changes nothing."""
    assert sorted(sorted(xs)) == sorted(xs)
```

## Where test data lives

- A canonical dataset → a file under `tests/data/` a fixture loads (`polars.scan_csv(path, try_parse_dates=True)`), not a literal in the test body.
- A tailored input → a fixture returning a builder function, or a fixture derived from another and narrowed.
- A whole-collection operation → one representative fixture asserted once, not a `parametrize` case per row.
- Expected values → a fixture that derives them from the raw data in plain Python (independent of the pipeline), passed into a `then` assertion. Where that would just reimplement the code, assert invariants instead (`then.conserves`, `then.column_sorted`).

## Assertions

Prefer a `then_` custom assertion to a bare `assert` in the test body — even for a simple equality. Collect them in a shared module imported as `then`, so every test reads the same way and each check is defined once:

```python
# tests/then.py
def equals(actual: object, expected: object) -> None:
    """Assert two values are equal."""
    assert actual == expected, f"expected {expected!r}, got {actual!r}"


def column_equals(
    frame: polars.DataFrame, column: str, values: collections.abc.Sequence[object]
) -> None:
    """Assert the frame's column holds exactly these values, in order."""
    equals(frame.get_column(column).to_list(), list(values))
```

A test body then reads `then.equals(code, 0)` or `then.column_equals(priced, "revenue", expected_revenue)`.

- Put `pythonpath = ["tests"]` in the pytest config so `import then` resolves under `--import-mode=importlib`.
- Give each helper a failure message (or call `pytest.register_assert_rewrite("then")` in `conftest.py`), since pytest only rewrites asserts in test modules, not an imported helper.
- Assert an expected exception with `with pytest.raises(SomeError):`, checking the type or message.
- Compare floats with `pytest.approx`, never `==`.

## Mocking

Prefer real objects and dependency injection.
Reach for `monkeypatch` or `pytest-mock` only at a genuine external boundary you can't inject.

## Coverage and markers

- `pytest-cov` reports coverage (`uv run pytest --cov`).
- Mark slow or external tests with a custom marker (`@pytest.mark.slow`) so the default run stays quick.

## Layout and import mode

```text
tests/
  conftest.py
  mypackage/
    test_core.py
  packages/
    test_httpx.py
```

- Your code mirrored under `tests/<package>/`; dependency-behaviour tests under `tests/packages/`.
- Set `--import-mode=importlib` (see `setup-python`) so nested folders and a test directory sharing the package's name don't confuse imports.

## Running

```bash
uv run pytest                      # everything under testpaths
uv run pytest tests/mypackage      # one directory
uv run pytest -k revenue           # tests whose name matches
uv run pytest -m slow              # tests carrying a marker
```

There is no `if __name__ == "__main__"` in a test file — pytest is the entry point.
