# Write entry points in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
Every driver lives under `code/drive/` (see `structure-python`); the libraries are `setup-python`'s house picks.
The running example is a weather app whose operation `operate.report(stations, fetch=...)` returns a `polars` frame of `station` and `average`, fetched through a `port.Fetch`.

## Packaging

Under `code/drive/`, each driver is a hollow **role package** over one or more **framework packages**:

- The **role package** (`cli`, `api`, `gui`) only re-exports the app object, giving a stable entry point (`mypackage.code.drive.cli:app`) that hides the library.
- The **framework packages** (`typer_`, `rich_`, `fastapi_`, `pydantic_`, `shiny_`) hold the library-coupled code, named with `write-python`'s trailing underscore.

**Every framework package keeps its app object in `driver.py`**, with the `run()` launcher where one is needed.
An app object must exist before anything decorates it, so in its own module the command and route modules stay flat alphabetical lists; `driver.py` imports no other `drive` module, so nothing cycles.
`__init__.py` then stays a pure re-export, and you know where the app is in any framework package without reading it.
`driver.app` also reads as `category.member`, where `app.app` would repeat the namespace.

**A framework package may hold a module that imports nothing from its framework**, where that framework is its only caller — `fastapi_/provide.py` naming the concrete adapter.
Lift it to a shared `drive/` module when a second driver needs it.

**A package of interchangeable adapters names its own members.** Where the core picks among adapters at runtime, `adapt/__init__.py` returns the mapping and every driver reads it; enumerating them in a driver means the next driver copies the list.
The driver still chooses to use the set and injects it.

## CLI

`typer` parses, `rich` renders.
The shape while there is one command group:

```text
cli/
  __init__.py     role, hollow: re-exports app
typer_/
  __init__.py     re-exports app; imports callback and command
  argument.py     functions returning a configured typer.Argument
  callback.py     the @app.callback() run before any command
  command.py      the @app.command() functions — the composition root
  driver.py       the typer.Typer() instance
  input_.py       gather(): what a command was given, by any route
  option.py       functions returning a configured typer.Option
  output.py       display() and report(): destination, form, and failure
rich_/
  __init__.py
  render.py       builds the rich table and nothing else
```

`command.py` is the composition root: each command injects an adapter into an operation and hands the result to `output`.

```python
import pathlib
import typing

from mypackage.code import operate
from mypackage.code.adapt import httpx_
from mypackage.code.drive.typer_ import argument, driver, option, output


@driver.app.command()
def report(
    stations: typing.Annotated[list[str], argument.stations()],
    path: typing.Annotated[pathlib.Path | None, option.output()] = None,
    pretty: typing.Annotated[bool, option.pretty()] = False,
) -> None:
    """Report the average temperature for each station."""
    output.display(
        operate.report(stations, fetch=httpx_.fetch), path=path, pretty=pretty
    )
```

`typer_/__init__.py` re-exports the app and imports the modules whose decorators register commands — a decorator runs only when its module is imported:

```python
from mypackage.code.drive.typer_ import callback as callback, command as command
from mypackage.code.drive.typer_.driver import app as app
```

`cli/__init__.py` re-exports it once more, so the console script never names the framework:

```python
from mypackage.code.drive.typer_ import app as app
```

### Commands and groups

- **A command's name is its function's name.** `typer` turns `list_stations` into `list-stations`; never pass `name=`, or a grep for the command a user typed finds nothing.
Where the natural name is a builtin (`list`, `type`), pick a better command name rather than overriding.
- **An `@app.callback()`** runs before every command — the home for app-wide options; keep it as thin as a command.
- **A command group** is its own `typer.Typer()`, mounted with `app.add_typer(users, name="users")`.
Every `typer.Typer()`, sub-apps included, lives in `driver`, so each group's module stays a flat list of commands and `command/__init__.py` only mounts them.
- **A group's arrival turns `command.py` into `command/`**, and `structure-python`'s same-kind rule promotes every sibling (`argument/`, `option/`, …) at the same moment.

### Arguments and options

**Give every argument and option a factory function returning its config**, keeping signatures readable:

```python
def stations() -> typer.models.ArgumentInfo:
    """Return the stations positional argument."""
    return typer.Argument(help="Station IDs, e.g. london.", show_default=False)
```

- **A factory naming its own flags frees the parameter name**: `typer.Option("--input", "-i")` lets the parameter be `input_` without the CLI seeing the underscore.
- **A repeated option defaults to `list[T] | None = None`**, resolved in the body: `list[T] = [x]` fails `ruff`'s B006, a tuple fails `pyright` against `list`, and `typer` refuses `Sequence`.
Restore the `--help` text with `show_default="daily"` on the factory.
- **A date or clock default is `None`, resolved where used** — a signature expression is evaluated once at import and goes stale.
Describe the behaviour in `show_default`, not a value nothing computes: an open upper date gets "as recent as there is", not "today", since passing today is a different request.
- **Parameterise a factory over systematic options.** A surface with a threshold per metric takes the axis as an argument — `minimum(metric: domain.Metric)` builds the help and `rich_help_panel` — and the body hands the whole option set on with `bounds.frame(**locals())`, rather than repeating every name in a second list that drifts.
`typer` reads real parameters, so the signature must still name each one.
- **Keep help terse and let defaults be the examples.** A default shows format and value at once; a required argument is the one place a bare example value earns its line, and only where the name leaves the format open.

**Set the `typer` options that make `--help` the documentation:**

- `no_args_is_help=True` on every `typer.Typer()`, so a bare group lists its commands as the root does.
- `context_settings={"help_option_names": ["-h", "--help"]}` on the root; it propagates.
- `rich_help_panel` once a command has more than a handful of options.
- `metavar` where the derived one reads wrong (`STATION...`, not `[stations]...`).
- `show_default` as a string wherever a default has behaviour to describe; `False` only where there is nothing to say.

Read the rest of `typer.Typer`'s signature before adding to it — `pretty_exceptions_show_locals` already defaults to `False`.

### Output

**Render the machine form and the person's form separately.** `rich` drops colour off a terminal, but a boxed table is still unparseable, so the plain form is a second path chosen by option, never by `Console().is_terminal`.
`output` decides; `rich_` only builds the table:

```python
def display(
    report: polars.DataFrame, *, path: pathlib.Path | None, pretty: bool
) -> None:
    """Draw the report as a table, or emit it as CSV."""
    with contextlib.ExitStack() as open_files:
        file = sys.stdout if path is None else open_files.enter_context(path.open("w"))
        if pretty:
            rich.console.Console(file=file).print(render.table(report))
        else:
            file.write(report.write_csv(include_header=False))
```

- **Build a table a level at a time**: a function per cell, one per row, one assembling them; a branch in a loop naming a column is the renderer sniffing the frame again.
- **Style a cell with a `rich.text.Text`**, never a row's `style=`, which paints the identity columns too.
- **Read input the same way**: type the argument `pathlib.Path` and treat `-` as standard input, so `mypackage-cli report -` works mid-pipeline.
- **Presentation config is a function**, `_colour(trend)` in `rich_`, not a module-level dict (see `write-python`).

**Send logs and errors to standard error.** `rich.logging.RichHandler()` builds its own `Console()` on standard output, so give it `rich.console.Console(stderr=True)` (see Logging); print errors with `typer.echo(message, err=True)`.

**Catch your own errors with a decorator on each command**, under `@app.command()` so `typer` still reads the signature: it catches your base error, prints the message to standard error and raises `typer.Exit(code=1)`.
It is `write-python`'s `handle` with `report=output.report`, and the one broad catch at a boundary; a `try` per command is missed on exactly the command that then shows a traceback.

A throwaway one-command tool may collapse `typer_` and `rich_` into one `cli.py`, with the work still in the core.

## API

`fastapi` for routing, `pydantic` for the schemas, `uvicorn` to serve:

```text
api/
  __init__.py   role, hollow: re-exports app and run
fastapi_/
  __init__.py   re-exports app and run from driver
  depend.py     factories returning a fastapi.Depends marker
  driver.py     app = fastapi.FastAPI(); includes the router; run()
  provide.py    the providers Depends calls — names the concrete adapter
  query.py      factories returning a configured fastapi.Query
  route.py      the path operations — the composition root
pydantic_/
  __init__.py
  schema.py     the request and response models
```

**A schema is not a domain type, even when the fields match.** The DTO (Data Transfer Object) is the external contract, the domain type the internal truth; separate, they evolve independently and untrusted input is validated at the boundary.
Map between them in `route.py`.

- **Use `pydantic` at trust boundaries** — API bodies, `pydantic-settings`, parsing an external response in an adapter.
In the core the data is already validated, so a frozen `dataclasses.dataclass` is the lighter default.
- **Never duplicate an enum**: a schema field references the domain's `enum.Enum` directly.
- **A model wanted in both `adapt` and `drive` is a domain model** — the two edges can't import each other — so it moves to `transform`/`domain`.

**`fastapi` declares parameters as `typer` does**, `typing.Annotated[T, marker()]`, so `fastapi_` mirrors `typer_` with a factory module per marker (`query.py`, `path.py`, `body.py` as used):

```python
def stations() -> fastapi.params.Query:
    """Return the stations query parameter."""
    return fastapi.Query(description="Station IDs.")
```

**`Depends(fn)` calls `fn` and injects its return value**, so it wraps a *provider* returning the adapter — `Depends(provide.fetch)`, never `Depends(httpx_.fetch)`, which would have `fastapi` call the adapter and read its parameters as request inputs:

```python
def fetch() -> fastapi.params.Depends:
    """Inject the temperature source."""
    return fastapi.Depends(provide.fetch)
```

```python
def fetch() -> port.Fetch:
    """Provide the temperature source adapter; overridden in tests."""
    return httpx_.fetch
```

`provide.py` is the injection seam: it imports no `fastapi`, depends on `port.Fetch` in its signature, and names `httpx_` only in its body.
It earns its place only because `Depends` needs a callable to resolve; naming an adapter is otherwise the route's own job.

```python
router = fastapi.APIRouter()


@router.get("/report")
def report(
    stations: typing.Annotated[list[str], query.stations()],
    fetch: typing.Annotated[port.Fetch, depend.fetch()],
) -> list[schema.Reading]:
    """Report the average temperature for each station."""
    return [
        schema.Reading(**row)
        for row in operate.report(stations, fetch=fetch).iter_rows(named=True)
    ]
```

An ASGI (Asynchronous Server Gateway Interface) app isn't callable to start a server, so `driver.py` adds a launcher:

```python
app = fastapi.FastAPI()
app.include_router(route.router)


def run() -> None:
    """Launch the API server."""
    uvicorn.run(app)
```

A test swaps the adapter with `app.dependency_overrides[provide.fetch] = lambda: fake_fetch` — no patching.

## GUI

`shiny` (Shiny for Python): its reactive model re-renders only the outputs a changed input affects, and its UI/server split matches shell over core, where `streamlit` reruns the whole script.

**Use Shiny Core, not Express, in a packaged app.** Core keeps layout and reactive callbacks apart and yields an explicit `shiny.App` for the launcher; Express suits only a throwaway single-view dashboard.

```text
gui/
  __init__.py   role, hollow: re-exports app and run
shiny_/
  __init__.py   re-exports app and run from driver
  callback.py   server(input, output, session) — the composition root
  driver.py     app = shiny.App(layout.root(), callback.server); run()
  layout.py     functions returning shiny.ui objects; root() is the top
```

Layouts are functions, so a reused panel is a function `root()` calls rather than copied markup:

```python
def root() -> htmltools.Tag:
    """Return the top-level layout."""
    return shiny.ui.page_fluid(
        shiny.ui.input_text("stations", label="Stations", value="london tokyo"),
        shiny.ui.output_data_frame("report"),
    )
```

```python
def server(input: shiny.Inputs, output: shiny.Outputs, session: shiny.Session) -> None:
    """Wire inputs to the core and render the results."""

    @shiny.render.data_frame
    def report() -> polars.DataFrame:
        """Render the report for the stations entered."""
        return operate.report(input.stations().split(), fetch=httpx_.fetch)
```

`driver.py` builds `app = shiny.App(layout.root(), callback.server)` and a `run()` calling `shiny.run_app(app)`.

## Jobs

A job is `command.py` without the parsing: a thin composition root wiring a source and a sink around an operation, run once by an **external** scheduler — cron, a systemd timer, a Kubernetes `CronJob`, a cloud trigger — so the schedule lives in infrastructure.

```python
def run() -> None:
    """Fetch the latest readings and store the daily averages."""
    operate.refresh(fetch=httpx_.fetch, store=postgres_.save)
```

Reach for a library only when the trigger must live inside the process, each in its own trailing-underscore package:

- **In-process scheduling** → `apscheduler`.
- **A task queue** → `dramatiq` over a Redis or RabbitMQ broker.
- **Orchestration** (dependent steps, retries, backfills) → `prefect` or `dagster`.

## Configuration

Load configuration once at the composition root and pass values into operations (see `structure-python`).
A `pydantic-settings` model in a driver-side `config` module validates the environment and fails fast on a bad value:

```python
class Settings(pydantic_settings.BaseSettings):
    """Application configuration, read from the environment."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="MYPACKAGE_")

    rate: float = 0.05
    timeout: float = 30.0
```

A secret is a `pydantic.SecretStr` field from the environment or a mounted file, never a default in code.

- **One value is a function, not a model.** A function reading one variable and raising an error naming it when unset costs nothing; grow into the model at the second field, and call sites don't change.
It also keeps a required value honest, where a model invites a default.
- **Validate at startup only what the running command needs.** A `typer` callback runs before every command, so validating there makes `--version` or a listing command fail for a credential it never uses; check in the commands that need it.

## Logging

Configure once at the composition root — from a `typer` callback, a `fastapi` lifespan hook, or the top of a job's `run()` — through a `logging_/` package, with destination and level exposed as options:

```python
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

`basicConfig` applies `format` only to a handler without one, so the file keeps its timestamps and `RichHandler` gets the bare message — leave `format` out and Rich prints the level twice.
Every other module just logs through `logging.getLogger(__name__)`.

## Run

Each entry point is a `[project.scripts]` command named `<project>-<role>` — it lands on `PATH` when installed, so never a bare `cli`.
It points at a callable app (`typer`) or a `run()` launcher (`uvicorn`, `shiny`, a job):

```toml
[project.scripts]
mypackage-api = "mypackage.code.drive.api:run"
mypackage-cli = "mypackage.code.drive.cli:app"
mypackage-gui = "mypackage.code.drive.gui:run"
mypackage-job = "mypackage.code.drive.job:run"
```

```bash
uv run mypackage-cli report london tokyo
```

- The API and GUI also run under their dev servers: `uvicorn mypackage.code.drive.api:app`, `shiny run mypackage.code.drive.gui:app`.
- A job carries no scheduler; the external trigger invokes its command.
