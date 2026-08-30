---
name: write-tests
description: >-
  How to write and structure tests in any language — the given-when-then shape,
  naming a test by its behaviour, testing behaviour over implementation,
  isolation, table-driven and property-based testing, testing the dependency
  behaviour you rely on, and layout. Use whenever writing, editing, or reviewing
  tests, adding coverage, or setting up a suite, even if the user just says
  "write a test", "add tests", "test this", or names a runner like pytest.
  Language-agnostic principles and the paradigm/pattern catalogue here; Python
  and pytest idioms in references/python.md. Tests are code: they follow the
  language's own conventions (Python → write-python).
---

# Write tests

A test is production code that happens to assert.
It follows the same conventions as the code it covers — in Python that's `write-python` (docstrings, typing, naming, ordering) — and layers the testing-specific judgment below on top.

Good tests buy two things: confidence to change code, and a precise signal when it breaks.
Both come from testing *behaviour* through the public surface, keeping each test small and isolated, and naming it so a failure reads like a false claim about the system.
Three mistakes account for most weak suites: asserting on internals instead of the public contract, building the *given* inline instead of injecting it, and reaching an expected value with the very code under test.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established test style or layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Tests are code

Hold a test to the same standard as the code it covers — documented, typed, named and ordered the same way, with no "it's only a test" exemption.
A test's description states the behaviour under test, not a restatement of its name.
Factor shared construction into the runner's setup mechanism or small named helpers, not copied boilerplate.

## Given, when, then

Structure every test as **given / when / then** — the behavioural form of the four-phase test (setup, exercise, verify).

- **Given** — the starting state, *arranged and injected* into the test rather than reconstructed inline (in `pytest`, as fixture arguments; see `references/python.md`).
- **When** — the single action under test.
- **Then** — the assertions on the outcome.

Name every test `test_when_<action>_then_<outcome>`.
The **given** stays in the arguments, so the name carries only the **when** (the action) and the **then** (the outcome it must produce).
`test_when_keep_valid_then_non_positive_rows_dropped`: the when is applying `keep_valid`, the then is that non-positive rows are dropped.
The prescriptive split forces both halves to be explicit and makes a failure read as a falsified claim, which is most of the diagnosis.
One when and one then per test — if either needs an "and", split the test.

Make the three beats visible through **structure and names, not comments** — the code should not need a `# given` label:

- *Given* arrives **entirely through the test's parameters** — every fixture and every piece of external data comes in as an argument (a fixture, or a fixture that loads a data file).
Never a module-level global, and never data built inline in the body.
- *When* is a single action on its own line, assigned to a well-named result.
- *Then* is the assertions, ideally `then_<expectation>` **custom assertions**.

```python
# Wrong: the given is built in the body, so the scenario has no name and the next test copies it.
def test_when_keep_valid_then_non_positive_rows_dropped() -> None:
    """Every kept row is positive."""
    raw_sales = polars.DataFrame({"quantity": [2, 0, -1, 5]})
    kept = keep_valid(raw_sales)
    assert kept.get_column("quantity").to_list() == [2, 5]


# Right: the given arrives as a parameter and the then is a named, reusable claim.
def test_when_keep_valid_then_non_positive_rows_dropped(
    raw_sales: polars.DataFrame,
) -> None:
    """Every kept row is positive."""
    kept = keep_valid(raw_sales)
    then_every_row_is_positive(kept)
```

A `then_` custom assertion carries its own failure message and reuses across tests, so it earns its place even for a bare equality — a shared set (`then.equals`, `then.column_equals`) reads far more uniformly than scattered `assert` statements.
Extract a `when_<action>` helper too when the action is compound or reads better named — but don't wrap a single, already well-named call for its own sake; that call is its own clearest *when*.

Grouped into shared modules, the three beats gain a matching vocabulary — `given` (fixtures), `when` (action helpers) and `then` (assertions) — so a body reads `when.summarise_by_region(sales)` then `then.conserves(...)`.
Add a `when` module only where actions earn a name; the `then` module almost always pays off, since every test asserts.

## Behaviour, not implementation

Test the observable contract — return values, raised errors, visible side effects — through the public surface, never private internals.
Tests bound to implementation break on every refactor and stop being a safety net; tests bound to behaviour survive refactors and *are* the net.

Lean hardest on the **pure functional core** (see `be-functional`): it holds the logic and the bugs, and it is cheap to test because it is deterministic and needs no setup.
Keep the imperative shell thin so little is left that needs slow integration tests — the **humble object** pattern.

**The adapter's *judgement* earns its own cases, being neither core nor the library's.**
Reading a document is the library's job; deciding *which field is the answer* is a claim about a source, and no core or dependency test covers it.
Which of several symbols is the home listing, which column marks a row as cash, what an absent field means — pin each against a saved response, no stub for the fetch.
Reaching the parse function directly is what the getting/parsing split is for (see `structure-python`), not a breach of the rule above.
Cover the case it was written for **and** the case it was not: a record missing the field is where a source surprises you.

This is also why you **mock sparingly**.
Prefer real objects and dependency injection to mocks: a mock asserts on *how* code calls its collaborators, coupling the test to implementation — the opposite of testing behaviour.
Fake at the seam you designed (pass a stub function or in-memory double), and reach for patching only at a genuine external boundary you can't inject.

**Where an adapter owns its client on purpose, the seam is one argument, not a patch.**
An adapter is built to keep its library's objects inside itself, so a test looking for something to inject finds nothing — and that is the boundary working rather than an oversight.
Most of what you wanted to test does not need it anyway: splitting retrieval from parsing leaves the parse taking a saved response, with no client in it at all.

What remains is genuinely about the client — which answers it treats as failures, what it retries, which page it fetches first.
Reach that by giving the function that *builds* the client an optional transport defaulting to the real one, which is the injection any impure dependency takes.
The test then hands it the library's own in-process transport, every layer above the wire stays the library's real code, and nothing private is patched.
Patching the builder instead replaces the one function the test was about.
See the test-double taxonomy under Patterns below.

## Isolation

- A test must pass **in any order and on its own** — no shared mutable state, no test depending on another having run.
- **Inject setup; never share through a global.** Shared data or context belongs in the runner's setup mechanism (a fixture), not a module-level constant, so each test gets its own fresh copy.
- Never touch the real clock, randomness, or network.
Inject them (the default-argument seams from `be-functional`) and pass fixed values, or seed the generator, so a run is reproducible.
- A flaky test is a broken test: fix or delete it, since one that cries wolf trains you to ignore the suite.

## Test data

Since every *given* value arrives through the signature (above), the open question is where a fixture gets it — and, harder, where an *expected* value comes from.
This is `write-python`'s "prefer a function over a bare variable or global" applied to tests: one source of truth, reusable, and free to change without editing each test.

- **Inputs → a fixture or builder**, or an external data file a fixture loads (keep a dataset out of the source as CSV/Parquet/JSON, inspectable as data).
Feed a function only the fields it reads.
- **Expected values → a fixture that derives them from the raw data**, or a stored answers file — then pass them into a `then_` custom assertion, not a literal buried in the body.
- **Reach an expected value by a route independent of the code under test.** A stored answers file, or a plain restatement of the spec, qualifies; re-deriving with the *same* transformation the code uses is circular and proves nothing.
- **Prefer invariants where deriving the answer would just reimplement the code.** Assert properties that hold for any input — conservation (group totals sum to the whole), ordering (sorted), membership (output ⊆ input) — so there's no expected value to compute at all, and drive them with property-based tests.

Feed a function only what it reads, and assert only what the behaviour promises.

## Many inputs

Run one assertion over many inputs instead of copy-pasted cases — the same instinct as preferring an expression over a loop.
A table covers the cases you can enumerate; a generator covers a rule you can only state.

**Table-driven** runs one assertion over many **independent** cases — different scalar inputs, distinct scenarios — instead of a loop or copy-pasted tests.
Each case is reported and fails separately (a loop stops at the first failure), and adding one is a single line.
Reserve it for cases that are genuinely separate.
Don't shred a single operation over a whole collection into a case per element: when a function transforms a list or dataframe, feed it the whole input and assert the whole output in **one** test — that exercises it the way it is actually called and reads far better than a row-at-a-time table.
The runner's parametrization syntax is in `references/python.md`.

**Property-based** lets a generator produce inputs across a whole input space and shrink any failure to a minimal counterexample (`hypothesis` in Python, `QuickCheck` elsewhere).
It is especially strong for numeric and algorithmic code, where example-based tests only spot-check.
Reach for it when you can state an **invariant**:

- Round-trips: `decode(encode(x)) == x`.
- Algebraic laws: commutativity, associativity, an identity element.
- Postconditions: the result is always sorted, within bounds, or the same length.
- Agreement with a slow, obviously-correct reference implementation.

**Check that the generator actually reaches the states you are testing.** A property that passes is evidence only about the inputs that were generated, and a naive generator usually produces the quiet ones: uniformly random prices almost never contain a nine-candle run, so an agreement property over them can pass a hundred examples having never once exercised the logic it was written for.
Bias the generator towards the interesting region — a walk with drift rather than independent draws — and then *measure* its reach before trusting it, by counting over a few hundred generated inputs how many arrive in each state that matters.
The measurement is throwaway; leaving the unbiased generator in place is what costs you.

**A reference implementation is neither a given, a when, nor a then** — it is an oracle, and it belongs in its own module beside them (`reference` alongside `given`/`when`/`then`), exposed to tests through a fixture like any other starting state.
Write it from the specification in the most obvious style available, not by paraphrasing the implementation: the agreement is worth something only because the two share no mechanism.

## Dependency tests

Write tests against the third-party behaviour your code depends on, kept separate from tests of your own code.
They are **not** exhaustive tests of the library — that's the maintainer's job — but a pinned record of the specific behaviour you rely on, doubling as executable documentation of *how* you use it and an early warning when an upgrade changes it.

- Assert only what your code assumes: that a parser yields the type you expect, that an aggregation totals the way you rely on, that one call runs several operations together.
- A breaking change then fails on the assumption itself, not somewhere deep in your code on the next upgrade.
- Keep the dependency-behaviour tests a directory level apart from your own — the reference shows the tree.

**Every default you overrode is an assumption, and it is the one most worth pinning.**
"Assert only what your code assumes" reads as a limit and is really a prompt: go and enumerate them.
The largest group hides because it is written as arguments — each one you passed because the library's default was wrong for you is a belief about what that default *is*, and the day it changes back you get a wrong answer rather than an error.

Pin them by their effect rather than their name: that the unadjusted close differs from the adjusted one, that a bound excludes its own date, that a search returns more than the default cap when told to.
Each of those fails loudly on the upgrade that would otherwise change your numbers quietly.

The rest of the enumeration is what you read off a response — the level names of an index you reshape, whether a missing record raises or comes back as nulls, whether a field is absent or empty.
A test per assumption is not over-testing; the assumptions are what the adapter is made of.

**A network-backed dependency is pinned without a network.**
"Never touch the network" and "pin the behaviour you rely on" only look opposed: what you rely on is how the client turns a response into what your code reads — the status it raises on, the encoding it picks, how it follows a redirect — and none of that needs a socket.
Use the client's **own** in-process transport rather than patching it, so every layer above the wire is still the library's real code, and feed it a response you recorded from the real service once and kept beside the test.
Patching the client out entirely tests neither the dependency nor your code, and reaching the real service makes the suite fail on someone else's outage; the transport seam is what gets you both.

## Coverage and speed

Measure coverage to find untested paths, then read *which* branches are uncovered — an uncovered error path matters, a percentage does not.
Chasing a number produces assertion-free tests that execute code without checking it.

Keep the suite fast so it runs on every change; a slow one gets skipped, which is when regressions land.
Tag genuinely slow or external tests so the default run stays quick and you opt into the rest in CI.

**A recorded response proves the parse, not the source, so run the real surface once before calling a build done.**
A fixture cannot say whether the address still serves it, whether every input the tool *claims* to serve resolves, or whether one comes back empty.
The recorded document is, by definition, one that worked.
So exercise the whole declared surface against the real thing and **read the counts, not the exit code**.
An input returning zero rows has passed every check a program can make on itself.
Keep it as a marked test outside the default run, or a documented command, so it lives in the repo rather than someone's memory.

**Zero is the loudest wrong count, not the dangerous one.**
Checking that nothing came back empty catches a source that moved and a name that no longer resolves, and it is worth having.
It does not catch the count that is plausible: a request for a full history quietly answered with one month looks exactly like a request that worked, and so does a search capped at a library default a quarter of what was asked for.

So assert the size against something you knew before the run, not against zero.
The cheapest form is a **relation between two runs** rather than a number — an unbounded fetch returns more than a bounded one, three timeframes return more rows than one, a limit of two hundred returns at least what fifty did.
Those hold as the data grows, where a literal does not, and each fails on exactly the default that was silently taken.

Assert the **categories** separately from the size, too.
"All three timeframes appeared" and "as many rows came back as should have" are two claims, and a test making only the first reads as though it made both.

## Paradigms

Reach beyond example-based unit tests when the problem fits.

- **TDD (Test-Driven Development)** — write a failing test, make it pass, refactor (red-green-refactor).
Drives design and guarantees every line exists to satisfy a stated intent.
- **BDD (Behaviour-Driven Development)** — express tests as given-when-then behaviour in domain language, the structure above.
Keeps tests tied to requirements, not implementation.
- **Property-based** — assert invariants over generated, shrinking inputs (`hypothesis`, `QuickCheck`), per Many inputs above.
- **Test pyramid (and trophy)** — many fast unit tests, fewer integration, fewest end-to-end.
A budgeting guide; lean toward integration (the "trophy") when units are trivial and the bugs live in the seams.
- **Characterization** — capture the *current* behaviour of existing code before changing it.
A safety net around legacy or unfamiliar code ahead of a refactor.
- **Approval / golden-master / snapshot** — assert output equals a stored, reviewed reference.
For complex output (rendered text, serialised structures) painful to assert field by field; review the diff when it changes.
- **Contract** — verify both sides of an integration agree on a shared contract (consumer-driven contracts, Pact).
Across boundaries you don't control end to end.
- **Fuzz** — feed random or adversarial inputs to surface crashes and unhandled cases.
On parsers and anything taking untrusted input.
- **Mutation** — inject faults into the code and check the suite catches them.
Run occasionally to measure whether tests actually assert, not merely execute.

## Patterns

Reach for a named pattern to structure a test or its suite.

- **Four-phase test** — setup, exercise, verify, teardown; given-when-then is its behavioural form.
The skeleton of every test.
- **Test doubles** — *dummy* (filler, unused), *stub* (canned answers), *spy* (records calls), *mock* (asserts on expected calls), *fake* (a working lightweight implementation).
- **Custom assertion** — a `then_<expectation>` helper encapsulating a check and its failure message, per Given, when, then above.
- **Test data builder** — a fluent builder for a valid object with overridable parts (`a_sale().with_quantity(0)`).
For objects with many fields where tests vary one at a time.
- **Object mother** — a factory of canonical, named test objects (`Sales.typical()`).
For a small set of standard scenarios shared across tests.
- **Parametrized / table-driven** — one test, a table of cases, per Many inputs above.
- **Humble object** — push logic out of a hard-to-test boundary (UI, I/O) into a plain, testable object; the functional-core / imperative-shell split is this pattern.
- **Fresh vs shared fixture** — a fresh fixture per test maximises isolation; a shared (module/session) one trades isolation for speed on expensive, read-only setup.
Default to fresh.
- **Suite layout** — separate the test cases (mirroring the source, dependency-behaviour tests kept apart), their data, and shared helpers; the concrete tree is language-specific.
- **Runner as entry point** — a runner discovers and runs the tests, so no test file needs a `main`; run the whole suite or select a slice by directory, name or tag.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (`pytest`: fixtures in the `pytest_` package, `parametrize`, `tmp_path`/`capsys`, `raises`/`approx`, `hypothesis`, `pytest-cov`, the `tests/` layout and import mode, running).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
