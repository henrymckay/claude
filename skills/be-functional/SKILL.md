---
name: be-functional
description: >-
  Functional programming done well — pure functions, immutability, composition,
  explicit data flow, algebraic data types and pattern matching, and deriving a
  program's functions from the shapes its data passes through. Use when the
  user asks for functional code, a "functional approach", pipelines or
  transformations over data, or wants to avoid mutation and side effects; when
  deciding where one function ends and the next begins, or whether a value is a
  parameter or really part of the input; and when refactoring imperative or
  stateful code toward a cleaner functional shape. This is an opt-in style
  skill: reach for a functional style where it genuinely fits, not by default.
  Language-agnostic principles here; Python idioms in references/python.md.
  Layers on write-python (the in-code baseline); be-oop is the object-oriented
  counterpart.
---

# Be functional

The goal is code that's **expressive, composable, and easy to use** — functional techniques are the means to that end, not a purity contest.
When behaviour depends only on a function's inputs (not hidden state or order of execution), code becomes easy to reason about, test, and reuse.
It builds on `write-python`'s in-code conventions, and `be-oop` is its object-oriented counterpart.
Three mistakes account for most of what goes wrong: reaching for ambient state instead of an argument, mutating a value rather than returning a new one, and letting a function's boundaries accrete instead of deriving them from the data flow.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**This is opt-in.** Reach for a functional style where it genuinely fits (below), not by default.

## When to use

- **Data transformations and pipelines** — mapping, filtering and aggregating data through composable steps.
- **Pure logic and calculations** — decisions that depend only on their inputs, cheap to test and safe to reuse.
- **The core of a stateful program** — keep the decision-making core pure and push I/O and mutation to a thin shell (see "Functional core, imperative shell").
- **Concurrent work** — immutability and no shared state remove whole classes of races.

If the code is naturally stateful throughout — I/O, UIs, long-lived objects — keep it imperative and apply this only at its edges.

## Core principles

- **Pure functions and referential transparency.** A pure function gives the same output for the same inputs and has no observable **side effects** (it doesn't mutate arguments, globals, or files, or otherwise touch the outside world).
Such a call is *referentially transparent* — you could replace it with its result and nothing else would change — which is exactly what makes pure functions easy to test and safe to compose.
Return results explicitly; never signal work by mutating shared state.
- **Immutability.** Don't mutate data in place; produce new values and treat inputs as read-only.
Shared mutable state is the source of most order-dependent bugs.
- **Explicit inputs and outputs.** Take everything a function needs as **arguments** rather than reaching for local or global state, and return results rather than writing them somewhere.
The more of a function's behaviour its arguments determine, the more reusable and testable it is — so add a parameter rather than read ambient state.
- **Express everything as a function.** Return a value from a function rather than declaring a bare constant — even a fixed value.
`def default_rate() -> float: return 0.05` can be passed around, composed, overridden, or later made to depend on inputs, where a module-level constant must be torn out to extend.
Functions are the unit of composition, so make everything one.
- **Composition and currying.** Build behaviour by combining small, single-purpose functions rather than one large procedure.
Write **generic** functions and derive specific variants by **currying** (binding some arguments — a.k.a. partial application) or **composing** (chaining functions end to end) instead of writing each from scratch — e.g. define a general `get_many`, then get `get_one` by composing it with `take_one`.
Two mechanisms performing the *same* operation on different fields — a date bounded by its own pair of parameters beside a generic bounds filter for every other column — is one function that has not been made generic yet, and it shows up as a special case in the caller, in the docs and in every test.
The field being special to the *domain* is not the test; the test is whether the operation differs, and "keep rows between two values" does not become a different operation because the values are dates.
- **Higher-order functions.** Treat functions as first-class values — pass them, return them, store them.
`map`/`filter`/`reduce` and friends express *what* you want done rather than spelling out *how* to loop.
- **Declarative over imperative.** Describe the transformation, not the step-by-step mechanics.
`[transform(x) for x in items if keep(x)]` states intent more directly than an accumulator loop.
- **Lazy evaluation.** Compute values only when needed.
Lazy sequences (generators/streams) let you work with large or infinite data and build pipelines that don't materialise intermediate collections — then force (materialise) the result at the boundary where you actually need it.

Of the three mistakes above, reaching for ambient state is the one that hides, so it is worth seeing spelled out:

- **Wrong** — `total(items)` reads an ambient `TAX_RATE`.
A caller who needs a second rate has to edit the module, and a test has to patch it.
- **Right** — `total(items, tax_rate)`.
Both are one call, and the signature now says everything the result depends on.

## Functional core, imperative shell

**Separate pure code from impure code.** Real programs must do I/O and hold state, so don't pretend otherwise: push side effects (input, output, network, mutation) to a thin outer **shell**, and keep the **core** — the decisions and transformations — pure.
The core is where the logic and the bugs live, so keeping it pure buys testability and clarity while the shell stays small and dumb.
A program often has *several* shells — one per entry point (a CLI, a dashboard, an HTTP API) — each thin and each owning its own **presentation** over the one shared core; so rendering and formatting belong with their entry point, never in the core.

**Inject impure dependencies as arguments.** When a function needs something impure — the environment, the clock, randomness, a data source — take it as a parameter rather than reaching for it.
Tests then pass explicit values, so the function stays pure and deterministic under test.

Where the default goes depends on *what* the effect is:

- **Ambient, standard-library effects** (the clock, `os.environ`, randomness) can **default to the real thing in place** — `def f(now=datetime.datetime.now)`.
Normal callers pass nothing; tests pass a fixed value.
See `references/python.md` for the `os.environ` and clock patterns.
- **A framework- or service-coupled dependency** (a database client, an HTTP-backed fetch, anything wrapping an external library) gets **no default in the core**.
Defaulting it would drag that library's import into the core and point the dependency arrow outward.
Instead the core takes it as a plain parameter typed as a *port* (an interface it defines), and the **entry point injects the concrete adapter** — the composition-root pattern in `structure-python`'s package layers (`transform` / `operate` / `adapt` / `drive`).
The core calls the dependency at runtime without ever importing it.

## Functions over classes

Default to functions, closures, and curried functions rather than classes.
A closure captures state just as an object does but without the ceremony, and a curried function specialises behaviour without a class hierarchy.
Reach for a **class only when extending an existing hierarchy** — subclassing a framework base, or overriding a hook the framework calls — where a class is what the API expects.
Otherwise a class holding a single method is just a function wearing a costume.
When a class genuinely *is* the right call, `be-oop` covers doing it well.

## Make illegal states unrepresentable

Use **algebraic data types** — *product* types (an "AND": a record/dataclass holding field A **and** field B **and** …) and *sum* types (an "OR": a value that is exactly **one of** several variants — a union, enum, or tagged union).
Design types so invalid combinations simply can't be constructed; then whole classes of validation and defensive checks disappear because the bad state has no representation.
Apply this to the values the core computes over, not to the syntax an input arrived in.
A variant per accepted phrasing models the grammar rather than the problem — parse each phrasing straight to the value the core needs, and the variants disappear with it.

## Pattern matching

Decompose data by its **shape** rather than a ladder of type checks and attribute access.
Matching on the variants of a sum type makes each case explicit and lets the compiler/linter flag ones you forgot — the natural companion to algebraic data types.

**A `match` whose every branch returns a different value is a lookup, not a match.**
Pattern matching earns its place by *destructuring* — binding the parts of a variant and doing different work with them.
Where each case names one member of a closed set and hands back a constant, a name or a row, the branches hold no pattern at all: the construction is a mapping written as control flow, it grows a case per member, and the set it encodes can be read by nobody but a person scrolling it.
Write the mapping instead and let the key's type carry the exhaustiveness.
Reach for `match` where the branches differ in what they *do*.

**What breaks is interpolating your word into a library's, not reaching a name dynamically.**
`getattr(client, f"get_{kind}")` assumes your vocabulary and theirs are one vocabulary, and they are not: a kind you call `coin` may be spelled `cryptocurrency`, and one you call `mutual-fund` carries a hyphen no identifier may — so two members of seven fail, at runtime, in front of whoever asked for them.
`getattr(client, kinds[kind])` is the same call with the mapping doing the reconciling, which is what a mapping was for.
Where its values are data — and a method's name is data — `structure-python` has where the mapping itself goes.

## Derive functions from the data flow

Before writing the core, write down the **sequence of shapes** the data passes through — the type going in, the type coming out, and the forms between.
A new shape appears where the **entity** changes (what the data is about), where its **grain** changes (what one element represents), or where a **new independent input enters**.
Those are the seams, and each span between two seams is one function — so the flow decides the decomposition and you read it off rather than choosing it.
Endpoints alone constrain nothing: one function doing every step still satisfies "X in, Y out".

**The seams set the functions that must exist, not the only ones allowed.** A step that changes nothing about the shape can still earn its own function by being independently useful — filtering drops rows without changing what a row is, so it is not a seam, yet it is worth naming because callers want it on its own and want to vary it.
Keep the distinction straight in both directions: a seam you skipped is a design error, where an extra well-chosen function is not.

**Intermediate workings are not shapes.** Detail derived at the same entity and grain, from the same input, belongs *inside* one function however many steps it takes.
The tell is whether you can name the whole thing without an "and" — "counts from candles" is one transformation, where "resample and count and align to dates" is three wearing one name.
Factor freely *below* that line — extract private helpers to keep a long function readable or to share logic — since the rule fixes that the **seam functions exist**, not that they are the only functions.

Give each function **exactly the arguments its span needs.**
Too many and it spans more than one seam, or depends on what it never uses: a value merely passed through, or restating what the input already carries, is not an argument.
Too few is subtler and worse — a function handed something upstream of its own seam must **reconstruct** its real input internally, swallowing the step before it, which is exactly how two transformations fuse and the seam between them stops existing.

**A value matched against the data element by element is input, not a parameter.** Joined, grouped by, or zipped against elements, it is an axis of the input and belongs in the input type; one genuinely fixed for the whole call (a threshold, a mode flag) stays a parameter.
Ask whether it could need to differ *between elements of a single call* — if so, it is data.

**Fix the shapes before implementing; let signatures settle as you go.** The sequence is a few lines to write, is where the design lives, and is costly to change once code is built on it.
Full argument lists can't be known up front, and inventing them early only produces speculative parameters (YAGNI).
But treat the urge to add a parameter that no shape accounts for as evidence the **flow itself is wrong**: revise the sequence rather than bolting the argument on.

**A type earns its place by crossing a seam.** Define a record for a shape the data actually takes between functions — one that survives more than one seam unchanged, holds an invariant its fields must satisfy together, or is a variant you genuinely `match` on.
A value assembled at one site and destructured at the next is not a type; it is that function's arguments wearing a name.
The symptoms are quick to check: one field is just the field, no fields at all is a sentinel rather than a type, and a record whose fields are all optional with defaults is an options bag that hides which ones a caller actually set.

**An options bag is usually a table that has not been recognised yet.** When the fields repeat one small shape across an axis — a bound per column, a rate per region, a threshold per metric — the record is a wide row, and the fix is to turn it the long way round: one row per value of that axis, joined onto the data where it applies.
Thirty optional fields become a frame of ten rows and three columns, the consumer stops naming any of them, and adding to the axis stops touching the type at all.
This is the same test as "a value matched against the data element by element is input, not a parameter", applied to a record instead of an argument.

## Make functions total

A *total* function returns a valid result for every input in its type; a *partial* one blows up or misbehaves on some (divide-by-zero, indexing an empty list, an unhandled case).
Make functions total by **narrowing the input** so every value is valid (accept a sum type/enum, not an arbitrary string) or by **widening the output** to represent the awkward cases (`X | None`, a `Result`) instead of raising.
Total functions compose without hidden landmines — the signature tells the caller nothing will explode.

## Choose axis of change

Closed sum types and exhaustive `match` trade one kind of extensibility for safety — the classic **expression problem**.
Code grows along two axes: new **variants** (kinds of data) and new **operations** (things you do with them).

- **Sum types + functions** (this style): adding an **operation** is easy — write another function over the type.
Adding a **variant** is hard — you must extend every `match`.
- **Classes + inheritance** (OOP): the mirror image — a new **variant** is just a subclass (touches nothing else), but a new **operation** means editing every class.

Neither is more extensible in the abstract; they're open along *opposite* axes.
Pick by what you expect to grow: **stable variants, growing operations → sum types + `match`** (keep the exhaustiveness safety); **variants others must extend → open dispatch (like `singledispatch`), a protocol/interface, or a class hierarchy** (the open escape hatch, per "Functions over classes").
Open dispatch buys that extensibility by giving up exhaustiveness — nothing statically checks that every variant has a handler, so a missing one fails at runtime, not at type-check time.

Extending *behaviour* is never in tension: composition, higher-order functions, and dependency injection add and reconfigure behaviour without modifying existing code — the open/closed principle, done functionally.

## Chain with monads

These sit on a progression worth naming: a **functor** is a wrapper you can `map` a plain function over; an **applicative** also combines several independently-wrapped values in a fixed way; a **monad** goes further, letting the next step *depend on* the previous result (`bind`).
(The `map`/`amap`/`bind` naming in `use-polars` for `.pipe()` steps follows exactly this functor/applicative/monad split.)
Monadic patterns thread optionality, errors, or effects through a chain of steps that each might short-circuit (`Optional`/`Result`/`Maybe` with their `map`/`bind`), sequencing operations without a ladder of `if` checks.
Use them where the language supports them well, but **don't force idioms a language doesn't have** — bolting Haskell-style monads onto a language without the syntax or types for them produces code nobody else can read.
Stay true to the language: in Python that's usually `X | None` and early returns, reaching for `returns` only when it genuinely pays (see `references/python.md`).

## Recursion

Recursion expresses self-similar and tree-shaped problems naturally, and in pure FP it stands in for mutation-driven loops.
But **stay true to the language**: where there's no tail-call optimisation (Python included), deep recursion overflows the stack — so prefer iteration or comprehensions for linear passes and reserve recursion for genuinely recursive structures.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (comprehensions, `functools`, `itertools`, frozen dataclasses, currying/composition with `toolz`, dependency injection).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
