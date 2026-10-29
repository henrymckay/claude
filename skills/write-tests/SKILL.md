---
name: write-tests
description: >-
  How to write and structure tests in any language — the given-when-then shape,
  naming a test by its behaviour, testing behaviour over implementation,
  isolation, where test data and expected values come from, table-driven and
  property-based testing, testing the dependency behaviour you rely on,
  checking a build against the real source, and layout. Use whenever writing,
  editing or reviewing tests, adding coverage, or setting up a suite, even if
  the user just says "write a test", "add tests", "test this", or names a
  runner like pytest. Language-agnostic principles and the paradigm and pattern
  catalogue here; Python and pytest idioms in references/python.md. Tests are
  code: they follow the language's own conventions (Python → write-python).
---

# Write tests

A test is production code that happens to assert, so it follows the conventions of the code it covers — in Python, `write-python` — with the testing judgment below on top.
Good tests buy confidence to change code and a precise signal when it breaks, both from testing *behaviour* through the public surface in small, isolated, well-named tests.
Three mistakes account for most weak suites: asserting on internals instead of the public contract, building the *given* inline instead of injecting it, and reaching an expected value with the very code under test.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established test style or layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Tests are code

Hold a test to the standard of the code it covers — documented, typed, named and ordered the same way, with no "it's only a test" exemption.
A test's description states the behaviour, not its name again.
Factor shared construction into the runner's setup mechanism or small named helpers, never copied boilerplate.

## Given, when, then

Structure every test as **given / when / then**, the behavioural form of setup, exercise, verify:

- **Given** — the starting state, arriving **entirely through the test's parameters** (fixtures, including ones that load data files) — never a module global, never built in the body.
- **When** — the single action under test, on its own line, assigned to a well-named result.
- **Then** — the assertions, ideally `then_<expectation>` custom assertions.

**Name every test `test_when_<action>_then_<outcome>`.** The given lives in the parameters, so the name carries the action and the outcome: `test_when_keep_valid_then_non_positive_rows_dropped`.
A failure then reads as a falsified claim, which is most of the diagnosis.
One when and one then per test — if either needs an "and", split it.

Make the beats visible through structure and names, not `# given` comments.

- **Wrong** — the test builds its sample data in the body, so the scenario has no name and the next test copies it.
- **Right** — the sample arrives as a named fixture parameter, and the outcome is a named assertion reused across tests.

**Prefer a custom assertion even for a bare equality**: it carries its own failure message, names the expected side so a transposed pair can't pass, and a shared set reads uniformly.
Add a `when_<action>` helper only where the action is compound; a single well-named call is its own clearest *when*.
Grouped, the beats become shared `given`, `when` and `then` modules, so a body reads `when.summarise(sales)` then `then.conserves(...)`.

## Behaviour, not implementation

Test the observable contract — return values, raised errors, visible effects — through the public surface.
Tests bound to implementation break on every refactor and stop being a safety net.

**Lean hardest on the pure core** (see `be-functional`): it holds the logic, and it is deterministic and needs no setup.
Keep the shell thin so little needs slow integration tests — the humble object pattern.

**Mock sparingly.** A mock asserts on *how* code calls its collaborators, coupling the test to implementation.
Prefer real objects and a fake at the seam you designed (a stub function, an in-memory double), and patch only at an external boundary you can't inject.

**Test an adapter's judgement on its own.** Reading a document is the library's job; deciding which field is the answer is a claim about the source that neither core nor dependency tests cover.
Pin it against a saved response, passed straight to the parse function (see `structure-python` on splitting getting from parsing), covering the case the code was written for **and** a record missing the field.

**Reach an owned client through one argument, not a patch.** An adapter keeps its library's client inside itself by design.
For what is genuinely about the client — what it treats as failure, what it retries — give the function that builds the client an optional transport defaulting to the real one, and hand the test the library's in-process transport; patching the builder replaces the one function under test.

## Isolation

- **Pass in any order and alone** — no shared mutable state, no test depending on another.
- **Inject setup through the runner's fixtures**, never a global, so each test gets a fresh copy.
- **Never touch the real clock, randomness or network.** Inject them (see `be-functional`) and pass fixed values or a seed.
- **Fix or delete a flaky test** — one that cries wolf trains everyone to ignore the suite.

## Test data

Every given arrives through the signature; the questions are where a fixture gets it and, harder, where an *expected* value comes from.

- **Inputs** come from a fixture, a builder, or a data file a fixture loads (CSV, Parquet, JSON kept out of the source).
Feed a function only the fields it reads.
- **Expected values** come from a fixture or a stored answers file, passed into a custom assertion — never a literal buried in the body.
- **Reach an expected value independently of the code under test** — a stored answer or a plain restatement of the spec; re-deriving it with the same transformation proves nothing.
- **Prefer invariants where deriving the answer would reimplement the code**: conservation (group totals sum to the whole), ordering, membership (output ⊆ input).

**Check the fixture can exhibit what you test for.** A test passes when the code is right *or* when the fixture can't show it wrong, and the two look identical.
The usual gap is a missing **dimension**: one series can't show what happens when two have different gaps, one page can't show the boundary between pages.
For each rule, ask what the input must contain for it to fire, and check the fixture has it — the smallest, easiest fixture to record is reliably the one exhibiting least.

## Many inputs

**Table-driven** runs one assertion over many **independent** cases — each reported separately, each one line to add.
Don't shred one operation over a collection into a case per element: feed the whole input and assert the whole output in one test, the way it is called.

**Property-based** generates inputs across a space and shrinks failures to a minimal counterexample (`hypothesis`, `QuickCheck`).
Reach for it when you can state an invariant:

- Round-trips: `decode(encode(x)) == x`.
- Algebraic laws: commutativity, associativity, identity.
- Postconditions: always sorted, within bounds, same length.
- Agreement with a slow, obviously correct reference implementation.

**Check the generator reaches the states you test.** Independent random draws rarely produce a long run or a trend, so a property can pass a hundred examples without once exercising its logic.
Bias the generator toward the interesting region (a drifting walk, not independent draws), then count over a few hundred inputs how many reach each state that matters; zero is a failure, not a pass.

**A reference implementation is an oracle**, its own module beside `given`/`when`/`then`, reached through a fixture.
Write it from the spec in the most obvious style, never by paraphrasing the implementation — the agreement is worth something only if they share no mechanism.

## Dependency tests

Pin the third-party behaviour your code relies on, kept apart from tests of your own code.
They are not exhaustive tests of the library but a record of your assumptions, failing on the assumption itself when an upgrade changes it.

**Pin every default you overrode, by its effect.** Each argument passed because the library's default was wrong for you is a belief about that default, and if it changes you get a wrong answer, not an error.
Assert the effect — that an unadjusted series differs from the adjusted one, that a range bound excludes its own date — and add what you read off responses: whether a missing record raises or returns nulls, whether a field is absent or empty.

**Pin a network-backed dependency without a network.** What you rely on — the status it raises on, the encoding, redirects — lives above the socket.
Use the client's own in-process transport with a response recorded once from the real service, so every layer above the wire is the library's real code.

## Coverage and speed

Use coverage to find untested paths, then read *which* branches are uncovered; chasing a percentage produces tests that execute code without checking it.
Keep the default run fast, tagging slow or external tests to opt into in CI.

**Run the real surface once before calling a build done.** A recorded response proves the parse, not that the source still serves it; exercise every input the tool claims against the real thing, as a marked test or a documented command.
**Read the counts, not the exit code**, and assert sizes against something known beforehand rather than against zero:

- **Relations between runs** — an unbounded fetch returns more than a bounded one, a limit of 200 at least what 50 did — hold as data grows, and each catches a default silently taken (a history quietly capped at one month).
- **Categories separately from size** — "every region appeared" and "as many rows as expected" are two claims.

## Paradigms

- **TDD (Test-Driven Development)** — red, green, refactor; every line exists to satisfy a stated intent.
- **BDD (Behaviour-Driven Development)** — given-when-then in domain language, the shape above.
- **Property-based** — invariants over generated inputs (Many inputs).
- **Test pyramid or trophy** — many unit, fewer integration, fewest end-to-end; lean toward integration where units are trivial and the bugs live in the seams.
- **Characterisation** — capture current behaviour before refactoring unfamiliar code.
- **Approval or snapshot** — compare complex output to a reviewed reference, and review the diff when it changes.
- **Contract** — both sides of an integration verify a shared contract (Pact).
- **Fuzz** — random or adversarial input for parsers and anything untrusted.
- **Mutation** — inject faults to check the suite asserts rather than merely executes.

## Patterns

- **Test doubles** — *dummy* (unused filler), *stub* (canned answers), *spy* (records calls), *mock* (asserts on calls), *fake* (working lightweight implementation).
- **Test data builder** — a valid object with overridable parts (`a_sale().with_quantity(0)`), for many-field objects varied one field at a time.
- **Object mother** — named canonical objects (`Sales.typical()`) for a few standard scenarios.
- **Fresh vs shared fixture** — default to fresh; share (module or session scope) only expensive, read-only setup.
- **Suite layout** — separate the cases (mirroring the source, dependency tests apart), their data, and shared helpers.
- **Runner as entry point** — no test file has a `main`; select a slice by directory, name or tag.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (`pytest`: the `pytest_` package, fixtures, `parametrize`, `hypothesis`, custom assertions, `httpx.MockTransport`, logging, running).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
