---
name: write-entry-points
description: >-
  How to build an application's entry points — the drivers that invoke it: a
  command-line interface, an HTTP API, a GUI or dashboard, and scheduled or
  event-triggered jobs. Each is a thin shell over the pure core and the
  composition root that injects a concrete adapter into an operation. Use
  whenever adding or structuring an entry point, wiring dependency injection at
  the boundary, splitting a driver into role and framework packages, or naming a
  launch command — even if the user just says "add a CLI", "expose an API",
  "build a dashboard", "run this on a schedule", or names typer, fastapi,
  uvicorn, pydantic, shiny, or a scheduler. Language-agnostic principles here;
  Python build-outs in references/python.md. Layers on structure-python's drive
  layer and be-functional.
---

# Write entry points

An **entry point** is a **driver**: a thin shell over the presentation-agnostic core, and the composition root that wires a concrete adapter into an operation.
Everything that reaches the app — a person at a terminal, an HTTP client, a browser, a scheduler — arrives through one.
It layers on `structure-python` (the `drive` layer) and `be-functional` (the functional core and imperative shell).

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established way of wiring its entry points, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Driver shell

Each entry point is a thin **shell** over the core: it reads its trigger, calls an operation, injects the adapter that operation needs, and renders the result its own way.
Keep it thin — the logic stays in the core, so a second entry point can serve or render the same results differently.
Presentation belongs to the entry point, never the core: a CLI's table, an API's JSON, a dashboard's widgets are each one driver's concern.

**Reshaping the data is not presentation, however much it looks like it.** Pivoting a long result into a column per key changes what one row *is*, and a change of grain is a seam in the core (see `be-functional`) — so it belongs to a transform even when the only reason you noticed you wanted it was a table.
The line is whether the step still yields your own data: a frame in and a frame out is core, and presentation starts where the result stops being data and becomes a `Table`, a response model, a widget.
Test it by asking what a second driver would do — an API serving the same report wants the same pivot and a completely different renderer, which places the pivot on the core's side of the line.

## Expose the stages

Where the core is a sequence of transforms, give each stage that is independently useful its own entry point over a shared interchange format, so they compose — commands in a pipeline, endpoints that take one another's output.
Then add a convenience path that runs the whole sequence in one call, for when composing is more ceremony than it is worth.

**One entry point carrying an option per stage hides the structure.** It forces the whole pipeline on someone who wants one step of it, leaves each stage reachable only through the others, and turns every new capability into another flag on an already-crowded signature.
The stages are already separate in the core (see `be-functional`, "Derive functions from the data flow"); the entry point should not weld them back together.

**A flag that swaps where a stage's input comes from is not an option per stage.** `--load` reading the interchange format instead of fetching it is the pipeline's *seam being used*, not hidden — the stage boundary has to already exist for the file to be writable at all.
What the rule forbids is a flag that decides whether a stage *runs*.
So the test is whether someone can get at each stage's output on its own; a `--save`/`--load` pair passes it, while a `--skip-fetch` or a `--with-filtering` does not.
Where a user asks for the pair rather than separate commands, take it — it costs one option and duplicates no option set, which a second command carrying the same thirty filters would.

## Compose with other tools

A command-line tool is one process in a pipeline, so its input and output are interfaces rather than decoration.
Build it to be driven by a person at a terminal *and* by the shell around it, since a tool that can only be read by eye has to be rewritten the first time someone wants to script it.

**Vary the form with the destination, never the content.** Render for a person when output is a terminal, and emit the plain machine-readable form when it is redirected to a file or a pipe — the same data, shaped for whoever is reading.
Offer the choice explicitly as well, through a format option and a destination option, because a person sometimes wants the raw form on screen and a script sometimes wants the rendered one captured.

**Take input the same way you give output.** Read a path where one is named and standard input otherwise, so the tool drops into the middle of a pipeline without a wrapper around it.

**Keep the channels apart.** Data goes to standard output; logs, progress, errors and prompts all go to standard error, so redirecting the data stream yields data alone.
Exit non-zero on failure, so `&&` and `set -e` behave.

**Make the log destination and level configurable.** Standard error is the right default, but a long run someone wants to keep belongs in a file, so offer an option that diverts it there and another that sets the level.
Standard output is a valid destination only for a process that emits no data on it — the platform convention for a service or a scheduled job, and never for a tool in a pipeline.

**Never let a prompt be the only way in.** Anything the tool can ask for interactively must also be settable by option, file or standard input, or it cannot be scripted at all.

## Composition root

The driver is the one place that imports **both** an operation and a concrete adapter, and injects the adapter into the operation.
This is the **composition root** — where the abstract core meets a concrete implementation.
Everywhere else the core depends only on its **ports** (the interfaces it defines); dependency injection is what lets the import arrow point inward while the driver alone names the real adapter (see `be-functional` and `structure-python`).

**One input can enter the program twice, and the driver is what derives the second use.** A bound the core filters on at the end often also decides how much the adapter has to fetch at the start — a date range selecting rows, and the same range sizing the request.
Miss that and you either fetch everything, which is correct but slow and grows with the data, or fetch exactly the range asked for, which is fast and **wrong**.

Wrong, because a windowed computation needs history *before* the earliest row it reports on: a running count, a moving average, a state that carries forward all read candles the user never asked to see.
So the driver derives the fetch window as the requested range **plus a warm-up margin**, and only the driver knows to do that — the filter stays generic and knows nothing about warm-up, and the core cannot ask for data it was not given.

Size the margin from evidence rather than instinct: measure how far back the state actually reaches over real data, and take a multiple of the observed worst case.
Where no bound is available at all, say so in the docs rather than guessing — an unbounded fetch is the honest default, and a margin that is too small fails silently, which is the worst of the three outcomes.

## Role and framework split

Split each shell into a **role** and one or more **framework** parts:

- The **role** — what the entry point *is* (a CLI, an API, a GUI) — is stable and hollow, exposing the app object behind a name that hides which library sits behind it.
- The **framework** part holds the library-coupled code: everything that uses or returns that library's objects.

Swap the library and only the framework part changes; the role's name and launch identity stay put.
The Python package mechanics — a hollow role package over trailing-underscore framework packages — are in `references/python.md`.

## Launch

Give each entry point a **named launch command**, namespaced to the project so it doesn't collide once installed (`myapp-cli`, `myapp-api`, never a bare `cli`).
The command points at whatever *starts* that entry point: a callable app object where the framework provides one, or a thin launcher function where it doesn't.

## Kinds

Each kind is a driver over the same core, differing only in trigger and presentation:

- **CLI** — arguments and options from a terminal, results rendered as text.
- **API** — HTTP requests over the core, results serialised to a wire format.
- **GUI** — a reactive user interface whose inputs drive operations and whose outputs render their results.
- **Jobs** — triggered by *time or events* rather than a person (a cron run, a queue worker, a webhook, a serverless function): the ETL (extract, transform, load) shape, with the transform in the core.

Two things look like entry points but aren't:

- A **library** — if the project is imported by other code, its public API *is* its interface; there's no shell, only the public surface (see `write-python`).
- A **data pipeline** — the transforms are core; the entry point is the *job* that runs them, not the pipeline itself.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (the role and framework packages, the `typer`, `fastapi` and `shiny` build-outs, jobs, and the dependency-injection seams).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
