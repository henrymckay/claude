---
name: setup-python
description: >-
  How to scaffold and structure a new Python project or package — directory
  layout, application architecture (a pure core behind ports, with adapters and
  entry-point drivers), pyproject.toml, dependency management, and toolchain.
  Use whenever starting a new Python project, package, script, or tool; adding
  packaging to existing code; setting up dependencies, virtual environments, or
  project config; structuring an app into layers; or deciding where a module,
  entry point (CLI, API, GUI, or job), IO adapter, or data asset (SQL,
  templates, static data) belongs — even if the user just says "new project",
  "set this up", or "make this a package". Standardizes
  on uv, ruff, taplo, pyright, and pytest, targeting the latest stable Python.
  For in-code style once files exist, see the write-python skill; the
  per-framework entry-point build-outs (CLI, API, GUI, jobs) are in
  references/entry-points.md.
---

# Setting up a Python project

Getting the skeleton right up front — layout, packaging, tooling — saves pain later.
This covers *structure and setup*; for how to write the code inside, see `write-python`, and for the tests, `write-tests`.

**Match an existing project first.** If there's already a `pyproject.toml` or an established layout, follow it rather than imposing this.

## pyproject.toml

One file for metadata, dependencies, and tool config.
A sensible starting point:

```toml
[project]
name = "mypackage"
version = "0.1.0"
description = "..."
requires-python = ">=3.14"
dependencies = []

[project.scripts]
mypackage-cli = "mypackage.code.drive.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mypackage"]

[tool.ruff]
line-length = 88
target-version = "py314"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "D", "UP", "B", "SIM", "C4"]

[tool.ruff.lint.pydocstyle]
convention = "pep257"

[tool.pyright]
typeCheckingMode = "standard"

[tool.pytest.ini_options]
testpaths = ["tests/suite"]
addopts = "--import-mode importlib -p pytest_.given"
pythonpath = ["tests"]
```

The non-obvious choices:

- `[project.scripts]` — a `<project>-<role>` command per launchable entry point (see [Entry points](#entry-points)).
- `[tool.hatch.build.targets.wheel]` spells out the package path so `hatchling` finds it under `src/`; without it the wheel build can't locate the package.
- `[tool.ruff.lint] select` opts into a broader baseline than ruff's `E`+`F` default: `I` (isort import sorting), `N` (pep8-naming), `D` (pydocstyle docstring presence), `UP` (pyupgrade modern syntax), `B` (bugbear likely-bug patterns), `SIM` (simplify) and `C4` (comprehensions).
- `pydocstyle` convention `pep257` checks that docstrings *exist* without imposing Google/NumPy section formatting, so the reST field-list style stays free (see `write-python`). Tests are held to the same standard — there is no `tests/` exemption.
- The `[tool.pytest.ini_options]`, `pythonpath` and `src` settings serve the test layout (see [Tests](#tests)).

**TOML array style.** Keep an array on one line while it fits the line width, and wrap to one item per line (with a trailing comma) only once it overflows — the same collapse/expand rule `ruff` applies to Python.
`ruff` formats Python only, not TOML, so `taplo` handles it (part of the toolchain below) — `taplo fmt` applies exactly this rule, collapsing the expanded arrays `uv add` leaves behind.

## Pick a layout

- **One-off script / tiny tool** → a single `.py` file.
  Don't ceremony it up.
  If it needs a dependency, use an inline script block (see [Standalone scripts](#standalone-scripts)).
- **Anything installable or that others import** → the **`src/` layout** below.

The `src/` layout puts the package one directory down so it *can't* be imported accidentally from the repo root before it's installed.
That forces you to test against the actually-installed package and catches packaging mistakes early — the whole reason it's the default.

```text
myproject/
  .gitignore
  pyproject.toml
  README.md
  src/
    mypackage/
  tests/
    data/
    pytest_/
    suite/
```

Keep modules small and cohesive (one responsibility).
This is just the skeleton; each part expands in its own section, with its own directory block: `mypackage/` in [The package layers](#the-package-layers), `tests/` in [Tests](#tests), and the `code/drive/` entry points in [Entry points](#entry-points).

## The package layers

Under `mypackage/`, keep all Python in a `code/` package and all non-code assets in a `data/` directory beside it — two parallel trees, `data/` mirroring the code layers (see [Package data and assets](#package-data-and-assets)).

```text
mypackage/
  __init__.py
  code/
    __init__.py
    adapt/
    drive/
    operate/
    port/
    transform/
  data/
```

Structure `code/` as two groups: a pure **core** that holds the logic, and an outer **edge** that does all the IO — the ports-and-adapters (hexagonal) shape.
The standard packages are `transform`, `port` and `operate` in the core, and `adapt` and `drive` at the edge, each named for what it does (imperative verbs for the behavioural layers per `write-python`; `port`, a package of definitions, stays a noun).

`mypackage/`, `code/`, and every layer under `code/` is a regular package — each carries an `__init__.py` — which is what makes `from mypackage.code import operate` and the `importlib.resources.files("mypackage")` anchor resolve; `data/` is a plain resource tree, not a package.

Two rules hold it together:

- **IO lives only at the edge.** The edge — driven adapters like `adapt`, and the drivers under `drive` — is the only code that touches the outside world: network, filesystem, clock, randomness, external services. The core (`transform`, `port`, `operate`) stays **pure** — deterministic and side-effect-free. Purity is about side effects, not dependencies: the core uses third-party *computation* libraries freely (`polars` for dataframes, `numpy`), and only avoids the IO/delivery frameworks (`fastapi`, `httpx`, `uvicorn`, `typer`, `shiny`) whose job *is* IO. (Even within `polars`, the transforms are core while `scan_csv`/`write_*` are edge.)
- **Imports point inward.** The edge imports the core; the core imports neither the edge nor anything outward. A driver is the one place that imports both an operation and a concrete adapter, to wire them together.

Control flows the other way: a running operation calls *out* through a port to whichever adapter a driver injected.
Dependency injection is what lets the import arrow point in while control flows out — the operation *calls* the adapter without *importing* it.
That injection is the essential idea (see `be-functional`).

**The names are a standard, not a fixed set.** What fixes a package is which group it's in — set by the two rules — not that it's spelled exactly `transform` or `adapt`. Add more pure packages beside `transform` as the core grows (a `domain`, a `pricing`), and more edge packages beside `adapt` as the IO grows — an `extract` for input and a `load` for output, say. Each new core package obeys the core's rules (no IO; imported, never importing outward); each new edge package obeys the edge's (does its own IO, imports the core, is never imported by it).

**Let it grow into the app.** A tiny tool is a module or two at the package root (`mypackage/transform.py` + `mypackage/drive.py`) — no `code/`/`data/` split; introduce the `code/` wrapper, `data/`, and the layer packages only once there's a real boundary to name — an external service, a second entry point, more than one operation, assets to separate from code. Don't scaffold the full set for a script (KISS, YAGNI).

**Reach each package through one qualified name.** A package presenting a single cohesive API re-exports it in `__init__.py`, so callers import the package and qualify through it — `transform.averages(...)`, `operate.report(...)`, `port.Fetch` — never a bare `averages` or a stuttering `average.averages`. A package of independent peers instead keeps them as separate modules you import and qualify directly — an adapter is `httpx_.fetch`, a typer module is `argument.stations()`. Either way you import a *module* and reach its members qualified through it (see `write-python`).

### transform — the pure core

The types and rules of the problem, plus the pure functions over them, depending on nothing outward.
Model data so illegal states can't be built (see `be-functional`).
Reads as a phrase where it's called: `transform.averages(readings)`.

```text
transform/
  __init__.py
  average.py
```

The domain types that model the problem — dataclasses and enums like a `Reading` or a `Scale` — live here too for a small app; split them into a dedicated `domain/` package (a noun) once they multiply, leaving the pure functions in `transform`. They're the domain's data, so they sit in the core, never in `port`.

### port — the seams

The *behavioural* interfaces the core needs the outside world to satisfy — `typing.Protocol`s or callable type aliases (`Fetch = collections.abc.Callable[[list[str]], dict[str, list[float]]]`).
A port names *what* the core needs, not *how*: `operate` depends on it, `adapt` implements it.
A noun, because it only defines.
Ports are interfaces, not data — the domain's own dataclasses and enums are *not* ports; they belong with the domain (see `transform` above), though a port's signature may reference them.

```text
port/
  __init__.py
  fetch.py
```

### operate — the use cases

The functions that orchestrate a whole task (`operate.report(stations, fetch)`): call `transform` for logic and a `port` for I/O, staying IO-free because the adapter is injected.
Imports `transform` and `port` only.

```text
operate/
  __init__.py
  report.py
```

Each use case is a module, re-exported in `operate/__init__.py` per the package-API rule above, so a driver calls `operate.report(...)`:

```python
from mypackage.code.operate.report import report

__all__ = ["report"]
```

### adapt — the driven adapters

The IO layer: concrete implementations of the ports, each adapting an outside system to what the core expects — `adapt`'s `httpx_.fetch` calls the weather service over HTTP and adapts its JSON response to the `Fetch` port.
Imports `transform`/`port` to conform to them; never imports `operate` or `drive`.
Library-coupled modules take trailing-underscore names.

```text
adapt/
  __init__.py
  httpx_.py
```

When the IO splits into the `extract`/`load` pair above, `load` means *persist to a store* — not on-screen presentation, which is a driver's job and belongs in `drive`.

### drive — the entry points

The driving side and composition root: the entry points (CLI, API, GUI, jobs) that start the program.
A driver imports both an operation and a concrete adapter and injects one into the other:

```python
from mypackage.code import operate
from mypackage.code.adapt import httpx_

operate.report(stations, fetch=httpx_.fetch)
```

The role packages, framework packages, and presentation a driver holds are covered in [Entry points](#entry-points) next.

```text
drive/
  cli/
  rich_/
  typer_/
```

## Entry points

Every project is reached through one or more **entry points** — the ways it gets invoked.
These are the **drivers**: each is a thin **shell** over the presentation-agnostic core (see [The package layers](#the-package-layers)) that calls an operation, injects the concrete adapter it needs, and owns its own presentation — so a second entry point can serve or render the same results its own way.
Every driver lives under `code/drive/`.

Split each shell into a **role package** and one or more **framework packages**:

- The **role package** (`cli`, `api`, `gui`) is named for *what it is* and is hollow — it just re-exports the app object, giving a stable entry point (`mypackage.code.drive.cli:app`) that hides which library is behind it.
- The **framework packages** (`typer_`, `rich_`, `fastapi_`, `shiny_`) hold the tightly-coupled code — everything that uses or returns that library's objects. They take the trailing-underscore name (per `write-python`), which both marks the coupling and avoids shadowing the real `typer`/`rich`. Swap the library and only the framework package changes; the role name stays put.

**Launch each entry point with a `[project.scripts]` command named `<project>-<role>`** — `mypackage-cli`, `mypackage-api`, `mypackage-gui`, run with `uv run mypackage-cli ...`.
That name is a *global* command (it lands on `PATH` when the package is installed), so it must be namespaced to the project, not a bare `cli`/`api`/`gui`; `uv run` scoping to the local env doesn't change that.
(If one interface is clearly primary you can give it the bare project name and suffix only the rest, but symmetric `<project>-<role>` reads better for peers.)
The command points at whatever *starts* that entry point: a callable app object where the framework gives one (a `typer` app is callable), or a thin `run()` launcher where it doesn't (`uvicorn.run(app)` for an API, `shiny.run_app(app)` for a GUI).

Two things are *not* separate entry points:

- A **library** — if the project is imported by other code, its public API *is* the interface; there is no shell, only the `__all__` / public surface (see `write-python`).
- A **data pipeline** — the transforms are core; the entry point is the *job* that runs them (see `references/entry-points.md`).

The shell types — CLI (`typer` + `rich`), API (`fastapi` + `pydantic`), GUI (`shiny`), and scheduled/event-driven jobs — are each built out in `references/entry-points.md`: the module layout, composition-root wiring, and launcher.

## Package data and assets

Non-code assets an app needs at runtime — SQL query files, HTML templates, static reference data — load through `importlib.resources`, never a path built from `__file__` or the repo root.

Keep them all in one `data/` directory whose inside **mirrors the code layers**, so every asset's path names the layer that owns it — `data/` and `code/` are the two parallel trees under the package. One place to manage, with ownership still explicit:

```text
mypackage/
  code/
    adapt/
    drive/
    operate/
    port/
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

Where `data/` sits follows whether the assets ship — the one place its level does *not* follow `tests/`. Package data must live **inside the package** (`src/mypackage/data/`, as above) to be installed and reachable via `importlib.resources` — not a bare `src/data/`, since `src/` is only a source root: just the package beneath it ships, with the `src/` prefix stripped, so a sibling of the package is neither packaged nor reachable as `mypackage`'s data. `tests/` can sit at the repo root precisely because it never ships. Reserve a repo-root `data/` (a sibling of `src/` and `tests/`, mirroring the package the same way) for data that deliberately stays out of the wheel — large datasets, dev seed data.

Reach a packaged asset by navigating from the package, not the filesystem:

```python
import importlib.resources

query = (
    importlib.resources.files("mypackage") / "data" / "adapt" / "orders.sql"
).read_text()
```

`hatchling` ships non-`.py` files under the package automatically, so a committed in-package `data/` needs no extra config; add `[tool.hatch.build.targets.wheel]` `artifacts` only for generated or git-ignored files. All of this is distinct from `tests/data/` — test fixtures that never ship (see [Tests](#tests)).

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
- **`pytest_/`** — the imported helpers, as a package (`__init__.py`): fixtures in `given.py`, custom assertions in `then.py`, and action helpers in `when.py` where actions earn a name. It's named `pytest_` (per `write-python`'s underscore rule) because it's all pytest-coupled — fixtures, and assertions written as bare `assert`s rather than `unittest`'s methods. Tests import it as `from pytest_ import then`.
- **`suite/`** — the test cases: your code mirrored in `suite/<package>/`, and dependency-behaviour tests in `suite/packages/`.

The pytest settings in the template serve this layout:

- `testpaths = ["tests/suite"]` collects only the cases.
- `--import-mode importlib` avoids `sys.path` clashes from the `src/` layout and nested folders.
- `pythonpath = ["tests"]` with `-p pytest_.given` makes `pytest_` importable and loads its fixtures.
- `src = ["src", "tests"]` marks `tests/` a source root so isort files `pytest_` as first-party.

Scaffold `tests/pytest_/given.py` (with its `__init__.py`) up front — `-p pytest_.given` fails to load if the module is missing.

That is the *scaffold*; the `write-tests` skill covers how to write the tests themselves — the given/when/then shape, naming, fixtures, and the rest.

## Dependencies & environment: use `uv`

`uv` manages the Python version, the virtualenv, and dependencies — fast, and it replaces `pip`, `pip-tools`, `pipenv`, `virtualenv` and `pyenv`.
If it isn't installed, use the standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`), which drops a prebuilt binary in `~/.local/bin`; prefer it over `brew install uv`, which on some machines falls back to a slow from-source build (compiling the whole Rust/LLVM toolchain).
The core workflow:

```bash
uv init
uv add httpx
uv add --dev pytest ruff pyright taplo
uv run pytest
uv sync
```

- `uv init` scaffolds a new project (or set one up by hand as above).
- `uv add httpx` adds a runtime dependency, writing it to `pyproject.toml` and the lock.
- `uv add --dev pytest ruff pyright taplo` adds dev-only tooling.
- `uv run pytest` runs inside the managed env — no manual `activate`.
- `uv sync` reproduces the env from `uv.lock`.

Commit `uv.lock` for applications (reproducible installs); libraries usually don't pin as hard.
Pin the Python version with a `.python-version` file so everyone's on the same interpreter.

**Target the newest Python release that all your dependencies support** for a new project — set `.python-version`, `requires-python`, and ruff's `target-version` to it.
That's usually the latest stable release, but a dependency without wheels for the very newest version can force you one release back, so pick the highest version for which `uv sync` resolves and the tests pass (and never a pre-release).
Determine it when you create the project rather than hardcoding a number that ages — the `>=3.14` / `py314` above are just today's answer, not a fixed target.
A library published for others is the exception: keep a lower `requires-python` floor so you don't lock out consumers on older interpreters, even while you develop against the latest.

## Reach-for libraries

Prefer the standard library by default; only when a task genuinely needs a dependency, reach for the house pick below (see `write-python` on preferring the simplest solution).
Listed by task:

- **CLI** → `typer` (type-hint-driven, generates `--help`, pairs with `rich`) or `fire` (reflects an object straight into a CLI) in preference to stdlib `argparse`; reach for `argparse` only as a zero-dependency fallback for a trivial one-or-two-flag script.
- **Web API** → `fastapi` (type-hint-driven, async, OpenAPI docs for free), served with `uvicorn` and pairing with `pydantic`.
- **Dashboard / web UI** → `shiny` (Shiny for Python) for its reactive model and clean UI/server split, over Streamlit's whole-script rerun.
- **Scheduled / background jobs** → no library by default (an external cron, systemd timer, or cloud scheduler runs a console script); `apscheduler` for in-process scheduling, `dramatiq` for a task queue (over Celery), `prefect` or `dagster` for orchestration.
- **Tabular / columnar data** → `polars` (see `use-polars`), including a dataframe another library hands you — convert a pandas result with `polars.from_pandas`. Keep the work in the frame rather than extracting to Python lists, per `write-python`.
- **HTTP** → `httpx` (sync and async) over `requests`.
- **Logging** → `logging` with `rich.logging.RichHandler`, or `rich.print` for one-off output, in preference to bare `logging` or `print`; `loguru` is an option for a more ergonomic API. `rich` formats output but isn't itself a logging framework.
- **Numerics** → `numpy` and `scipy` for numerical work, `sympy` for symbolic maths.
- **Terminal output** → `rich` for tables, progress bars, colour, and readable tracebacks.
- **Testing** → `pytest`, with `hypothesis` for property-based tests (assert invariants over generated inputs — strong for numeric and algorithmic code) and `pytest-cov` for coverage.
- **Validation & settings** → `pydantic` v2 for data models and validation, `pydantic-settings` for typed config from the environment.

## Standalone scripts

A single script that needs a package shouldn't require a whole project.
Declare deps inline (PEP 723) and run with `uv run script.py` — uv builds a throwaway env on the fly:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx"]
# ///
```

Never bundle an interpreter or assume packages are globally installed — declare what's needed and let uv resolve it.

## Pre-commit hooks

Enforce formatting and linting on every commit with the `pre-commit` framework — deterministic, so it holds regardless of how the code got written.
Add `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.x.x
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/ComPWA/taplo-pre-commit
    rev: v0.x.x
    hooks:
      - id: taplo-format
```

Pin each `rev` to the current release and bump it later with `pre-commit autoupdate`.
Then `uv add --dev pre-commit` and `pre-commit install` (once per clone, to register the git hook).
`ruff-check --fix` auto-fixes and `ruff-format` reformats Python; `taplo-format` does the same for TOML; if a hook changes files the commit stops so you can re-stage.
This is also where a Conventional Commits `commit-msg` hook belongs (see `use-git`).

## Toolchain summary

Set these up once and defer to them everywhere:

- **`uv`** — Python version, env, dependencies, running.
- **`ruff`** — format + lint + import sort for Python (`ruff format`, `ruff check --fix`).
- **`taplo`** — format + lint for TOML (`taplo fmt`), since `ruff` handles Python only.
- **`pyright`** — type checking (the `pyright-lsp` plugin surfaces it live).
- **`pytest`** — tests in `tests/`.

Add a `.gitignore` covering `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`, build artifacts, and the editor/OS cruft a collaborator's setup drops in (`.idea/`, `.vscode/`, `.DS_Store`).
See the `use-git` skill for repo hygiene.
