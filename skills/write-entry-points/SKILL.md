---
name: write-entry-points
description: >-
  How to build an application's entry points — the drivers that invoke it: a
  command-line interface, an HTTP API, a GUI or dashboard, and scheduled or
  event-triggered jobs. Each is a thin shell over the pure core and the
  composition root that injects a concrete adapter into an operation, designed
  as a public surface and built to compose with the tools around it. Use
  whenever adding or structuring an entry point, designing a command's options
  or an API's surface, deciding what goes to standard output and what to
  standard error, taking input from arguments, files or standard input, wiring
  dependency injection at the boundary, splitting a driver into role and
  framework packages, or naming a launch command — even if the user just says
  "add a CLI", "expose an API", "build a dashboard", "run this on a schedule",
  or names typer, fastapi, uvicorn, pydantic, shiny, or a scheduler.
  Language-agnostic principles here; Python build-outs in references/python.md.
  Layers on structure-python's drive layer and be-functional.
---

# Write entry points

An **entry point** is a **driver**: a thin shell over the core, and the composition root that wires a concrete adapter into an operation.
Everything that reaches the app — a person at a terminal, an HTTP client, a browser, a scheduler — arrives through one.
It layers on `structure-python` (the `drive` layer) and `be-functional` (the functional core and imperative shell).
Three mistakes account for most of what goes wrong: logic that settles in the shell instead of the core, output shaped for a person while something is piping it, and a capability reachable only as a side effect of asking for something else.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established way of wiring its entry points, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Driver shell

Each entry point reads its trigger, calls an operation with the adapter it needs injected, and renders the result its own way.
Keep it thin: logic in the shell can't be reused by a second entry point.
Presentation belongs to the driver, never the core — a CLI's table, an API's JSON, a dashboard's widgets.

**Reshaping data is not presentation.** A pivot changes what a row *is*, a change of grain that belongs to a core transform (see `be-functional`) even if a table is why you wanted it.
Ask what a second driver would do: an API serving the same report wants the same pivot and a different renderer, so the pivot is core.
The converse holds too: columns computed only for the renderer to consume and drop — a colour, a bar width — are presentation, pure or not.

**One renderer for the whole tool, told what to show rather than guessing.** A renderer that recognises column names (colouring where it finds a `close`) has put the domain in the one place meant to be domain-free, and breaks when a later command reuses a name.
Pass a **per-column description** beside the data instead — how to show each column, including its precision, since a float's own repr drops trailing zeros and a column stops lining up.

## Design the surface

An entry point is a public API: people script against it, so a renamed flag breaks a caller and a missing capability forces a fork.
Design it against three demands at once:

- **Comprehensive** — everything the core can do is reachable, each capability on its own, not as a side effect of asking for something else.
- **Expressive** — the unusual request is still sayable.
- **Brief** — defaults carry the common case, so the everyday invocation is nearly bare.

They pull against each other; resolve it with options that **combine rather than multiply** — orthogonal options mixed freely beat a flag per combination, and one option taking a value beats three variations.

- **Spell the same idea the same way everywhere**, so one command predicts the next.
- **Treat `--help` as the documentation.** A surface understood only through a README needs redesigning.
- **Never make a prompt the only way in.** Anything asked interactively must also be settable by option, file or standard input.
- **Name the options that duplicate the shell, to whoever specified the surface.** `--output PATH` does what `> PATH` does; keeping it for convention is fine (`curl` and `sort` take `-o`), but an option nobody decided to add is one nobody will decide to remove.
Say so in a sentence before building it.

**Where a specification fixes the option set, keep the shape and drop the extras.** Several rules here recommend options — a log destination, a format switch.
If leaving one out makes the tool behave *incorrectly* (logs in the data stream), it is shape and stays; if it only makes something harder to reach, the specification may decline it.
Say which you dropped, and check what that strands: with no way to raise the log level, `info` lines are dead code.

## Expose the stages

Where the core is a sequence of transforms, give each independently useful stage its own entry point over a shared interchange format, so they compose; then add a convenience path running the whole sequence.

**An option per stage on one entry point hides the structure** — the caller who wants one step gets the whole pipeline, and each new capability is another flag.
A flag swapping where a stage's *input* comes from (`--load` reading the interchange format instead of fetching) is the seam being used, and is fine; a flag deciding whether a stage *runs* (`--skip-fetch`) is not.

## Compose with other tools

A command-line tool is one process in a pipeline, so its input and output are interfaces.
**Aim to be indistinguishable from the tools beside it**: someone who knows `grep`, `sort` and `jq` should use yours without reading anything.
The shell's plumbing is the specification:

```bash
myapp report london | jq '.[0]'
myapp report london > report.csv
myapp report - < stations.txt
myapp report london 2> run.log
```

**Fix the form by option, never by destination.** Emit the plain machine form by default and render for a person only when asked.

- **Wrong** — the command checks whether standard output is a terminal and draws a table if so.
The form you check by hand is then never the form a script receives, and the parse fails in production.
- **Right** — a format option picks the form and an output option the destination; the same bytes reach a terminal, a pipe and a file.

Dropping *colour* off a terminal is not this — the structure is identical, and the rendering library does it for you.

**Keep the channels apart.** Data goes to standard output; logs, progress, errors and prompts to standard error, so redirecting the data yields data alone.
Exit non-zero on failure, so `&&` and `set -e` work.
**Make log destination and level configurable**, defaulting to standard error; standard output is a log destination only for a service or job that emits no data on it.

**Take input the way you give output**: from arguments or a named file, and from standard input otherwise.

- **The routes converge on one value, normalised once.** Arguments, file and standard input resolve to one list at the edge, and one function trims, folds case and deduplicates it.
Split across routes, each cleans what its own bytes obviously needed and what none made obvious is done by none.
- **The explicit routes union; standard input fills in.** Arguments and a named file were both typed, so both count.
Standard input is often attached incidentally, so read it only when no explicit source was given — as `cat a b < c` ignores `c` — and silently; an explicit `-` among the arguments mixes it in.
- **An argument is optional only when another route supplies the same value.** Optional for any other reason makes leaving it off change *what* the command does, which is a mode and belongs in an option.

## Composition root

The driver is the one place importing **both** an operation and a concrete adapter, injecting one into the other.
Everywhere else the core depends only on its ports, so the import arrow points inward while the driver alone names the real adapter (see `structure-python`).

**One input can enter twice.** A bound the core filters on at the end often also sizes the fetch at the start — and a windowed computation (a running count, a moving average) needs history *before* the first row it reports.
Fetch exactly the range asked for and the answer is fast and **wrong**; the fetch window is the requested range plus a warm-up margin.

- **Derive the margin wherever the port is called** — usually the operation, since how far back the state reaches is a fact about the computation.
A driver deriving it has been taught the domain, and every second entry point re-derives it.
- **Size it from evidence**: measure how far back state reaches over real data and take a multiple of the worst case.
Where no bound exists, fetch unbounded and say so — a margin too small fails silently.
- **Check that the filter after a widened fetch removes anything.** A request aligned to whole periods may already return exactly what was asked for; a filter that drops nothing on any input is a second interpretation of the bounds to delete.
Run it and count.

## Role and framework split

Split each driver into a **role** and one or more **framework** parts:

- The **role** (CLI, API, GUI) is hollow and stable, exposing the app object under a name that hides the library.
- The **framework** part holds everything that uses or returns that library's objects.

Swap the library and only the framework part changes.

**The driver owns the destination and the choice of form; the framework package only renders.** A `display()` branching on a format flag inside the presentation library's package mostly doesn't use the library — the plain form is the data library's serialisation, the destination a file handle.
So one driver module owns input arriving by any route, another output leaving in either form, and the framework package builds its object and stops.
The package mechanics are in `references/python.md`.

## Run

Give each entry point a **launch command namespaced to the project** (`myapp-cli`, `myapp-api`, never a bare `cli`), pointing at whatever starts it: a callable app object, or a thin launcher where the framework has none.

## Kinds

Each kind is a driver over the same core, differing in trigger and presentation:

- **CLI** — arguments from a terminal, results as text.
- **API** — HTTP requests, results serialised to a wire format.
- **GUI** — a reactive interface whose inputs drive operations.
- **Jobs** — triggered by time or events (cron, a queue worker, a webhook): the ETL (extract, transform, load) shape, with the transform in the core.

A **library** has no driver — its public API is the interface (see `write-python`) — and a **data pipeline**'s transforms are core, with the job that runs them as its entry point.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (the role and framework packages, the `typer`, `fastapi` and `shiny` build-outs, jobs, configuration, logging and launch).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
