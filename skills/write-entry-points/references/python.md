# Write entry points in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
Every driver lives under `code/drive/` (see `structure-python`); the house libraries are the picks in `setup-python`'s Libraries section.
The running example is a weather-station app whose one operation, `operate.report`, averages readings fetched through a `port.Fetch`.

## Packaging

Split each driver into a hollow **role package** and one or more **framework packages** under `code/drive/`:

- The **role package** (`cli`, `api`, `gui`) is named for *what it is* and just re-exports the app object, giving a stable entry point (`mypackage.code.drive.cli:app`) that hides which library is behind it.
- The **framework packages** (`typer_`, `rich_`, `fastapi_`, `pydantic_`, `shiny_`) hold the tightly-coupled code — everything that uses or returns that library's objects.
They take the trailing-underscore name (per `write-python`), which both marks the coupling and avoids shadowing the real `typer`/`rich`.

Swap the library and only the framework package changes; the role name stays put.

**A framework package may hold a module that imports nothing from that framework**, where the framework is its only caller — `fastapi_/provide.py` naming the concrete adapter, `typer_/bound.py` turning the CLI's own options into the shape the core filters with.
Both are driver work rather than library work, so the trailing-underscore name slightly overstates the coupling; it earns its place there because keeping it beside its one caller beats a package of one loose module.
Lift it to a shared `drive/` module the moment a second driver needs it.

## CLI

`typer` for the CLI, `rich` for output (see Libraries in `setup-python`).
Three packages under `code/drive/`:

```text
cli/
  __init__.py   role, hollow: re-exports app
typer_/
  __init__.py     re-exports app; imports callback and command
  driver.py       the typer.Typer() instance — imports no drive module
  argument.py     functions returning a configured typer.Argument
  callback.py     the @app.callback() run before any command
  command.py      the @app.command() functions — the composition root
  option.py       functions returning a configured typer.Option
rich_/
  __init__.py
  render.py     builds the rich table from the core's plain results
```

`command.py` holds the commands and is the **composition root**: each imports an operation and a concrete adapter, injects one into the other, and hands the plain result to `rich_` to render.
Unlike `fastapi`'s `APIRouter`, `typer` has no flat command *router* to decorate off a separate object — `add_typer` composes sub-apps only as command *groups* (below), not flat commands.

**Give the app object its own module.**
A framework anchor has to be defined before anything decorates it, so leaving it at the top of `command.py` fixes the order of that file and pushes the callback ahead of the commands — and the commands are what a reader came for.
Put it in `driver.py` and `command.py` is a flat alphabetical list of commands, `write-python`'s ordering intact.
`driver.py` imports no other `drive` module, so nothing cycles.

**Every framework package keeps its app object in `driver.py`** — `typer_`, `fastapi_`, `shiny_` alike, together with the `run()` launcher where the framework needs one.
Two things fall out of the fixed home.
You know where the app is in any framework package without reading it, which matters precisely because that object is the one thing they all have and the one thing named differently by each library's own docs.
And `__init__.py` stays a **pure re-export** in all three, which is the only shape `write-python` gives a marker for — a file that both defines and re-exports needs the redundant alias on half its lines and nothing on the other half.

Name the module and the instance apart, so `driver.app` reads like `argument.stations()`.
`application.app` would repeat the namespace in the name it qualifies, the same fault as `user.user_name` (see `write-python`).

```python
import typing

import typer

from mypackage.code import operate
from mypackage.code.adapt import httpx_
from mypackage.code.drive.rich_ import render
from mypackage.code.drive.typer_ import argument, driver


@driver.app.command()
def report(stations: typing.Annotated[list[str], argument.stations()]) -> None:
    """Report the average temperature for each station."""
    render.table(operate.report(stations, fetch=httpx_.fetch))
```

`typer_/__init__.py` re-exports the app and names the modules whose import registers the decorators — without those two imports the app carries no commands, because a decorator only runs when its module is imported:

```python
from mypackage.code.drive.typer_ import callback as callback, command as command
from mypackage.code.drive.typer_.driver import app as app
```

`cli/__init__.py` re-exports that `app` as the stable entry point, so the console script never names the framework behind it:

```python
from mypackage.code.drive.typer_ import app as app
```

A `typer` app is callable, so its console script points straight at the app object (see Run).

**Callbacks and command groups scale the same shape.** An `@app.callback()` runs before any command — the home for app-wide options and setup (a global `--verbose`, loading config); keep it as thin as a command.
Sub-commands like `mypackage-cli users create` are command *groups*: each is its own `typer.Typer()`, mounted on the main app with `app.add_typer(users.app, name="users")`.
Grow `command.py` into a `command/` package once a group exists — a module per group owning its sub-app and `@`-decorated commands, with `command/__init__.py` holding the main `app` and mounting each; a grouped command is still a thin composition root, the grouping only presentation.

**A command's name is its function's name.** `typer` turns `list_names` into `list-names`, so let it and never pass `name=`.
An override makes the CLI and the code disagree, so someone grepping for the command a user typed finds nothing, and the decorator becomes a second place the name lives.
Where the natural name collides with a builtin — `list`, `type`, `filter`, `id` — that is the *surface's* problem to solve rather than the code's to paper over.
Pick a command name that is not the collision: `list-names` says what `list` left to inference anyway.

**Break each argument and option out into a function returning its config — at any size.**
A `typer` command's inline `Annotated[...]` bloats the signature fast, so define the argument or option once and reference it — the same shared-helper idea as `given`/`when`/`then` in tests, config defined once and signatures kept readable:

```python
def stations() -> typer.models.ArgumentInfo:
    """Return the stations positional argument."""
    return typer.Argument(help="Weather station IDs, e.g. london tokyo.")
```

The factory names a noun, so a noun-phrase docstring is the instinct — but it is a function like any other, and `ruff`'s `D401` requires the imperative, so write `Return the …` (see `write-python`).

**Where the options are systematic, parameterise the factory and pass the whole option set on.**
A command whose surface is one option per column of a report — a bound per count on each timeframe, a threshold per metric — reaches twenty or thirty options, and writing a factory each is as much duplication as inlining them.
Take the axes as arguments instead, so one factory serves the lot and the help panels fall out of it:

```python
def minimum(
    count: domain.Count, timeframe: domain.Timeframe
) -> typer.models.OptionInfo:
    """Return the option bounding one count on one timeframe from below."""
    return typer.Option(
        help=f"Keep rows whose {timeframe} {count} count is at least this.",
        rich_help_panel=f"{str(timeframe).capitalize()} counts",
        show_default=False,
    )
```

The signature still has to name every option — `typer` reads the real parameters, so there is no generating them — but the *body* must not restate them.
Hand the whole option set to the function that shapes it and let that pick out what it needs by name:

```python
def count(
    daily_setup_min: Bound,
    daily_setup_max: Bound,
    # one pair per count per timeframe, plus the command's own arguments
) -> None:
    """Report the counts, keeping only the rows within the bounds given."""
    bounds = bound.frame(**locals())
```

`Bound` stands for the `typing.Annotated[...]` the factory above returns; the real signature spells each one out.

`locals()` at the top of a command body is exactly its arguments, and the alternative — repeating all thirty names in a call — is a second list to keep in step with the first, which drifts the moment an option is added.
Say in the docstring that the parameter names are the keys, and have the receiving function ignore anything it does not recognise so the paths and dates passing through cost nothing.

**Keep help text terse — lean on defaults, not examples.**
Don't stuff usage examples into a help string; a well-chosen **default** documents both the format and a sensible value at once (a `--days` defaulting to `7` is its own example), and `typer` shows defaults in `--help`.
A **required** argument is the one place an example earns its line, because a default is exactly what would make it optional — `typer`, `click` and `argparse` all read "has a default" as "not required", so there is no default to lean on without changing what the argument is.
Even then, only where the name leaves the format open: `NAME...` does not say whether a name is typed as a ticker or a phrase, so one example settles it, where `PATH` says everything already.
Keep it to a bare value or two rather than a sentence, since the value itself is the documentation.

**Serve the terminal and the pipeline from one command** (see Compose with other tools in `SKILL.md`).
`rich` drops colour by itself when standard output is not a terminal, which is *not* enough — a boxed table is still unparseable — so the machine form has to be a second render rather than the same one unstyled.
Keep both in `rich_` and let the option decide, never `Console().is_terminal`:

```python
def write(report: polars.DataFrame, console: rich.console.Console, table: bool) -> None:
    """Draw the report as a table, or emit it as CSV."""
    if table:
        console.print(_table(report))
    else:
        console.file.write(report.write_csv())
```

The command stays a one-liner over it, and `--output PATH` just swaps the console's `file`.
Read input the same way: type the argument `pathlib.Path` and treat `-` as standard input, so `demark count - --daily-setup 9` works mid-pipeline.

**Send logs to standard error, or they corrupt the data stream.**
`rich.logging.RichHandler()` builds its own `Console()`, which writes to standard output — so the default wiring puts log lines in the middle of piped output.
Pass it a stderr console explicitly:

```python
logging.basicConfig(
    handlers=[rich.logging.RichHandler(console=rich.console.Console(stderr=True))]
)
```

The same applies to any error or prompt the driver prints: `typer.echo(message, err=True)`, or a second `Console(stderr=True)` held for the purpose.
Fail with `raise typer.Exit(code=1)` so the shell sees it.

Presentation config obeys the function-over-constant rule — a `_colour(direction)` function in `rich_`, not a module-level `dict` (see `be-functional`).
A throwaway one-command tool can collapse `typer_` and `rich_` into a single `cli.py` (KISS) — but keep it out of the core.

## API

`fastapi` for an HTTP API (see Libraries in `setup-python`), served with `uvicorn` and its models built on `pydantic`.
Under `code/drive/`, a hollow `api/` role package re-exports the app and launcher, over two framework packages — `fastapi_/` for the routing and `pydantic_/` for the schemas — the way the CLI splits `typer_/` and `rich_/`:

```text
api/
  __init__.py   role, hollow: re-exports app and run
fastapi_/
  __init__.py   re-exports app and run from driver
  driver.py     app = fastapi.FastAPI(); includes the router; run() launcher
  depend.py     factories returning a fastapi.Depends marker
  provide.py    the providers Depends calls — names the concrete adapter
  query.py      functions returning a configured fastapi.Query
  route.py      the path operations that call the core
pydantic_/
  __init__.py
  schema.py     the request/response models (BaseModel DTOs)
```

`schema.py` holds the boundary DTOs (Data Transfer Objects) — the `pydantic.BaseModel`s `fastapi` validates and serialises (a `Reading` with `station: str` and `average: float`).
These are pydantic-coupled, so they live in a `pydantic_` package, not `fastapi_` — the `fastapi_` (routing) / `pydantic_` (data schemas) split parallels the CLI's `typer_` (parsing) / `rich_` (presentation); the schema *is* the API's presentation.

A DTO is **not** a domain type, even when their fields match.
The schema is the external **contract**; the domain model is the internal truth; keep them separate so they evolve independently (API versioning vs domain logic) and untrusted input is validated at the boundary.
Map between them in `route.py`, as `schema.Reading(...)` does below.
Neither belongs in `port/`, which is protocols only; the domain types live in `transform`/`domain`.

`pydantic` is best used at exactly this kind of **trust boundary** — validating and (de)serialising data as it crosses in or out: API bodies here, `pydantic-settings` for config from the environment, or parsing an external response inside an adapter.
It's a data library, not an IO framework, so it's *allowed* in the pure core too — but there the data is already validated, so a plain frozen `dataclasses.dataclass` is the lighter default; reach for `pydantic` in the core only when you specifically want its validation or serialisation there.
Enums are the one thing you never duplicate: `pydantic` accepts a stdlib `enum.Enum`, so a domain `Scale` is imported and referenced straight in a schema field; only a genuinely API-only enum (a sort order) lives in the driver.

**A model shared across layers moves inward, to the core.** `pydantic_` here holds *only* the API's own schemas.
Because `adapt` never imports `drive`, the two edges can't share a boundary model — so a `pydantic` model you find yourself wanting in *both* `adapt` and `drive` isn't a boundary DTO, it's a **domain model**: put it in `transform`/`domain`, which both edges import inward (`pydantic` is fine there).
Each boundary DTO otherwise stays with its own edge — the API's schemas in `drive/pydantic_`, an external service's shape in the `adapt` module that parses it — never hoisted into one shared edge package.

**`fastapi` declares parameters exactly as `typer` does** — the same author built both, and both read `typing.Annotated[T, marker()]`, the marker carrying the framework metadata.
`typer`'s `Argument`/`Option` are `fastapi`'s `Query`, `Path`, `Body`, `Header` and `Depends`.
So `fastapi_` mirrors `typer_`'s structure: where `typer_` splits factory functions across `argument.py` and `option.py`, `fastapi_` has **a module per request marker** — `query.py`, plus `path.py`/`body.py`/`header.py` as those markers are used — each holding functions that return a configured marker, one per parameter (`query.stations()`, read as `category.member`).
`fastapi.Query` alone takes many arguments (validation, docs, deprecation), and an app has many query parameters, so `query.py` earns its place exactly as `argument.py` does.

```python
import fastapi


def stations() -> fastapi.params.Query:
    """Return the stations query parameter."""
    return fastapi.Query(description="Station IDs.")
```

`Depends` is the exception — not request-parameter config but **dependency injection** — and it needs *two* functions, which split by coupling.
`depend.py` holds the marker factory (fastapi-coupled, like `query.py`); `provide.py` holds the **provider** it wraps — the function that names the concrete adapter.
`Depends(fn)` **calls `fn` and injects its return value**, so the provider *returns* the adapter — the factory passes the provider, `Depends(provide.fetch)`, never `Depends(httpx_.fetch)`, which would make `fastapi` call the adapter itself as a dependency and parse its arguments as request inputs:

```python
import fastapi

from mypackage.code.drive.fastapi_ import provide


def fetch() -> fastapi.params.Depends:
    """Inject the temperature source."""
    return fastapi.Depends(provide.fetch)
```

`provide.py` is the **injection seam** — the driver's place for naming a concrete adapter.
It imports no `fastapi` (its signature is `-> port.Fetch`, its body returns `httpx_.fetch`); it lives inside `fastapi_` only because `fastapi` is the sole caller — lift it to a shared `drive/provide.py` if a second driver ever needs the same wiring.

**A `provide` module earns its place only where the framework needs a callable to resolve a dependency**, as `Depends(provide.fetch)` does.
Naming an adapter is not on its own a reason for one.

**A package of interchangeable adapters names its own members.**
Where the core picks between several adapters at runtime, which ones exist is a fact about what `adapt` ships, so `adapt/__init__.py` returns the mapping and every driver reads the same one.
Enumerate them in a driver instead and the next driver copies the list, so adding an adapter edits every entry point rather than the package that gained it.
That is not the composition root moving: the driver still chooses whether to use that set, and still injects it into the operation.

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

`fastapi_/driver.py` builds the app, includes the router, and adds the launcher — an ASGI (Asynchronous Server Gateway Interface) app isn't callable to start a server, so `run()` calls `uvicorn.run(app)`; `api/__init__.py` re-exports `app` and `run`:

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

An ASGI app isn't callable, so its console script points at `run()` (see Run).
Because the adapter arrives through `Depends`, a test swaps it for a fake by overriding the provider — `app.dependency_overrides[provide.fetch] = lambda: fake_fetch` — the fastapi-native seam, no patching.

## GUI

`shiny` (Shiny for Python, from Posit) for a GUI or dashboard (see Libraries in `setup-python`) — its reactive model (only the outputs affected by a changed input re-render) and clean UI/server split fit shell-over-core far better than `streamlit`'s whole-script rerun.

**Use Shiny Core, not Express, in a packaged app.** Express is easier — it intermingles the layout and the callbacks in one module, so a throwaway single-view dashboard is fewer lines.
But Core keeps the **layout** and the **reactive/render callbacks** in separate expressions, which is exactly the shell split we want, is Posit's own recommendation for large or long-lived apps, and yields an explicit `app = shiny.App(layout.root(), callback.server)` object for the launcher.
So `shiny_/` separates the way `typer_/` does:

```text
gui/
  __init__.py   role, hollow: re-exports app and run
shiny_/
  __init__.py   re-exports app and run from driver
  driver.py     app = shiny.App(layout.root(), callback.server); run() launcher
  layout.py     functions returning shiny.ui objects; root() is the top-level
  callback.py   the server(input, output, session) reactive callbacks
```

`layout.py` is a module of functions returning `shiny.ui` objects — `root()` is the top-level layout passed to `shiny.App`.
A function beats a module-level constant (see `write-python`): layouts compose, so a reused panel or header is its own function that `root()` calls, and a variant builds on it instead of copying markup.

```python
import htmltools
import shiny


def root() -> htmltools.Tag:
    """Return the top-level layout."""
    return shiny.ui.page_fluid(
        shiny.ui.input_text("stations", label="Stations", value="london tokyo"),
        shiny.ui.output_text("report"),
    )
```

`callback.py` holds the reactive callbacks in shiny's `server` function and is the **composition root**: each render binds an input to an operation with the injected adapter, exactly like the CLI's `command.py`:

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

`shiny_/driver.py` wires the two halves and adds the launcher — a `shiny.App` isn't callable to start a server, so `run()` calls `shiny.run_app(app)`; `gui/__init__.py` re-exports `app` and `run`:

```python
import shiny

from mypackage.code.drive.shiny_ import callback, layout

app = shiny.App(layout.root(), callback.server)


def run() -> None:
    """Launch the Shiny server."""
    shiny.run_app(app)
```

A `shiny.App` isn't callable, so its console script points at `run()` (see Run).
A throwaway single-view dashboard can collapse the split into one Shiny Express module (`gui.py`) — the parallel of collapsing a one-command CLI into `cli.py` — but keep the work in the core either way.

## Jobs

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

Its console script points at `run()` (see Run), invoked by the external trigger.
Reach for a library only when the trigger must live *inside* the process (see Libraries in `setup-python`):

- **In-process scheduling** (a long-running process firing work on a clock) → `apscheduler`, in an `apscheduler_/` package holding the scheduler.
- **A task queue** (events enqueue work, worker processes consume it) → `dramatiq` (a cleaner `celery`) over a Redis/RabbitMQ broker, its actors in a `dramatiq_/` package.
- **Orchestration** (dependent steps, retries, backfills, observability) → `prefect` or `dagster`.

Whichever it is, the scheduler or broker is the shell; the work stays an operation over the pure core.

## Configuration

Load configuration once, at the composition root, and pass its values into operations — the core never reads `os.environ` (see `structure-python`).

A `pydantic-settings` model reads and validates the environment at the boundary.
It's edge code, so it lives in a `config` module the driver imports:

```python
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    """Application configuration, read from the environment."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="MYPACKAGE_")

    rate: float = 0.05
    timeout: float = 30.0
```

The driver instantiates it at startup and passes the values an operation needs, beside the adapters and through the same seam:

```python
settings = config.Settings()
render.table(operate.report(stations, fetch=httpx_.fetch, rate=settings.rate))
```

`config.Settings()` reads `MYPACKAGE_RATE` and validates it, failing fast on a bad value.
A secret is a `pydantic.SecretStr` field and arrives the same way — from the environment or a mounted file, never a default baked into the code (see `use-git`).

**One value from the environment is a function, not a settings model.**
`pydantic-settings` earns its place on a handful of fields — a prefix worth declaring once, types to coerce, defaults to state, a secret to wrap — and a single string buys none of that while costing a dependency, a class and a module.
Read it with a function that raises a clear error naming the variable when it is unset, and grow into the model when a second field arrives; the call sites do not change, because they were calling a function either way (see `be-functional`).
The lighter form is also what keeps a *required* value honest: a settings model invites a default, and a default for an address a publisher is meant to reply to ships a lie.

**Validate at startup only what the command about to run actually needs.**
Failing fast is worth having where a long run would otherwise waste work, so a driver that reads its settings in a `typer` callback stops before the first request rather than midway through fifty.
But a callback runs before *every* command, so validating there makes the command that fetches nothing — listing what the tool offers, printing a version — fail for want of a value it will never use.
Read it where it is used and let the first use fail, or check it in the commands that need it; a tool that cannot list its own contents without a network credential has made the check cost more than it saves.

## Logging

Configure logging once, at the composition root — the root logger and one handler — then let every module emit through `logging.getLogger(__name__)` (see `structure-python`).
Expose the destination and the level as options, defaulting to standard error so logs never land in piped data (see Compose with other tools in `SKILL.md`).
It's the application-side mirror of the session logging the suite installs (see `write-tests`), so it lives in a `logging_/` package (the trailing underscore keeps it clear of the stdlib `logging`, per `write-python`):

```python
import logging
import pathlib

import rich.console
import rich.logging


def configure(
    *, level: int = logging.WARNING, path: pathlib.Path | None = None
) -> None:
    """Route application logs to a file, or to standard error through Rich."""
    logging.basicConfig(
        force=True,
        format="%(message)s",
        handlers=[_file(path) if path else _stderr()],
        level=level,
    )


def _file(path: pathlib.Path) -> logging.Handler:
    """Return a handler writing plain, timestamped records to a file."""
    handler = logging.FileHandler(path)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    return handler


def _stderr() -> logging.Handler:
    """Return a handler rendering records on standard error."""
    return rich.logging.RichHandler(
        console=rich.console.Console(stderr=True), rich_tracebacks=True
    )
```

`basicConfig` only applies its `format` to a handler that has none, so the file handler keeps its own timestamped one while `RichHandler` gets the bare message it expects — leave `format` out and Rich prints the level twice.

The driver calls `logging_.configure()` once at startup, before the operation runs — from a `typer` `@app.callback()`, a `fastapi` lifespan hook, or the top of a job's `run()`.
Every other module then logs without touching configuration:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("fetched %s stations", len(stations))
```

## Run

Each entry point is launched by a `[project.scripts]` console command named `<project>-<role>` — a *global* command once installed (it lands on `PATH`), so namespace it to the project, never a bare `cli`/`api`/`gui`; `uv run` scoping to the local env doesn't change that.
(If one interface is clearly primary you can give it the bare project name and suffix only the rest, but symmetric `<project>-<role>` reads better for peers.)
The command points at whatever *starts* the entry point: a callable app where the framework gives one (a `typer` app is callable), or a thin `run()` launcher where it doesn't (`uvicorn.run(app)`, `shiny.run_app(app)`).

```toml
[project.scripts]
mypackage-cli = "mypackage.code.drive.cli:app"
mypackage-api = "mypackage.code.drive.api:run"
mypackage-gui = "mypackage.code.drive.gui:run"
mypackage-job = "mypackage.code.drive.job:run"
```

Run any with `uv run <command>`, or the bare command once installed:

```bash
uv run mypackage-cli report london tokyo
uv run mypackage-api
uv run mypackage-gui
uv run mypackage-job
```

- The API and GUI also take a framework dev server — `uvicorn mypackage.code.drive.api:app`, `shiny run mypackage.code.drive.gui:app`.
- The CLI adds `python -m mypackage.code.drive.cli` if you give it a `__main__.py` that calls `app()`.
- A job carries no scheduler of its own; an external trigger (cron, a timer, a queue) invokes its command.
