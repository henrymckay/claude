---
name: write-tests
description: >-
  How to write and structure Python tests with pytest — the given-when-then
  shape, naming, fixtures over globals, parametrization, property-based testing
  with Hypothesis, testing the dependency behaviour you rely on, and the layout
  that separates the two. Use whenever writing, editing, or reviewing tests,
  adding coverage, or setting up a suite, even if the user just says "write a
  test", "add tests", "test this", or names pytest. Tests are code: they follow
  write-python in full (docstrings, typing, naming, imports); this skill adds the
  test-specific judgment on top. For installing pytest and the tests/ layout, see
  setup-python.
---

# Writing tests

A test is production code that happens to assert.
It follows every `write-python` convention — annotate every function, docstring every function, qualified imports, alphabetical ordering — and layers the testing-specific decisions below on top.
The runner is `pytest`; `setup-python` installs it and owns the `tests/` layout.

Good tests buy two things: confidence to change code, and a precise signal when it breaks.
Both come from testing *behaviour* through the public surface, keeping each test small and isolated, and naming it so a failure reads like a false claim about the system.

## Tests are code

- **Docstring and annotate every test**, same as any function — there is no `per-file-ignores` exemption for `tests/`.
  Annotate the return as `-> None` and type every fixture parameter (`tmp_path: pathlib.Path`, `capsys: pytest.CaptureFixture[str]`).
- **Make the docstring earn its line** — state the behaviour under test, not a restatement of the name.
- Factor shared construction into fixtures, or into small annotated, docstringed helpers.

## Given, when, then

Structure every test as **given / when / then** — the behavioural form of the four-phase test (setup, exercise, verify).

- **Given** — the starting state, supplied as **fixture arguments**. A fixture names and builds the scenario so the body doesn't set it up inline. (A trivial one-off input can still be built in the body.)
- **When** — the single call to the code under test.
- **Then** — the assertions on the outcome.

Keep the three beats visually distinct. When a *when* or *then* step is shared or reads better named, extract it into a `when_<action>` helper and a `then_<expectation>` custom assertion, so the body reads as a sentence:

```python
def test_keep_valid_drops_non_positive_rows(raw_sales: polars.LazyFrame) -> None:
    """Rows with a non-positive quantity or price are dropped."""
    kept = when_kept_valid(raw_sales)
    then_every_row_is_positive(kept)
```

A `then_` helper is the **custom assertion** pattern — it carries its own failure message and is reusable across tests.
Inline the assertions instead when the test is simple; don't extract for its own sake.

## Name the behaviour: when and then

The test name states the **when and then** — the action and its expected outcome — while the **given** lives in the fixture arguments, not the name.
In `test_keep_valid_drops_non_positive_rows`, the when is `keep_valid` and the then is `drops_non_positive_rows`; the input scenario is whichever fixture the test takes.
The name then reads as a sentence a failure would falsify, which is most of the diagnosis.
One when-and-then per test — if the name needs an "and", split it.

## Assert on behaviour, not implementation

Test the observable contract — return values, raised errors, visible side effects — through the public surface, never private internals.
Tests bound to implementation break on every refactor and stop being a safety net; tests bound to behaviour survive refactors and *are* the net.

Lean hardest on the **pure functional core** (see `be-functional`): it holds the logic and the bugs, and it is cheap to test because it is deterministic and needs no setup.
Keep the imperative shell thin so little is left that needs slow integration tests — the **humble object** pattern.

## Fixtures over globals

Shared setup or data belongs in a `@pytest.fixture`, never a module-level constant — `write-python` prefers a function over a global, and a fixture is that function plus scoping and composition.

- Put fixtures shared across files in a `conftest.py`; pytest discovers it automatically.
- Use the narrowest correct **scope**: per-function (the default) keeps tests independent; widen to `module`/`session` only for expensive, read-only setup.
- Build files under the `tmp_path` fixture; never read or write the repo tree or a real home directory.

## Parametrize tables of cases

Use `@pytest.mark.parametrize` to run one assertion over many inputs instead of a loop or copy-pasted tests.
Each case is reported and fails separately (a loop stops at the first failure), and adding a case is one line.

```python
@pytest.mark.parametrize(
    ("quantity", "price", "expected"),
    [(2, 10.0, 20.0), (0, 10.0, 0.0), (3, 4.5, 13.5)],
)
def test_revenue_multiplies_quantity_by_price(
    quantity: int, price: float, expected: float
) -> None:
    """Revenue is quantity times unit price."""
    assert revenue(quantity, price) == expected
```

Give cases `ids` when the values don't read clearly in the output.

## Property-based tests with Hypothesis

For a rule that should hold across a whole input space, let `hypothesis` generate inputs and shrink any failure to a minimal counterexample.
It is especially strong for numeric and algorithmic code, where example-based tests only spot-check.
Reach for it when you can state an **invariant**:

- Round-trips: `decode(encode(x)) == x`.
- Algebraic laws: commutativity, associativity, an identity element.
- Postconditions: the result is always sorted, within bounds, or the same length.
- Agreement with a slow, obviously-correct reference implementation.

```python
@hypothesis.given(xs=hypothesis.strategies.lists(hypothesis.strategies.integers()))
def test_sort_is_idempotent(xs: list[int]) -> None:
    """Sorting an already-sorted list changes nothing."""
    assert sorted(sorted(xs)) == sorted(xs)
```

## Test the packages you rely on

Write tests against the third-party behaviour your code depends on, kept separate from tests of your own code.
They are **not** exhaustive tests of the package — that's the maintainer's job — but a pinned record of the specific behaviour you rely on, doubling as executable documentation of *how* you use it and an early warning when an upgrade changes it.

- Assert only what your code assumes: that `polars.scan_csv(try_parse_dates=True)` yields a date dtype, that `group_by().agg(sum)` totals per group, that `collect_all` runs several plans together.
- A breaking change then fails on the assumption itself, not somewhere deep in your code on the next upgrade.
- One file per package under `tests/packages/`.

## Layout

`setup-python` owns the `tests/` tree. Tests of your code mirror the package under `tests/<package>/`; package-behaviour tests live under `tests/packages/`:

```text
tests/
  conftest.py
  sales_insights/
    test_cli.py
    test_pipeline.py
  packages/
    test_polars.py
```

Set `--import-mode=importlib` (see `setup-python`) so nested folders and a test directory sharing the package's name don't confuse imports.

## Isolation and determinism

- Tests must pass **in any order and in isolation** — no shared mutable state, no test depending on another.
- Never touch the real network, clock, or randomness. Inject them (the default-argument seams from `be-functional`) and pass fixed values, or seed the generator, so a run is reproducible.
- A flaky test is a broken test: fix or delete it, since one that cries wolf trains you to ignore the suite.

## Mock sparingly

Prefer real objects and dependency injection to mocks.
A mock asserts on *how* code calls its collaborators, coupling the test to implementation — the opposite of testing behaviour.
Fake at the seam you designed (pass a stub function or in-memory double), and reach for `monkeypatch` or `pytest-mock` only at a genuine external boundary you can't inject.
See the test-double taxonomy in `references/patterns.md`.

## Assertions

- Use the plain `assert` statement; pytest rewrites it to show the operands, so `assert x == y` needs no message.
- Assert an expected exception with `with pytest.raises(SomeError):`, checking the type or message, not merely that something raised.
- Compare floats with `pytest.approx`, never `==`.

## Coverage is a guide, not a target

Use `pytest-cov` to find untested paths, then read *which* branches are uncovered — an uncovered error path matters, a percentage does not.
Chasing a number produces assertion-free tests that execute code without checking it.

## Keep the suite fast

A fast suite gets run on every change; a slow one gets skipped, which is when regressions land.
Mark genuinely slow or external tests (`@pytest.mark.slow`) so the default run stays quick.

## Paradigms and patterns

Reach beyond example-based unit tests when the problem fits. The ones that shape this house style:

- **TDD** (red-green-refactor) — write the failing test first to drive design.
- **BDD / given-when-then** — the structure above.
- **Property-based** (Hypothesis) — invariants over generated inputs.
- **Characterization / approval tests** — pin current output to make a refactor safe.
- **Test doubles**, **custom assertions** and **builders** — keep tests decoupled and expressive.

`references/patterns.md` catalogues these and more, with when to reach for each.
