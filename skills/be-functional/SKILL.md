---
name: be-functional
description: >-
  Write code in a functional style — pure functions, immutability, composition,
  and explicit data flow — in any language. Use when the user asks for
  functional code, a "functional approach", pipelines/transformations over
  data, or wants to avoid mutation and side effects; and when refactoring
  imperative or stateful code toward a cleaner functional shape. This is an
  opt-in style skill: apply it when a functional approach is requested or
  clearly fits, not to every piece of code. Principles here are
  language-agnostic; language-specific idioms live in references/<language>.md
  (start with references/python.md).
---

# Being functional

The goal is code that's **expressive, composable, and easy to use** — functional
techniques are the means to that end, not a purity contest. When behavior depends
only on a function's inputs (not hidden state or order of execution), code becomes
easy to reason about, test, and reuse. This file is the *mindset and principles*;
concrete idioms for a language live in `references/` (e.g. `references/python.md`).

**This is opt-in.** Apply it when a functional approach is asked for or clearly
fits (data transformations, pipelines, pure logic). Don't force it onto naturally
stateful code (I/O, UIs, long-lived objects) — there, apply it at the *edges*
(see "Functional core, imperative shell", below).

## Core principles

1. **Pure functions & referential transparency.** A pure function gives the same
   output for the same inputs and has no observable **side effects** (it doesn't
   mutate arguments, globals, or files, or otherwise touch the outside world).
   Such a call is *referentially transparent* — you could replace it with its
   result and nothing else would change — which is exactly what makes pure
   functions easy to test and safe to compose. Return results explicitly; never
   signal work by mutating shared state.

2. **Immutability.** Don't mutate data in place; produce new values and treat
   inputs as read-only. Shared mutable state is the source of most
   order-dependent bugs.

3. **Explicit inputs and outputs.** Take everything a function needs as
   **arguments** rather than reaching for local or global state, and return
   results rather than writing them somewhere. The more of a function's behavior
   its arguments determine, the more reusable and testable it is — so prefer
   adding a parameter over reading ambient state.

4. **Express everything as a function.** Prefer a function returning a value over
   a bare constant — even a fixed value. `def default_rate() -> float: return
   0.05` can be passed around, composed, overridden, or later made to depend on
   inputs, where a module-level constant must be torn out to extend. Functions
   are the unit of composition, so make everything one.

5. **Composition & currying.** Build behavior by combining small, single-purpose
   functions rather than one large procedure. Write **generic** functions and
   derive specific variants by **currying** (binding some arguments — a.k.a.
   partial application) or **composing** (chaining functions end to end) instead
   of writing each from scratch — e.g. define a general `get_many`, then get
   `get_one` by composing it with `take_one`.

6. **Higher-order functions.** Treat functions as first-class values — pass them,
   return them, store them. `map`/`filter`/`reduce` and friends express *what*
   you want done rather than spelling out *how* to loop.

7. **Declarative over imperative.** Describe the transformation, not the
   step-by-step mechanics. `[transform(x) for x in items if keep(x)]` states
   intent more directly than an accumulator loop.

8. **Lazy evaluation.** Compute values only when needed. Lazy sequences
   (generators/streams) let you work with large or infinite data and build
   pipelines that don't materialize intermediate collections — then force
   (materialize) the result at the boundary where you actually need it.

## Functional core, imperative shell

**Separate pure code from impure code.** Real programs must do I/O and hold
state, so don't pretend otherwise: push side effects (input, output, network,
mutation) to a thin outer **shell**, and keep the **core** — the decisions and
transformations — pure. The core is where the logic and the bugs live, so keeping
it pure buys testability and clarity while the shell stays small and dumb.

**Inject impure dependencies as default arguments.** When a function needs
something impure — the environment, the clock, randomness, a database handle —
take it as a parameter whose *default* is the real thing. Normal callers pass
nothing (convenient); tests pass explicit values (so the function stays pure and
deterministic under test). See `references/python.md` for the `os.environ` and
clock patterns.

## Functions over classes

Default to functions, closures, and curried functions rather than classes. A
closure captures state just as an object does but without the ceremony, and a
curried function specialises behavior without a class hierarchy. Reach for a
**class only when extending an existing hierarchy** — subclassing a framework
base, or overriding a hook the framework calls — where a class is what the API
expects. Otherwise a class holding a single method is just a function wearing a
costume. When a class genuinely *is* the right call, `be-oop` covers doing it
well.

## Model data so illegal states are unrepresentable

Use **algebraic data types** — *product* types (an "AND": a record/dataclass
holding field A **and** field B **and** …) and *sum* types (an "OR": a value that
is exactly **one of** several variants — a union, enum, or tagged union). Design
types so invalid combinations simply can't be constructed; then whole classes of
validation and defensive checks disappear because the bad state has no
representation.

## Prefer total functions

A *total* function returns a valid result for every input in its type; a
*partial* one blows up or misbehaves on some (divide-by-zero, indexing an empty
list, an unhandled case). Make functions total by **narrowing the input** so
every value is valid (accept a sum type/enum, not an arbitrary string) or by
**widening the output** to represent the awkward cases (`X | None`, a `Result`)
instead of raising. Total functions compose without hidden landmines — the
signature tells the caller nothing will explode.

## Pattern matching

Decompose data by its **shape** rather than a ladder of type checks and attribute
access. Matching on the variants of a sum type makes each case explicit and lets
the compiler/linter flag ones you forgot — the natural companion to algebraic
data types.

## Extensibility: choose your axis of change

Closed sum types and exhaustive `match` trade one kind of extensibility for
safety — the classic **expression problem**. Code grows along two axes: new
**variants** (kinds of data) and new **operations** (things you do with them).

- **Sum types + functions** (this style): adding an **operation** is easy — write
  another function over the type. Adding a **variant** is hard — you must extend
  every `match`.
- **Classes + inheritance** (OOP): the mirror image — a new **variant** is just a
  subclass (touches nothing else), but a new **operation** means editing every
  class.

Neither is more extensible in the abstract; they're open along *opposite* axes.
Pick by what you expect to grow: **stable variants, growing operations → sum
types + `match`** (keep the exhaustiveness safety); **variants others must extend
→ open dispatch (like `singledispatch`), a protocol/interface, or a class
hierarchy** (the open escape hatch, per "Functions over classes"). Open dispatch
buys that extensibility by giving up exhaustiveness — nothing statically checks
that every variant has a handler, so a missing one fails at runtime, not at
type-check time.

Extending *behavior* is never in tension: composition, higher-order functions,
and dependency injection add and reconfigure behavior without modifying existing
code — the open/closed principle, done functionally.

## Chain with monads where they fit — but stay idiomatic

Monadic patterns thread optionality, errors, or effects through a chain of steps
that each might short-circuit (`Optional`/`Result`/`Maybe` with their `map`/`bind`),
sequencing operations without a ladder of `if` checks. Use them where the language
supports them well, but **don't force idioms a language doesn't have** — bolting
Haskell-style monads onto a language without the syntax or types for them produces
code nobody else can read. Stay true to the language: in Python that's usually
`X | None` and early returns, reaching for `returns` only when it genuinely pays
(see `references/python.md`).

## Recursion, idiomatically

Recursion expresses self-similar and tree-shaped problems naturally, and in pure
FP it stands in for mutation-driven loops. But **stay true to the language**:
where there's no tail-call optimization (Python included), deep recursion
overflows the stack — so prefer iteration or comprehensions for linear passes and
reserve recursion for genuinely recursive structures.

## Language idioms

Read the file for the language you're working in:

- **Python** → `references/python.md` (comprehensions, `functools`, `itertools`,
  frozen dataclasses, currying/composition with `toolz`, dependency injection).

Add a new `references/<language>.md` when you start applying this in another
language rather than stuffing idioms into this file.
