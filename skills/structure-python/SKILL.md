---
name: structure-python
description: >-
  How to structure a non-trivial Python application into clean layers — the
  hexagonal (ports-and-adapters) shape: a pure core of domain types, logic,
  and use cases behind ports; driven adapters for IO; and entry-point drivers
  (CLI, API, GUI, jobs) that wire a concrete adapter into an operation at a
  composition root. Use when organising an app into layers, deciding where a
  module, entry point, IO adapter, or data asset belongs, applying dependency
  injection, or laying out the code/data/tests directories — even if the user
  just says "structure this app", "where does this go", or "clean/hexagonal
  architecture". Layers on write-python and be-functional; for scaffolding,
  packaging, and tooling, see setup-python.
---

# Structure a Python application

How to organise a non-trivial application's code — the layers, the boundaries between them, and where each module, entry point, and asset belongs.
This is the macro structure that sits above `write-python`'s in-code conventions and `be-functional`'s core/shell split; for scaffolding, packaging, and tooling, see `setup-python`.

**Match an existing project first.** If there's already an established layout, follow it rather than imposing this.

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

### Layers

Structure `code/` as two groups: a pure **core** that holds the logic, and an outer **edge** that does all the IO — the ports-and-adapters (hexagonal) shape.
The standard packages are `transform`, `port` and `operate` in the core, and `adapt` and `drive` at the edge, each named for what it does (imperative verbs for the behavioural layers per `write-python`; `port`, a package of definitions, stays a noun).

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
Add more pure packages beside `transform` as the core grows (a `domain`, a `pricing`), and more edge packages beside `adapt` as the IO grows — an `extract` for input and a `load` for output, say.
Each new core package obeys the core's rules (no IO; imported, never importing outward); each new edge package obeys the edge's (does its own IO, imports the core, is never imported by it).

**Let it grow into the app.** A tiny tool is a module or two at the package root (`mypackage/transform.py` + `mypackage/drive.py`) — no `code/`/`data/` split; introduce the `code/` wrapper, `data/`, and the layer packages only once there's a real boundary to name — an external service, a second entry point, more than one operation, assets to separate from code.
Don't scaffold the full set for a script (KISS, YAGNI).

**Reach each package through one qualified name.** A package presenting a single cohesive API re-exports it in `__init__.py`, so callers import the package and qualify through it — `transform.averages(...)`, `operate.report(...)`, `port.Fetch` — never a bare `averages` or a stuttering `average.averages`.
A package of independent peers instead keeps them as separate modules you import and qualify directly — an adapter is `httpx_.fetch`, a typer module is `argument.stations()`.
Either way you import a *module* and reach its members qualified through it (see `write-python`).

### transform

The types and rules of the problem, plus the pure functions over them, depending on nothing outward.
Model data so illegal states can't be built (see `be-functional`).
Reads as a phrase where it's called: `transform.averages(readings)`.

```text
transform/
  __init__.py
  average.py
```

The domain types that model the problem — dataclasses and enums like a `Reading` or a `Scale` — live here too for a small app; split them into a dedicated `domain/` package (a noun) once they multiply, leaving the pure functions in `transform`.
They're the domain's data, so they sit in the core, never in `port`.

### port

The *behavioural* interfaces the core needs the outside world to satisfy — `typing.Protocol`s or callable type aliases (`Fetch = collections.abc.Callable[[list[str]], dict[str, list[float]]]`).
A port names *what* the core needs, not *how*: `operate` depends on it, `adapt` implements it.
A noun, because it only defines.
Ports are interfaces, not data — the domain's own dataclasses and enums are *not* ports; they belong with the domain (see `transform` above), though a port's signature may reference them.

```text
port/
  __init__.py
  fetch.py
```

### operate

The functions that orchestrate a whole task (`operate.report(stations, fetch)`): call `transform` for logic and a `port` for I/O, staying IO-free because the adapter is injected.
Imports `transform` and `port` only.

```text
operate/
  __init__.py
  report.py
```

Each use case is a module, re-exported in `operate/__init__.py` per the qualified-name rule above, so a driver calls `operate.report(...)`:

```python
from mypackage.code.operate.report import report

__all__ = ["report"]
```

### adapt

The IO layer: concrete implementations of the ports, each adapting an outside system to what the core expects — `adapt`'s `httpx_.fetch` calls the weather service over HTTP and adapts its JSON response to the `Fetch` port.
Imports `transform`/`port` to conform to them; never imports `operate` or `drive`.
Library-coupled modules take trailing-underscore names.

```text
adapt/
  __init__.py
  httpx_.py
```

When the IO splits into an `extract`/`load` pair above, `load` means *persist to a store* — not on-screen presentation, which is a driver's job and belongs in `drive`.

### drive

The driving side and composition root: the entry points (CLI, API, GUI, jobs) that start the program.
A driver imports both an operation and a concrete adapter and injects one into the other:

```python
from mypackage.code import operate
from mypackage.code.adapt import httpx_

operate.report(stations, fetch=httpx_.fetch)
```

The role packages, framework packages, and presentation a driver holds are covered under Entry points below.

```text
drive/
  __init__.py
  cli/
    __init__.py
  rich_/
    __init__.py
  typer_/
    __init__.py
```

### Entry points

Every project is reached through one or more **entry points** — the ways it gets invoked.
These are the **drivers**: each is a thin **shell** over the presentation-agnostic core (see [Layers](#layers) above) that calls an operation, injects the concrete adapter it needs, and owns its own presentation — so a second entry point can serve or render the same results its own way.
Every driver lives under `code/drive/`.

Split each shell into a **role package** and one or more **framework packages**:

- The **role package** (`cli`, `api`, `gui`) is named for *what it is* and is hollow — it just re-exports the app object, giving a stable entry point (`mypackage.code.drive.cli:app`) that hides which library is behind it.
- The **framework packages** (`typer_`, `rich_`, `fastapi_`, `shiny_`) hold the tightly-coupled code — everything that uses or returns that library's objects.
  They take the trailing-underscore name (per `write-python`), which both marks the coupling and avoids shadowing the real `typer`/`rich`.
  Swap the library and only the framework package changes; the role name stays put.

**Launch each entry point with a `[project.scripts]` command named `<project>-<role>`** — `mypackage-cli`, `mypackage-api`, `mypackage-gui`, run with `uv run mypackage-cli ...`.
That name is a *global* command (it lands on `PATH` when the package is installed), so it must be namespaced to the project, not a bare `cli`/`api`/`gui`; `uv run` scoping to the local env doesn't change that.
(If one interface is clearly primary you can give it the bare project name and suffix only the rest, but symmetric `<project>-<role>` reads better for peers.)
The command points at whatever *starts* that entry point: a callable app object where the framework gives one (a `typer` app is callable), or a thin `run()` launcher where it doesn't (`uvicorn.run(app)` for an API, `shiny.run_app(app)` for a GUI).

Two things are *not* separate entry points:

- A **library** — if the project is imported by other code, its public API *is* the interface; there is no shell, only the `__all__` / public surface (see `write-python`).
- A **data pipeline** — the transforms are core; the entry point is the *job* that runs them (see [Jobs](#jobs) below).

Each shell type is built out below.

### CLI

`typer` for the CLI, `rich` for output (see Reach-for libraries in `setup-python`).
Three packages under `code/drive/`:

- **`cli/`** — the hollow role package, re-exporting the app as the stable entry point `mypackage.code.drive.cli:app`.
- **`typer_/`** — the typer-coupled code, in singular modules read as `category.member`: `argument.py` and `option.py` return a configured `typer.Argument`/`typer.Option`, and `command.py` holds the commands.
- **`rich_/`** — the rich-coupled rendering, building the table and colours from the core's plain results.

`cli/__init__.py` is a one-line re-export, so the entry point never names the framework behind it:

```python
from mypackage.code.drive.typer_ import app

__all__ = ["app"]
```

`typer_/__init__.py` creates the app, then imports `command` for the side effect of registering its `@app.command()` decorators — the import sits after `app` exists, hence the `noqa`:

```python
import typer

app = typer.Typer()

from mypackage.code.drive.typer_ import command  # noqa: E402, F401
```

`command.py` is the **composition root**: the one place that imports an operation and a concrete adapter, injects the adapter into the operation, and hands the plain result to `rich_` to render:

```python
import typing

from mypackage.code import operate
from mypackage.code.adapt import httpx_
from mypackage.code.drive.rich_ import render
from mypackage.code.drive.typer_ import app, argument, option


@app.command()
def report(stations: typing.Annotated[list[str], argument.stations()]) -> None:
    """Report the average temperature for each station."""
    render.table(operate.report(stations, fetch=httpx_.fetch))
```

A `typer` app is callable, so the console script points straight at it (`mypackage-cli = "mypackage.code.drive.cli:app"` under `[project.scripts]`); run it with `uv run mypackage-cli ...`, or `mypackage-cli` once installed.
Add a thin `__main__.py` that imports `app` and calls `app()` only if you also want `python -m mypackage.code.drive.cli`.

**Break each argument and option out into a function returning its config — at any size.**
A `typer` command's inline `Annotated[...]` bloats the signature fast, so define the argument or option once and reference it — the same shared-helper idea as `given`/`when`/`then` in tests, config defined once and signatures kept readable:

```python
def stations() -> typer.models.ArgumentInfo:
    """The stations positional argument."""
    return typer.Argument(help="Weather station IDs, e.g. london tokyo.")
```

**Keep help text terse — lean on defaults, not examples.**
Don't stuff usage examples into a help string; a well-chosen **default** documents both the format and a sensible value at once (a `--days` defaulting to `7` is its own example), and `typer` shows defaults in `--help`.

Presentation config obeys the function-over-constant rule — a `_colour(direction)` function in `rich_`, not a module-level `dict` (see `be-functional`).
A throwaway one-command tool can collapse `typer_` and `rich_` into a single `cli.py` (KISS) — but keep it out of the core.

### API

`fastapi` for an HTTP API (see Reach-for libraries in `setup-python`), served with `uvicorn` and its models built on `pydantic`.
Under `code/drive/`, a hollow `api/` role package re-exports the app and launcher, over two framework packages — `fastapi_/` for the routing and `pydantic_/` for the schemas — the way the CLI splits `typer_/` and `rich_/`:

```text
api/
  __init__.py   role, hollow: re-exports app and run
fastapi_/
  __init__.py   app = fastapi.FastAPI(); includes the router; run() launcher
  depend.py     factories returning a fastapi.Depends marker
  provide.py    the providers Depends calls — names the concrete adapter
  query.py      functions returning a configured fastapi.Query
  route.py      the path operations that call the core
pydantic_/
  __init__.py
  schema.py     the request/response models (BaseModel DTOs)
```

`schema.py` holds the boundary DTOs — the `pydantic.BaseModel`s FastAPI validates and serialises (a `Reading` with `station: str` and `average: float`).
These are pydantic-coupled, so they live in a `pydantic_` package, not `fastapi_` — the `fastapi_` (routing) / `pydantic_` (data schemas) split parallels the CLI's `typer_` (parsing) / `rich_` (presentation); the schema *is* the API's presentation.

A DTO is **not** a domain type, even when their fields match.
The schema is the external **contract**; the domain model is the internal truth; keep them separate so they evolve independently (API versioning vs domain logic) and untrusted input is validated at the boundary.
Map between them in `route.py`, as `schema.Reading(...)` does below.
Neither belongs in `port/`, which is protocols only; the domain types live in `transform`/`domain`.

Pydantic is best used at exactly this kind of **trust boundary** — validating and (de)serialising data as it crosses in or out: API bodies here, `pydantic-settings` for config from the environment, or parsing an external response inside an adapter.
It's a data library, not an IO framework, so it's *allowed* in the pure core too — but there the data is already validated, so a plain frozen `dataclasses.dataclass` is the lighter default; reach for pydantic in the core only when you specifically want its validation or serialisation there.
Enums are the one thing you never duplicate: pydantic accepts a stdlib `enum.Enum`, so a domain `Scale` is imported and referenced straight in a schema field; only a genuinely API-only enum (a sort order) lives in the driver.

**A model shared across layers moves inward, to the core.** `pydantic_` here holds *only* the API's own schemas.
Because `adapt` never imports `drive`, the two edges can't share a boundary model — so a pydantic model you find yourself wanting in *both* `adapt` and `drive` isn't a boundary DTO, it's a **domain model**: put it in `transform`/`domain`, which both edges import inward (pydantic is fine there).
Each boundary DTO otherwise stays with its own edge — the API's schemas in `drive/pydantic_`, an external service's shape in the `adapt` module that parses it — never hoisted into one shared edge package.

**FastAPI declares parameters exactly as Typer does** — the same author built both, and both read `typing.Annotated[T, marker()]`, the marker carrying the framework metadata.
Typer's `Argument`/`Option` are FastAPI's `Query`, `Path`, `Body`, `Header` and `Depends`.
So `fastapi_` mirrors `typer_`'s structure: where `typer_` splits factory functions across `argument.py` and `option.py`, `fastapi_` has **a module per request marker** — `query.py`, plus `path.py`/`body.py`/`header.py` as those markers are used — each holding functions that return a configured marker, one per parameter (`query.stations()`, read as `category.member`).
`fastapi.Query` alone takes many arguments (validation, docs, deprecation), and an app has many query parameters, so `query.py` earns its place exactly as `argument.py` does.

```python
import fastapi


def stations() -> fastapi.params.Query:
    """The stations query parameter."""
    return fastapi.Query(description="Station IDs.")
```

`Depends` is the exception — not request-parameter config but **dependency injection** — and it needs *two* functions, which split by coupling.
`depend.py` holds the marker factory (FastAPI-coupled, like `query.py`); `provide.py` holds the **provider** it wraps — the function that names the concrete adapter.
`Depends(fn)` **calls `fn` and injects its return value**, so the provider *returns* the adapter — the factory passes the provider, `Depends(provide.fetch)`, never `Depends(httpx_.fetch)`, which would make FastAPI call the adapter itself as a dependency and parse its arguments as request inputs:

```python
import fastapi

from mypackage.code.drive.fastapi_ import provide


def fetch() -> fastapi.params.Depends:
    """Inject the temperature source."""
    return fastapi.Depends(provide.fetch)
```

`provide.py` is the **injection seam** — the driver's place for naming a concrete adapter.
It imports no FastAPI (its signature is `-> port.Fetch`, its body returns `httpx_.fetch`); it lives inside `fastapi_` only because FastAPI is the sole caller — lift it to a shared `drive/provide.py` if a second driver ever needs the same wiring.

```python
from mypackage.code import port
from mypackage.code.adapt import httpx_


def fetch() -> port.Fetch:
    """Provide the temperature source adapter; overridden in tests."""
    return httpx_.fetch
```

Naming `httpx_` in `provide.py` doesn't leak it into the core: it's part of the driver — the **composition root** — so naming the one concrete adapter is its job.
The invariant that holds is that `operate` imports only `port`; and even here the signature depends on the abstraction `port.Fetch` while only the body names `httpx_`.

`route.py`'s endpoints then receive the injected adapter as a parameter (where the CLI's `command.py` passes it by hand) and shape the core's result into the response models:

```python
import typing

import fastapi

from mypackage.code import operate, port
from mypackage.code.drive.fastapi_ import depend, query
from mypackage.code.drive.pydantic_ import schema

router = fastapi.APIRouter()


@router.get("/report")
def report(
    stations: typing.Annotated[list[str], query.stations()],
    fetch: typing.Annotated[port.Fetch, depend.fetch()],
) -> list[schema.Reading]:
    """Report the average temperature for each station."""
    averages = operate.report(stations, fetch=fetch)
    return [
        schema.Reading(station=station, average=average)
        for station, average in averages.items()
    ]
```

`fastapi_/__init__.py` builds the app, includes the router, and adds the launcher — an ASGI app isn't callable to start a server, so `run()` calls `uvicorn.run(app)`; `api/__init__.py` re-exports `app` and `run`:

```python
import fastapi
import uvicorn

from mypackage.code.drive.fastapi_ import route

app = fastapi.FastAPI()
app.include_router(route.router)


def run() -> None:
    """Launch the API server."""
    uvicorn.run(app)
```

Launch with `mypackage-api = "mypackage.code.drive.api:run"`, or serve directly with `uvicorn mypackage.code.drive.api:app`.
Because the adapter arrives through `Depends`, a test swaps it for a fake by overriding the provider — `app.dependency_overrides[provide.fetch] = lambda: fake_fetch` — the FastAPI-native seam, no patching.

### GUI

`shiny` (Shiny for Python, from Posit) for a GUI or dashboard (see Reach-for libraries in `setup-python`) — its reactive model (only the outputs affected by a changed input re-render) and clean UI/server split fit shell-over-core far better than Streamlit's whole-script rerun.

**Use Shiny Core, not Express, in a packaged app.** Express is easier — it intermingles the layout and the callbacks in one module, so a throwaway single-view dashboard is fewer lines.
But Core keeps the **layout** and the **reactive/render callbacks** in separate expressions, which is exactly the shell split we want, is Posit's own recommendation for large or long-lived apps, and yields an explicit `app = shiny.App(app_ui, server)` object for the launcher.
So `shiny_/` separates the way `typer_/` does:

```text
gui/
  __init__.py   role, hollow: re-exports app and run
shiny_/
  __init__.py   app = shiny.App(app_ui, server); run() launcher
  server.py     the server(input, output, session) callbacks
  ui.py         the app_ui layout
```

`ui.py` is pure declarative layout:

```python
import shiny

app_ui = shiny.ui.page_fluid(
    shiny.ui.input_text("stations", "Stations", "london tokyo"),
    shiny.ui.output_text("report"),
)
```

`server.py` holds the reactive callbacks and is the **composition root**: each render binds an input to an operation with the injected adapter, exactly like the CLI's `command.py`:

```python
import shiny

from mypackage.code import operate
from mypackage.code.adapt import httpx_


def server(input: shiny.Inputs, output: shiny.Outputs, session: shiny.Session) -> None:
    """Wire inputs to the core and render the results."""

    @shiny.render.text
    def report() -> str:
        averages = operate.report(input.stations().split(), fetch=httpx_.fetch)
        return "\n".join(
            f"{station}: {average}" for station, average in averages.items()
        )
```

`shiny_/__init__.py` wires the two halves and adds the launcher — a `shiny.App` isn't callable to start a server, so `run()` calls `shiny.run_app(app)`; `gui/__init__.py` re-exports `app` and `run`:

```python
import shiny

from mypackage.code.drive.shiny_.server import server
from mypackage.code.drive.shiny_.ui import app_ui

app = shiny.App(app_ui, server)


def run() -> None:
    """Launch the Shiny server."""
    shiny.run_app(app)
```

Launch with `mypackage-gui = "mypackage.code.drive.gui:run"`, or `shiny run mypackage.code.drive.gui:app`.
A throwaway single-view dashboard can collapse the split into one Shiny Express module (`gui.py`) — the parallel of collapsing a one-command CLI into `cli.py` — but keep the work in the core either way.

### Jobs

A cron run, a queue worker, a webhook handler, or a serverless function is a driver triggered by *time or events* rather than a person.
It reads its trigger, runs an operation — injecting the adapters, the composition root's job — and writes the result through an output adapter (this is the ETL shape: `extract` in, `transform` in the core, `load` out); keep the trigger wiring thin so the work stays in the core.

**Default to no library.** The cleanest scheduler is *external* to the app — cron, a systemd timer, a Kubernetes `CronJob`, a cloud scheduler, or a serverless trigger — so the schedule lives in infrastructure, not code.
The app just exposes a console script that runs once and exits.
A job is `command.py` without the parsing: a thin composition root wiring a source and a sink around an operation.

```python
from mypackage.code import operate
from mypackage.code.adapt import httpx_, postgres_


def run() -> None:
    """Fetch the latest readings and store the daily averages."""
    operate.refresh(fetch=httpx_.fetch, store=postgres_.save)
```

`mypackage-job = "mypackage.code.drive.job:run"`, invoked by the external trigger.
Reach for a library only when the trigger must live *inside* the process (see Reach-for libraries in `setup-python`):

- **In-process scheduling** (a long-running process firing work on a clock) → `apscheduler`, in an `apscheduler_/` package holding the scheduler.
- **A task queue** (events enqueue work, worker processes consume it) → `dramatiq` (a cleaner Celery) over a Redis/RabbitMQ broker, its actors in a `dramatiq_/` package.
- **Orchestration** (dependent steps, retries, backfills, observability) → `prefect` or `dagster`.

Whichever it is, the scheduler or broker is the shell; the work stays an operation over the pure core.

## Data

Non-code assets an app needs at runtime — SQL query files, HTML templates, static reference data — load through `importlib.resources`, never a path built from `__file__` or the repo root.

Keep them all in one `data/` directory whose inside **mirrors the code layers**, so every asset's path names the layer that owns it — `data/` and `code/` are the two parallel trees under the package.
One place to manage, with ownership still explicit:

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
Package data must live **inside the package** (`src/mypackage/data/`, as above) to be installed and reachable via `importlib.resources` — not a bare `src/data/`, since `src/` is only a source root: just the package beneath it ships, with the `src/` prefix stripped, so a sibling of the package is neither packaged nor reachable as `mypackage`'s data.
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
  It's named `pytest_` (per `write-python`'s underscore rule) because it's all pytest-coupled — fixtures, and assertions written as bare `assert`s rather than `unittest`'s methods.
  Tests import it as `from pytest_ import then`.
- **`suite/`** — the test cases: your code mirrored in `suite/<package>/`, and dependency-behaviour tests in `suite/packages/`.

The pytest settings in `setup-python`'s `pyproject.toml` serve this layout:

- `testpaths = ["tests/suite"]` collects only the cases.
- `--import-mode importlib` avoids `sys.path` clashes from the `src/` layout and nested folders.
- `pythonpath = ["tests"]` with `-p pytest_.given` makes `pytest_` importable and loads its fixtures.
- `src = ["src", "tests"]` marks `tests/` a source root so isort files `pytest_` as first-party.

Scaffold `tests/pytest_/given.py` (with its `__init__.py`) up front — `-p pytest_.given` fails to load if the module is missing.

That is the *scaffold*; the `write-tests` skill covers how to write the tests themselves — the given/when/then shape, naming, fixtures, and the rest.
