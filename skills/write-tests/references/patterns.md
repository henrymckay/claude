# Test paradigms and patterns

A catalogue to reach for; the main skill covers the day-to-day workflow.
Each entry says what it is and when it earns its place.

## Paradigms (how to approach testing)

- **Test-Driven Development (TDD)** — write a failing test, make it pass, refactor (red-green-refactor). Drives design and guarantees every line exists to satisfy a stated intent, not as an afterthought.
- **Behaviour-Driven Development (BDD)** — express tests as given-when-then behaviour in domain language. Keeps tests readable and tied to requirements rather than implementation.
- **Property-based testing** — assert invariants over inputs a generator produces and shrinks (Hypothesis, QuickCheck). For pure, algorithmic, or numeric code where you can state a law but not enumerate cases.
- **The test pyramid (and trophy)** — many fast unit tests, fewer integration, fewest end-to-end. A budgeting guide; lean toward integration (the "testing trophy") when units are trivial and the bugs live in the seams.
- **Characterization testing** — write tests that capture the *current* behaviour of existing code before changing it. Builds a safety net around legacy or unfamiliar code ahead of a refactor.
- **Approval / golden-master / snapshot testing** — assert output equals a stored, reviewed reference. For complex output (rendered text, serialized structures) that's painful to assert field by field; you review the diff when it changes.
- **Contract testing** — verify both sides of an integration agree on a shared contract (e.g. consumer-driven contracts, Pact). Across service or module boundaries you don't control end to end.
- **Fuzz testing** — feed random or adversarial inputs to surface crashes and unhandled cases. On parsers and anything taking untrusted input.
- **Mutation testing** — inject faults into the code and check the suite catches them. Run occasionally to measure whether tests actually assert, not merely execute.

## Patterns (how to structure a test)

- **Four-phase test** — setup, exercise, verify, teardown; given-when-then is its behavioural form. The skeleton of every test.
- **Test doubles** (Meszaros, Fowler) — *dummy* (filler passed but unused), *stub* (canned answers), *spy* (records calls for later inspection), *mock* (asserts on the calls it expects), *fake* (a working lightweight implementation, e.g. in-memory). Prefer fakes and injection; reserve mocks for genuine boundaries.
- **Custom assertion** — a `then_<expectation>` helper that encapsulates a check and its failure message. Names a domain expectation and reuses it across tests.
- **Test data builder** — a fluent builder that constructs a valid object with overridable parts (`a_sale().with_quantity(0)`). For objects with many fields where tests vary one at a time.
- **Object mother** — a factory of canonical, named test objects (`Sales.typical()`). For a small set of standard scenarios shared across tests.
- **Parametrized / table-driven test** — one test, a table of cases. For the same assertion over many inputs.
- **Humble object** — push logic out of a hard-to-test boundary (UI, I/O) into a plain, testable object; the functional-core / imperative-shell split is this pattern. Makes untestable code testable by relocating the logic.
- **Fresh vs shared fixture** — a fresh fixture per test maximises isolation; a shared (module/session) fixture trades some isolation for speed on expensive, read-only setup. Default to fresh.
