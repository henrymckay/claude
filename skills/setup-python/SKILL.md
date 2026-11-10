---
name: setup-python
description: >-
  How to scaffold and configure a Python project — the src/ layout,
  pyproject.toml with the uv_build backend, dependency and environment
  management with uv, a committed lock file, the floor of Python 3.14, the
  house-pick libraries for common tasks (typer, httpx with tenacity and
  pyrate-limiter, polars, shiny with plotly, pydantic-settings, rich logging),
  standalone scripts, pre-commit hooks run through uv, releases with uv
  version, and the ruff/taplo/pyright-strict/pytest toolchain with the strict
  pytest flags. Use whenever starting a new Python project, package, script,
  or tool; adding packaging to existing code; setting up dependencies, virtual
  environments, project config or hooks; cutting a release; or choosing a
  house-pick library for a task — even if the user just says "new project",
  "set this up", or "make this a package". Standardises on uv, ruff, taplo,
  pyright and pytest, with no task runner, Docker only for a deployed API or
  job, and no CI until a project earns it; a PLAN.md decision overrides any
  pick. Plan a new project first with plan-project. For how to organise the
  application's code into layers, see structure-python; for in-code style,
  write-python; for the tests themselves, write-tests.
---

# Set up a Python project

This covers *scaffolding, packaging, and tooling*; plan a new project first with `plan-project` (a one-off script needs no plan); for how to organise the code into layers, see `structure-python`; for in-code style, `write-python`; for tests, `write-tests`.
Three mistakes account for most of what goes wrong: reaching for a tool the standard five already cover, laying the package out flat where `src/` would have caught the import mistake, and hand-rolling what a house-pick library already does.
Every pick here is a default: a decision recorded in the project's `PLAN.md` overrides it, and so does a dependency that no longer supports the pick, recorded there too.

**In an existing project, ask first.** Where a repo already has a `pyproject.toml` or an established layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Toolchain

Standardise on these five tools; set them up once and defer to them everywhere:

- **`uv`** — Python version, env, dependencies, running, building and the version bump.
- **`ruff`** — format + lint + import sort for Python (`ruff format`, `ruff check --fix`).
- **`taplo`** — format + lint for TOML (`taplo fmt`, `taplo lint`), since `ruff` handles Python only.
- **`pyright`** — type checking in `strict` mode (the `pyright-lsp` plugin surfaces it live).
`ty`, Astral's checker, is still a `0.0.x` pre-release that changes its diagnostics between versions, so a suite clean today fails on next week's install; switch when it reaches `1.0`.
- **`pytest`** — tests in `tests/`.

Nothing else by default: no task runner (`just`, `make`) until a project has a command `uv run` can't express; Docker only for an API or job that is deployed somewhere other than the machine it was built on, from the `ghcr.io/astral-sh/uv` image; documentation is the README plus `--help`; CI is declined until a project has a second contributor or a deploy (the plan records the exception).

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
requires = ["uv_build>=0.11,<0.12"]
build-backend = "uv_build"

[tool.ruff]
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "D", "UP", "B", "SIM", "C4", "RUF", "PT", "TC"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D"]

[tool.ruff.lint.pydocstyle]
convention = "pep257"

[tool.pyright]
typeCheckingMode = "strict"

[tool.pytest.ini_options]
addopts = "--import-mode importlib --strict-config --strict-markers -p pytest_.given"
filterwarnings = ["error"]
markers = ["slow: opt in with -m slow"]
pythonpath = ["tests"]
testpaths = ["tests/suite"]
xfail_strict = true
```

The non-obvious choices:

- `[project.scripts]` — a `<project>-<role>` command per launchable entry point (see `write-entry-points`).
- **`uv_build`** is what `uv init --package` writes: zero config for a `src/` layout, and it ships every file under the package, data included, so nothing names a path.
`hatchling` does the same and adds a plugin system; reach for it only when a build plugin is needed (a version from git tags, generated files), since it is a second tool to pin.
- `[tool.ruff]` names no `target-version`: `ruff` reads it from `requires-python`, so the floor lives in one place.
- `[tool.ruff.lint] select` opts into a broader baseline than `ruff`'s `E`+`F` default: `I` (import sorting), `N` (naming), `D` (docstring presence), `UP` (modern syntax), `B` (likely bugs), `SIM` (simplify), `C4` (comprehensions), `RUF` (`ruff`'s own, including unused `noqa`), `PT` (`pytest` style) and `TC` (imports only a type checker needs).
- `"tests/**" = ["D"]` drops docstrings from tests and fixtures, since the test name is the claim (see `write-tests`).
- `pydocstyle` convention `pep257` checks that docstrings *exist* without imposing Google/NumPy section formatting, so the reStructuredText field-list style stays free (see `write-python`).
- `pyright` `strict` on a greenfield project: `standard` (the default) lets an unannotated parameter through as `Unknown`, so a wrong argument is found at runtime; `strict` reports it at the definition.
An existing codebase adopts `strict` file by file with `# pyright: strict`.
- `--strict-markers` and `--strict-config` turn a misspelt marker or option into an error instead of a silently unselected test; `xfail_strict` fails a test that passes while marked `xfail`; `filterwarnings = ["error"]` turns a dependency's deprecation into a failing test the day it appears, with a `markers` entry per marker the suite uses.
- The `-p pytest_.given`, `pythonpath` and `testpaths` lines serve `structure-python`'s full `tests/` layout.
A small tool that keeps `tests/` flat drops them and sets `testpaths = ["tests"]`.

**TOML formatting.** Run `taplo fmt` — it keeps arrays on one line until they overflow the line width, and collapses what `uv add` leaves expanded.

## Pick a layout

- **One-off script / tiny tool** → a single `.py` file.
Don't ceremony it up.
If it needs a dependency, use an inline script block (see [Standalone scripts](#standalone-scripts)).
- **Anything installable or that others import** → the **`src/` layout** below.

The `src/` layout puts the package one directory down, so the repo root holds no importable package.
In a flat layout `import mypackage` from the repo root resolves to the working tree, so the tests pass against uncommitted source while the wheel is missing a file; under `src/` every import resolves to the installed package, and the missing file fails the first test.

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

How `mypackage/` splits into `code/` and `data/` layers, and how `tests/` is laid out, is covered in `structure-python`.
Keep a real `.gitignore` from the start (`uv init` writes one), so no generated file is ever staged.

## Dependencies and environment

`uv` manages the Python version, the virtualenv, and dependencies — fast, and it replaces `pip`, `pip-tools`, `pipenv`, `virtualenv` and `pyenv`.
If it isn't installed, use the standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`), which drops a prebuilt binary in `~/.local/bin`.
The core workflow:

```bash
uv init --package
uv python pin 3.14
uv add httpx
uv add --dev pytest ruff pyright taplo pre-commit
uv run pytest
uv sync
```

- **Commit `uv.lock`, for a library as much as an application.** It pins what the suite was green against; without it a contributor's `uv sync` resolves differently from yours and the first bug report is a version skew nobody can reproduce.
The published library still carries only `pyproject.toml`'s ranges, so consumers are not pinned.
- **Declare a lower bound and no upper cap** (`polars>=2.1`), since a cap blocks the upgrade that fixes the bug you hit; run `uv lock --upgrade` and the suite together on a schedule, and the lock moves only when the tests still pass.
- **Pin the Python version** with `uv python pin`, which writes `.python-version`, so everyone is on the same interpreter.

**Target the latest stable Python release**, 3.14 at the time of writing, in `.python-version` and `requires-python`; `write-python` writes to that floor, and `uv init` writes a release or two lower, so set both.
Go one release back only when a dependency has no wheels for it and `uv sync` fails to resolve, and record that under the plan's Decisions so the next sweep tries again; never a pre-release.
A library published for others is the exception: keep a lower `requires-python` floor so you don't lock out consumers on older interpreters, even while you develop against the latest.

## Libraries

For these common tasks the house pick is the default, not a dependency of last resort — reach for it over the standard-library alternative (`typer` over `argparse`, `pytest` over `unittest`).
Everywhere else the stdlib-first rule holds — don't add a dependency you don't actually need (see `write-python`).
No optional-extras split (`mypackage[dashboard]`): one install carries every driver, since a split means a second resolution to test and a user who installed the wrong one.

- **CLI** → `typer` (type-hint-driven, generates `--help`, pairs with `rich`) over stdlib `argparse`; `cyclopts` is the alternative when `typer`'s decorator model fights a surface built from plain functions, and `argparse` only for a zero-dependency one-or-two-flag script.
- **Dashboard / web UI** → `shiny` (Shiny for Python) for its reactive model and clean UI/server split, over `streamlit`'s whole-script rerun.
- **HTML tables** → `pandas.read_html`, converted at once with `polars.from_pandas`; it reads every table on a page in one call, and `extract_links="body"` keeps each cell's link as a `(text, href)` pair.
- **HTTP** → sync `httpx.Client` over `requests`, with `tenacity` for retries and `pyrate-limiter` for a stated rate; `structure-python`'s Write an adapter has the mechanics.
A hand-rolled `time.sleep` loop gets jitter, give-up and the final re-raise wrong, and `httpx`'s async client only where a driver or adapter needs it (see `write-python`).
- **Logging** → stdlib `logging` with `rich.logging.RichHandler` on standard error for a person, and JSON lines only where a collector reads them (see `run-unattended`); never `loguru`, which replaces the logger every dependency already writes to.
`write-entry-points` has the configuration.
- **Numerics** → `numpy` and `scipy` for numerical work, `sympy` for symbolic maths.
- **Plotting** → `plotly`, rendered in `shiny` through `shinywidgets`; `matplotlib` only for a static image a report embeds.
- **Scheduled / background jobs** → no library by default (an external cron, systemd timer, or cloud scheduler runs a console script; see `run-unattended`); `apscheduler` for in-process scheduling, `dramatiq` for a task queue (over `celery`), `prefect` or `dagster` for orchestration.
- **Spreadsheets** → `polars.read_excel`, with `fastexcel` (the `calamine` backend) as the reader engine.
`polars` names the function but ships no engine, so a project that declares none fails at the first call rather than at install.
- **Storage** → hive-partitioned Parquet for pipeline output, DuckDB to query it, SQLite for small single-writer state; `store-data` has the picks and their cases.
- **Tabular / columnar data** → `polars` (see `use-polars`), converting another library's `pandas` frame with `polars.from_pandas` plus `pyarrow`.
- **Terminal output for a person** → `rich` for tables, progress bars, colour, and readable tracebacks; a command's data output stays plain bytes on standard output (see `write-entry-points`).
- **Testing** → `pytest`, with `hypothesis` for property-based tests, `time-machine` for the clock, the `anyio` plugin for async code (not `pytest-asyncio`) and `pytest-cov` for coverage.
- **Validation and settings** → `pydantic` v2 at a trust boundary (see `write-python`), `pydantic-settings` for typed config from the environment and a local `.env`.
- **Web API** → `fastapi` (type-hint-driven, OpenAPI docs for free), served with `uvicorn` and pairing with `pydantic`.
- **XML and other markup** → `lxml`, by XPath or CSS selector, over a hand-rolled parser or regex.
Match XML elements on `local-name()` rather than a declared namespace, since two producers of one schema may declare it differently and a namespace-bound XPath then matches nothing.

## Standalone scripts

A single script that needs a package shouldn't require a whole project.
Declare deps inline (PEP 723) and run with `uv run script.py` — `uv` builds a throwaway env on the fly:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["httpx"]
# ///
```

## Pre-commit hooks

Enforce formatting and linting on every commit with the `pre-commit` framework — deterministic, so it holds regardless of how the code got written.
Add `.pre-commit-config.yaml`:

```yaml
default_install_hook_types: [pre-commit, commit-msg]
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types_or: [python, pyi]
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types_or: [python, pyi]
      - id: taplo-format
        name: taplo fmt
        entry: uv run taplo fmt
        language: system
        types: [toml]
      - id: taplo-lint
        name: taplo lint
        entry: uv run taplo lint
        language: system
        types: [toml]
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v4.5.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

- **`repo: local` hooks run the `ruff` and `taplo` that `uv.lock` pins**, so the hook, the editor and the suite agree on one version; the `ruff-pre-commit` mirror pins its own `rev`, which drifts from the lock until a commit passes the hook and fails `uv run ruff check`.
- **`conventional-pre-commit`** enforces `use-git`'s Conventional Commits header, the one hook that needs a `rev`; `default_install_hook_types` makes `pre-commit install` register the `commit-msg` stage too, which it otherwise skips.

Then `pre-commit install` once per clone, and `pre-commit autoupdate` to bump the `rev`.
If a hook changes files the commit stops so you can re-stage.

## Release

Cut a release with `uv version --bump patch` (or `minor`, `major`), which rewrites `pyproject.toml` and the lock in one step, then commit and tag as `use-git`'s Release says; `uv build` and `uv publish` take it from there.
No `bump2version` or `setuptools_scm`: the version is a line in `pyproject.toml`, and a tool deriving it from tags makes a checkout without tags build as `0.0.0`.
