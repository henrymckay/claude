---
name: setup-python
description: >-
  How to scaffold and configure a Python project — the src/ layout,
  pyproject.toml with the uv_build backend, dependency and environment
  management with uv, a committed lock file upgraded on a schedule, the floor
  of Python 3.15, the house-pick libraries for common tasks (typer, httpx with
  tenacity and pyrate-limiter, polars, a web front end or dash for a
  dashboard, pydantic-settings, rich logging), standalone scripts, pre-commit hooks run through uv, releases
  with uv version, and the ruff/taplo/pyright-strict/pytest toolchain with the
  strict pytest flags and an untyped dependency kept out of strict's way, plus
  sqlfluff's hook once the project holds SQL. Use
  whenever scaffolding a new Python project, package, script, or tool; adding
  packaging to existing code; setting up dependencies, virtual environments,
  project config or hooks; cutting a release; or choosing a house-pick library
  for a task — even if the user just says "set this up", "add a dependency",
  or "make this a package". Standardises on uv, ruff, taplo, pyright and
  pytest, with no task runner, Docker only for a container platform, and no
  CI until a project earns it; a PLAN.md decision overrides any pick. Plan a
  new project first with plan-project. For how to organise the application's
  code into layers, see structure-python; for in-code style, write-python; for
  the tests themselves, write-tests.
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

`sqlfluff` joins them for SQL once a project holds a `.sql` file (Pre-commit hooks).
A web front end brings its own under `web/`: `npm` from the development dependency `nodejs-wheel`, run as `uv run npm --prefix web …` so no system Node is needed, TypeScript's checker in its build, `oxlint` as its linter and `vitest` for its tests (`write-entry-points`).
Nothing else by default: no task runner (`just`, `make`) until a project has a command `uv run` can't express; Docker only for an API or job deployed to a container platform such as Cloud Run (`deploy-project`), from the `ghcr.io/astral-sh/uv` image, since a machine you own and an Actions runner both install from `uv.lock`; documentation is the README plus `--help`; CI is declined until a project has a second contributor or a deploy (the plan records the exception).

## Configure the project

`pyproject.toml` is the one file for metadata, dependencies and tool config:

```toml
[project]
name = "mypackage"
version = "0.1.0"
description = "..."
requires-python = ">=3.15"
dependencies = []

[project.scripts]
mypackage-cli = "mypackage.code.drive.cli:app"

[build-system]
requires = ["uv_build>=0.13,<0.14"]
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
reportMissingTypeStubs = false
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
- `[tool.ruff.lint] select` replaces `ruff`'s default set — `E`+`F` until 0.16, since then about 400 rules that add `PIE`, `PYI`, `PL`, `DTZ`, `ASYNC` and more — with this list: `I` (import sorting), `N` (naming), `D` (docstring presence), `UP` (modern syntax), `B` (likely bugs), `SIM` (simplify), `C4` (comprehensions), `RUF` (`ruff`'s own, including unused `noqa`), `PT` (`pytest` style) and `TC` (imports only a type checker needs).
- `"tests/**" = ["D"]` drops docstrings from tests and fixtures, since the test name is the claim (see `write-tests`).
- `pydocstyle` convention `pep257` checks that docstrings *exist* without imposing Google/NumPy section formatting, so the reStructuredText field-list style stays free (see `write-python`).
- `pyright` `strict` on a greenfield project: `standard` (the default) lets an unannotated parameter through as `Unknown`, so a wrong argument is found at runtime; `strict` reports it at the definition.
An existing codebase adopts `strict` file by file with `# pyright: strict`.
- `reportMissingTypeStubs = false` is the one strict check turned off project-wide: strict fails the import of any dependency that ships no types (`plotly`), and a typed one (`shiny`) is checked as before (pyright 1.1.414).
`pyright` then infers the untyped library from its source, so its methods still report `reportUnknownMemberType`; confine its calls to the one module coupled to it and open that module with `# pyright: reportUnknownMemberType=false`, keeping every other file fully strict.
That source accepts nearly any argument, so a wrong-typed call there is caught by the test that builds the figure (`write-tests`), not by the checker.
- `--strict-markers` and `--strict-config` turn a misspelt marker or option into an error instead of a silently unselected test; `xfail_strict` fails a test that passes while marked `xfail`; `filterwarnings = ["error"]` turns a dependency's deprecation into a failing test the day it appears, with a `markers` entry per marker the suite uses.
- The `-p pytest_.given`, `pythonpath` and `testpaths` lines serve `structure-python`'s full `tests/` layout.
A small tool that keeps `tests/` flat drops them and sets `testpaths = ["tests"]`.

**TOML formatting.** Run `taplo fmt` — it keeps arrays on one line until they overflow the line width, and collapses what `uv add` leaves expanded.
Scaffold a `.taplo.toml` holding `exclude = [".venv/**"]` beside it: `taplo` does not read `.gitignore`, so a bare run otherwise walks the virtual environment, fails `fmt --check` on TOML its packages ship and rewrites it on `fmt` (taplo 0.9.3); the pre-commit hook passes staged paths and hides this.

## Pick a layout

- **One-off script / tiny tool** → a single `.py` file, with an inline script block if it needs a dependency (see [Standalone scripts](#standalone-scripts)).
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

## Dependencies and environment

`uv` manages the Python version, the virtualenv and dependencies, in place of `pip`, `pip-tools`, `pipenv`, `virtualenv` and `pyenv`; if it isn't installed, use the standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
uv init --package
uv python pin 3.15
uv add httpx
uv add --dev pytest ruff pyright taplo pre-commit
uv run pytest
uv sync
```

- **Commit `uv.lock`, for a library as much as an application.** It pins what the suite was green against; without it a contributor's `uv sync` resolves differently from yours and the first bug report is a version skew nobody can reproduce.
The published library still carries only `pyproject.toml`'s ranges, so consumers are not pinned.
- **Declare a lower bound and no upper cap** (`polars>=2.1`), since a cap blocks the upgrade that fixes the bug you hit; run `uv lock --upgrade` and the suite together on a schedule — by hand, or from a workflow that opens a pull request, which is not the CI declined above since it gates nothing — and the lock moves only when the tests still pass.

**Target the latest stable Python release**, 3.15 at the time of writing, in `.python-version` (`uv python pin`) and `requires-python`; `write-python` writes to that floor, and `uv init` writes a release or two lower, so set both.
Go one release back only when a dependency has no wheels for it and `uv sync` fails to resolve, and record that under the plan's Decisions so the next sweep tries again; never a pre-release.
When `uv python list` offers only a pre-release of it, check `uv` before stepping back: a `uv` lists no Python released after itself, so `uvx uv@latest python list 3.15` shows whether the final exists and `uv self update` brings it.
A library published for others is the exception: keep a lower `requires-python` floor so you don't lock out consumers on older interpreters, even while you develop against the latest.

## Libraries

For these common tasks the house pick is the default, over the standard-library alternative (`typer` over `argparse`, `pytest` over `unittest`); everywhere else `write-python`'s Simplicity holds.
No optional-extras split (`mypackage[dashboard]`): one install carries every driver, since a split means a second resolution to test and a user who installed the wrong one.

- **CLI** → `typer` (type-hint-driven, generates `--help`, pairs with `rich`) over stdlib `argparse`; `cyclopts` is the alternative when `typer`'s decorator model fights a surface built from plain functions, and `argparse` only for a zero-dependency one-or-two-flag script.
- **Dashboard / web UI** → a built web front end (Vite, React, TypeScript, Tailwind with shadcn/ui) served by the `fastapi` API, with Node as the development dependency `nodejs-wheel`; `dash` with `dash-mantine-components` and `dash-ag-grid` where the code must stay Python, and `shiny` for an existing Shiny app; never `streamlit`, which reruns the whole script on every interaction (`write-entry-points`, Dashboard, has the cases and the trial behind them).
- **HTML tables** → `pandas.read_html`, converted at once with `polars.from_pandas`; it reads every table on a page in one call, and `extract_links="body"` keeps each cell's link as a `(text, href)` pair.
- **HTTP** → sync `httpx.Client` over `requests`, with `tenacity` for retries and `pyrate-limiter` for a stated rate; `structure-python`'s `references/http.md` has the mechanics.
A hand-rolled `time.sleep` loop gets jitter, give-up and the final re-raise wrong, and paces only the calls you remembered.
- **Logging** → stdlib `logging` with `rich.logging.RichHandler` on standard error for a person; never `loguru`, which replaces the logger every dependency already writes to.
`write-entry-points` has the configuration.
- **Numerics** → `numpy` and `scipy` for numerical work, `sympy` for symbolic maths.
- **Plotting** → in a web front end, ECharts, and Lightweight Charts for candles; in Python, `plotly` (in `dash` natively, in `shiny` through `shinywidgets`), and `matplotlib` only for a static image a report or a message embeds.
- **Scheduled / background jobs** → no library by default (an external cron, systemd timer, or cloud scheduler runs a console script; see `run-unattended`); `apscheduler` for in-process scheduling, `dramatiq` for a task queue (over `celery`), `prefect` or `dagster` for orchestration.
- **Spreadsheets** → `polars.read_excel`, with `fastexcel` (the `calamine` backend) as the reader engine.
`polars` names the function but ships no engine, so a project that declares none fails at the first call rather than at install.
- **Storage** → hive-partitioned Parquet for pipeline output, DuckDB to query it, SQLite for small single-writer state, and `platformdirs` for the data directory's default; `store-data` has the picks and their cases.
- **Tabular / columnar data** → `polars` (see `use-polars`), converting another library's `pandas` frame with `polars.from_pandas` plus `pyarrow`.
- **Terminal output for a person** → `rich` for tables, progress bars, colour, and readable tracebacks; a command's data output stays plain bytes on standard output (see `write-entry-points`).
- **Testing** → `pytest`, with `hypothesis` for property-based tests, `time-machine` for the clock, the `anyio` plugin for async code (not `pytest-asyncio`) and `coverage` for coverage: `uv run coverage run -m pytest`, then `uv run coverage report --show-missing`, with `branch = true` and `source = ["mypackage"]` under `[tool.coverage.run]`.
Not `pytest-cov`: a `-p` plugin in `addopts` that imports the package does so before `--cov` starts measuring, so every import line and each module of nothing but declarations reads as missed and the total comes out far too low, with a `module-not-measured` warning the only sign (pytest-cov 7.1).
- **Validation and settings** → `pydantic` v2 at a trust boundary (see `write-python`), `pydantic-settings` for typed config from the environment and a local `.env`, and `pyyaml` for the per-source constants in package data (see `structure-python`).
- **Web API** → `fastapi` (type-hint-driven, OpenAPI docs for free), served with `uvicorn` and pairing with `pydantic`.
- **XML and other markup** → `lxml`, by XPath or CSS selector, over a hand-rolled parser or regex.
Match XML elements on `local-name()` rather than a declared namespace, since two producers of one schema may declare it differently and a namespace-bound XPath then matches nothing.

## Standalone scripts

A single script that needs a package shouldn't require a whole project.
Declare deps inline (PEP 723) and run with `uv run script.py` — `uv` builds a throwaway env on the fly:

```python
# /// script
# requires-python = ">=3.15"
# dependencies = ["httpx"]
# ///
```

## Pre-commit hooks

Enforce formatting and linting on every commit with the `pre-commit` framework, in `.pre-commit-config.yaml`:

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
- **`conventional-pre-commit`** enforces `use-git`'s Conventional Commits header, pinned by `rev` like any hook from its own repository, such as `secure-project`'s `gitleaks`; `default_install_hook_types` makes `pre-commit install` register the `commit-msg` stage too, which it otherwise skips.
- **Add two `sqlfluff` hooks under `repo: local` in the commit that adds the project's first `.sql` file**, after `uv add --dev sqlfluff` and with the configuration `write-sql`'s Style gives in `pyproject.toml`; before then they would run on nothing:

```yaml
      - id: sqlfluff-format
        name: sqlfluff format
        entry: uv run sqlfluff format
        language: system
        types: [sql]
      - id: sqlfluff-lint
        name: sqlfluff lint
        entry: uv run sqlfluff lint
        language: system
        types: [sql]
```

Then `pre-commit install` once per clone, and `pre-commit autoupdate` to bump the `rev`.

## Release

Cut a release with `uv version --bump patch` (or `minor`, `major`), which rewrites `pyproject.toml` and the lock in one step, then commit and tag as `use-git`'s Release says; `uv build` and `uv publish` take it from there.
No `bump2version` or `setuptools_scm`: the version is a line in `pyproject.toml`, and a tool deriving it from tags makes a checkout without tags build as `0.0.0`.
