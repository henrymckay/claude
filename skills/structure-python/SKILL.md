---
name: structure-python
description: >-
  How to structure a non-trivial Python application — the hexagonal
  (ports-and-adapters) layers of a pure core (domain types, logic, and use
  cases behind ports) and an outer edge (driven adapters for IO, entry-point
  drivers at a composition root), plus where runtime data assets and the test
  suite sit alongside the code. Use when organising an app into layers,
  deciding where a module, entry point, IO adapter, data asset, or test
  belongs, packaging data through importlib.resources, applying dependency
  injection, wiring configuration and logging through the edge, or laying out the code/data/tests directories — even if the user
  just says "structure this app", "where does this go", or "clean/hexagonal
  architecture". Layers on write-python and be-functional; for building the
  entry points themselves, see write-entry-points; for scaffolding, packaging,
  and tooling, see setup-python.
---

# Structure a Python application

How to organise a non-trivial application's code — the layers, the boundaries between them, and where each module, entry point, and asset belongs.
This is the macro structure that sits above `write-python`'s in-code conventions and `be-functional`'s core/shell split; for building the entry-point drivers, see `write-entry-points`; for scaffolding, packaging, and tooling, see `setup-python`.

**In an existing project, ask first.** Where a repo already has an established layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Code

Under `mypackage/`, all the Python lives in a `code/` package, split into layers; the non-code assets sit in a `data/` directory beside it, mirroring those layers (see [Data](#data)).

```text
mypackage/
  __init__.py
  code/
    __init__.py
    adapt/
      __init__.py
    drive/
      __init__.py
    operate/
      __init__.py
    port/
      __init__.py
    transform/
      __init__.py
  data/
```

Structure `code/` as two groups: a pure **core** that holds the logic, and an outer **edge** that does all the IO — the ports-and-adapters (hexagonal) shape.
The five standard packages, each named for what it does (imperative verbs for the behavioural layers per `write-python`; `port`, a package of definitions, stays a noun):

- **`transform`** (core) — the problem's types and rules, and the pure functions over them, depending on nothing outward.
Model data so illegal states can't be built (see `be-functional`); the domain's dataclasses and enums live here too, splitting into a dedicated `domain/` package (a noun) once they multiply — never `port`.
- **`port`** (core) — the *behavioural* interfaces the core needs the outside world to satisfy, as `typing.Protocol`s or callable aliases (`Fetch = collections.abc.Callable[[list[str]], dict[str, list[float]]]`).
A noun that names *what* the core needs, not *how* — `operate` depends on it, `adapt` implements it.
Interfaces, not data, so the domain's own types stay in `transform`.
- **`operate`** (core) — the functions that orchestrate a whole task (`operate.report(stations, fetch)`), calling `transform` for logic and a `port` for IO and staying IO-free because the adapter is injected.
Imports `transform` and `port` only, one use case per module, each re-exported so a driver calls `operate.report(...)`.
- **`adapt`** (edge) — concrete implementations of the ports, each adapting an outside system to what the core expects (`httpx_.fetch` calls the weather service over HTTP and adapts its JSON to the `Fetch` port).
Imports `transform`/`port` to conform to them, never `operate` or `drive`; library-coupled modules take trailing-underscore names.
- **`drive`** (edge) — the driving side and composition root: the entry points that start the program, each importing an operation and a concrete adapter, injecting the adapter into the operation (`operate.report(stations, fetch=httpx_.fetch)`), built out in `write-entry-points`.

`mypackage/`, `code/`, and every layer under `code/` is a regular package — each carries an `__init__.py` — which is what makes `from mypackage.code import operate` and the `importlib.resources.files("mypackage")` anchor resolve; `data/` is a plain resource tree, not a package.

Two rules hold it together:

- **IO lives only at the edge.** The edge — driven adapters like `adapt`, and the drivers under `drive` — is the only code that touches the outside world: network, filesystem, clock, randomness, external services.
The core (`transform`, `port`, `operate`) stays **pure** — deterministic and side-effect-free.
Purity is about side effects, not dependencies: the core uses third-party *computation* libraries freely (`polars` for dataframes, `numpy`), and only avoids the IO/delivery frameworks (`fastapi`, `httpx`, `uvicorn`, `typer`, `shiny`) whose job *is* IO.
(Even within `polars`, the transforms are core while `scan_csv`/`write_*` are edge.)
- **Imports point inward.** The edge imports the core; the core imports neither the edge nor anything outward.
A driver is the one place that imports both an operation and a concrete adapter, to wire them together.

Control flows the other way: a running operation calls *out* through a port to whichever adapter a driver injected.
Dependency injection is what lets the import arrow point in while control flows out — the operation *calls* the adapter without *importing* it.
That injection is the essential idea (see `be-functional`).

**The names are a standard, not a fixed set.** What fixes a package is which group it's in — set by the two rules — not that it's spelled exactly `transform` or `adapt`.
Add more pure packages beside `transform` as the core grows (a `domain`, a `pricing`), and more edge packages beside `adapt` as the IO grows — an `extract` for input and a `load` for output, say (where `load` means *persist to a store*, not the on-screen presentation a driver owns).
Each new core package obeys the core's rules (no IO; imported, never importing outward); each new edge package obeys the edge's (does its own IO, imports the core, is never imported by it).

**Let it grow into the app.** A tiny tool is a module or two at the package root (`mypackage/transform.py` + `mypackage/drive.py`) — no `code/`/`data/` split; introduce the `code/` wrapper, `data/`, and the layer packages only once there's a real boundary to name — an external service, a second entry point, more than one operation, assets to separate from code.
Don't scaffold the full set for a script (KISS, YAGNI).

**Design the core's shape before the edge's.** An entry point's interface — a CLI's flags, an API's schema — invites a design pass before it's built; the core's data shape rarely does, and it is the one that matters more.
A driver is cheap to replace and serves one presentation, where the core's shape is what every adapter, operation and test is then built on, and a second entry point inherits it wholesale.
So settle the core's shapes first — `be-functional`'s "Derive functions from the data flow" is how to arrive at them.

**Reach each package through one qualified name.** A package presenting a single cohesive API re-exports it in `__init__.py`, so callers import the package and qualify through it — `transform.averages(...)`, `operate.report(...)`, `port.Fetch` — never a bare `averages` or a stuttering `average.averages`.
A package of independent peers instead keeps them as separate modules you import and qualify directly — an adapter is `httpx_.fetch`, a `typer` module is `argument.stations()`.
Either way you import a *module* and reach its members qualified through it (see `write-python`).

## Configuration

Configuration is **input crossing the boundary**, so it takes the same path as any other IO: read at the edge, validated there, injected inward.

- **Read and validate at the edge.** An adapter reads the source — environment variables, a `.env` file, a settings file — and validates it into a typed object at the boundary, the way a DTO (Data Transfer Object) validates an API body.
A `pydantic-settings` model is the usual tool.
- **Inject inward; the core never reaches out.** An operation takes the values it needs as arguments (a `rate`, a `timeout`), never a global `Settings` object and never `os.environ` — reading ambient config is IO.
This is `be-functional`'s "inject the environment as a default argument" applied to the whole app.
- **Wire it at the composition root.** The driver loads the settings once at startup and injects them into operations beside the adapters — configuration and dependencies enter through the same seam.
The concrete `pydantic-settings` loading lives in `write-entry-points`.
- **Secrets are configuration too** — the same path, from the environment or a secret store, validated at the boundary and never committed (see `use-git`).

## Logging

Logging is **output**, so like all IO it's configured at the edge — but it's pervasive, so it's carried by convention rather than a port.

- **Configure once, at the composition root.** The driver sets up the root logger and its handler at startup — level, format, a `RichHandler`; nothing else touches logging configuration.
A library or core module that calls `logging.basicConfig` hijacks its host, so configuration lives *only* in the driver (see `write-entry-points`), exactly as the suite configures it once per session (see `write-tests`).
- **Emit through a module logger.** Every module — the core included — logs through `logging.getLogger(__name__)`.
A logger is inert until the root configuration decides what to do with a record, so module loggers don't cost the core its purity under test: with no handler installed, a `debug` line simply vanishes.
- **The shell narrates; the core stays quiet.** The edge logs the IO and the boundaries it crosses — a request served, an adapter called, a job run, an error caught.
The core logs sparingly if at all: it *returns* its results, and its behaviour is pinned by tests rather than narrated in logs.
- **`rich`, and lazy.** Render through a `RichHandler` on the root logger, matching `write-tests`' session setup; write log lines with `logging`'s lazy `%` args, never f-strings (see `write-python`).
The concrete driver wiring lives in `write-entry-points`.

## Data

Load the non-code assets an app needs at runtime — SQL query files, HTML templates, static reference data — through `importlib.resources`, never a path built from `__file__` or the repo root.

Keep them all in one `data/` directory whose inside **mirrors the code layers**, so every asset's path names the layer that owns it — `data/` and `code/` are the two parallel trees under the package.
One place to manage, with ownership still explicit — only the layers that own assets need a directory:

```text
mypackage/
  code/
    adapt/
    drive/
    transform/
  data/
    adapt/
      orders.sql
    drive/
      report.html
    transform/
      regions.csv
```

- `data/adapt/` — SQL and other files a driven adapter runs.
- `data/drive/` — templates and static web files a driver renders.
- `data/transform/` — static reference data the core computes over; an edge still *loads* it and passes it in, keeping the core pure (reading a file is IO).

Where `data/` sits follows whether the assets ship — the one place its level does *not* follow `tests/`.
Package data must live **inside the package** (`src/mypackage/data/`, as above) to be installed and reachable via `importlib.resources` — not a bare `src/data/`.
`src/` is only a source root: just the package beneath it ships, with the `src/` prefix stripped, so a sibling of the package is neither packaged nor reachable as `mypackage`'s data.
`tests/` can sit at the repo root precisely because it never ships.
Reserve a repo-root `data/` (a sibling of `src/` and `tests/`, mirroring the package the same way) for data that deliberately stays out of the wheel — large datasets, dev seed data.

Reach a packaged asset by navigating from the package, not the filesystem:

```python
from importlib import resources

query = resources.files("mypackage").joinpath("data/adapt/orders.sql").read_text()
```

`hatchling` ships non-`.py` files under the package automatically, so a committed in-package `data/` needs no extra config; add `[tool.hatch.build.targets.wheel]` `artifacts` only for generated or git-ignored files.
All of this is distinct from `tests/data/` — test fixtures that never ship (see [Tests](#tests)).

## Tests

Tests live in `tests/`, never beside the source, split three ways:

```text
tests/
  data/
  pytest_/
    __init__.py
    given.py
    then.py
    when.py
  suite/
    mypackage/
    packages/
```

- **`data/`** — data files the tests load.
- **`pytest_/`** — the imported helpers, as a package (`__init__.py`): fixtures in `given.py`, custom assertions in `then.py`, and action helpers in `when.py` where actions earn a name.
It's named `pytest_` (per `write-python`'s underscore rule) because it's all `pytest`-coupled — fixtures, and assertions written as bare `assert`s rather than `unittest`'s methods.
Tests import it as `from pytest_ import then`.
- **`suite/`** — the test cases: your code mirrored in `suite/<package>/`, and dependency-behaviour tests in `suite/packages/`.
Neither `suite/` nor its subdirectories is a package — `--import-mode importlib` (below) collects the test files by path with no `__init__.py`; only `pytest_/` needs one, because it's *imported* rather than collected.
Keep the test dirs non-packages: it's `pytest`'s recommendation for new projects, and path-based collection lets same-named test files in different directories coexist without clashing.

The `pytest` settings in `setup-python`'s `pyproject.toml` serve this layout:

- `testpaths = ["tests/suite"]` collects only the cases.
- `--import-mode importlib` avoids `sys.path` clashes from the `src/` layout and nested folders.
- `pythonpath = ["tests"]` with `-p pytest_.given` makes `pytest_` importable and loads its fixtures.
- `src = ["src", "tests"]` marks `tests/` a source root so isort files `pytest_` as first-party.

Scaffold `tests/pytest_/given.py` (with its `__init__.py`) up front — `-p pytest_.given` fails to load if the module is missing.

That is the *scaffold*; the `write-tests` skill covers how to write the tests themselves — the given/when/then shape, naming, fixtures, and the rest.
