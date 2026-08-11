# GUI entry point — `shiny`

Part of `setup-python`'s Entry points — see `SKILL.md` for the shared role/framework pattern, `[project.scripts]` naming, and the core architecture.

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
