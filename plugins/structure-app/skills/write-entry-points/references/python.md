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

The key never leaves this function (`structure-python`, Configuration); `rates`, `daily` and `timeout` are the source's YAML constants, and `budget` is the day's remaining requests (`structure-python`'s `references/http.md`).
`fetch` and `nightly` hand the operation the store's sinks (`store-data`) and display the manifest row they wrote.

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
- **An `@app.callback()`** is the home for app-wide options, as thin as a command.
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
- **Parameterise a factory over systematic options.** A surface with a threshold per metric takes the axis as an argument — `minimum(metric: domain.Metric)` builds the help and `rich_help_panel` — and the body hands the whole option set on with `bounds.frame(**locals())`, rather than repeating every name in a second list that drifts; `typer` reads real parameters, so the signature still names each one.
- **Keep help terse and let defaults be the examples**; a required argument is the one place a bare example value earns its line, and only where the name leaves the format open.

**Set the `typer` options that make `--help` the documentation:**

- `no_args_is_help=True` on every `typer.Typer()`, so a bare group lists its commands as the root does.
- `context_settings={"help_option_names": ["-h", "--help"]}` on the root; it propagates.
- `rich_help_panel` once a command has more than a handful of options.
- `metavar` where the derived one reads wrong (`STATION...`, not `[stations]...`).
- `show_default` as a string wherever a default has behaviour to describe; `False` only where there is nothing to say.

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

**Send logs and errors to standard error.** `rich.logging.RichHandler()` builds its own `Console()` on standard output, so give it `rich.console.Console(stderr=True)` (see Logging); print errors with `typer.echo(message, err=True)`.

**Catch your own errors with a decorator on each command**, under `@app.command()` so `typer` still reads the signature: `write-python`'s `handle` with `report=output.report`, which prints the message to standard error and raises `typer.Exit(code=1)`, or `code=2` for the `ConfigurationError` from `config.read_settings()` (`run-unattended`, Report the outcome).
A `try` per command is missed on exactly the command that then shows a traceback.

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

An ASGI (Asynchronous Server Gateway Interface) app isn't callable to start a server, so `driver.py` adds a launcher, and holds the one `exception_handler`:

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
    """Launch the API, and the web front end it serves, on port 8000."""
    uvicorn.run(app, port=8000)
```

`uvicorn.run` binds `127.0.0.1` by default, so wrap `app` in the Loopback guard below; pass `host="0.0.0.0"` only when another machine must reach it, and add authentication in the same change (`SKILL.md`, HTTP surface).
A test swaps the adapter with `app.dependency_overrides[provide.store] = lambda: fake_store` — no patching.

## Dashboard

Three build-outs, in `SKILL.md`'s order of preference: a web front end served by the API or as static files, Dash with Mantine, and Shiny.
Each reads the store through `operate.*`, takes its look from `design-interface` (its `references/python.md` builds the Plotly, Mantine and Shiny themes from one tokens module), and sets `data-ready` once its first screen has data.

### Web front end

The front end is its own folder beside `src/`, and the API serves both its JSON and its built files from one process:

```text
web/
  index.html          the scheme script and the root element
  package.json        with package-lock.json, committed
  vite.config.ts      builds into src/mypackage/data/web; proxies /api in dev
  src/
    main.tsx
    App.tsx           the header, the navigation and the screens
    index.css         the tokens (design-interface)
    lib/data.ts       the data module: every request a screen makes
    lib/format.ts     every number and date formatter
    components/ui/    shadcn/ui's components, added one by one
    components/       tile, chart card, table, status chip, error note
    views/            one file per screen in the plan
src/mypackage/
  code/drive/fastapi_/
    route.py          the /api routes the data module calls
    driver.py         mounts the built files at / after the routes
  data/web/           the build, git-ignored, shipped in the wheel
```

- **Node is a development dependency**: `uv add --dev nodejs-wheel` puts `node`, `npm` and `npx` in `.venv/bin`, so `uv run npm --prefix web ci` and `uv run npm --prefix web run build` work on a machine with no Node installed, at the version `uv.lock` pins (`nodejs-wheel` 24.22).
- **Scaffold with the tools' own generators** — `npm create vite@latest web -- --template react-ts`, then Tailwind's Vite plugin and `npx shadcn@latest init` — and commit `package-lock.json`, which pins the front end as `uv.lock` pins the Python.
- **Build into the package** with `build.outDir` set to `../src/mypackage/data/web` and `emptyOutDir: true`, so `uv_build` ships the built files in the wheel and the API finds them with `importlib.resources.files("mypackage.data") / "web"`.
- **Mount the files after the routes**: `app.mount("/", fastapi.staticfiles.StaticFiles(directory=web, html=True), name="web")` as the last line of `driver.py`, since a mount at `/` registered first answers every `/api` request with a 404.
- **Keep the screens in the page's state, not in paths**, a tab or a `?view=` parameter, since the static mount answers a path it has no file for with a 404.
- **In development run both servers**: the API under `uvicorn` on 8000, and `npm run dev` with `server.proxy` sending `/api` to it, so the page reloads on save.
- **`lib/data.ts` is the only module that fetches**, one typed function per route returning parsed rows, so a screen never builds a URL.
Each answer is a JSON array of rows, as the API's schemas define, with dates as ISO strings the formatting module turns into `12 Nov 2026`.
- **Poll the manifest, not the data**: one hook asks `GET /api/runs/latest` every 60 seconds and bumps a counter only when its `ended` changes, and every data hook takes that counter as a dependency; the age chip re-renders on the same tick.

**The static version swaps `lib/data.ts` for one that reads Parquet**, written by an `export` command into `web/public/data/`, small and pre-aggregated per screen, with `hyparquet`'s `asyncBufferFromUrl` and `parquetReadObjects`.
Keep each file to a few megabytes: Cloudflare caps a file at 25 MiB and ignores Range requests, so a reader that fetches by range downloads the whole file there (`deploy-project`).
The manifest's last run ships as a small JSON file beside them, polled the same way.

**Test it** with `fastapi.testclient.TestClient(app)` and the store overridden (API above) for every route, `vitest` for `lib/format.ts` and any shaping in `lib/data.ts`, and a Playwright smoke test per screen, marked `slow`, against the built app on a free port:

```python
@pytest.mark.slow
def test_each_screen_draws_its_data(
    served: str, page: playwright.sync_api.Page
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(served)
    page.wait_for_selector("html[data-ready='1']")
    for view in ("store", "runs"):
        page.click(f"[data-view='{view}']")
        page.wait_for_load_state("networkidle")
    assert errors == []
```

`served` is a fixture that starts `uvicorn` on the app in a thread over a temporary store and yields its URL; the browser is Playwright's headless shell, installed into the project as `build-project`'s evaluator says.

### Dash

`dash` with `dash-mantine-components` for the controls and layout, `dash-ag-grid` for tables and `plotly` for charts:

```text
gui/
  __init__.py   role, hollow: re-exports app and run
dash_/
  __init__.py   re-exports app and run from driver
  callback.py   the @dash.callback functions — the composition root
  driver.py     app = dash.Dash(...); app.layout = layout.root; run()
  figure.py     functions turning a frame into a colourless plotly figure
  layout.py     functions returning components; root() is the top
  provide.py    the settings, the store's read port and the manifest stamp
  theme.py      the Mantine theme (design-interface)
plotly_/
  template.py   house_light and house_dark (design-interface)
```

- **`driver.py` imports `callback`, sets the React version and builds the app**; `@dash.callback` registers each callback globally as its module is imported, as `typer_/__init__.py` imports its commands, and `dash-mantine-components` 3 needs React 19 where Dash 4.5 serves 18.3.1 by default, so without the call every Mantine component fails to render:

```python
import dash
import dash_mantine_components

from mypackage.code.drive.dash_ import callback as callback
from mypackage.code.drive.dash_ import layout
from mypackage.code.drive.plotly_ import template

dash._dash_renderer._set_react_version("19.2.4")  # pyright: ignore[reportPrivateUsage]
dash_mantine_components.pre_render_color_scheme()
template.register()

app = dash.Dash(__name__, title="My app", update_title=None)
app.layout = layout.root
```

- **`app.layout` is the function `layout.root`, not its result**, so each page load reads the store afresh; a layout built once at import shows the data the process started with.
- **Every id is a constant in `layout.py`**, which `callback.py` imports, so a renamed component fails at import rather than as a callback that silently never fires.
- **A callback calls `operate.*` over `provide.store()` and returns plain data**: a figure from `figure.py`, rows for the grid as `frame.to_dicts()`, text for a tile; a callback that edits one property of a large figure returns a `dash.Patch()`.
- **Catch the app's own error in the callback and return an error note** to the outputs it fills, since an uncaught one leaves them as they were and tells the viewer nothing (`write-python`, the error model).
- **Refresh by the manifest's stamp**: a `dcc.Interval` of 60 seconds drives a callback that reads the last run's `ended` into a `dcc.Store`, returning `dash.no_update` when it has not changed, and every data callback takes that store as an input, so data is re-read once a night rather than once a minute; the age chip reads the same tick.
- **Re-theme figures on `dmc.ColorSchemeToggle`'s `computedColorScheme`** with a `dash.Patch()` that sets `layout.template` (`design-interface`).
- **Test a callback by calling it**: `@dash.callback` returns the function it decorates, so a test calls it with the inputs and a fake store and asserts on what it returns; the browser smoke test is the web front end's, pointed at `run()`'s port.

`driver.py`'s `run()` calls `app.run(port=8001, debug=False)`, which serves on loopback through Flask; Dash is a WSGI app, so the Loopback guard's ASGI wrapper does not fit it, and the same check is a `before_request` hook on `app.server` refusing a `Host` or `Origin` outside the loopback names with `flask.abort(403)`.
A host runs `app.server` under `gunicorn` (`deploy-project`).

### Shiny

`shiny`'s UI/server split matches shell over core.

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
  theme.py      the Bootstrap theme (design-interface)
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

- **The dashboard calls `operate.*` over the store**, as the API does (`SKILL.md`, Dashboard); `callback.server` is its composition root, and a dashboard that shells out to the CLI or calls the API has added a hop that fails on its own.
- **Refresh by watching the run manifest** (`store-data`), through `provide.watch_runs()`, which returns the decorator for wherever the store is, so `server` is the same on the laptop and the host.
Over the data directory it is `shiny.reactive.poll` on the file's modification time and size, read as `None` while the file does not exist, since `shiny.reactive.file_reader` raises `FileNotFoundError` on a fresh store with no manifest yet and ends the session (`shiny` 1.9):

```python
type _Reader = collections.abc.Callable[[], polars.DataFrame]


def _stamp(path: pathlib.Path) -> tuple[int, int] | None:
    """Return the file's modification time and size, or None before it exists."""
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def watch_runs() -> collections.abc.Callable[[_Reader], _Reader]:
    """Re-run the decorated reader whenever the nightly rewrites the manifest."""
    manifest = settings().data_dir / "runs.parquet"
    return shiny.reactive.poll(functools.partial(_stamp, manifest), interval_secs=1)
```

Against MotherDuck there is no file, so it is `shiny.reactive.poll(read_last_run, interval_secs=300)`, where `read_last_run` asks the `runs` table for its latest `ended`: the manifest changes once a night, and every check is a query against MotherDuck's monthly compute, where the one-second default would run 86,400 a day per session.
Either way every output depending on `runs()` updates without a timer of its own, and `read_runs` answers an empty frame before the first run.
- **Show the last run's age, re-judged on a slow clock**: the output that says how old the data is calls `shiny.reactive.invalidate_later(3600)` and compares the latest `ended` with now, since a night that never ran rewrites nothing and a tab left open would otherwise show yesterday's verdict for ever.
- **Read the store in a `shiny.reactive.calc` or the render function, never a `shiny.reactive.effect`.** An exception raised in an effect ends the session — every output unrendered, "Session fatal error" — while one raised in a calc shows as an error in the outputs that read it and nowhere else (`shiny` 1.9).
- **Theme it from `design-interface`**: `shiny.ui.page_navbar(..., theme=theme.build())` with `shiny.ui.input_dark_mode(id="scheme")` in the navbar, and every figure's render function reading `input.scheme()` to pick `house_light` or `house_dark`.
- **Charts are `plotly` through `shinywidgets`**: `shinywidgets.output_widget("chart")` in the layout, `@shinywidgets.render_plotly` in the server, the figure built with `plotly.graph_objects` from the frame's columns; `plotly.express` needs the `express` extra and a `pandas` frame, so the frame would leave `polars` for a chart.
`shinywidgets` brings the IPython and `ipywidgets` stack, 24 packages over `shiny` and `plotly` (`shinywidgets` 0.8.2); a figure rendered with `fig.to_html(include_plotlyjs=False, full_html=False)` through `shiny.render.ui`, with `plotly.js` served from the app's `static_assets`, avoids them and loses the widget's in-place updates.
- **The callbacks nested in `server` carry no docstring**, as `write-python` says of a nested function; the blank line after `server`'s own docstring is that skill's exception for a short function's beats.

`driver.py` builds `app = starlette_.loopback_only(shiny.App(layout.root(), callback.server), port=8001)` (Loopback guard) and a `run()` calling `shiny.run_app(app, port=8001)`: `shiny.run_app`, `shiny run` and `uvicorn.run` all default to 8000, so the two launchers collide unless the dashboard moves.

**Test the server in process with `shiny.testserver.test_server(app)`** (`shiny` 1.9): set inputs, let the graph settle, and assert each output's `status` and `value`, with no browser; a widget output's value is only its model id, so test each figure at the plain function that builds it, and raise `timeout_secs` past its five-second default where the first import of the widget stack is slow.

## Loopback guard

A server answering on loopback with no authentication checks `Host` and any `Origin`, as `secure-project`'s Guard what is served says.
`drive/starlette_.py` wraps any app that runs on Starlette, the dashboard's and the API's alike, since `starlette.middleware.trustedhost.TrustedHostMiddleware` checks `Host` but lets a WebSocket from a foreign `Origin` through:

```python
_LOOPBACK = ("127.0.0.1", "localhost")


def loopback_only(
    app: starlette.types.ASGIApp,
    *,
    names: collections.abc.Sequence[str] = (),
    port: int,
) -> starlette.types.ASGIApp:
    """Refuse a request whose Host, or a WebSocket whose Origin, names elsewhere."""
    hosts = {f"{name}:{port}" for name in _LOOPBACK} | set(names)
    origins = {f"{scheme}://{host}" for host in hosts for scheme in ("http", "https")}

    async def guarded(
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        if scope["type"] not in ("http", "websocket"):
            await app(scope, receive, send)
            return
        host = [value.decode() for key, value in scope["headers"] if key == b"host"]
        origin = [value.decode() for key, value in scope["headers"] if key == b"origin"]
        foreign = (
            len(host) != 1
            or host[0] not in hosts
            or len(origin) > 1
            or any(value not in origins for value in origin)
        )
        if not foreign:
            await app(scope, receive, send)
        elif scope["type"] == "websocket":
            await send({"code": 1008, "type": "websocket.close"})
        else:
            await send({"headers": [], "status": 403, "type": "http.response.start"})
            await send({"body": b"", "type": "http.response.body"})

    return guarded
```

It reads the header list, not a mapping, so a repeated header is refused rather than resolved to whichever copy a mapping keeps; `names` takes the machine's Tailscale name when the server is shared over it (`deploy-project`).
Under Shiny 1.9 and uvicorn 0.54 it refused a foreign `Host` and a foreign-`Origin` WebSocket that the bare app answered.

## Jobs

**The scheduled path is `nightly` in `command.py`** (`SKILL.md`, Expose the stages), so the schedule lives in infrastructure (`run-unattended`).
A `job/` driver for an event trigger sits in its own trailing-underscore package (`setup-python` names the picks), with the work still an operation over the core.

## Configuration

A `pydantic-settings` model in `drive/config.py` reads the environment and the project's `.env`, and fails fast on a bad value (`structure-python`, Configuration, says which value lives here):

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
- **`.env` is for the laptop** (`secure-project`, Keep secrets out); the environment wins over it, so a container sets variables and the file is never deployed.
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
The default `WARNING` is for an interactive command; the scheduled level and when a run takes `--log-file` are `run-unattended`'s, and the `httpx` pins are `structure-python`'s Logging.
The file rotates at midnight and keeps thirty days, since a plain file handler grows until the disk is full; JSON lines belong only behind a collector that indexes them.

## Run

Each entry point is a `[project.scripts]` command in `setup-python`'s `pyproject.toml`, named as `SKILL.md`'s Run says: `mypackage-cli = "mypackage.code.drive.cli:app"` for the callable `typer` app, and `mypackage-api = "mypackage.code.drive.api:run"` or `mypackage-gui = "...gui:run"` for a `run()` launcher.
With a web front end, `mypackage-api` serves the dashboard too, once `uv run npm --prefix web run build` has written it into the package; in development the API runs under `uvicorn mypackage.code.drive.api:app --reload` beside `uv run npm --prefix web run dev`.
A Dash or Shiny `gui` runs on 8001, under `mypackage-gui` or `shiny run --port 8001 mypackage.code.drive.gui:app`, the port given because `shiny run` defaults to the API's 8000.
