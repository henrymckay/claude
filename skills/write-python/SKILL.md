---
name: write-python
description: >-
  In-code conventions for writing Python that a formatter can't decide —
  function/member ordering, public API design, typing, docstrings, import
  style, error handling, and idioms. Use whenever writing, editing,
  refactoring, or reviewing Python code, even if the user doesn't explicitly
  mention "conventions", "style", or "clean code". Targets Python 3.11+.
  Formatting/linting is delegated to ruff and type-checking to pyright — this
  skill does NOT restate their rules, only the judgment calls they can't make.
  These are the baseline conventions that apply to all Python; layer a paradigm
  skill on top as needed — be-functional for functional style, be-oop for
  object-oriented design. For project structure and packaging, see setup-python.
---

# Writing Python

The judgment calls that make Python readable and maintainable — the decisions a formatter or linter can't make for you.

**Scope, so this skill earns its place:** `ruff` handles formatting, import sorting, line length, and lint rules; `pyright` handles type checking.
Don't restate or fight those tools.
Spend attention on API design, typing intent, and idioms instead.
Project layout and dependencies live in `setup-python`.

In particular, **don't spend effort on what `ruff format` fixes automatically** on pre-commit — line length, wrapping and stacking function arguments, quote style, trailing commas.
Write it naturally and let the hook format it; hand-formatting just creates needless churn and diff noise.

**Above all: match the surrounding code.** An existing project's patterns beat anything below.
These conventions are for new code or projects with no strong existing style.

**Prefer the simplest solution.** Reach for built-in language and standard library features before writing custom code or pulling in a dependency — out-of-the-box beats bespoke, because there's less to maintain and fewer places for bugs to hide.
Add complexity (another abstraction, a dependency, a clever trick) only when a concrete need forces it.
This is **KISS** (keep it simple), **YAGNI** (you aren't gonna need it — don't build for imagined futures), and **DRY** (don't repeat yourself — factor out *real* duplication, but don't over-abstract chasing it).

## Ordering

Order things alphabetically so every name has *one predictable location* — you never scan a whole file to find something, and diffs stay stable as code grows.

- **Module-level definitions** (functions, classes, constants) alphabetically where possible.
  Carve-outs: dunders and a script's entry point (e.g. `main`) may sit conventionally, and grouped constants/`__all__` can stay at the top.
- **Class methods** alphabetically, with dunders (`__init__`, `__repr__`, …) first in conventional order.
- **Function arguments** alphabetically where possible, both when defining and when calling.
  "Where possible" is doing real work here: `self`/`cls` come first, positional-only and required-before-default constraints win, and don't reorder where argument order itself carries meaning.
  It applies most cleanly to keyword arguments at the call site.

Don't reorder purely to enforce this in a file that already uses another scheme — consistency within a file wins.

## Public API & typing

Be deliberate about what's public.
A leading underscore (`_helper`, `_Internal`) signals "implementation detail, may change" — use it freely so the real surface is obvious.
In a package's `__init__.py`, define `__all__` to make the public API explicit and keep `import *` honest.

**Annotate every function** — every argument and the return value, on public and internal functions alike.
Full signatures let pyright check call sites, document intent, and make refactors safe. **Don't annotate local variables** inside function bodies — let inference do its job and keep bodies uncluttered (add a hint only in the rare case inference genuinely can't resolve a type).

Typing conventions (Python 3.11+):

- **Native types, not `typing` equivalents:** `list[int]`, `dict[str, int]`, `tuple[str, ...]` — never `typing.List`, `typing.Dict`, etc.
- **Union with `|`:** `str | None`, not `typing.Optional[str]` or a `Union[...]`.
- **`import collections.abc` and qualify** (`collections.abc.Iterable`, `.Sequence`, `.Mapping`) for parameters — accept the most general type that works (take an `Iterable`, return a `list`).
- **`typing.Any`** for a genuinely unspecified type, and **`typing.Callable`** for callable types (qualified, per the import rule above).

Reach for `dataclasses.dataclass` for plain data holders before hand-writing `__init__`.
Use `typing.Protocol` for structural "duck typing" interfaces rather than forcing an ABC inheritance hierarchy.

## Docstrings (reStructuredText / Sphinx style)

**Every function gets a docstring** — public or internal — as do every module, class, and method.
Use reST (Sphinx field-list) style:

```python
def fetch_user(user_id: int, *, include_archived: bool = False) -> User:
    """Fetch a user by ID.

    :param user_id: Primary key of the user.
    :param include_archived: If True, also return soft-deleted users.
    :returns: The matching user.
    :raises UserNotFoundError: If no user has that ID.
    """
```

Types stay out of the docstring — the annotations already carry them, so don't add `:type:`/`:rtype:` fields.

Document the *why* and the non-obvious (units, side effects, what raises), not the mechanically obvious.
A trivial function still gets a docstring, but keep it a single line that says something its signature doesn't — a bare restatement of the name is wasted space, so make it earn its line.

Presence and basic hygiene are enforced by ruff's pydocstyle (`D`) rules on pre-commit.
Note ruff has no reST convention, so it's configured with `pep257` — it checks that docstrings *exist* but doesn't impose section formatting, leaving the field-list style to you.
See `setup-python`.

## Imports

**Import modules, not names, and qualify at every use site.** Import the module or package and reach members through it — `import polars` then `polars.DataFrame`, never `from polars import DataFrame`.
Qualified names make it obvious where every name comes from and eliminate collisions, which is worth the extra characters.

This is strict and applies to the standard library too:

```python
import pathlib          # pathlib.Path(...)
import dataclasses      # @dataclasses.dataclass
import collections.abc  # def f(xs: collections.abc.Iterable[int]): ...
```

For a deep internal path, bind the nearest useful module — `from mypackage import db` then `db.session` (still qualified) — rather than importing `session` bare.

Use **absolute imports** within a package; they survive moving files.
Relative imports (`from . import db`) are fine for tight intra-package references but get confusing across several levels.

**Avoid `as` renames** unless genuinely unavoidable (a real name clash) — that includes the popular ones: prefer `import polars` / `polars.col(...)` over the conventional `import polars as pl`.
When a rename truly is forced, derive it from the *true* name with an underscore prefix or suffix (`import numpy as numpy_`), never an arbitrary short alias like `np`.

**Name a local directory that extends a third-party package with a trailing underscore** — e.g. `polars_/` for your own Polars helpers — so it never shadows or gets confused with the real `polars`.

Circular imports are a design smell — usually two modules that want to be one, or a missing third module they should both depend on.
Restructure rather than papering over it with function-local imports.
(Dependency management lives in `setup-python`.)

## Error handling

Catch the **specific** exception you can actually handle, never a bare `except:` (it swallows `KeyboardInterrupt` and real bugs).
`except Exception` is acceptable only at a genuine top-level boundary where you log and re-raise/exit.

Raise **specific, meaningful** exceptions.
For a library or non-trivial app, define a small hierarchy rooted in one base so callers can catch broadly or narrowly:

```python
class AppError(Exception):
    """Base class for this application's errors."""

class UserNotFoundError(AppError):
    """Raised when a user lookup fails."""
```

Let exceptions propagate to where they can be handled meaningfully — don't catch-and-continue to hide failures.
When re-raising with context, use `raise NewError(...) from original` to preserve the chain.
Reserve returning `None` for genuinely expected "not found" cases, and make it obvious in the type (`User | None`) and docstring.

## Idioms & things to avoid

- **Mutable default arguments** are a classic trap: `def f(x=[])` shares one list across all calls.
  Use `def f(x: list | None = None)` and create inside.
- **Comprehensions** for simple transforms/filters; a plain loop once it needs multiple statements or gets hard to read.
  Don't nest past two levels.
- **`pathlib.Path`** for filesystem work, not string paths.
- **Context managers** (`with`) for anything with cleanup — files, locks, connections.
  Write your own with `contextlib.contextmanager` when useful.
- **f-strings** for formatting.
  Use `logging` with `%`-style lazy args (`logger.info("got %s", x)`) so the string isn't built when not logged.
- **EAFP over LBYL** where it reads well — try the operation and handle the exception rather than pre-checking; avoids races and is often clearer.
- Avoid `from module import *` in code (fine only in a curated `__init__.py`).
- Don't reach for a class when a function will do; don't add abstraction (factories, base classes, config layers) before there's a second case.
- **Prefer a function returning a value over a hardcoded module global.** A function can later compute, parameterize, or override the value without callers changing; a bare global has to be torn out to extend.
  (Genuinely fixed constants can stay globals.)
- **Don't introduce a single-use local variable — inline the expression.** A name for a value used exactly once adds reading overhead without payoff.
  Keep the name only when it meaningfully documents an otherwise opaque expression.
- **Pass-through variadics use `*a` / `**k`**, not `*args` / `**kwargs`.
  When a function only forwards its variadic arguments onward, the short names keep the noise down; reserve descriptive names for when the function actually inspects them.
