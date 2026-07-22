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

Make the three beats visible through **structure and names, not comments** — the code should not need a `# given` label:

- *Given* is the fixture parameter list — injected setup, not rebuilt in the body.
- *When* is a single action on its own line, assigned to a well-named result.
- *Then* is the assertions, ideally `then_<expectation>` **custom assertions**, with a blank line separating them from the when.

```
def test_when_keep_valid_then_non_positive_rows_dropped(raw_sales):
    kept = keep_valid(raw_sales)

    then_every_row_is_positive(kept)
```

A `then_` custom assertion carries its own failure message and reuses across tests, so it earns its place. Extract a `when_<action>` helper too when the action is compound or reads better named — but don't wrap a single, already well-named call for its own sake; that call is its own clearest *when*.

## Name the behaviour: when and then

Name every test `test_when_<action>_then_<outcome>`. The **given** stays in the arguments, so the name carries only the **when** (the action) and the **then** (the outcome it must produce).
`test_when_keep_valid_then_non_positive_rows_dropped`: the when is applying `keep_valid`, the then is that non-positive rows are dropped.
The prescriptive split forces both halves to be explicit and makes a failure read as a falsified claim, which is most of the diagnosis.
One when and one then per test — if either needs an "and", split the test.

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

Return every input **and expected value** from a function or fixture — never an inline literal in the test body. This is `write-python`'s "prefer a function over a bare variable or global" applied to tests: one source of truth, reusable, and free to change without editing each test.

- **Inputs → a fixture or builder**, or an external data file a fixture loads (keep a dataset out of the source as CSV/Parquet/JSON, inspectable as data). Feed a function only the fields it reads.
- **Expected values → a fixture that derives them from the raw data**, or a stored answers file — then pass them into a `then_` custom assertion, not a literal buried in the body.
- **Reach an expected value by a route independent of the code under test.** A stored answers file, or a plain restatement of the spec, qualifies; re-deriving with the *same* transformation the code uses is circular and proves nothing.
- **Prefer invariants where deriving the answer would just reimplement the code.** Assert properties that hold for any input — conservation (group totals sum to the whole), ordering (sorted), membership (output ⊆ input) — so there's no expected value to compute at all, and drive them with property-based tests.

Feed a function only what it reads, and assert only what the behaviour promises.

## Table-driven tests

Run one assertion over many **independent** cases — different scalar inputs, distinct scenarios — instead of a loop or copy-pasted tests.
Each case is reported and fails separately (a loop stops at the first failure), and adding one is a single line.

Reserve it for cases that are genuinely separate.
Don't shred a single operation over a whole collection into a case per element: when a function transforms a list or dataframe, feed it the whole input and assert the whole output in **one** test — that exercises it the way it is actually called and reads far better than a row-at-a-time table.
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
