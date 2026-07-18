---
name: setup-python
description: >-
  How to scaffold and structure a new Python project or package — directory
  layout, pyproject.toml, dependency management, and toolchain. Use whenever
  starting a new Python project, package, script, or tool; adding packaging to
  existing code; setting up dependencies, virtual environments, or project
  config; or deciding where files should live — even if the user just says
  "new project", "set this up", or "make this a package". Standardizes on uv,
  ruff, pyright, and pytest for Python 3.11+. For in-code style once files
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

```
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
requires-python = ">=3.11"
dependencies = []

[project.scripts]
mycli = "mypackage.cli:main"   # only if it's a CLI

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
# ruff owns formatting + linting; keep line length etc. here, not in your head
line-length = 88
target-version = "py311"

[tool.ruff.lint]
# ruff's defaults are just E+F; opt into a broader baseline
select = [
    "E", "F",   # pycodestyle + pyflakes (defaults)
    "I",        # isort — import sorting
    "N",        # pep8-naming — naming conventions
    "D",        # pydocstyle — docstring presence + style
    "UP",       # pyupgrade — modernize syntax (matches 3.11+ typing rules)
    "B",        # flake8-bugbear — likely-bug patterns
    "SIM",      # flake8-simplify
    "C4",       # flake8-comprehensions
]

[tool.ruff.lint.pydocstyle]
# ruff has no reST convention; pep257 enforces docstring presence + hygiene
# without imposing Google/NumPy section formatting, so reST field lists are fine
convention = "pep257"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D"]       # don't require docstrings on test functions

[tool.pyright]
typeCheckingMode = "standard"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Dependencies & environment: use `uv`

`uv` manages the Python version, the virtualenv, and dependencies — fast, and it replaces pip / pip-tools / virtualenv / pyenv.
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

## Standalone scripts

A single script that needs a package shouldn't require a whole project.
Declare deps inline (PEP 723) and run with `uv run script.py` — uv builds a throwaway env on the fly:

```python
# /// script
# requires-python = ">=3.11"
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
    rev: v0.x.x          # pin current; run `pre-commit autoupdate` to bump
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
```

Then `uv add --dev pre-commit` and `pre-commit install` (once per clone, to register the git hook).
`ruff-check --fix` auto-fixes and `ruff-format` reformats; if a hook changes files the commit stops so you can re-stage.
This is also where a Conventional Commits `commit-msg` hook belongs (see `use-git`).

## Toolchain summary

Set these up once and defer to them everywhere:

- **`uv`** — Python version, env, dependencies, running.
- **`ruff`** — format + lint + import sort (`ruff format`, `ruff check --fix`).
- **`pyright`** — type checking (the `pyright-lsp` plugin surfaces it live).
- **`pytest`** — tests in `tests/`.

Add a `.gitignore` covering `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`, and build artifacts.
See the `use-git` skill for repo hygiene.
