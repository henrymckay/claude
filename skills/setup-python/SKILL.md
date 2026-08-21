---
name: setup-python
description: >-
  How to scaffold and configure a Python project — the src/ layout,
  pyproject.toml, dependency and environment management with uv, house-pick
  libraries for common tasks, standalone scripts, pre-commit, and the
  ruff/taplo/pyright/pytest toolchain. Use whenever starting a new Python
  project, package, script, or tool; adding packaging to existing code; setting
  up dependencies, virtual environments, or project config; or choosing a
  house-pick library for a task — even if the user just says "new project", "set
  this up", or "make this a package". Standardises on uv, ruff, taplo, pyright,
  and pytest, targeting the latest stable Python. For how to organise the
  application's code into layers, see structure-python; for in-code style,
  write-python; for the tests themselves, write-tests.
---

# Set up a Python project

Getting the skeleton right up front — layout, packaging, tooling — saves pain later.
This covers *scaffolding, packaging, and tooling*; for how to organise the code into layers, see `structure-python`; for in-code style, `write-python`; for tests, `write-tests`.
Three mistakes account for most of what goes wrong: reaching for a tool the standard five already cover, laying the package out flat where `src/` would have caught the import mistake, and hand-rolling what a house-pick library already does.

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

- `[project.scripts]` — a `<project>-<role>` command per launchable entry point (see `write-entry-points`).
- `[tool.hatch.build.targets.wheel]` spells out the package path so `hatchling` finds it under `src/`; without it the wheel build can't locate the package.
- `[tool.ruff.lint] select` opts into a broader baseline than `ruff`'s `E`+`F` default: `I` (isort import sorting), `N` (pep8-naming), `D` (pydocstyle docstring presence), `UP` (pyupgrade modern syntax), `B` (bugbear likely-bug patterns), `SIM` (simplify) and `C4` (comprehensions).
- `pydocstyle` convention `pep257` checks that docstrings *exist* without imposing Google/NumPy section formatting, so the reStructuredText field-list style stays free (see `write-python`).
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

**Target the newest Python release that all your dependencies support** for a new project — set `.python-version`, `requires-python`, and `ruff`'s `target-version` to it.
That's usually the latest stable release, but a dependency without wheels for the very newest version can force you one release back, so pick the highest version for which `uv sync` resolves and the tests pass (and never a pre-release).
Determine it when you create the project rather than hardcoding a number that ages — the `>=3.14` / `py314` above are just today's answer, not a fixed target.
A library published for others is the exception: keep a lower `requires-python` floor so you don't lock out consumers on older interpreters, even while you develop against the latest.

## Libraries

For these common tasks the house pick is the default, not a dependency of last resort — reach for it over the standard-library alternative (`typer` over `argparse`, `pytest` over `unittest`, `rich` over bare `print`).
Everywhere else the stdlib-first rule holds — don't add a dependency you don't actually need (see `write-python`).

- **CLI** → `typer` (type-hint-driven, generates `--help`, pairs with `rich`) or `fire` (reflects an object straight into a CLI) in preference to stdlib `argparse`; reach for `argparse` only as a zero-dependency fallback for a trivial one-or-two-flag script.
- **Configuration and reference data files** → `pyyaml` (always `yaml.safe_load`, never `yaml.load`) for anything that isn't naturally a table, and `polars.read_csv` where it is; `structure-python` has the rule for choosing between them.
`tomllib` reads TOML from the stdlib but cannot write it, so leave TOML to the files a tool already owns.
- **Dashboard / web UI** → `shiny` (Shiny for Python) for its reactive model and clean UI/server split, over `streamlit`'s whole-script rerun.
- **HTML tables** → `pandas.read_html`, converting the result with `polars.from_pandas` and never touching `pandas` again.
It reads every table on a page into frames in one call, where the same job by hand is a parser, an XPath and a loop rebuilding rows the reader already had.
Pass `extract_links="body"` where a cell's link carries what its text does not — every cell then arrives as a `(text, href)` pair, which is what stops a linked table needing a parser after all.
It brings `pandas` and `pyarrow`, which are large; pay that once and use it for every table rather than mixing two approaches to one job.
- **HTTP** → `httpx` (sync and async) over `requests`.
- **Logging** → `logging` with `rich.logging.RichHandler`, or `rich.print` for one-off output, in preference to bare `logging` or `print`; `loguru` is an option for a more ergonomic API.
`rich` formats output but isn't itself a logging framework.
- **Numerics** → `numpy` and `scipy` for numerical work, `sympy` for symbolic maths.
- **Retries** → `tenacity` for retrying flaky IO, with exponential backoff and a predicate that retries only what is worth retrying.
A hand-rolled loop with `time.sleep` gets the jitter, the give-up condition and the final re-raise wrong, and it retries the errors that will never succeed alongside the ones that might.
- **Scheduled / background jobs** → no library by default (an external cron, systemd timer, or cloud scheduler runs a console script); `apscheduler` for in-process scheduling, `dramatiq` for a task queue (over `celery`), `prefect` or `dagster` for orchestration.
- **Spreadsheets** → `polars.read_excel`, which needs a reader engine installed beside it — `fastexcel` (the `calamine` backend) is the default and the fastest.
`polars` names the function but ships no engine, so a project that never adds one fails at the first call rather than at install; declare it as a dependency the moment a source publishes `.xlsx`.
- **Tabular / columnar data** → `polars` (see `use-polars`), including a dataframe another library hands you — convert a `pandas` result with `polars.from_pandas`, adding `pyarrow` alongside it, which that conversion needs for anything beyond plain numpy-backed columns.
Keep the work in the frame rather than extracting to Python lists, per `write-python`.
- **Terminal output** → `rich` for tables, progress bars, colour, and readable tracebacks.
- **Testing** → `pytest`, with `hypothesis` for property-based tests (assert invariants over generated inputs — strong for numeric and algorithmic code) and `pytest-cov` for coverage.
- **Validation and settings** → `pydantic` v2 for data models and validation, `pydantic-settings` for typed config from the environment.
- **Web API** → `fastapi` (type-hint-driven, async, OpenAPI docs for free), served with `uvicorn` and pairing with `pydantic`.
- **XML and other markup** → `lxml` for pulling data out of a document that is not a table, reaching elements by XPath or CSS selector, over a hand-rolled parser or a regex.
For XML use `lxml.etree` over the stdlib `xml.etree`, and match on `local-name()` rather than the namespace a document declares, since two publishers filing the same schema declare it differently and a namespace-bound XPath silently matches nothing.

## Standalone scripts

A single script that needs a package shouldn't require a whole project.
Declare deps inline (PEP 723) and run with `uv run script.py` — `uv` builds a throwaway env on the fly:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx"]
# ///
```

Never bundle an interpreter or assume packages are globally installed — declare what's needed and let `uv` resolve it.

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
