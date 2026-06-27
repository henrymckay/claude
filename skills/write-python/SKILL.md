---
name: write-python
description: >-
  Conventions for writing and organizing Python so it matches a consistent,
  maintainable house style. Use whenever creating, editing, refactoring, or
  reviewing Python — single scripts, modules, packages, or whole projects —
  even if the user doesn't explicitly mention "conventions", "style", or
  "structure". Covers project layout, public APIs and typing, docstrings,
  imports and dependencies, error handling, and idioms. Targets Python 3.11+.
  Formatting/linting is delegated to ruff and type-checking to pyright — this
  skill does NOT restate their rules, only the judgment calls they can't make.
---

# Writing Python

These are the judgment calls that make Python readable and maintainable —
the decisions a formatter or linter can't make for you. Apply them when
writing or changing Python.

**Scope, so this skill earns its place:** `ruff` handles formatting, import
sorting, line length, and lint rules; `pyright` handles type checking. Don't
restate or fight those tools here. Defer to them, and spend your attention on
structure, API design, and idioms instead.

**Above all: match the surrounding code.** An existing project's established
patterns beat anything below. These conventions are for new code and for
projects with no strong existing style.

## Project & module layout

Use the **`src/` layout** for anything installable (a package others import or
you ship):

```
project/
  pyproject.toml
  src/
    mypackage/
      __init__.py
      ...
  tests/
  README.md
```

The `src/` layout exists to stop accidental imports of the in-tree package
before it's installed — it forces you to test against the *installed* package,
which catches packaging mistakes early. For a throwaway script or a tiny tool,
a flat single file is fine; don't ceremony it up.

Keep modules **small and cohesive** — one clear responsibility each. Split a
module when it grows past a few hundred lines or starts mixing concerns (e.g.
HTTP handling tangled with business logic). Group related modules into a
subpackage rather than letting a flat namespace sprawl. Tests live in `tests/`
mirroring the package layout, not next to the source.

## Public API & typing

Be deliberate about what's public. A leading underscore (`_helper`,
`_Internal`) signals "implementation detail, may change" — use it freely so the
real surface is obvious. In a package's `__init__.py`, define `__all__` to make
the public API explicit and to keep `import *` honest.

**Type hints on public functions and class attributes** are worth the keystrokes
— they're checked by pyright, they document intent, and they make refactors
safe. Internal one-liners don't always need them; use judgment. Prefer modern
syntax (3.11+):

- `list[int]`, `dict[str, int]`, `tuple[str, ...]` — not `typing.List` etc.
- `X | None` — not `Optional[X]`
- `from collections.abc import Iterable, Sequence, Mapping` for parameters —
  accept the most general type that works (take `Iterable`, return `list`)

Reach for `dataclasses` for plain data holders before hand-writing `__init__`.
Use `typing.Protocol` for structural "duck typing" interfaces rather than
forcing an ABC inheritance hierarchy.

## Docstrings (Google style)

Document modules, public functions, classes, and methods. Skip docstrings on
obvious internals — a docstring that just restates the function name is noise.
Use **Google style**:

```python
def fetch_user(user_id: int, *, include_archived: bool = False) -> User:
    """Fetch a user by ID.

    Args:
        user_id: Primary key of the user.
        include_archived: If True, also return soft-deleted users.

    Returns:
        The matching User.

    Raises:
        UserNotFoundError: If no user has that ID.
    """
```

Document the *why* and the non-obvious (units, side effects, what raises),
not the mechanically obvious. A one-line summary is enough for simple functions.

## Imports & dependencies

Use **absolute imports** within a package (`from mypackage.db import session`) —
they survive moving files and reading a line tells you exactly what's imported.
Relative imports (`from .db import session`) are acceptable for tight intra-
package references but get confusing across several levels.

**Reach for the standard library first.** `pathlib` over `os.path`,
`dataclasses`, `itertools`, `functools`, `collections`, `datetime` — a lot of
problems don't need a dependency. Add a third-party package when it genuinely
earns its weight, not reflexively.

Circular imports are a design smell — usually two modules that want to be one,
or a missing third module they should both depend on. Restructure rather than
papering over it with function-local imports.

**Dependencies & running:** prefer **`uv`** — `uv add` to manage deps,
`uv run script.py` to run. For a self-contained script that needs a package,
use an inline dependency block so it runs anywhere without a project:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
```

Don't bundle an interpreter or assume packages are globally installed — declare
what's needed and let `uv` resolve it.

## Error handling

Catch the **specific** exception you can actually handle, never a bare
`except:` (it swallows `KeyboardInterrupt` and real bugs). `except Exception`
is acceptable only at a genuine top-level boundary where you log and re-raise
or exit.

Raise **specific, meaningful** exceptions. For a library or non-trivial app,
define a small exception hierarchy rooted in one base so callers can catch
broadly or narrowly:

```python
class AppError(Exception):
    """Base class for this application's errors."""

class UserNotFoundError(AppError):
    """Raised when a user lookup fails."""
```

Let exceptions propagate to where they can be handled meaningfully — don't
catch-and-continue to hide failures. When re-raising with context, use
`raise NewError(...) from original` to preserve the chain. Reserve return-value
error signaling (e.g. returning `None`) for genuinely expected "not found"
cases, and make that obvious in the type (`User | None`) and docstring.

## Idioms & things to avoid

- **Mutable default arguments** are a classic trap: `def f(x=[])` shares one
  list across all calls. Use `def f(x: list | None = None)` and create inside.
- **Comprehensions** for simple transforms/filters; a plain loop once it needs
  multiple statements or gets hard to read. Don't nest them past two levels.
- **`pathlib.Path`** for filesystem work, not string paths.
- **Context managers** (`with`) for anything with cleanup — files, locks,
  connections. Write your own with `contextlib.contextmanager` when useful.
- **f-strings** for formatting. Use `logging` with `%`-style lazy args
  (`logger.info("got %s", x)`) so the string isn't built when not logged.
- **EAFP over LBYL** where it reads well — try the operation and handle the
  exception rather than pre-checking, which avoids races and is often clearer.
- Avoid `from module import *` in code (fine only in a curated `__init__.py`).
- Don't reach for a class when a function will do; don't add abstraction
  (factories, base classes, config layers) before there's a second case.

## Tooling baseline

Assume and defer to these — don't hand-format or re-implement their checks:

- **`ruff`** — formatting + linting + import sorting (replaces black/isort/flake8).
  Run `ruff format` and `ruff check --fix`.
- **`pyright`** — type checking (the `pyright-lsp` plugin surfaces this live).
- **`uv`** — environments, dependencies, and running.
- **`pytest`** — tests, in `tests/`.

If a project already configures these in `pyproject.toml`, follow its settings
over any default above.
