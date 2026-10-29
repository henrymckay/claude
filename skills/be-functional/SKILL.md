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

- **Pure functions.** Same output for the same inputs, and no observable side effects — no mutating arguments, globals or files.
Such a call is *referentially transparent*: replace it with its result and nothing changes, which is what makes it easy to test and safe to compose.
- **Immutability.** Produce new values and treat inputs as read-only; shared mutable state causes most order-dependent bugs.
- **Explicit inputs and outputs.** Take everything as arguments and return results, rather than reading ambient state or writing somewhere; the more the arguments determine, the more reusable the function.
A fixed value is a function too (`write-python`'s function over a module global), so it can later be overridden or depend on inputs.
- **Composition and currying.** Build behaviour from small single-purpose functions; write a **generic** function and derive variants by currying (binding some arguments) or composing — `get_one` as `take_one` composed with `get_many`.
Two mechanisms doing the *same* operation on different fields — dates bounded by their own parameters beside a generic range filter for every other column — are one function not yet made generic.
The test is whether the operation differs, not whether the field is special to the domain.
- **Higher-order and declarative.** Pass, return and store functions; say *what* (`[transform(x) for x in items if keep(x)]`), not how to loop.
- **Lazy evaluation.** Build pipelines over generators or streams that never materialise intermediates, and force the result at the boundary that needs it.

Ambient state is the mistake that hides:

- **Wrong** — `total(items)` reads an ambient `TAX_RATE`.
A caller who needs a second rate has to edit the module, and a test has to patch it.
- **Right** — `total(items, tax_rate)`.
Both are one call, and the signature now says everything the result depends on.

## Functional core, imperative shell

**Separate pure code from impure code.** Push side effects — input, output, network, mutation — to a thin **shell**, and keep the **core** of decisions and transformations pure; the core holds the logic and the bugs, so purity there buys the most.
A program may have several shells, one per entry point, each owning its own presentation over the shared core.

**Inject impure dependencies as arguments** — the environment, the clock, randomness, a data source — so tests pass fixed values.
Where the default goes depends on the effect:

- **Ambient standard-library effects** (clock, environment, randomness) default to the real thing in place; callers pass nothing, tests pass a value (patterns in `references/python.md`).
- **A library- or service-coupled dependency** gets **no default in the core**, which would import the library inward.
The core types it as a *port* it defines, and the entry point injects the concrete adapter — `structure-python`'s composition root.

## Functions over classes

Default to functions, closures and curried functions: a closure captures state without the ceremony, and currying specialises without a hierarchy.
Reach for a class only where `be-oop`'s When to use applies — extending a framework hierarchy, a long-lived stateful object, an invariant to guard — since a one-method class is a function in costume.

## Make illegal states unrepresentable

Use **algebraic data types** — *product* types (a record of field A **and** field B) and *sum* types (exactly **one of** several variants: a union, enum or tagged union) — so invalid combinations can't be constructed and the checks guarding against them disappear.
Model the values the core computes over, not the syntax input arrived in: a variant per accepted phrasing models the grammar, so parse each phrasing straight to the value instead.

## Pattern matching

Decompose data by its **shape** rather than a ladder of type checks; matching a sum type's variants makes each case explicit and lets the checker flag a forgotten one.

**A `match` whose every branch returns a constant is a lookup.** Pattern matching earns its place by destructuring — binding a variant's parts and doing different work with them.
Branches that each map one member of a closed set to a value are a mapping written as control flow, growing a case per member; write the mapping, and keep `match` for branches that differ in what they *do*.

**Don't interpolate your word into a library's name.** `getattr(client, f"get_{kind}")` assumes both vocabularies agree, and they don't — your `fund` is their `mutual_fund`, your `real-estate` has a hyphen no identifier can — so some members fail at runtime.
`getattr(client, methods[kind])` lets a mapping reconcile them; `structure-python` says where that mapping lives.

## Derive functions from the data flow

Before writing the core, write down the **sequence of shapes** the data passes through — the type going in, the type coming out, and the forms between.
A new shape appears where the **entity** changes (what the data is about), where its **grain** changes (what one element represents), or where a **new independent input enters**.
Those are the seams, and each span between two seams is one function — so the flow decides the decomposition and you read it off rather than choosing it.
Endpoints alone constrain nothing: one function doing every step still satisfies "X in, Y out".

**The seams set the functions that must exist, not the only ones allowed.** A step that changes nothing about the shape can still earn its own function by being independently useful — filtering drops rows without changing what a row is, so it is not a seam, yet it is worth naming because callers want it on its own and want to vary it.
Keep the distinction straight in both directions: a seam you skipped is a design error, where an extra well-chosen function is not.

**Intermediate workings are not shapes.** Detail derived at the same entity and grain, from the same input, belongs *inside* one function however many steps it takes.
The tell is whether you can name the whole thing without an "and" — "totals from orders" is one transformation, where "deduplicate and total and align to months" is three wearing one name.
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
Make functions total by **narrowing the input** so every value is valid (accept a sum type/enum, not an arbitrary string) or by **widening the output** to represent the *expected* awkward cases (`X | None`, a `Result`) instead of raising; a genuine failure still raises.
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

A **functor** is a wrapper you can `map` a function over; an **applicative** also combines independently wrapped values in a fixed way; a **monad** lets the next step *depend on* the previous result (`bind`) — the split `use-polars` names its `map_`/`amap_`/`bind_` steps by.
Monads thread optionality, errors or effects through steps that may short-circuit, without a ladder of `if`s.
**Don't force idioms the language lacks**: Haskell-style monads without the syntax for them produce code nobody can read — in Python, `X | None` and early returns usually suffice (see `references/python.md`).

## Recursion

Recursion suits tree-shaped problems, but without tail-call optimisation (Python included) deep recursion overflows the stack, so use iteration for linear passes and recursion for genuinely recursive structures.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (comprehensions, `functools`, `itertools`, frozen dataclasses, currying/composition with `toolz`, dependency injection).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
