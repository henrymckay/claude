---
name: setup-python
description: >-
  How to scaffold and structure a new Python project or package — directory
  layout, pyproject.toml, dependency management, and toolchain. Use whenever
  starting a new Python project, package, script, or tool; adding packaging to
  existing code; setting up dependencies, virtual environments, or project
  config; or deciding where files should live — even if the user just says
  "new project", "set this up", or "make this a package". Standardizes on uv,
  ruff, pyright, and pytest, targeting the latest stable Python. For in-code style once files
  exist, see the write-python skill.
---

# Setting up a Python project

Getting the skeleton right up front — layout, packaging, tooling — saves pain later.
This covers *structure and setup*; for how to write the code inside, see `write-python`.

**Match an existing project first.** If there's already a `pyproject.toml` or an established layout, follow it rather than imposing this.

## Pick a layout

- **One-off script / tiny tool** → a single `.py` file.
  Don't ceremony it up.
  If it needs a dependency, use an inline script block (see bottom).
- **Anything installable or that others import** → the **`src/` layout** below.

The `src/` layout puts the package one directory down so it *can't* be imported accidentally from the repo root before it's installed.
That forces you to test against the actually-installed package and catches packaging mistakes early — the whole reason it's the default.

```text
myproject/
  pyproject.toml
  README.md
  .gitignore
  src/
    mypackage/
      __init__.py
      core.py
  tests/
    test_core.py
```

Keep modules small and cohesive (one responsibility).
Tests live in `tests/`, mirroring the package — not beside the source.

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
mycli = "mypackage.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mypackage"]

[tool.ruff]
line-length = 88
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "D", "UP", "B", "SIM", "C4"]

[tool.ruff.lint.pydocstyle]
convention = "pep257"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D"]

[tool.pyright]
typeCheckingMode = "standard"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

The non-obvious choices:

- `[project.scripts]` only when it's a CLI — it maps a command to an entry point.
- `[tool.hatch.build.targets.wheel]` spells out the package path so hatchling finds it under `src/`; without it the wheel build can't locate the package.
- `[tool.ruff.lint] select` opts into a broader baseline than ruff's `E`+`F` default: `I` (isort import sorting), `N` (pep8-naming), `D` (pydocstyle docstring presence), `UP` (pyupgrade modern syntax), `B` (bugbear likely-bug patterns), `SIM` (simplify) and `C4` (comprehensions).
- `pydocstyle` convention `pep257` checks that docstrings *exist* without imposing Google/NumPy section formatting, so the reST field-list style stays free (see `write-python`).
- `per-file-ignores` drops the `D` rules on `tests/*`, since test functions don't need docstrings.

## Dependencies & environment: use `uv`

`uv` manages the Python version, the virtualenv, and dependencies — fast, and it replaces pip / pip-tools / virtualenv / pyenv.
If it isn't installed, use the standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`), which drops a prebuilt binary in `~/.local/bin`; prefer it over `brew install uv`, which on some machines falls back to a slow from-source build (compiling the whole Rust/LLVM toolchain).
Core workflow:

```bash
uv init                 # scaffold a new project (or set up by hand as above)
uv add httpx            # add a runtime dependency (writes to pyproject + lock)
uv add --dev pytest ruff pyright   # dev-only tooling
uv run pytest           # run inside the managed env, no manual activate
uv sync                 # reproduce the env from uv.lock
```

Commit `uv.lock` for applications (reproducible installs); libraries usually don't pin as hard.
Pin the Python version with a `.python-version` file so everyone's on the same interpreter.

**Target the newest Python release that all your dependencies support** for a new project — set `.python-version`, `requires-python`, and ruff's `target-version` to it.
That's usually the latest stable release, but a dependency without wheels for the very newest version can force you one release back, so pick the highest version for which `uv sync` resolves and the tests pass (and never a pre-release).
Determine it when you create the project rather than hardcoding a number that ages — the `>=3.14` / `py314` above are just today's answer, not a fixed target.
A library published for others is the exception: keep a lower `requires-python` floor so you don't lock out consumers on older interpreters, even while you develop against the latest.

## Reach-for libraries

Prefer the standard library by default; only when a task genuinely needs a dependency, reach for the house pick below (see `write-python` on preferring the simplest solution).
Listed by task:

- **CLI** → `argparse` (stdlib) for a trivial one-or-two-flag script; `typer` once it grows, since it's type-hint-driven, generates `--help`, and pairs with `rich`. Reserve `fire` for a throwaway internal tool where reflecting an object straight into a CLI saves time.
- **DataFrames** → `polars` (see the `use-polars` skill).
- **HTTP** → `httpx` (sync and async) over `requests`.
- **Logging** → stdlib `logging`, optionally with `rich.logging.RichHandler` for pretty console output, or `loguru` for a more ergonomic API. `rich` itself formats output; it isn't a logging framework.
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
```

Pin `rev` to the current `ruff-pre-commit` release and bump it later with `pre-commit autoupdate`.
Then `uv add --dev pre-commit` and `pre-commit install` (once per clone, to register the git hook).
`ruff-check --fix` auto-fixes and `ruff-format` reformats; if a hook changes files the commit stops so you can re-stage.
This is also where a Conventional Commits `commit-msg` hook belongs (see `use-git`).

## Toolchain summary

Set these up once and defer to them everywhere:

- **`uv`** — Python version, env, dependencies, running.
- **`ruff`** — format + lint + import sort (`ruff format`, `ruff check --fix`).
- **`pyright`** — type checking (the `pyright-lsp` plugin surfaces it live).
- **`pytest`** — tests in `tests/`.

Add a `.gitignore` covering `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, build artifacts, and the editor/OS cruft a collaborator's setup drops in (`.idea/`, `.vscode/`, `.DS_Store`).
See the `use-git` skill for repo hygiene.
