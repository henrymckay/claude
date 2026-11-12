---
name: be-functional
description: >-
  Functional programming done well — pure functions, immutability,
  composition, explicit data flow, algebraic data types and pattern matching,
  deriving a program's functions from the shapes its data passes through, and
  specialising a generic function by partial application. Load it before the
  first line of any code you write, tidy or refactor, even a snippet answered
  inline. Use by default whenever writing, reviewing or refactoring code in
  any language, even if the user never says "functional" — and especially for
  pipelines or transformations over data; when deciding where one function
  ends and the next begins, or whether a value is a parameter or really part
  of the input; and when refactoring imperative or stateful code toward a
  cleaner functional shape. Language-agnostic principles here; Python idioms
  in references/python.md, including when toolz or plum earn their place over
  the stdlib. Layers on write-python (the in-code baseline and the error
  model); be-oop is the object-oriented counterpart.
---

# Be functional

Functional techniques are the means to code that's **expressive, composable and easy to use**, not a purity contest.
It builds on `write-python`'s in-code conventions, and `be-oop` is its object-oriented counterpart.
Three mistakes account for most of what goes wrong: reaching for ambient state instead of an argument, mutating a value rather than returning a new one, and letting a function's boundaries accrete instead of deriving them from the data flow.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Where it bends

This is the house style for all code.
Where code is stateful throughout — I/O, UIs, long-lived objects — keep it imperative with this at its edges, and reach for `be-oop` where its When to use applies.

## Core principles

- **Explicit inputs and outputs.** Take everything as arguments and return results, rather than reading ambient state or writing somewhere.
A fixed value is a function too (`write-python`'s function over a module global), so it can later be overridden or depend on inputs.
- **Write the generic function and specialise it.** Derive variants by partial application or composition — `get_one` as `take_one` after `get_many` — rather than hand-writing each.
Two mechanisms doing the *same* operation on different fields — a date filter with its own parameters beside a generic range filter for every other column — are one function not yet made generic, however special the field is to the domain.

Ambient state is the mistake that hides:

- **Wrong** — `total(items)` reads an ambient `TAX_RATE`, so a caller who needs a second rate edits the module and a test patches it.
- **Right** — `total(items, tax_rate)`: still one call, and the signature says everything the result depends on.

## Functional core, imperative shell

**Push side effects — input, output, network, mutation — to a thin shell and keep the core pure**; the core holds the logic and the bugs, so purity there buys the most.
A program may have several shells, one per entry point, each owning its own presentation over the shared core.

**Inject impure dependencies as arguments** — the environment, the clock, randomness, a data source — so tests pass fixed values.
Where the default goes depends on the effect:

- **Ambient standard-library effects** (clock, environment, randomness) default to the real thing in place; callers pass nothing, tests pass a value (patterns in `references/python.md`).
In a layered app the core takes them with no default and the driver passes the real thing, since `structure-python` keeps the core free of IO.
- **A library- or service-coupled dependency** gets **no default in the core**, which would import the library inward.
The core types it as a *port* it defines, and the entry point injects the concrete adapter — `write-entry-points`' Composition root.

## Functions over classes

Default to functions, closures and partial application; reach for a class only where `be-oop`'s When to use applies, since a one-method class is a function in costume.

## Make illegal states unrepresentable

Use **algebraic data types** — *product* records and *sum* types (exactly one of several variants: a union, enum or tagged union) — so invalid combinations can't be constructed and the checks guarding against them disappear.
Model the values the core computes over, not the syntax input arrived in: a variant per accepted phrasing models the grammar, so parse each phrasing straight to the value instead.

## Pattern matching

**A `match` whose every branch returns a constant is a lookup.** Pattern matching earns its place by destructuring — binding a variant's parts and doing different work with them.
Branches that each map one member of a closed set to a value are a mapping written as control flow, growing a case per member; write the mapping, and keep `match` for branches that differ in what they *do*.

**Don't interpolate your word into a library's name.** `getattr(client, f"get_{kind}")` assumes both vocabularies agree, and they don't — your `car` is their `automobile`, your `e-bike` has a hyphen no identifier can — so some members fail at runtime.
`getattr(client, methods[kind])` lets a mapping reconcile them; `structure-python` says where that mapping lives.

## Derive functions from the data flow

Before writing the core, write down the **sequence of shapes** the data passes through — the type going in, the type coming out, and the forms between.
A new shape appears where the **entity** changes (what the data is about), where its **grain** changes (what one element represents), or where a **new independent input enters**.
Those are the seams, and each span between two seams is one function, so you read the decomposition off the flow rather than choosing it.
Endpoints alone constrain nothing: one function doing every step still satisfies "X in, Y out".

**The seams set the functions that must exist, not the only ones allowed.** A step that leaves the shape alone can still earn its own function by being independently useful — a filter drops rows without changing what a row is, yet callers want it on its own and want to vary it.
A seam you skipped is a design error; an extra well-chosen function is not.

**Intermediate workings are not shapes.** Detail derived at the same entity and grain, from the same input, belongs *inside* one function however many steps it takes.
The tell is whether you can name the whole thing without an "and" — "totals from orders" is one transformation, where "deduplicate and total and align to months" is three wearing one name.
Below that line, extract private helpers freely to keep a function readable or share logic.

Give each function **exactly the arguments its span needs.**
Too many and it spans more than one seam, or depends on what it never uses: a value merely passed through, or restating what the input already carries, is not an argument.
Too few is subtler and worse — a function handed something upstream of its own seam must **reconstruct** its real input internally, swallowing the step before it, which is exactly how two transformations fuse and the seam between them stops existing.

**A value matched against the data element by element is input, not a parameter.** Joined, grouped by, or zipped against elements, it is an axis of the input and belongs in the input type; one genuinely fixed for the whole call (a threshold, a mode flag) stays a parameter.
Ask whether it could need to differ *between elements of a single call* — if so, it is data.

**Fix the shapes before implementing; let signatures settle as you go.** The sequence is a few lines, is where the design lives, and is costly to change once code is built on it; full argument lists can't be known up front, and inventing them early produces speculative parameters.
Treat the urge to add a parameter no shape accounts for as evidence the **flow itself is wrong**: revise the sequence rather than bolting the argument on.

**A type earns its place by crossing a seam.** Define a record for a shape the data actually takes between functions — one that survives more than one seam unchanged, holds an invariant its fields must satisfy together, or is a variant you genuinely `match` on.
A value assembled at one site and destructured at the next is that function's arguments wearing a name.
The symptoms: one field is just the field, no fields is a sentinel, and a record whose fields are all optional with defaults is an options bag that hides which ones a caller set.

**An options bag is usually a table not yet recognised.** When the fields repeat one small shape across an axis — a limit per region, a rate per currency, a threshold per metric — the record is a wide row: turn it the long way round, one row per value of that axis, joined onto the data where it applies.
The consumer stops naming fields, and adding to the axis stops touching the type — the element-by-element test above, applied to a record.

## Make functions total

Make every function *total* — valid for every input in its type — by **narrowing the input** (a sum type or enum, not an arbitrary string) or by **widening the output** for the one expected awkward case, `X | None` for a lookup miss; anything else raises, under `write-python`'s error model.

## Choose axis of change

Closed sum types with exhaustive `match` and classes with inheritance are open along *opposite* axes — the **expression problem**.
A sum type takes a new **operation** as one more function but a new **variant** only by editing every `match`; a class hierarchy takes a new variant as a subclass but a new operation only by editing every class.

Pick by what you expect to grow: **stable variants, growing operations → sum types + `match`**, keeping exhaustiveness; **variants others must extend → open dispatch (like `singledispatch`), a protocol or a class hierarchy**.
Open dispatch gives up exhaustiveness: nothing checks that every variant has a handler, so a missing one fails at runtime, not at type-check time.
Adding behaviour without editing code — open/closed — is composition, higher-order functions and injection, on either axis.

## Chain with monads

A **functor** is a wrapper you can `map` over; an **applicative** also combines independently wrapped values; a **monad** lets the next step *depend on* the previous result (`bind`) — the split `use-polars` names its `map_`/`amap_`/`bind_` steps by.
**Don't force idioms the language lacks**: Haskell-style monads without the syntax for them produce code nobody can read — in Python, `X | None` and early returns suffice.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (frozen dataclasses, sum types with `match`, partial application and composition, dependency injection, where `toolz` and `plum` earn their place).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
