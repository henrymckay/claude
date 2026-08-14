---
name: setup-python
description: >-
  How to scaffold and configure a Python project — the src/ layout,
  pyproject.toml, dependency and environment management with uv, standalone
  scripts, pre-commit, and the ruff/taplo/pyright/pytest toolchain. Use whenever
  starting a new Python project, package, script, or tool; adding packaging to
  existing code; setting up dependencies, virtual environments, or project
  config; or choosing a house-pick library for a task — even if the user just
  says "new project", "set this up", or "make this a package". Standardises on
  uv, ruff, taplo, pyright, and pytest, targeting the latest stable Python. For
  how to organise the application's code into layers, see structure-python; for
  in-code style, write-python.
---

# Set up a Python project

Getting the skeleton right up front — layout, packaging, tooling — saves pain later.
This covers *scaffolding, packaging, and tooling*; for how to organise the code into layers, see `structure-python`; for in-code style, `write-python`; for tests, `write-tests`.

**In an existing project, ask first.** Where a repo already has a `pyproject.toml` or an established layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Toolchain

Standardise on these five tools; set them up once and defer to them everywhere:

- **`uv`** — Python version, env, dependencies, running.
- **`ruff`** — format + lint + import sort for Python (`ruff format`, `ruff check --fix`).
- **`taplo`** — format + lint for TOML (`taplo fmt`), since `ruff` handles Python only.
- **`pyright`** — type checking (the `pyright-lsp` plugin surfaces it live).
- **`pytest`** — tests in `tests/`.

## Configure the project

`pyproject.toml` is the one file for metadata, dependencies, and tool config.
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

- `[project.scripts]` — a `<project>-<role>` command per launchable entry point (see `structure-python`).
- `[tool.hatch.build.targets.wheel]` spells out the package path so `hatchling` finds it under `src/`; without it the wheel build can't locate the package.
- `[tool.ruff.lint] select` opts into a broader baseline than ruff's `E`+`F` default: `I` (isort import sorting), `N` (pep8-naming), `D` (pydocstyle docstring presence), `UP` (pyupgrade modern syntax), `B` (bugbear likely-bug patterns), `SIM` (simplify) and `C4` (comprehensions).
- `pydocstyle` convention `pep257` checks that docstrings *exist* without imposing Google/NumPy section formatting, so the reST field-list style stays free (see `write-python`).
Tests are held to the same standard — there is no `tests/` exemption.
- The `[tool.pytest.ini_options]`, `pythonpath` and `src` settings serve the test layout (see `structure-python`).

**TOML formatting.** Run `taplo fmt` — it keeps arrays on one line until they overflow the line width, and collapses what `uv add` leaves expanded.

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
      __init__.py
  tests/
```

An `__init__.py` marks a directory as an importable package — here only `mypackage/` is one; `src/` and `tests/` are plain directories.
Keep modules small and cohesive (one responsibility).
This is just the top-level skeleton; how `mypackage/` splits into `code/` and `data/` layers, and how `tests/` is laid out, is covered in `structure-python`.

Keep a real `.gitignore` from the start, covering `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`, build artifacts, and the editor/OS cruft a collaborator's setup drops in (`.idea/`, `.vscode/`, `.DS_Store`).
See the `use-git` skill for repo hygiene.

## Dependencies and environment

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

## Libraries

Prefer the standard library by default; only when a task genuinely needs a dependency, reach for the house pick below (see `write-python` on preferring the simplest solution).
Listed by task:

- **CLI** → `typer` (type-hint-driven, generates `--help`, pairs with `rich`) or `fire` (reflects an object straight into a CLI) in preference to stdlib `argparse`; reach for `argparse` only as a zero-dependency fallback for a trivial one-or-two-flag script.
- **Dashboard / web UI** → `shiny` (Shiny for Python) for its reactive model and clean UI/server split, over Streamlit's whole-script rerun.
- **HTTP** → `httpx` (sync and async) over `requests`.
- **Logging** → `logging` with `rich.logging.RichHandler`, or `rich.print` for one-off output, in preference to bare `logging` or `print`; `loguru` is an option for a more ergonomic API.
`rich` formats output but isn't itself a logging framework.
- **Numerics** → `numpy` and `scipy` for numerical work, `sympy` for symbolic maths.
- **Scheduled / background jobs** → no library by default (an external cron, systemd timer, or cloud scheduler runs a console script); `apscheduler` for in-process scheduling, `dramatiq` for a task queue (over Celery), `prefect` or `dagster` for orchestration.
- **Tabular / columnar data** → `polars` (see `use-polars`), including a dataframe another library hands you — convert a pandas result with `polars.from_pandas`.
Keep the work in the frame rather than extracting to Python lists, per `write-python`.
- **Terminal output** → `rich` for tables, progress bars, colour, and readable tracebacks.
- **Testing** → `pytest`, with `hypothesis` for property-based tests (assert invariants over generated inputs — strong for numeric and algorithmic code) and `pytest-cov` for coverage.
- **Validation & settings** → `pydantic` v2 for data models and validation, `pydantic-settings` for typed config from the environment.
- **Web API** → `fastapi` (type-hint-driven, async, OpenAPI docs for free), served with `uvicorn` and pairing with `pydantic`.

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
