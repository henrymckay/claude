---
name: write-python
description: >-
  In-code conventions for writing Python that a formatter can't decide —
  function/member ordering, naming, public API design, typing, docstrings,
  import style, error handling, and idioms. Use whenever writing, editing,
  refactoring, or reviewing Python code, even if the user doesn't explicitly
  mention "conventions", "style", or "clean code". Targets Python 3.11+.
  Formatting/linting is delegated to ruff and type-checking to pyright — this
  skill does NOT restate their rules, only the judgment calls they can't make.
  These are the baseline conventions that apply to all Python; layer a paradigm
  skill on top as needed — be-functional for functional style, be-oop for
  object-oriented design, write-tests for test suites. For project structure, see
  structure-python; for packaging and tooling, setup-python.
---

# Write Python

The judgment calls that make Python readable and maintainable — the decisions a formatter or linter can't make for you.
It focuses on API design, typing intent, and idioms — the baseline that `be-functional`, `be-oop` and `write-tests` layer on; project structure lives in `structure-python`, packaging and dependencies in `setup-python`.

**In an existing project, ask first.** Where a codebase already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Formatting & linting

`ruff` handles formatting, import sorting, line length, and lint rules; `pyright` handles type checking.
Don't restate or fight those tools.
**Don't spend effort on what `ruff format` fixes automatically** on pre-commit — line length, wrapping and stacking function arguments, quote style, trailing commas.
Write it naturally and let the hook format it; hand-formatting just creates needless churn and diff noise.

## Public API

Be deliberate about what's public.
A leading underscore (`_helper`, `_Internal`) signals "implementation detail, may change" — use it freely so the real surface is obvious.
In a package's `__init__.py`, define `__all__` to make the public API explicit and keep `import *` honest.

## Typing

**Annotate every function** — every argument and the return value, on public and internal functions alike.
Full signatures let `pyright` check call sites, document intent, and make refactors safe.
**Don't annotate local variables** inside function bodies — let inference do its job and keep bodies uncluttered (add a hint only in the rare case inference genuinely can't resolve a type).

Typing conventions (Python 3.11+):

- **Native types, not `typing` equivalents:** `list[int]`, `dict[str, int]`, `tuple[str, ...]` — never `typing.List`, `typing.Dict`, etc.
- **Union with `|`:** `str | None`, not `typing.Optional[str]` or a `Union[...]`.
- **`import collections.abc` and qualify** (`collections.abc.Iterable`, `.Sequence`, `.Mapping`) for parameters — accept the most general type that works (take an `Iterable`, return a `list`).
- **`typing.Any`** for a genuinely unspecified type, and **`typing.Callable`** for callable types (qualified, per the import rule above).

Reach for `dataclasses.dataclass` for plain data holders before hand-writing `__init__`.
Use `typing.Protocol` for structural "duck typing" interfaces rather than forcing an ABC (Abstract Base Class) inheritance hierarchy.

## Docstrings

**Every function gets a docstring** — public or internal — as do every module, class, and method.
Use reStructuredText (reST) in the Sphinx field-list style:

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
Phrase the summary line in the **imperative mood** ("Return the top products", not "Returns the top products" or the noun phrase "The top products") — `ruff`'s `D401` flags anything else.

Presence and basic hygiene are enforced by `ruff`'s pydocstyle (`D`) rules on pre-commit.
Note `ruff` has no reST convention, so it's configured with `pep257` — it checks that docstrings *exist* but doesn't impose section formatting, leaving the field-list style to you.
See `setup-python`.

## Comments

Prefer self-documenting code to `#` comments.
A descriptive name, a named constant, or a small well-named helper carries the same meaning as a comment and can't drift out of sync with the code the way a comment does — so lift the intent into a name (`invalid_rows = 3`, not a bare `3` with a comment).
When a genuine *why* still needs stating — a non-obvious workaround or a subtle invariant — put it in the docstring, not a trailing comment.
Reserve `#` for what has nowhere else to live: tooling directives (`# noqa`, `# type: ignore`) and the PEP 723 inline-script header.
Keep config files (`pyproject.toml`, pre-commit, CI) comment-free the same way, explaining any non-obvious setting in prose in the docs rather than inline.

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

**Name a package for what it does or holds.** A package that *performs* an action — a behavioural or pipeline layer — takes an imperative verb (`transform/`, `operate/`, `adapt/`, `drive/`); a package that only *defines* or *holds* things takes a noun (`port/`, `domain/`, and the `cli`/`api`/`gui` role packages).
Functions, methods, and CLI commands are imperative verbs regardless.
`structure-python`'s package layers are the worked example.

**Name a local package of code tightly coupled to a third-party library with a trailing underscore** — `polars_/` for your `polars` helpers, `typer_/` for a CLI's `typer` code, `rich_/` for its rendering, `pytest_/` for test fixtures and bare-`assert` helpers — so the name both marks the coupling and never shadows the real `polars`/`typer`/`pytest`.
Pair it with a role-named package (`cli`, `api`, `gui`) that re-exports the app; see `write-entry-points` for the split.

Circular imports are a design smell — usually two modules that want to be one, or a missing third module they should both depend on.
Restructure rather than papering over it with function-local imports.
(Dependency management lives in `setup-python`.)

## Ordering

Order things alphabetically so every name has *one predictable location* — you never scan a whole file to find something, and diffs stay stable as code grows.

- **Module-level definitions** (functions, classes, constants) alphabetically where possible.
Carve-outs: dunders and a script's entry point (e.g. `main`) may sit conventionally, and grouped constants/`__all__` can stay at the top.
- **Class methods** alphabetically, with dunders (`__init__`, `__repr__`, …) first in conventional order.
- **Function arguments** alphabetically where possible, both when defining and when calling.
"Where possible" is doing real work here: `self`/`cls` come first, positional-only and required-before-default constraints win, and don't reorder where argument order itself carries meaning.
It applies most cleanly to keyword arguments at the call site.

Place a new definition in its alphabetical slot, but don't reshuffle an existing file just to enforce this — the diff noise and broken `git blame` outweigh the tidiness.

## Simplicity

**Prefer the simplest solution.** Reach for built-in language and standard library features before writing custom code or pulling in a dependency — out-of-the-box beats bespoke, because there's less to maintain and fewer places for bugs to hide.
Add complexity (another abstraction, a dependency, a clever trick) only when a concrete need forces it — and when a dependency is warranted, `setup-python` lists the house pick for common tasks.
**Once a dependency is in play, use *its* built-in features rather than hand-rolling around them.** Before writing validation, grouping, parsing, retries, or serialisation yourself, check the library's own API — a CLI framework's callbacks and validation, a dataframe library's operations, an HTTP client's retry/auth.
Reinventing what a dependency already offers is more code to maintain and usually a worse version.
(Do confirm the feature exists, though — not every library has every convenience; a genuine gap is fine to fill.)
This is **KISS** (keep it simple), **YAGNI** (you aren't gonna need it — don't build for imagined futures), and **DRY** (don't repeat yourself — factor out *real* duplication, but don't over-abstract chasing it).

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

## Idioms

- **Comprehensions** for simple transforms/filters; a plain loop once it needs multiple statements or gets hard to read.
Don't nest past two levels.
- **`pathlib.Path`** for filesystem work, not string paths.
- **Prefer a named method to an overloaded operator when both exist — especially when chaining off the result.** `path.joinpath("a/b").read_text()` reads left-to-right, where the operator form needs parens (`(path / "a/b").read_text()`) because attribute access binds tighter than `/`.
A named method also reads in evaluation order and says what a symbol only implies — `polars`'s `col.mul(2)`/`col.gt(0)` over `*`/`>` (see `use-polars`).
Keep operators where they're the plain idiom: arithmetic on numbers, and short expressions you don't chain off.
- **Context managers** (`with`) for anything with cleanup — files, locks, connections.
Write your own with `contextlib.contextmanager` when useful.
- **f-strings** for formatting.
Use `logging` with `%`-style lazy args (`logger.info("got %s", x)`) so the string isn't built when not logged.
- **EAFP over LBYL** (Easier to Ask Forgiveness than Permission, over Look Before You Leap) where it reads well — try the operation and handle the exception rather than pre-checking; avoids races and is often clearer.
- **Prefer a function returning a value over a hardcoded module global.** A function can later compute, parameterise, or override the value without callers changing; a bare global has to be torn out to extend.
(Genuinely fixed constants can stay globals.)
- **Pass-through variadics use `*a` / `**k`**, not `*args` / `**kwargs`.
When a function only forwards its variadic arguments onward, the short names keep the noise down; reserve descriptive names for when the function actually inspects them.
- **For tabular or columnar data, work in a dataframe library's expressions — not Python lists and loops.** When data is rows-and-columns, or another library hands you a dataframe, keep it in the frame (convert a `pandas` result with `polars.from_pandas`) and compute across all rows at once; pulling columns out to lists and looping or folding over them throws away the vectorised engine.
Stack every group into one long-form frame rather than processing a group at a time.
See the `use-polars` skill.

## Avoid

- **Mutable default arguments** are a classic trap: `def f(x=[])` shares one list across all calls.
Use `def f(x: list | None = None)` and create inside.
- `from module import *` in code (fine only in a curated `__init__.py`).
- Reaching for a class when a function will do, or adding abstraction (factories, base classes, config layers) before there's a second case.
- **A single-use local variable** — inline the expression instead.
A name for a value used exactly once adds reading overhead without payoff.
Keep the name only when it meaningfully documents an otherwise opaque expression.
- **Hand-placed blank lines inside a function body** to group statements — keep the body contiguous and leave vertical spacing to the formatter.
The urge to separate chunks with whitespace usually means the function is doing too much, so extract a helper instead.
(Blank lines *between* definitions are the formatter's job.)
- **Repeating a namespace in the name it qualifies.** A module or class already supplies the context, so drop the redundant prefix — `then.equals`, not `then.then_equals`; `user.name`, not `user.user_name`.
It's the payoff of importing and qualifying: the qualifier carries the meaning, so the member name stays short.
