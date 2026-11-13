---
name: write-entry-points
description: >-
  How to build an application's entry points — a CLI, an HTTP API, a dashboard
  or web front end, and the command a scheduler calls — as thin drivers over
  the core: output forms, exit codes, settings read once, a guarded loopback
  server. Load it before adding or changing a CLI, API, dashboard or scheduled
  command. Use whenever building or structuring one — even if the user just
  says "add a CLI", "expose an API" or "build a dashboard".
---

# Write entry points

An **entry point** is a **driver**: a thin shell over the core, and the composition root that wires a concrete adapter into an operation.
Everything that reaches the app — a person at a terminal, an HTTP client, a browser, a scheduler — arrives through one.
It layers on `structure-python` (the `drive` layer) and `be-functional` (the functional core and imperative shell); how a surface looks is `design-interface`'s, what a scheduled command does when nobody is watching is `run-unattended`'s, the data it writes is `store-data`'s, and what a served surface must guard is `secure-project`'s.
Three mistakes account for most of what goes wrong: logic that settles in the shell instead of the core, output shaped for a person while something is piping it, and a capability reachable only as a side effect of asking for something else.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**In an existing project, ask first.** Where a repo already has an established way of wiring its entry points, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Driver shell

Each entry point reads its trigger, calls an operation with the adapter it needs injected, and renders the result its own way.
Logic in the shell can't be reused by a second entry point; presentation — a CLI's table, an API's JSON, a dashboard's widgets — belongs to the driver, never the core.

**Reshaping data is not presentation.** A pivot changes what a row *is*, a change of grain that belongs to a core transform (`be-functional`): an API serving the same report wants the same pivot and a different renderer.
Conversely, columns computed only for the renderer to consume and drop — a colour, a bar width — are presentation, pure or not.

**One renderer for the whole tool, told what to show rather than guessing.** A renderer that recognises column names (colouring where it finds a `status`) has put the domain in the one place meant to be domain-free, and breaks when a later command reuses a name.
Pass a **per-column description** beside the data instead, precision included, since a float's own repr drops trailing zeros and a column stops lining up.

## Design the surface

An entry point is a public API: a renamed flag breaks a caller and a missing capability forces a fork.
Design it against three demands at once:

- **Comprehensive** — everything the core can do is reachable, each capability on its own, not as a side effect of asking for something else.
- **Expressive** — the unusual request is still sayable.
- **Brief** — defaults carry the common case, so the everyday invocation is nearly bare.

Resolve the pull between them with options that **combine rather than multiply** — orthogonal options mixed freely beat a flag per combination, and one option taking a value beats three variations.

**An option that duplicates the shell earns its place only where the shell can't do the job.** `--output PATH` does what `> PATH` does for text, but a binary form can't be typed at a terminal, so `--format parquet` requires `--output`; for text, say that it duplicates `>` before building it, and keep it only by convention (`curl` and `sort` take `-o`).

**Where the user or the plan fixes the option set, keep the shape and drop the extras.** An option whose absence makes the tool behave *incorrectly* (logs in the data stream) is shape and stays; one that only makes something harder to reach the user may decline.
Say which you dropped, and check what that strands: with no way to raise the log level, `info` lines are dead code.

## Expose the stages

Where the core is a sequence of transforms, give each independently useful stage its own entry point over a shared interchange format, so they compose; then add one command running the whole sequence (`nightly`), and that command is what a scheduler invokes (see `run-unattended`).
One composition root serves the person and the scheduler alike; a separate job driver exists only where the trigger is an event — a queue message, a webhook — whose framework needs its own app object.

**An option per stage on one entry point hides the structure** — the caller who wants one step gets the whole pipeline, and each new capability is another flag.
A flag swapping where a stage's *input* comes from (`--load` reading the interchange format instead of fetching) is fine; a flag deciding whether a stage *runs* (`--skip-fetch`) is not.
Two stages that differ only in what they read are one command with a positional choice from a closed set (`export records|metrics`), not two copies of the same options.

## Compose with other tools

**A command-line tool is one process in a pipeline**, so the shell's plumbing is the specification:

```bash
myapp report london --format json | jq 'select(.average > 10)'
myapp report london > report.csv
myapp report - < stations.txt
myapp report london 2> run.log
```

**Fix the form by option, never by destination.** Emit CSV with a header by default, `--format json` for newline-delimited JSON, `--format table` for a person, and `--format parquet` to a required `--output`.
CSV is the form every neighbour reads — `sort`, a spreadsheet, `polars.read_csv` — and the header makes a column addressable by name downstream, where a headerless stream needs a schema the reader has to know.

- **Wrong** — the command checks whether standard output is a terminal and draws a table if so.
The form you check by hand is then never the form a script receives, and the parse fails in production.
- **Right** — a format option picks the form and an output option the destination; the same bytes reach a terminal, a pipe and a file.

Dropping *colour* off a terminal is not this — the structure is identical, and the rendering library does it for you.

**Every command emits rows on standard output, sized to what it did, never prose.** A stage that produces data emits the data; a stage that acts (`fetch`, `compute`) emits the manifest row it wrote (`store-data`), or nothing when it found the lock held (`run-unattended`), so a scheduler's log shows the run without a second command; `status` emits key/value rows.

**Exit with the codes `run-unattended`'s Report the outcome sets**, from every command, interactive or scheduled, so a script and a scheduler read one meaning.
**Make log destination and level configurable**, defaulting to standard error at `warning` for a person; standard output is a log destination only for a service or job that emits no data on it, and the level and file a scheduled run takes are `run-unattended`'s.

**Take input the way you give output**: from arguments or a named file, and from standard input otherwise.

- **The routes converge on one value, normalised once.** Arguments, file and standard input resolve to one list at the edge, and one function trims, folds case and deduplicates it; split across routes, a step no route's bytes made obvious is done by none.
- **The explicit routes union; standard input fills in.** Arguments and a named file were both typed, so both count; standard input is often attached incidentally, so read it silently and only when no explicit source was given, as `cat a b < c` ignores `c`, unless an explicit `-` mixes it in.
- **An argument is optional only when another route supplies the same value**; otherwise leaving it off changes *what* the command does, a mode that belongs in an option.
The user-editable list is such a route: bare `fetch` reads the active rows of `items.csv` (`structure-python`, Configuration) and `fetch ITEM...` overrides it.
- **A date range is inclusive at both ends**, `--from` and `--to` alike, since a person asking for Monday to Friday means Friday too; the API's `start` and `end` say the same, or one request gets two answers.

## HTTP surface

An API is the CLI's surface over HTTP: the same options become query parameters and the same rows a JSON array.

- **Bound a range by date, never by offset.** `start` and `end` give the same answer on every call; `offset=200` shifts as rows arrive, so a client paging through a live source skips or repeats rows and nothing tells it.
- **An API and a dashboard read the store, never the source**, through an operation over the store's read port (`store-data`); a request reaching the rate-limited source would spend the quota a browser reload at a time, and answer differently from the nightly.
- **One handler maps the app's errors to statuses** — an absent thing `404`, bounds out of range `422`, the rest `500` — so no route catches anything.
- **No version prefix until a second client exists.** `/v1/` promises a `/v2/` nobody has asked for; add it when a breaking change meets a client you can't update.
- **Bind to the loopback interface and skip authentication while the API is read-only on one machine**; the `Host` and `Origin` check, and the authentication that arrives once it binds beyond the machine or writes, are `secure-project`'s Guard what is served.
- **Settings reach a handler through one cached provider**, read once per process, so a handler is a function of its request; the Python reference has the mechanics.

## Dashboard

A dashboard is a driver like the others; its look is `design-interface`'s.

**Build it as a web front end behind one data module**, by default: Vite, React and TypeScript with Tailwind and shadcn/ui, Lightweight Charts for candles and ECharts for the rest.
Every screen asks one module, `web/src/lib/data.ts`, for its data, in one of two versions, so moving a dashboard between a static host and the API changes one module:

- **Over the API**, where the project is Python: the same process serves the API's JSON and the built front end, on one port.
- **Over files**, where nothing needs a server: small pre-aggregated Parquet files beside the page, read in the browser with `hyparquet`, on a static host (`deploy-project`).

In a trial of one three-screen dashboard over two million rows on loopback (2026-11-12), this pick was ready in 0.45 s from 340 KB with each interaction in 50 to 180 ms; the static version in 0.74 s from 3.5 MB.
The cost is a second toolchain, Node, carried as a development dependency (the Python reference).

- **Dash with Mantine** when the code must stay Python only — the owner will maintain it without TypeScript, or a host runs Python only; it reached the same look (`design-interface`) but took 1.6 s and 9.8 MB to be ready, with interactions of 180 ms to 1.1 s.
- **Shiny** for an existing Shiny app, or where every interaction must run Python on the server; restyled it matched the look, at 2.2 s and 6.2 MB.
- **Observable Framework** for a report that is mostly prose around charts, rebuilt by the pipeline; **DuckDB-WASM** only when the viewer must write SQL, since it ships tens of megabytes.
- **Ruled out** by the same research: Streamlit, which reruns the whole script on every interaction, server BI tools and Evidence.

**Re-read the store when the run manifest changes**: poll the manifest's last run and fetch the data again only when it changes.
**Re-judge the last run's age on a slow clock** — a minute to an hour — since a night that never ran changes no file, and a tab left open would show yesterday's verdict for ever.
**Give the browser two signals**: each screen's navigation control carries `data-view="<screen>"`, and the root element's `data-ready` is `1` once the screen on show has drawn its data and `0` while another loads, so a smoke test and the build's evaluator wait for data, never a guessed delay, and never shoot a skeleton.

**Test it as `write-tests` tests a dashboard**, each screen through the framework's in-process client and one browser smoke test per screen that waits for `data-ready`; the Python reference has each build-out.

## Composition root

The driver is the one place importing **both** an operation and a concrete adapter, injecting one into the other (`structure-python`, Code).

**The root reads the settings once and binds each secret into the adapter it builds**, so no adapter reads the environment and no port carries a key (`structure-python`, Configuration).
A scheduler starts the job outside the repo, so the settings find the `.env` by an absolute path, never one relative to the working directory; the Python reference has it.

**One input can enter twice.** A windowed computation (a running count, a moving average) needs history *before* the first row it reports, so the bound the core filters on at the end also sizes the fetch at the start: fetch exactly the range asked for and the answer is fast and **wrong**, so fetch the range plus a warm-up margin.

- **Derive the margin wherever the port is called** — usually the operation, since how far back the state reaches is a fact about the computation; a driver deriving it has been taught the domain, and the next entry point re-derives it.
- **Size it from evidence**: a multiple of the worst case measured over real data, or, where no bound exists, an unbounded fetch said so — a margin too small fails silently.
- **Check by counting that the filter after a widened fetch removes anything**: a request aligned to whole periods may already return exactly what was asked for, and a filter that drops nothing on any input is a second interpretation of the bounds to delete.

## Role and framework split

Split each driver into a **role** and one or more **framework** parts:

- The **role** (CLI, API, GUI) is hollow and stable, exposing the app object under a name that hides the library.
- The **framework** part holds everything that uses or returns that library's objects.

Swap the library and only the framework part changes.

**The driver owns the destination and the choice of form; the framework package only renders.** A `display()` branching on a format flag inside the presentation library's package mostly doesn't use the library — the plain form is the data library's serialisation, the destination a file handle — so one driver module owns input by any route, another output in either form.

## Run

Give each entry point a **launch command namespaced to the project** (`myapp-cli`, `myapp-api`, never a bare `cli`), pointing at whatever starts it: a callable app object, or a thin launcher where the framework has none.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (the role and framework packages, the `typer` and `fastapi` build-outs, the dashboard as a web front end, with Dash and with Shiny, and testing each, the loopback guard, the scheduled command, `pydantic-settings` and the `.env`, the log handler, and launch).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
