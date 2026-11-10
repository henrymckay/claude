---
name: write-tests
description: >-
  How to write and structure tests in any language — tests held to the code's
  own standard, the given-when-then shape, naming a test by its behaviour,
  testing behaviour over implementation, a bare assert for equality and a
  custom assertion for a domain claim, where test data and expected values
  come from and how a recorded response is refreshed, table-driven and
  property-based testing with an imported oracle, testing the dependency
  behaviour you rely on, the seams a paced client needs, checking that a
  fixture can exhibit the failure and a generator reaches the state, testing a
  store and a dashboard, and checking a build against the real source by its
  counts; no coverage target, no mutation testing, no snapshots until earned.
  Use whenever writing, editing or reviewing tests, adding coverage, or
  setting up a suite, even if the user just says "write a test", "add tests",
  "test this", or names a runner like pytest. Language-agnostic principles
  here; Python and pytest idioms in references/python.md. Layers on
  write-python, since tests are code.
---

# Write tests

A test is production code that happens to assert, so it follows the conventions of the code it covers — in Python, `write-python` — with the testing judgement below on top.
Good tests buy confidence to change code and a precise signal when it breaks, both from testing *behaviour* through the public surface in small, isolated, well-named tests.
Three mistakes account for most weak suites: asserting on internals instead of the public contract, building the *given* inline instead of injecting it, and reaching an expected value with the very code under test.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established test style or layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Tests are code

Hold a test to the standard of the code it covers — typed, named and ordered the same way, with no "it's only a test" exemption.
A test has no docstring: its name is the claim, and a docstring restating it is the waste `write-python` forbids.
Factor shared construction into the runner's setup mechanism or small named helpers, never copied boilerplate.

## Given, when, then

Structure every test as **given / when / then**, the behavioural form of setup, exercise, verify:

- **Given** — the starting state, arriving **through the test's parameters** (fixtures, including ones that load data files) — never a module-level value, and built in the body only for a boundary literal with no scenario to name, such as an empty table with its schema.
- **When** — the single action under test, on its own line, assigned to a well-named result.
- **Then** — the assertions: a bare `assert` for an equality, a shared `then.<claim>` for a domain claim (below).

**Name every test `test_when_<action>_then_<outcome>`.** The given lives in the parameters, so the name carries the action and the outcome: `test_when_keep_valid_then_non_positive_rows_dropped`.
A failure then reads as a falsified claim, which is most of the diagnosis.
One when and one then per test — if either needs an "and", split it.

Make the beats visible through structure and names, not `# given` comments.

- **Wrong** — the test builds its sample data in the body, so the scenario has no name and the next test copies it.
- **Right** — the sample arrives as a named fixture parameter, and the outcome is a named assertion reused across tests.

**A bare `assert` for an equality, a custom assertion for a domain claim.** The runner's rewritten `assert` shows the diff between the two sides, which no hand-written message matches; a `then.conserves(...)` names a claim about the domain that several tests share, and a transposed pair there reports the failure backwards rather than passing.
Add a `when.<action>` helper only where the action is compound; a single well-named call is its own clearest *when*.
Grouped, the beats become shared `given`, `when` and `then` modules, so a body reads `when.summarise(sales)` then `then.conserves(...)`.

## Behaviour, not implementation

Test the observable contract — return values, raised errors, visible effects — through the public surface.

**Lean hardest on the pure core** (see `be-functional`): it holds the logic, and it is deterministic and needs no setup.
Keep the shell thin so little needs slow integration tests — the humble object pattern — and lean toward integration where the units are trivial and the bugs live in the seams.

**Use real objects and a fake at the seam you designed** (a stub function, an in-memory double), and patch only at an external boundary you can't inject; a mock that asserts on *how* code calls its collaborators couples the test to the implementation.

**Test an adapter's judgement on its own.** Reading a document is the library's job; deciding which field is the answer is a claim about the source that neither core nor dependency tests cover.
Pin it against a saved response, passed straight to the parse function (see `structure-python` on splitting getting from parsing), covering the case the code was written for **and** a record missing the field.

**Reach an owned client through one argument, not a patch.** An adapter keeps its library's client inside itself by design.
For what is genuinely about the client — what it treats as failure, what it retries, how it paces — give the function that builds the client an optional transport defaulting to the real one, and a `sleep` the retry and pacing policy call, so the test hands it the library's in-process transport and a spy that counts the waits; patching the builder replaces the one function under test.

**Never touch the real clock, randomness or network**, except in the marked real-surface run below; inject them (see `be-functional`) and pass fixed values or a seed, since a test that sleeps for real is a slow test that still proves nothing about the wait.

## Test data

Every given arrives through the signature; the questions are where a fixture gets it and, harder, where an *expected* value comes from.

- **Inputs** come from a fixture, a builder, or a data file a fixture loads (CSV, Parquet, JSON kept out of the source); a fixture is fresh per test, and shared at module or session scope only for expensive read-only setup.
Feed a function only the fields it reads.
- **Expected values** come from a fixture or a stored answers file — never a literal buried in the body, except the parameters of a table-driven case, which are the table.
- **Reach an expected value independently of the code under test** — a stored answer or a plain restatement of the spec; re-deriving it with the same transformation proves nothing.
- **Assert invariants where deriving the answer would reimplement the code**: conservation (group totals sum to the whole), ordering, membership (output ⊆ input).

**Check the fixture can exhibit what you test for.** A test passes when the code is right *or* when the fixture can't show it wrong, and the two look identical.
The usual gap is a missing **dimension**: one series can't show what happens when two have different gaps, one page can't show the boundary between pages.
For each rule, ask what the input must contain for it to fire, and check the fixture has it — the smallest, easiest fixture to record is reliably the one exhibiting least.

## Many inputs

**Table-driven** runs one assertion over many **independent** cases — each reported separately, each one line to add.
Don't shred one operation over a collection into a case per element: feed the whole input and assert the whole output in one test, the way it is called.

**Property-based** generates inputs across a space and shrinks failures to a minimal counterexample (`hypothesis`, `QuickCheck`).
Reach for it when you can state an invariant — a round-trip, an algebraic law, a postcondition, agreement with a slow and obviously correct reference.

**Check the generator reaches the states you test.** Independent random draws rarely produce a long run or a trend, so a property can pass a hundred examples without once exercising its logic.
Bias the generator toward the interesting region (a drifting walk, not independent draws), then count over a few hundred inputs how many reach each state that matters; zero is a failure, not a pass.

**A reference implementation is an oracle**, its own module beside `given`/`when`/`then`, imported by the property test rather than injected: a per-test fixture under a property runs once for every generated example, and the generator's health check fails the test for it.
Write it from the spec in the most obvious style, never by paraphrasing the implementation — the agreement is worth something only if they share no mechanism.

## Dependency tests

Pin the third-party behaviour your code relies on, kept apart from tests of your own code.
They are not exhaustive tests of the library but a record of your assumptions, failing on the assumption itself when an upgrade changes it.

**Pin every default you overrode, by its effect.** Each argument passed because the library's default was wrong for you is a belief about that default, and if it changes you get a wrong answer, not an error.
Assert the effect — that a timestamp is not converted to local time, that a range bound excludes its own date — and add what you read off responses: whether a missing record raises or returns nulls, whether a field is absent or empty.

**Pin a network-backed dependency without a network.** What you rely on — the status it raises on, the encoding, redirects — lives above the socket.
Use the client's own in-process transport with a response recorded once from the real service, so every layer above the wire is the library's real code.
**Record the response with a script kept beside the data**, run against the real source with its credential from the environment and redacting the credential before saving, so the fixture can be refreshed when the source changes shape rather than hand-edited into something the source never sent.

**Test a store against the real file format on a temporary path**, with a round-trip property over generated records; the core gets an in-memory fake of the same port (see `structure-python`).
A dashboard's test checks that its layout renders from a given frame; a browser test waits until a screen has a bug no render check would catch.

## Coverage and speed

Use coverage to find untested paths, then read *which* branches are uncovered; no percentage is targeted and nothing fails under a number, since chasing one produces tests that execute code without checking it.
Mutation testing is not run, and approval or snapshot tests have no tool until a project earns one by rendering output too large to assert on.
Keep the default run fast, tagging slow or external tests to opt into.

**Run the real surface once before calling a build done.** A recorded response proves the parse, not that the source still serves it; exercise every input the tool claims against the real thing, as a marked test or a documented command.
**Read the counts, not the exit code**, and assert sizes against something known beforehand rather than against zero:

- **Relations between runs** — an unbounded fetch returns more than a bounded one, a limit of 200 at least what 50 did — hold as data grows, and each catches a default silently taken (a listing quietly capped at one page).
- **Categories separately from size** — "every region appeared" and "as many rows as expected" are two claims.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (`pytest`: the `pytest_` package, fixtures, `parametrize`, `hypothesis` and its health check, assert rewriting, `monkeypatch` and `time-machine`, `httpx.MockTransport` and the recording script, running).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
