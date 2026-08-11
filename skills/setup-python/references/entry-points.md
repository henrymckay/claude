# Entry points — building each shell

This is the concrete build-out for `setup-python`'s Entry points section. That section covers the overview — the role/framework split, `[project.scripts]` naming, and what isn't an entry point; this file is how each shell type is actually structured: its framework packages, the composition-root wiring, and the launcher. Every one is a thin driver over the shared core (`operate` over `transform` and `port`) — see `SKILL.md` for that architecture.

## Command-line interfaces

`typer` for the CLI, `rich` for output (see Reach-for libraries in `SKILL.md`).
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

## APIs

`fastapi` for an HTTP API (see Reach-for libraries in `SKILL.md`), served with `uvicorn` and its models built on `pydantic`. Under `code/drive/`, a hollow `api/` role package re-exports the app and launcher, over two framework packages — `fastapi_/` for the routing and `pydantic_/` for the schemas — the way the CLI splits `typer_/` and `rich_/`:

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

`schema.py` holds the boundary DTOs — the `pydantic.BaseModel`s FastAPI validates and serialises (a `Reading` with `station: str` and `average: float`). These are pydantic-coupled, so they live in a `pydantic_` package, not `fastapi_` — the `fastapi_` (routing) / `pydantic_` (data schemas) split parallels the CLI's `typer_` (parsing) / `rich_` (presentation); the schema *is* the API's presentation.

A DTO is **not** a domain type, even when their fields match. The schema is the external **contract**; the domain model is the internal truth; keep them separate so they evolve independently (API versioning vs domain logic) and untrusted input is validated at the boundary. Map between them in `route.py`, as `schema.Reading(...)` does below. Neither belongs in `port/`, which is protocols only; the domain types live in `transform`/`domain`.

Pydantic is best used at exactly this kind of **trust boundary** — validating and (de)serialising data as it crosses in or out: API bodies here, `pydantic-settings` for config from the environment, or parsing an external response inside an adapter. It's a data library, not an IO framework, so it's *allowed* in the pure core too — but there the data is already validated, so a plain frozen `dataclasses.dataclass` is the lighter default; reach for pydantic in the core only when you specifically want its validation or serialisation there. Enums are the one thing you never duplicate: pydantic accepts a stdlib `enum.Enum`, so a domain `Scale` is imported and referenced straight in a schema field; only a genuinely API-only enum (a sort order) lives in the driver.

**A model shared across layers moves inward, to the core.** `pydantic_` here holds *only* the API's own schemas. Because `adapt` never imports `drive`, the two edges can't share a boundary model — so a pydantic model you find yourself wanting in *both* `adapt` and `drive` isn't a boundary DTO, it's a **domain model**: put it in `transform`/`domain`, which both edges import inward (pydantic is fine there). Each boundary DTO otherwise stays with its own edge — the API's schemas in `drive/pydantic_`, an external service's shape in the `adapt` module that parses it — never hoisted into one shared edge package.

**FastAPI declares parameters exactly as Typer does** — the same author built both, and both read `typing.Annotated[T, marker()]`, the marker carrying the framework metadata. Typer's `Argument`/`Option` are FastAPI's `Query`, `Path`, `Body`, `Header` and `Depends`. So `fastapi_` mirrors `typer_`'s structure: where `typer_` splits factory functions across `argument.py` and `option.py`, `fastapi_` has **a module per request marker** — `query.py`, plus `path.py`/`body.py`/`header.py` as those markers are used — each holding functions that return a configured marker, one per parameter (`query.stations()`, read as `category.member`). `fastapi.Query` alone takes many arguments (validation, docs, deprecation), and an app has many query parameters, so `query.py` earns its place exactly as `argument.py` does.

```python
import fastapi


def stations() -> fastapi.params.Query:
    """The stations query parameter."""
    return fastapi.Query(description="Station IDs.")
```

`Depends` is the exception — not request-parameter config but **dependency injection** — and it needs *two* functions, which split by coupling. `depend.py` holds the marker factory (FastAPI-coupled, like `query.py`); `provide.py` holds the **provider** it wraps — the function that names the concrete adapter. `Depends(fn)` **calls `fn` and injects its return value**, so the provider *returns* the adapter — the factory passes the provider, `Depends(provide.fetch)`, never `Depends(httpx_.fetch)`, which would make FastAPI call the adapter itself as a dependency and parse its arguments as request inputs:

```python
import fastapi

from mypackage.code.drive.fastapi_ import provide


def fetch() -> fastapi.params.Depends:
    """Inject the temperature source."""
    return fastapi.Depends(provide.fetch)
```

`provide.py` is the **injection seam** — the driver's place for naming a concrete adapter. It imports no FastAPI (its signature is `-> port.Fetch`, its body returns `httpx_.fetch`); it lives inside `fastapi_` only because FastAPI is the sole caller — lift it to a shared `drive/provide.py` if a second driver ever needs the same wiring.

```python
from mypackage.code import port
from mypackage.code.adapt import httpx_


def fetch() -> port.Fetch:
    """Provide the temperature source adapter; overridden in tests."""
    return httpx_.fetch
```

Naming `httpx_` in `provide.py` doesn't leak it into the core: it's part of the driver — the **composition root** — so naming the one concrete adapter is its job. The invariant that holds is that `operate` imports only `port`; and even here the signature depends on the abstraction `port.Fetch` while only the body names `httpx_`.

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

## Graphical interfaces

`shiny` (Shiny for Python, from Posit) for a GUI or dashboard (see Reach-for libraries in `SKILL.md`) — its reactive model (only the outputs affected by a changed input re-render) and clean UI/server split fit shell-over-core far better than Streamlit's whole-script rerun.

**Use Shiny Core, not Express, in a packaged app.** Express is easier — it intermingles the layout and the callbacks in one module, so a throwaway single-view dashboard is fewer lines. But Core keeps the **layout** and the **reactive/render callbacks** in separate expressions, which is exactly the shell split we want, is Posit's own recommendation for large or long-lived apps, and yields an explicit `app = shiny.App(app_ui, server)` object for the launcher. So `shiny_/` separates the way `typer_/` does:

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

## Scheduled and event-driven jobs

A cron run, a queue worker, a webhook handler, or a serverless function is a driver triggered by *time or events* rather than a person. It reads its trigger, runs an operation — injecting the adapters, the composition root's job — and writes the result through an output adapter (this is the ETL shape: `extract` in, `transform` in the core, `load` out); keep the trigger wiring thin so the work stays in the core.

**Default to no library.** The cleanest scheduler is *external* to the app — cron, a systemd timer, a Kubernetes `CronJob`, a cloud scheduler, or a serverless trigger — so the schedule lives in infrastructure, not code. The app just exposes a console script that runs once and exits. A job is `command.py` without the parsing: a thin composition root wiring a source and a sink around an operation.

```python
from mypackage.code import operate
from mypackage.code.adapt import httpx_, postgres_


def run() -> None:
    """Fetch the latest readings and store the daily averages."""
    operate.refresh(fetch=httpx_.fetch, store=postgres_.save)
```

`mypackage-job = "mypackage.code.drive.job:run"`, invoked by the external trigger. Reach for a library only when the trigger must live *inside* the process (see Reach-for libraries in `SKILL.md`):

- **In-process scheduling** (a long-running process firing work on a clock) → `apscheduler`, in an `apscheduler_/` package holding the scheduler.
- **A task queue** (events enqueue work, worker processes consume it) → `dramatiq` (a cleaner Celery) over a Redis/RabbitMQ broker, its actors in a `dramatiq_/` package.
- **Orchestration** (dependent steps, retries, backfills, observability) → `prefect` or `dagster`.

Whichever it is, the scheduler or broker is the shell; the work stays an operation over the pure core.
