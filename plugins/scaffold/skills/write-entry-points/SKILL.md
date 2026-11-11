---
name: write-entry-points
description: >-
  How to build an application's entry points — the drivers that invoke it: a
  command-line interface, an HTTP API, a GUI or dashboard, and the scheduled
  command a scheduler calls. Each is a thin shell over the pure core and the
  composition root that reads settings once, binds the secret into the adapter
  it builds and injects it into an operation, designed as a public surface and
  built to compose with the tools around it: CSV with a header by default and
  a format option for JSON lines, a table or Parquet, the manifest row from a
  command that acts, the exit codes run-unattended sets, a positional list
  overriding the configured one, date ranges inclusive at both ends on the CLI
  and the API, resource paths bounded by date, one handler mapping the app's
  errors to statuses, an API and a dashboard that read the store and never the
  source, and a dashboard that refreshes when the run manifest changes. Load
  it before adding or changing a CLI, API, dashboard or scheduled command,
  even before reading the package. Use whenever adding or structuring an entry
  point, designing a command's options or an API's surface, deciding what goes
  to standard output and what to standard error, taking input from arguments,
  files or standard input, exposing each pipeline stage as its own command,
  wiring dependency injection at the boundary, reading settings and finding
  the .env under a scheduler, sizing a fetch that needs warm-up history,
  picking a command's log destination and level, splitting a driver into role
  and framework packages at the right rung, or naming a launch command — even
  if the user just says "add a CLI", "expose an API", "build a dashboard",
  "run this on a schedule", or names typer, fastapi, uvicorn,
  pydantic-settings, shiny, shinywidgets or a scheduler. Language-agnostic
  principles here; Python build-outs in references/python.md. Layers on
  structure-python's drive layer and be-functional; run-unattended owns what
  the scheduled command does unwatched and its exit codes, store-data the data
  it writes, and a PLAN.md decision overrides any rule here.
---

# Write entry points

An **entry point** is a **driver**: a thin shell over the core, and the composition root that wires a concrete adapter into an operation.
Everything that reaches the app — a person at a terminal, an HTTP client, a browser, a scheduler — arrives through one.
It layers on `structure-python` (the `drive` layer) and `be-functional` (the functional core and imperative shell); what a scheduled command does when nobody is watching is `run-unattended`'s, and the data it writes is `store-data`'s.
Three mistakes account for most of what goes wrong: logic that settles in the shell instead of the core, output shaped for a person while something is piping it, and a capability reachable only as a side effect of asking for something else.
Every rule here is a default a decision in the project's `PLAN.md` overrides.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established way of wiring its entry points, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Driver shell

Each entry point reads its trigger, calls an operation with the adapter it needs injected, and renders the result its own way.
Keep it thin: logic in the shell can't be reused by a second entry point.
Presentation belongs to the driver, never the core — a CLI's table, an API's JSON, a dashboard's widgets.

**Reshaping data is not presentation.** A pivot changes what a row *is*, a change of grain that belongs to a core transform (see `be-functional`) even if a table is why you wanted it.
Ask what a second driver would do: an API serving the same report wants the same pivot and a different renderer, so the pivot is core.
The converse holds too: columns computed only for the renderer to consume and drop — a colour, a bar width — are presentation, pure or not.

**One renderer for the whole tool, told what to show rather than guessing.** A renderer that recognises column names (colouring where it finds a `status`) has put the domain in the one place meant to be domain-free, and breaks when a later command reuses a name.
Pass a **per-column description** beside the data instead — how to show each column, including its precision, since a float's own repr drops trailing zeros and a column stops lining up.

## Design the surface

An entry point is a public API: people script against it, so a renamed flag breaks a caller and a missing capability forces a fork.
Design it against three demands at once:

- **Comprehensive** — everything the core can do is reachable, each capability on its own, not as a side effect of asking for something else.
- **Expressive** — the unusual request is still sayable.
- **Brief** — defaults carry the common case, so the everyday invocation is nearly bare.

They pull against each other; resolve it with options that **combine rather than multiply** — orthogonal options mixed freely beat a flag per combination, and one option taking a value beats three variations.

- **An option that duplicates the shell earns its place only where the shell can't do the job.** `--output PATH` does what `> PATH` does for text, but a binary form can't be typed at a terminal, so `--format parquet` requires `--output` and the option is shape; for text, say in a sentence that it duplicates `>` before building it, and keep it only by convention (`curl` and `sort` take `-o`).

**Where the user or the plan fixes the option set, keep the shape and drop the extras.** Several rules here recommend options — a log destination, a format switch.
If leaving one out makes the tool behave *incorrectly* (logs in the data stream), it is shape and stays; if it only makes something harder to reach, the user may decline it.
Say which you dropped, and check what that strands: with no way to raise the log level, `info` lines are dead code.

## Expose the stages

Where the core is a sequence of transforms, give each independently useful stage its own entry point over a shared interchange format, so they compose; then add one command running the whole sequence (`nightly`), and that command is what a scheduler invokes (see `run-unattended`).
One composition root serves the person and the scheduler alike; a separate job driver exists only where the trigger is an event — a queue message, a webhook — whose framework needs its own app object.

**An option per stage on one entry point hides the structure** — the caller who wants one step gets the whole pipeline, and each new capability is another flag.
A flag swapping where a stage's *input* comes from (`--load` reading the interchange format instead of fetching) is the seam being used, and is fine; a flag deciding whether a stage *runs* (`--skip-fetch`) is not.
Two stages that differ only in what they read are one command with a positional choice — `export records|metrics`, the choice a closed set the parser lists under `--help` — not a command each, which would be two copies of the same options.

## Compose with other tools

A command-line tool is one process in a pipeline, so its input and output are interfaces.
**Aim to be indistinguishable from the tools beside it**: someone who knows `grep`, `sort` and `jq` should use yours without reading anything.
The shell's plumbing is the specification:

```bash
myapp report london --format json | jq 'select(.average > 10)'
myapp report london > report.csv
myapp report - < stations.txt
myapp report london 2> run.log
```

**Fix the form by option, never by destination.** Emit CSV with a header by default, `--format json` for newline-delimited JSON, `--format table` for a person, and `--format parquet` to a required `--output`.
CSV is the form every neighbour reads — `sort`, a spreadsheet, `polars.read_csv` — and the header is what makes a column addressable by name downstream; a headerless stream pairs with nothing but a schema the reader has to know.

- **Wrong** — the command checks whether standard output is a terminal and draws a table if so.
The form you check by hand is then never the form a script receives, and the parse fails in production.
- **Right** — a format option picks the form and an output option the destination; the same bytes reach a terminal, a pipe and a file.

Dropping *colour* off a terminal is not this — the structure is identical, and the rendering library does it for you.

**Every command emits rows on standard output, sized to what it did.** A stage that produces data emits the data; a stage that acts (`fetch`, `compute`) emits the manifest row it wrote (`store-data`) — what, how many, how long, with what outcome, and nothing when it found the lock held and wrote none (`run-unattended`) — so a scheduler's log shows the run without a second command and nothing is summarised twice; `status` emits key/value rows.
A command that prints prose on success has nothing a script can read.

**Exit with the codes `run-unattended`'s Report the outcome sets**, from every command, interactive or scheduled, so a script and a scheduler read one meaning.
**Make log destination and level configurable**, defaulting to standard error at `warning` for a person; standard output is a log destination only for a service or job that emits no data on it, and the level and file a scheduled run takes are `run-unattended`'s.

**Take input the way you give output**: from arguments or a named file, and from standard input otherwise.

- **The routes converge on one value, normalised once.** Arguments, file and standard input resolve to one list at the edge, and one function trims, folds case and deduplicates it.
Split across routes, each cleans what its own bytes obviously needed and what none made obvious is done by none.
- **The explicit routes union; standard input fills in.** Arguments and a named file were both typed, so both count.
Standard input is often attached incidentally, so read it only when no explicit source was given — as `cat a b < c` ignores `c` — and silently; an explicit `-` among the arguments mixes it in.
- **An argument is optional only when another route supplies the same value.** Optional for any other reason makes leaving it off change *what* the command does, which is a mode and belongs in an option.
The user-editable list is such a route: `fetch ITEM...` fetches the items named and bare `fetch` reads the active rows of `items.csv` (`structure-python`, Configuration), so a one-off re-fetch needs no edit to the file.
- **A date range is inclusive at both ends**, `--from` and `--to` alike, since a person asking for Monday to Friday means Friday too; the API's `start` and `end` say the same, or one request gets two answers.

## HTTP surface

An API is the CLI's surface over HTTP, so the same options become query parameters and the same rows a JSON array; design it against the same three demands.

- **A path names a resource, a query parameter narrows it**: `/readings?station=LHR&start=2026-01-01`, not `/getReadings`.
- **Bound a range by date, never by offset.** `start` and `end` (inclusive, as the CLI's `--from`/`--to` are) give the same answer on every call; `offset=200` shifts as rows arrive, so a client paging through a live source skips or repeats rows and nothing tells it.
- **An API and a dashboard read the store, never the source.** Each request calls an operation over the store's read port (`store-data`); a request that reached the rate-limited source would spend the quota a browser reload at a time, and show a different answer from the nightly's.
- **A dashboard refreshes when the run manifest changes**, not on a clock of its own, so it re-reads once a night and shows its own staleness; the Python reference has the local and the hosted mechanics.
- **One handler maps the app's errors to statuses** — an absent thing `404`, bounds out of range `422`, the rest `500` — so no route catches anything.
- **No version prefix until a second client exists.** `/v1/` promises a `/v2/` nobody has asked for; add it when a breaking change meets a client you can't update.
- **Bind to the loopback interface and skip authentication while the API is read-only on one machine**; the moment it binds beyond the machine or writes, both arrive together, since an unauthenticated writer on a network is a public form.
- **Settings reach a handler through one cached provider**, read once per process, so a handler is a function of its request, synchronous as `write-python` says; the Python reference has the mechanics.

## Composition root

The driver is the one place importing **both** an operation and a concrete adapter, injecting one into the other.
Everywhere else the core depends only on its ports, so the import arrow points inward while the driver alone names the real adapter (see `structure-python`).

**The root reads the settings once and binds each secret into the adapter it builds**, so no adapter reads the environment and no port carries a key (`structure-python`, Configuration).
A scheduler starts the job outside the repo, so the settings find the `.env` by an absolute path, never one relative to the working directory; the Python reference has it.

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

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (the role and framework packages at three rungs, the composition root binding the key, the `typer`, `fastapi` and `shiny` build-outs, the scheduled command, configuration with `pydantic-settings` and where the `.env` is found, the log handler for a terminal, a capture and a file, and launch).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
