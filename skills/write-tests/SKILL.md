---
name: write-tests
description: >-
  How to write and structure tests in any language — the given-when-then shape,
  naming a test by its behaviour, testing behaviour over implementation,
  isolation, table-driven and property-based testing, testing the dependency
  behaviour you rely on, and layout. Use whenever writing, editing, or reviewing
  tests, adding coverage, or setting up a suite, even if the user just says
  "write a test", "add tests", "test this", or names a runner like pytest. Tests
  are code: they follow the language's own conventions (Python → write-python).
  Language-agnostic principles here; Python and pytest idioms in
  references/python.md, the wider paradigms and patterns in references/patterns.md.
---

# Writing tests

A test is production code that happens to assert.
It follows the same conventions as the code it covers — in Python that's `write-python` (docstrings, typing, naming, ordering) — and layers the testing-specific judgment below on top.
This file is the language-agnostic mindset; the concrete runner idioms live in `references/python.md` (pytest), and the wider paradigm and pattern catalogue in `references/patterns.md`.

Good tests buy two things: confidence to change code, and a precise signal when it breaks.
Both come from testing *behaviour* through the public surface, keeping each test small and isolated, and naming it so a failure reads like a false claim about the system.

## Tests are code

Hold a test to the same standard as the code it covers — documented, typed, named and ordered the same way, with no "it's only a test" exemption.
A test's description states the behaviour under test, not a restatement of its name.
Factor shared construction into the runner's setup mechanism or small named helpers, not copied boilerplate.

## Given, when, then

Structure every test as **given / when / then** — the behavioural form of the four-phase test (setup, exercise, verify).

- **Given** — the starting state, *arranged and injected* into the test rather than reconstructed inline (in pytest, as fixture arguments; see `references/python.md`).
- **When** — the single action under test.
- **Then** — the assertions on the outcome.

Keep the three beats visually distinct. When a *when* or *then* step is shared or reads better named, extract it into a `when_<action>` helper and a `then_<expectation>` **custom assertion**, so the body reads as a sentence:

```
def test_keep_valid_drops_non_positive_rows(raw_sales):
    kept = when_kept_valid(raw_sales)
    then_every_row_is_positive(kept)
```

Inline the assertions instead when the test is simple; don't extract for its own sake.

## Name the behaviour: when and then

The test name states the **when and then** — the action and its expected outcome — while the **given** lives in the arranged inputs, not the name.
In `test_keep_valid_drops_non_positive_rows`, the when is `keep_valid` and the then is `drops_non_positive_rows`; the input scenario is whichever setup the test takes.
The name then reads as a sentence a failure would falsify, which is most of the diagnosis.
One when-and-then per test — if the name needs an "and", split it.

## Assert on behaviour, not implementation

Test the observable contract — return values, raised errors, visible side effects — through the public surface, never private internals.
Tests bound to implementation break on every refactor and stop being a safety net; tests bound to behaviour survive refactors and *are* the net.

Lean hardest on the **pure functional core** (see `be-functional`): it holds the logic and the bugs, and it is cheap to test because it is deterministic and needs no setup.
Keep the imperative shell thin so little is left that needs slow integration tests — the **humble object** pattern.

## Isolate each test

- A test must pass **in any order and on its own** — no shared mutable state, no test depending on another having run.
- Prefer **injected setup over globals**: shared data or context belongs in the runner's setup mechanism (a fixture), not a module-level constant, so each test gets its own fresh copy.
- Never touch the real clock, randomness, or network. Inject them (the default-argument seams from `be-functional`) and pass fixed values, or seed the generator, so a run is reproducible.
- A flaky test is a broken test: fix or delete it, since one that cries wolf trains you to ignore the suite.

## Where test data lives

Put each input where it keeps the test readable:

- **Salient values → table cases.** When the specific inputs are the point of the test (a formula, an edge case), pass them as parametrized `(input, expected)` rows and build the smallest structure the code actually reads — only the fields it uses, not a padded object. The reader sees input and expected output together.
- **A canonical, reused dataset → an external file loaded by setup.** Keep a shared sample out of the source: a data file (CSV, Parquet, JSON) that a fixture loads. It stays inspectable as data and the test stays about behaviour — this matters most for dataframes and anything past a few rows.
- **A tailored object → a builder or derived fixture.** For inputs that vary per test, a fixture can return a builder exposing only what varies, or narrow another fixture. Reach for this only when several tests need different shapes; a one-off is clearer built inline.

Keep the padding out either way — a test should carry the data its assertion depends on and nothing more.

## Table-driven tests

Run one assertion over many input rows instead of a loop or copy-pasted tests.
Each row is reported and fails separately (a loop stops at the first failure), and adding a case is one line.
The runner's parametrization syntax is in `references/python.md`.

## Property-based tests

For a rule that should hold across a whole input space, let a generator produce inputs and shrink any failure to a minimal counterexample (Hypothesis in Python, QuickCheck elsewhere).
It is especially strong for numeric and algorithmic code, where example-based tests only spot-check.
Reach for it when you can state an **invariant**:

- Round-trips: `decode(encode(x)) == x`.
- Algebraic laws: commutativity, associativity, an identity element.
- Postconditions: the result is always sorted, within bounds, or the same length.
- Agreement with a slow, obviously-correct reference implementation.

## Test the dependencies you rely on

Write tests against the third-party behaviour your code depends on, kept separate from tests of your own code.
They are **not** exhaustive tests of the library — that's the maintainer's job — but a pinned record of the specific behaviour you rely on, doubling as executable documentation of *how* you use it and an early warning when an upgrade changes it.

- Assert only what your code assumes: that a parser yields the type you expect, that an aggregation totals the way you rely on, that one call runs several operations together.
- A breaking change then fails on the assumption itself, not somewhere deep in your code on the next upgrade.
- Keep them a directory level apart from your own tests (see Layout).

## Mock sparingly

Prefer real objects and dependency injection to mocks.
A mock asserts on *how* code calls its collaborators, coupling the test to implementation — the opposite of testing behaviour.
Fake at the seam you designed (pass a stub function or in-memory double), and reach for patching only at a genuine external boundary you can't inject.
See the test-double taxonomy in `references/patterns.md`.

## Coverage is a guide, not a target

Measure coverage to find untested paths, then read *which* branches are uncovered — an uncovered error path matters, a percentage does not.
Chasing a number produces assertion-free tests that execute code without checking it.

## Keep the suite fast

A fast suite gets run on every change; a slow one gets skipped, which is when regressions land.
Tag genuinely slow or external tests so the default run stays quick and you opt into the rest in CI.

## Layout

Tests of your code **mirror the source** under `tests/<unit>/`; tests of the **dependency behaviour you rely on** live separately under `tests/packages/`, one file per dependency.
The concrete tree, import mode, and runner setup are language-specific — see `references/python.md` and `setup-python`.

## Running the suite

The **test runner is the entry point** — a test file never needs a `main`. Run the whole suite or a slice, selecting by directory, name, or tag.
The exact commands are in `references/python.md`.

## Paradigms and patterns

Reach beyond example-based unit tests when the problem fits. The ones that shape this house style:

- **TDD** (red-green-refactor) — write the failing test first to drive design.
- **BDD / given-when-then** — the structure above.
- **Property-based** — invariants over generated inputs.
- **Characterization / approval tests** — pin current output to make a refactor safe.
- **Test doubles**, **custom assertions** and **builders** — keep tests decoupled and expressive.

`references/patterns.md` catalogues these and more, with when to reach for each.

## Language idioms

Read the file for the language you're working in:

- **Python** → `references/python.md` (pytest: fixtures and `conftest.py`, `parametrize`, `tmp_path`/`capsys`, `raises`/`approx`, Hypothesis, `pytest-cov`, the `tests/` layout and import mode, running).

Add a new `references/<language>.md` when you start testing in another language rather than stuffing idioms into this file.
