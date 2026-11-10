# Write entry points in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
Every driver lives under `code/drive/` (see `structure-python`); the libraries are `setup-python`'s house picks.
The running example is a weather app whose operation `operate.report(stations, fetch=...)` returns a `polars` frame of `station` and `average`, fetched through a `port.Records` that `noaa.fetch_records` satisfies, and whose `operate.records(items, *, end, start, store=...)` reads the store back (`store-data`).
Settings live in `drive/config.py`, logging in `drive/logging_.py` (Configuration and Logging below).

## Role and framework split

Under `code/drive/`, each driver is a hollow **role package** over one or more **framework packages**:

- The **role package** (`cli`, `api`, `gui`) only re-exports the app object, giving a stable entry point (`mypackage.code.drive.cli:app`) that hides the library.
- The **framework packages** (`typer_`, `rich_`, `fastapi_`, `pydantic_`, `shiny_`) hold the library-coupled code, named with `write-python`'s trailing underscore.

**Every framework package keeps its app object in `driver.py`**, with the `run()` launcher where one is needed.
An app object must exist before anything decorates it, so in its own module the command and route modules stay flat alphabetical lists; `driver.py` imports no other `drive` module, so nothing cycles.
`__init__.py` then stays a pure re-export, and you know where the app is in any framework package without reading it.

**A framework package may hold a module that imports nothing from its framework**, where that framework is its only caller — `fastapi_/provide.py` naming the concrete adapter.
Lift it to a shared `drive/` module when a second driver needs it.

**A package of interchangeable adapters names its own members.** Where the core picks among adapters at runtime, a function in `adapt/__init__.py` returns the mapping and every driver calls it; enumerating them in a driver means the next driver copies the list.
The driver still chooses to use the set and injects it.

## CLI

`typer` parses, `rich` renders, at one of three rungs:

- **A throwaway one-command tool** is one `cli.py`, with the work still in the core.
- **The middle rung**, for most tools: the `cli/` role package over one `typer_.py` and one `rich_.py` module, each holding what the packages below hold.
- **The full rung** promotes each module to a package when it would be worth opening a file at a time (`structure-python`'s module rule) — in practice at the second command group or the second output form.

The full rung while there is one command group:

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

`command.py` is the composition root (`SKILL.md`): it reads the settings once, opens the one client of the run with the key bound into it, builds the port's callable from the source module and the paced getter, and hands the result to `output`:

```python
import datetime
import functools
import pathlib
import typing

from mypackage.code import operate
from mypackage.code.adapt import httpx_, noaa, parquet
from mypackage.code.drive import config
from mypackage.code.drive.typer_ import argument, driver, option, output


@driver.app.command()
def report(
    stations: typing.Annotated[list[str], argument.stations()],
    form: typing.Annotated[output.Form, option.form()] = output.Form.CSV,
    path: typing.Annotated[pathlib.Path | None, option.output()] = None,
) -> None:
    """Report the average temperature for each station."""
    settings = config.read_settings()
    constants = noaa.read_constants()
    store = parquet.Store(settings.data_dir)
    today = datetime.datetime.now(datetime.UTC).date()
    with httpx_.build_client(
        settings.api_key.get_secret_value(), timeout=constants.timeout
    ) as client:
        get = httpx_.build_get_document(
            client,
            budget=constants.daily - store.count_requests(today),
            rates=constants.rates,
        )
        averages = operate.report(
            stations, fetch=functools.partial(noaa.fetch_records, get=get)
        )
    output.display(averages, form=form, path=path)
```

The key never leaves this function: `structure-python`'s Configuration says why the port carries no secret and the adapter reads no environment, and `rates`, `daily` and `timeout` are the source's YAML constants, not settings; `budget` is the day's limit less the requests the manifest already records (`structure-python`, Write an adapter).
`fetch` and `nightly` hand the operation the store's sinks — `parquet.Store`, then `motherduck.Store` when `motherduck_token` is set (`store-data`) — and display the manifest row they wrote (`SKILL.md`, Compose with other tools).


`typer_/__init__.py` re-exports the app and imports the modules whose decorators register commands — a decorator runs only when its module is imported:

```python
from mypackage.code.drive.typer_ import callback as callback
from mypackage.code.drive.typer_ import command as command
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
- **A group's arrival turns `command.py` into `command/`**, one module per group; `argument.py` and `option.py` follow only when they too would be worth opening a file at a time.

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

**`output` picks the form `SKILL.md` fixes by option; `rich_` only builds the table.** The form is an `enum.StrEnum`, since it crosses the boundary (see `write-python`): `typer` lists its members under `--help` and exits 2 on any other value.

```python
class Form(enum.StrEnum):
    """The forms a command can emit."""

    CSV = "csv"
    JSON = "json"
    TABLE = "table"


def display(report: polars.DataFrame, *, form: Form, path: pathlib.Path | None) -> None:
    """Emit the report in the form asked for, to the destination asked for."""
    with contextlib.ExitStack() as open_files:
        file = sys.stdout if path is None else open_files.enter_context(path.open("w"))
        match form:
            case Form.TABLE:
                rich.console.Console(file=file).print(render.table(report))
            case Form.JSON:
                file.write(report.write_ndjson())
            case Form.CSV:
                file.write(report.write_csv())
            case _:
                typing.assert_never(form)
```

`write_csv()` keeps its header and `write_ndjson()` is the JSON form; a binary form (`PARQUET`) is `report.write_parquet(path)` after a check that `path` was given, raising the usage error before anything is opened.

- **Build a table a level at a time**: a function per cell, one per row, one assembling them; a branch in a loop naming a column is the renderer sniffing the frame again.
- **Style a cell with a `rich.text.Text`**, never a row's `style=`, which paints the identity columns too.
- **Read input the same way**: type the argument `pathlib.Path` and treat `-` as standard input, so `mypackage-cli report -` works mid-pipeline.
- **Presentation config is a function**, `_colour(trend)` in `rich_`, not a module-level dict (see `write-python`).

**Send logs and errors to standard error.** `rich.logging.RichHandler()` builds its own `Console()` on standard output, so give it `rich.console.Console(stderr=True)` (see Logging); print errors with `typer.echo(message, err=True)`.

**Catch your own errors with a decorator on each command**, under `@app.command()` so `typer` still reads the signature: it catches your base error, prints the message to standard error and raises `typer.Exit(code=1)` — or `typer.Exit(code=2)` for the `ConfigurationError` that `config.read_settings()` raises around `pydantic.ValidationError`, joining the `2` `typer` already returns for a bad invocation (`run-unattended`, Report the outcome).
It is `write-python`'s `handle` with `report=output.report`, and the one broad catch at a boundary; a `try` per command is missed on exactly the command that then shows a traceback.

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
A `start`/`end` pair is inclusive at both ends, as `SKILL.md`'s Compose with other tools fixes for the CLI.

- **`pydantic` validates at the API boundary — request and response models — and in `pydantic-settings`.** An adapter returning a frame declares a `polars` schema instead (see `structure-python`), since a model per row re-validates what the frame's dtypes already fix; one returning records parses with `pydantic` (see `write-python`), and the core takes frozen dataclasses either way.
- **Never duplicate an enum**: a schema field references the domain's `enum.Enum` directly.
- **A model wanted in both `adapt` and `drive` is a domain model** — the two edges can't import each other — so it moves to `transform`/`domain`.

**`fastapi` declares parameters as `typer` does**, `typing.Annotated[T, marker()]`, so `fastapi_` mirrors `typer_` with a factory module per marker (`query.py`, `path.py`, `body.py` as used):

```python
def items() -> fastapi.params.Query:
    """Return the items query parameter."""
    return fastapi.Query(description="Item IDs.")
```

**`Depends(fn)` calls `fn` and injects its return value**, so it wraps a *provider* returning the adapter — `Depends(provide.store)`, never `Depends(parquet.Store)`, which would have `fastapi` call the adapter and read its parameters as request inputs:

```python
def store() -> fastapi.params.Depends:
    """Inject the store."""
    return fastapi.Depends(provide.store)
```

```python
@functools.cache
def settings() -> config.Settings:
    """Provide the settings once per process; overridden in tests."""
    return config.read_settings()


def store() -> port.Store:
    """Provide the store adapter; overridden in tests."""
    return parquet.Store(settings().data_dir)
```

`provide.py` is the injection seam: it imports no `fastapi`, depends on `port.Store` in its signature, and names `parquet` only in its body.
It earns its place only because `Depends` needs a callable to resolve; naming an adapter is otherwise the route's own job.
The API provides the store and no source adapter (`SKILL.md`, HTTP surface).

A date-range bound is a required `fastapi.Query()` with no default, so a call without it is a `422` rather than an unbounded scan.

```python
router = fastapi.APIRouter()


@router.get("/records")
def records(
    end: typing.Annotated[datetime.date, query.end()],
    items: typing.Annotated[list[str], query.items()],
    start: typing.Annotated[datetime.date, query.start()],
    store: typing.Annotated[port.Store, depend.store()],
) -> list[schema.Record]:
    """Return the stored records for the items from start to end, inclusive."""
    stored = operate.records(items, end=end, start=start, store=store)
    return [schema.Record(**row) for row in stored.iter_rows(named=True)]
```

An ASGI (Asynchronous Server Gateway Interface) app isn't callable to start a server, so `driver.py` adds a launcher, and one `exception_handler` maps the app's errors to statuses, so no route catches anything:

```python
_STATUS: typing.Final = {error.AbsentError: 404, error.BoundsError: 422}

app = fastapi.FastAPI()
app.include_router(route.router)


@app.exception_handler(error.AppError)
def explain(
    request: fastapi.Request, failure: error.AppError
) -> fastapi.responses.JSONResponse:
    """Answer an app error with the status its kind maps to."""
    return fastapi.responses.JSONResponse(
        {"detail": str(failure)}, status_code=_STATUS.get(type(failure), 500)
    )


def run() -> None:
    """Launch the API server on port 8000; the dashboard takes 8001."""
    uvicorn.run(app, port=8000)
```

`uvicorn.run` binds `127.0.0.1` by default; pass `host="0.0.0.0"` only when another machine must reach it, and add authentication in the same change (`SKILL.md`, HTTP surface).
A test swaps the adapter with `app.dependency_overrides[provide.store] = lambda: fake_store` — no patching.

## GUI

`shiny`, `setup-python`'s pick for a GUI, whose UI/server split matches shell over core.

**Use Shiny Core, not Express, in a packaged app.** Core keeps layout and reactive callbacks apart and yields an explicit `shiny.App` for the launcher; Express suits only a throwaway single-view dashboard.

```text
gui/
  __init__.py   role, hollow: re-exports app and run
shiny_/
  __init__.py   re-exports app and run from driver
  callback.py   server(input, output, session) — the composition root
  driver.py     app = shiny.App(layout.root(), callback.server); run()
  layout.py     functions returning shiny.ui objects; root() is the top
  provide.py    the settings, the store's read port and the manifest watch
```

Layouts are functions, so a reused panel is a function `root()` calls rather than copied markup:

```python
def root() -> htmltools.Tag:
    """Return the top-level layout."""
    return shiny.ui.page_fluid(
        shiny.ui.input_text("items", label="Items", value="LHR MAN"),
        shiny.ui.input_date_range("window", label="Days"),
        shiny.ui.output_data_frame("records"),
        shinywidgets.output_widget("chart"),
    )
```

```python
def server(input: shiny.Inputs, output: shiny.Outputs, session: shiny.Session) -> None:
    """Wire inputs to the core and render the results."""

    @provide.watch_runs()
    def runs() -> polars.DataFrame:
        return provide.store().read_runs()

    @shiny.render.data_frame
    def records() -> polars.DataFrame:
        start, end = input.window()
        return operate.records(
            input.items().split(), end=end, start=start, store=provide.store()
        )

    @shinywidgets.render_plotly
    def chart() -> plotly.graph_objects.Figure:
        return plotly.graph_objects.Figure(
            plotly.graph_objects.Bar(
                x=runs().get_column("source").to_list(),
                y=runs().get_column("rows").to_list(),
            )
        )
```

- **The dashboard calls `operate.*` over the store**, as the API does (`SKILL.md`, HTTP surface); `callback.server` is its composition root, and a dashboard that shells out to the CLI or calls the API has added a hop that fails on its own.
- **Refresh by watching the run manifest** (`store-data`), through `provide.watch_runs()`, which returns the decorator for wherever the store is, so `server` is the same on the laptop and the host.
Over the data directory it is `shiny.reactive.file_reader` on `runs.parquet`, which checks the file's modification time each second and re-runs its function when the nightly rewrites it.
Against MotherDuck there is no file, so it is `shiny.reactive.poll(read_last_run, interval_secs=300)` (`shiny` 1.9), where `read_last_run` asks the `runs` table for its latest `ended`: the manifest changes once a night, and every check is a query against MotherDuck's monthly compute, where the one-second default would run 86,400 a day per session.
Either way every output depending on `runs()` updates without a timer of its own.
- **Charts are `plotly` through `shinywidgets`**: `shinywidgets.output_widget("chart")` in the layout, `@shinywidgets.render_plotly` in the server, the figure built with `plotly.graph_objects` from the frame's columns; `plotly.express` needs the `express` extra and a `pandas` frame, so the frame would leave `polars` for a chart.
- **The callbacks nested in `server` carry no docstring**, as `write-python` says of a nested function; the blank line after `server`'s own docstring is that skill's exception for a short function's beats.

`driver.py` builds `app = shiny.App(layout.root(), callback.server)` and a `run()` calling `shiny.run_app(app, port=8001)`: `shiny.run_app` and `uvicorn.run` both default to 8000, so the two launchers collide unless the dashboard moves.

## Jobs

**The scheduled path is a CLI command**: `nightly` in `command.py` runs the whole sequence, and `myapp-cli nightly` is what the scheduler invokes (see `run-unattended`), so the CLI stays the one composition root and the schedule lives in infrastructure.
A `job/` driver exists only for an event trigger — a queue message, a webhook — whose framework needs its own app object, in its own trailing-underscore package (`setup-python` names the picks), with the work still an operation over the core.

## Configuration

Load configuration once at the composition root and pass values into operations (see `structure-python`, which says which value lives in settings and which in a source's YAML).
A `pydantic-settings` model in `drive/config.py` reads the environment and the project's `.env`, and fails fast on a bad value:

```python
_ROOT = pathlib.Path(__file__).resolve().parents[4]


class Settings(pydantic_settings.BaseSettings):
    """Application configuration, read from the environment and the project's .env."""

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=os.environ.get("MYAPP_ENV_FILE", _ROOT / ".env"),
        env_prefix="MYAPP_",
    )

    api_key: pydantic.SecretStr
```

`store-data` adds `data_dir`; `read_settings()` wraps `Settings()` in `write-python`'s `handle`, turning `pydantic.ValidationError` into the app's `ConfigurationError` that the CLI exits 2 on.

- **`env_file` is an absolute path**: four parents above `src/mypackage/code/drive/config.py` is the checkout, which an editable install (`uv sync`'s default for the project) still points at, and `MYAPP_ENV_FILE` overrides it for a wheel or a scheduler with its own secrets file.
A bare `".env"` is resolved against the current directory, which under a scheduler is not the repo, so the key is silently absent and every night exits 2.
- **`.env` is for the laptop and is ignored by git**; the environment wins over it, so a container sets variables and the file is never deployed.
Commit a `.env.example` naming every variable with a placeholder, so a fresh clone knows what to set without reading the model.
- **A secret is a `pydantic.SecretStr` field** with no default, so a missing key fails at startup and a `repr` or a log line shows `**********`.
- **One value is a function, not a model.** A function reading one variable and raising an error naming it when unset costs nothing; grow into the model at the second field, and call sites don't change.
It also keeps a required value honest, where a model invites a default.
- **Validate at startup only what the running command needs.** A `typer` callback runs before every command, so validating there makes `--version` or a listing command fail for a credential it never uses; check in the commands that need it.

## Logging

The composition root configures logging (`structure-python`) from a `typer` callback or a `fastapi` lifespan hook, through `drive/logging_.py`, with destination and level exposed as options:

```python
def _plain(handler: logging.Handler) -> logging.Handler:
    """Give a handler the timestamped plain format a file or a capture keeps."""
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    return handler


def _pick_handler(path: pathlib.Path | None) -> logging.Handler:
    """Return a rotated file, Rich for a person, or plain lines for a capture."""
    if path is not None:
        return _plain(
            logging.handlers.TimedRotatingFileHandler(
                path, backupCount=30, when="midnight"
            )
        )
    if sys.stderr.isatty():
        return rich.logging.RichHandler(
            console=rich.console.Console(stderr=True), rich_tracebacks=True
        )
    return _plain(logging.StreamHandler(sys.stderr))


def configure(
    *, level: int = logging.WARNING, path: pathlib.Path | None = None
) -> None:
    """Route application logs to a file or to standard error."""
    logging.basicConfig(
        force=True,
        format="%(message)s",
        handlers=[_pick_handler(path)],
        level=level,
    )
    for dependency in ("httpcore", "httpx"):
        logging.getLogger(dependency).setLevel(logging.WARNING)
```

**Rich when standard error is a terminal, the plain format when it is not**, so a person gets colour and a scheduler's or a runner's capture gets timestamped lines with no escape codes; this is the rendering library's colour rule from `SKILL.md`'s Compose with other tools, applied to the log.
`basicConfig` applies `format` only to a handler without one, so the plain handlers keep their timestamps and `RichHandler` gets the bare message — leave `format` out and Rich prints the level twice.
The default `WARNING` is for an interactive command; the scheduled `nightly` passes `logging.INFO`, so its log shows each adapter call at the level `structure-python`'s Logging gives it, and the two `httpx` loggers are pinned because they narrate every request at INFO.
The file rotates at midnight and keeps thirty days, since a plain file handler grows until the disk is full; when a run takes `--log-file` is `run-unattended`'s, and JSON lines belong only behind a collector that indexes them.

## Run

Each entry point is a `[project.scripts]` command in `setup-python`'s `pyproject.toml`, named as `SKILL.md`'s Run says: `mypackage-cli = "mypackage.code.drive.cli:app"` for the callable `typer` app, and `mypackage-api = "mypackage.code.drive.api:run"` or `mypackage-gui = "...gui:run"` for a `run()` launcher.
The API and GUI also run under their dev servers: `uvicorn mypackage.code.drive.api:app`, `shiny run mypackage.code.drive.gui:app`.
