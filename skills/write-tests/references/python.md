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

```python
@pytest.mark.parametrize(
    ("quantity", "unit_price", "expected"),
    [(2, 10.0, 20.0), (0, 10.0, 0.0), (3, 4.5, 13.5)],
)
def test_revenue_multiplies_quantity_by_price(
    quantity: int, unit_price: float, expected: float
) -> None:
    """Revenue is quantity times unit price."""
    assert revenue(quantity, unit_price) == expected
```

Give cases `ids` when the values don't read clearly in the output.

## Property-based: Hypothesis

```python
@hypothesis.given(xs=hypothesis.strategies.lists(hypothesis.strategies.integers()))
def test_sort_is_idempotent(xs: list[int]) -> None:
    """Sorting an already-sorted list changes nothing."""
    assert sorted(sorted(xs)) == sorted(xs)
```

## Where test data lives

- Salient values → `@pytest.mark.parametrize`, building the smallest frame or object the code under test actually reads.
- A canonical dataset → a file under `tests/data/` that a fixture loads (`polars.scan_csv(path, try_parse_dates=True)`), not a literal in the test.
- A tailored input → a fixture that returns a builder function, or a fixture derived from another and narrowed.

## Assertions

- Use the plain `assert` statement; pytest rewrites it to show the operands, so `assert x == y` needs no message.
- Assert an expected exception with `with pytest.raises(SomeError):`, checking the type or message, not merely that something raised.
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
