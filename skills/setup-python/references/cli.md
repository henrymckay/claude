# CLI entry point — `typer` + `rich`

Part of `setup-python`'s Entry points — see `SKILL.md` for the shared role/framework pattern, `[project.scripts]` naming, and the core architecture.

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
