---
name: write-python
description: >-
  In-code conventions for writing Python that a formatter can't decide — typing,
  docstrings, comments, import style, public API design, naming, call-site
  argument style, member ordering, error handling, and idioms. Use whenever
  writing, editing, refactoring, or reviewing Python code, even if the user
  doesn't explicitly mention "conventions", "style", or "clean code". Targets
  Python 3.12+.
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
Three habits account for most of what goes wrong: importing names instead of modules, leaving a function unannotated or undocumented, and reaching for a class or an abstraction before a second case calls for one.

**In an existing project, ask first.** Where a codebase already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Formatting and linting

`ruff` handles formatting, import sorting, line length, and lint rules; `pyright` handles type checking.
Don't restate or fight those tools.
**Don't spend effort on what `ruff format` fixes automatically** on pre-commit — line length, wrapping and stacking function arguments, quote style, trailing commas.
Write it naturally and let the hook format it; hand-formatting just creates needless churn and diff noise.

## Typing

**Annotate every function** — every argument and the return value, on public and internal functions alike.
Full signatures let `pyright` check call sites, document intent, and make refactors safe.
**Don't annotate local variables** inside function bodies — let inference do its job and keep bodies uncluttered (add a hint only in the rare case inference genuinely can't resolve a type).

Typing conventions (Python 3.12+):

- **Native types, not `typing` equivalents:** `list[int]`, `dict[str, int]`, `tuple[str, ...]` — never `typing.List`, `typing.Dict`, etc.
- **Union with `|`:** `str | None`, not `typing.Optional[str]` or a `Union[...]`.
- **`import collections.abc` and qualify** (`collections.abc.Iterable`, `.Sequence`, `.Mapping`) for parameters — accept the most general type that works (take an `Iterable`, return a `list`).
- **`typing.Any`** for a genuinely unspecified type, and **`typing.Callable`** for callable types (qualified, per the import rule above).

Reach for `dataclasses.dataclass` before hand-writing `__init__` — but first check the data holder is warranted, since a record built at one call site and unpacked at the next is just that function's arguments (see `be-functional`).
Use `typing.Protocol` for structural "duck typing" interfaces rather than forcing an ABC (Abstract Base Class) inheritance hierarchy.

## Docstrings

**Every function gets a docstring** — public or internal — as do every module, class, and method.
Use reStructuredText (reST) in the Sphinx field-list style:

```python
def holdings(name: str, *, get: Get = get) -> polars.DataFrame:
    """Return the symbol published against each of a fund's holdings.

    :param name: The fund's ticker, as ``names`` spells it.
    :param get: How to retrieve a published document.
    :returns: A one-column ``symbol`` frame, a row per published holding.
    :raises HoldingsError: If the fund publishes nothing this can be read from.
    """
```

Types stay out of the docstring — the annotations already carry them, so don't add `:type:`/`:rtype:` fields.

**A docstring is a summary line and its fields, and that is the whole of it.**
A sentence of prose between them is the exception rather than the default, earned by a fact neither the signature nor the body can state — a unit, a side effect, an invariant the caller has to respect.
One such sentence needs a reason, a second needs a better one, and by the third it has stopped documenting the function and started arguing for it.

**A module docstring is one line.** It says what the module is for, and a reader who opens the file is already looking at the answer to anything longer.

Document the *why* and the non-obvious, never the mechanically obvious.
A trivial function still gets a docstring, but a bare restatement of the name is wasted space, so make the line say something the signature doesn't.

Length comes from putting the *design* in them — why this approach beat another, what the data looked like, which cases were weighed.
That reasoning is worth keeping, but neither docstring is where it goes: why the code changed belongs in the commit message and behaviour a user meets belongs in the README, both of which are where someone would go looking and neither of which is in the way of a caller who just wants to know what comes back.
Pushing it up into the module docstring only moves the wall of text from one place a reader scrolls past to another.

**Phrase the summary line in the imperative mood.** "Return the top products", not "Returns the top products" or the noun phrase "The top products".
`ruff`'s `D401` flags anything else, and a noun-phrase summary is the instinct precisely where it is wrong — a factory or a getter still describes what it *does*.

Presence and basic hygiene are enforced by `ruff`'s pydocstyle (`D`) rules on pre-commit.
Note `ruff` has no reST convention, so it's configured with `pep257` — it checks that docstrings *exist* but doesn't impose section formatting, leaving the field-list style to you.
See `setup-python`.

## Comments

Write self-documenting code instead of `#` comments.
A descriptive name, a named constant, or a small well-named helper carries the same meaning as a comment and can't drift out of sync with the code the way a comment does — so lift the intent into a name (`invalid_rows = 3`, not a bare `3` with a comment).
When a genuine *why* still needs stating — a non-obvious workaround or a subtle invariant — put it in the docstring, not a trailing comment.
Reserve `#` for what has nowhere else to live: tooling directives (`# noqa`, `# type: ignore`) and the PEP 723 inline-script header.
**A suppression names what it suppresses** — `# noqa: D103`, `# type: ignore[arg-type]`, never the bare form.
A bare `# noqa` turns off every rule on that line for good, including ones that did not exist when it was written, so the line stops being checked rather than stops being noisy.
It reads as a considered exception when it is usually the reverse: forty bare suppressions across a package is a rule nobody decided to disable, disabled.
Keep config files (`pyproject.toml`, pre-commit, CI) comment-free the same way, explaining any non-obvious setting in prose in the docs rather than inline.

## Imports

**Import modules, not names, and qualify at every use site.** Import the module or package and reach members through it — `import polars` then `polars.DataFrame`, never `from polars import DataFrame`.
Qualified names make it obvious where every name comes from and eliminate collisions, which is worth the extra characters.

This is strict and applies to the standard library too:

```python
import pathlib  # pathlib.Path(...)
import dataclasses  # @dataclasses.dataclass
import collections.abc  # def f(xs: collections.abc.Iterable[int]): ...
```

For a deep internal path, bind the nearest useful module — `from mypackage import db` then `db.session` (still qualified) — rather than importing `session` bare.

**Import a submodule explicitly — importing its parent does not bind it.** `import polars` alone leaves `polars.testing` an `AttributeError`, because a package only exposes the submodules it imports itself; add `import polars.testing` beside it (both lines, since you use both names).
`import collections.abc` above is the same rule, and it is easy to miss on a library whose top level *does* re-export most of what you reach for.

Use **absolute imports** within a package; they survive moving files.
Relative imports (`from . import db`) are fine for tight intra-package references but get confusing across several levels.

**Avoid `as` renames** unless genuinely unavoidable (a real name clash) — that includes the popular ones: prefer `import polars` / `polars.col(...)` over the conventional `import polars as pl`.
A **redundant** alias is the exception and is not a rename at all: `from .membership import resolve as resolve` renames nothing and exists to mark a deliberate re-export (see Public API, below).
When a rename truly is forced, derive it from the *true* name with an underscore prefix or suffix (`import numpy as numpy_`), never an arbitrary short alias like `np`.

**Name a local package of code tightly coupled to a third-party library with a trailing underscore** — `polars_/` for your `polars` helpers, `typer_/` for a CLI's `typer` code, `rich_/` for its rendering, `pytest_/` for test fixtures and bare-`assert` helpers — so the name both marks the coupling and never shadows the real `polars`/`typer`/`pytest`.
**Make it a package even when one module would do** — `httpx_/__init__.py` rather than `httpx_.py`.
The coupled code is the part that grows when the library is swapped or its surface is used harder, so the directory that will be wanted is worth having from the start, and a name that reads as a package everywhere it appears does not change shape the day a second module arrives.
Pair it with a role-named package (`cli`, `api`, `gui`) that re-exports the app; see `write-entry-points` for the split.

Circular imports are a design smell — usually two modules that want to be one, or a missing third module they should both depend on.
Restructure rather than papering over it with function-local imports.
(Dependency management lives in `setup-python`.)

## Public API

Be deliberate about what's public.
A leading underscore (`_helper`, `_Internal`) signals "implementation detail, may change" — use it freely so the real surface is obvious.
**Mark a re-export with a redundant alias — `from .membership import resolve as resolve` — not with `__all__`.**
A name imported into an `__init__.py` for callers to reach is never used in that file, so it is indistinguishable from a leftover; something has to say it is deliberate.
The alias is the smallest thing that does, and it is what the typing spec defines an explicit re-export to be, so `pyright` and `mypy` read it the same way `ruff` does.
`__all__` says the same thing at the cost of a second list beside the imports, and the two drift the moment a name is added to one and not the other; a blanket `per-file-ignores` for `__init__.py` says it by silencing the check, and then never tells you about a genuinely stale import either.
So skip `__all__` entirely: an `__init__.py` that only *defines* its own names needs no marker at all, and neither does a plain module.

## Naming

**Name a function `verb_noun`**, and let the verb decide which side the noun refers to.
`fetch_holdings` returns holdings; `parse_csv` consumes one.
Choose the verb that puts the noun you need to say in the role you need it to play:

- **Transfer** — `read`, `write`, `fetch`, `load`, `get`, `send`.
The noun is the thing moved, and it exists on both sides of the call, so there is nothing to disambiguate: `fetch_holdings` has them at the publisher and arriving here.
- **Transformation** — `parse`, `convert`, `render`, `serialise`.
The noun is the source representation, since that is the half that varies; the target is the return annotation.
- **Derivation** — `find`, `pick`, `build`, `gather`, `derive`.
The noun is the result, since the input is usually a generic container the parameter names.

**A preposition overrides the verb's default and names the other side.**
`derive_from_documentation` names the source precisely because bare `derive` would have named the result; `parse_into_frame`, `find_in_catalogue` and `fetch_from_website` do the same for their families.
Reach for it where the half the verb would name is the obvious one and the other half is what varies — `derive_from_documentation` beside `derive_from_api` — and not otherwise, since a preposition on a noun nobody was going to misread is three syllables of noise.

**The qualifier need not be a noun.** Where the verb selects a subset, an adjective is what distinguishes it and the noun is left to the parameter: `keep_tradeable(holdings)`, `drop_empty(rows)`.
Read it as the elided noun it is — "keep the tradeable ones" — and the rule holds.

**Never say in the noun what the parameter names and annotations already say.**
`parse_csv(document: str)` cannot be `parse_document` — the parameter said that — so the noun earns its place by naming the format instead.
Where both sides are already explained, drop the noun: `transform.resolve(names, catalogue)` needs nothing more, because `names` *is* what gets resolved.
**A parameter only supplies the noun when it is the noun.**
`get(url)` does not get the URL — it gets a document *from* one, so the parameter names the address and the noun is still missing; `get_document(url)` is the honest name.
The test is whether the verb and the parameter read as a sentence: "resolve the names" does, "get the url" does not.

**Judge redundancy against the siblings, not just the signature.**
`parse_holdings` reads well until you notice `fetch_holdings` and `read_holdings` beside it in the same module, at which point the shared half says nothing and the format half says everything.
Line a module's functions up and name each for what distinguishes it from the others — which is also why `polars` has `read_csv` beside `read_parquet` where an adapter has `read_funds` beside `read_exchanges`, both naming the input, one by format and one by payload.

**A bare noun promises a value, not work.**
`_funds()` reads like an attribute, so callers reach for it wherever convenient; `_read_funds()` puts the cost at every call site.
Keep noun-only names for something cheap and effect-free — a fixed `_timeout()`, a `_headers()` dict, a test fixture naming the state it hands over — and give a verb to anything touching the network, the disk, the clock or a cache.
The tell that this has gone wrong is one file being read four times in a run because nothing in the name suggested it would be.

**A type stays a noun even when the thing it names does work.**
A port is `Holdings` — what the core needs, not how it is got (see `structure-python`) — while the function satisfying it is `fetch_holdings`.
Where that port is a **callable alias**, two adapters behind it each say which is expensive: `ark.fetch_holdings` beside `pytickersymbols_.read_holdings`.
Where it is a **`typing.Protocol`**, they cannot, and this rule gives way to the contract: the protocol's member name *is* the interface, so every adapter spells it identically and the cost moves to the module name, where `pytickersymbols_` already says the data ships with the package.
So settle which kind of port you have before naming the function — `structure-python`'s "Declare a port" owns that trade and states it in full.

**A domain prefix goes in front of the finished name, and never replaces the verb.**
`use-polars` marks a `.pipe()` step's functional shape with `map_`/`amap_`/`bind_`; form the name by the rules above first, then prefix it — `map_keep_tradeable`, `amap_join_orders`.
The prefix says how the step behaves in a chain, which is a different question from what the function does.

**Don't repeat a namespace in the name it qualifies.**
A module or class already supplies the context, so drop the redundant prefix — `then.equals`, not `then.then_equals`; `user.name`, not `user.user_name`.
It's the payoff of importing and qualifying: the qualifier carries the meaning, so the member name stays short.

**A decorator and a context manager are functions, so they are imperative too** — `@handle(...)` and `with report():`, never `@handled` or `with reported():`.
The past participle is tempting because it describes what happens to the thing decorated rather than what the call does, and third-party decorators encourage it.
But it makes the one kind of function whose body you cannot see at the call site the one kind whose name has stopped saying what it does.
Functions, methods and CLI commands are imperative regardless of what wraps them.

**Name a package for what it does or holds.**
A package that *performs* an action — a behavioural or pipeline layer — takes an imperative verb (`transform/`, `operate/`, `adapt/`, `drive/`); a package that only *defines* or *holds* things takes a noun (`port/`, `domain/`, and the `cli`/`api`/`gui` role packages).
`structure-python`'s package layers are the worked example.

**Spell a package or module as words, separated by underscores — never run together.**
`granny_shots`, not `grannyshots`; `market_cap`, not `marketcap`.
This overrides PEP 8, which allows the underscore in a module name and discourages it in a package name — a split not worth keeping, since a name is read far more often than typed and running the words together costs a parse every time to save one character.
Spell it from what the thing is *called*, not from however a domain name ran the words together: `granny_shots` though the site is `grannyshots.com`, and `vaneck` because the firm spells its own name as one word.

**Take the shortest name that still identifies it, since the package around it supplies the rest.**
A source of market-capitalisation rankings inside `adapt/` is `market_cap`, not `companies_market_cap`: the layer has already said it is a source, and nothing else in there is about market capitalisation.
This is the namespace rule above applied one level up — the qualifier carries the meaning, so the member name stays short.

**Name an adapter for what it actually reads, not for whose data it is.**
An adapter fetching an aggregator's already-parsed filings is `info_13f`, not `sec`.
The regulator is where the data originates; the site is what breaks, what the reference table addresses and what changes under you, so it is the one the name has to point at.

## Arguments

**Name an argument at the call site unless it is the one thing the function is about.**
A positional value is readable only to someone who already knows the signature, so every unnamed argument past the first sends the reader to another file to learn what it meant.
Naming it puts the answer in the line they are already reading.

```python
# Wrong: three values whose meaning lives in another file.
handle(polars.exceptions.PolarsError, error.HoldingsError, "Could not read {name}")

# Right: the call itself says what each value is for.
handle(
    polars.exceptions.PolarsError,
    report=error.HoldingsError,
    message="Could not read {name}",
)
```

The exception is the **subject** — the thing the function acts on, which the function's own name has already announced.
`parse_csv(document)`, `len(items)` and `polars.col("close")` need no label, and `parse_csv(document=document)` is exactly the stutter the Naming section rules out.
So the shape is a bare subject and a name on everything after it.

**A value that already carries the name does not need it twice.** `revenue(quantity, unit_price)` is as clear as `revenue(quantity=quantity, unit_price=unit_price)` and shorter, because the point of the label is to say what an opaque value means and a variable spelled like its parameter is not opaque.
The rule bites on literals, expressions and mismatched names, which is where the meaning is genuinely missing.

**A boolean or a bare number is never the subject.** `render(symbols, True)` tells a reader nothing and the value offers no type to guess from, where `render(symbols, table=True)` is the same call made readable.

**Put a `*` in the signature rather than trusting the caller to remember.** Everything optional or modal goes after it, so the language enforces at every call site what this section otherwise only asks for — and a parameter that arrives keyword-only can be reordered later without breaking anyone:

```python
def fetch_user(user_id: int, *, include_archived: bool = False) -> User: ...
```

Two things bound the rule.
A named argument binds callers to the parameter's *name*, so renaming one is a breaking change where renaming a positional is not — a real constraint on a published API and almost none on your own code.
And some callables remove the choice: `len`, `abs`, `int` and much of the C-implemented standard library take positional-only parameters, so `len(obj=items)` raises `TypeError` rather than reading better.

## Ordering

Order things alphabetically so every name has *one predictable location* — you never scan a whole file to find something, and diffs stay stable as code grows.

Sort on **visibility first, then name**: dunders, then the underscore-prefixed names alphabetically, then the public ones alphabetically.
That is the dunder convention extended rather than a second rule — `__init__` comes first because it is the most internal thing in the class, and a `_helper` is the next most internal.
It also means a definition is met before it is used, since the public functions are the ones calling the helpers, and nothing is buried by it: the underscore prefix already says which names are not the surface, so a reader scanning for the public ones skips the block above them.

Anything Python reads as the file executes outranks the sort, so a base class sits above its subclasses and an exception hierarchy stays base-first.

- **Module-level definitions** (functions, classes, constants) in that order — private alphabetically, then public alphabetically.
Carve-outs: a script's entry point (e.g. `main`) may sit conventionally, and grouped constants stay at the top.
- **Class members** the same way: dunders (`__init__`, `__repr__`, …) first in conventional order, then private methods alphabetically, then public methods alphabetically.
- **Function arguments** alphabetically where possible, both when defining and when calling.
"Where possible" is doing real work here: `self`/`cls` come first, positional-only and required-before-default constraints win, and don't reorder where argument order itself carries meaning.
It applies most cleanly to keyword arguments at the call site.

Place a new definition in its alphabetical slot, but don't reshuffle an existing file just to enforce this — the diff noise and broken `git blame` outweigh the tidiness.

## Simplicity

**Take the simplest solution.** Reach for built-in language and standard library features before writing custom code or pulling in a dependency — out-of-the-box beats bespoke, because there's less to maintain and fewer places for bugs to hide.
Add complexity (another abstraction, a dependency, a clever trick) only when a concrete need forces it — and when a dependency is warranted, `setup-python` lists the house pick for common tasks.
**Once a dependency is in play, use *its* built-in features rather than hand-rolling around them.** Before writing validation, grouping, parsing, reshaping, retries, or serialisation yourself, check the library's own API — a CLI framework's callbacks and validation, a dataframe library's reshapes and joins, an HTTP client's retry/auth.
Assume a mature library already names any standard manipulation, and go and look before writing more than a few lines of your own.
Reinventing what a dependency already offers is more code to maintain and usually a worse version.
(Do confirm the feature exists, though — not every library has every convenience; a genuine gap is fine to fill.)

**A record a library hands back is part of its API, so read every field before deriving one.**
The instinct is to check a library's *functions* and treat the data it returns as raw material, but a field you never noticed is the same reinvention as a method you never looked up — and a worse one, because a derived value can be wrong where the field is right.
The publisher of the data knows things you cannot compute: which of a company's listings is its home one, which of several identifiers is canonical, which row the source considers current.
Deriving those from the other fields produces a rule that needs a lookup table, misses the cases the table does not cover, and is silently wrong rather than absent.
So print one whole record and read the keys before writing anything that computes over it, and where a field answers the question directly, take it and fall back only where it is missing.
This is KISS again rather than a new rule, but it hides where KISS usually does not, because the hand-rolled version *works* — it just answers a fraction of the rows.

**The field being absent is a case, not an edge case — write the fallback.**
"Take it and fall back where it is missing" is two instructions, and the second is the one that gets dropped, because the field is present on every record you happened to look at.

Its absence bites twice.
It is *absent* rather than empty, so subscripting raises instead of yielding a null — and it raises for the whole batch, so one record without the key fails an entire group that was otherwise fine.
Reach for it with `.get`, and the rows survive to be judged.

Then give the fallback a target: the next-best field of the same kind the record carries, taken **only** where the direct one is absent.
Preferring the fallback wherever it looks more complete is the over-correction and is worse than having none, because it replaces right answers with plausible ones — a company's home listing swapped for whichever exchange happened to be listed first.
Where the record carries no second field either, that row has no answer and should say so by being empty rather than by being guessed.

**A call's defaults are decisions somebody else made for a different problem.**
The instinct is to pass the arguments your task names and let the rest stand, because a default reads as the sensible choice — and it is, for the caller its author had in mind.
It is not a choice *you* made, and nothing in the code records that you saw it.
So read the signature before the first call and decide each default, not only the ones you already meant to change.

The ones that hurt share a shape: silent and plausible.
A price series adjusting for dividends by default returns numbers that look right and answer a different question.
A fetch falling back to one month when given no dates returns twenty rows and looks exactly like a fetch that worked.
A progress bar defaulting to on narrates on the channel a driver owns.
None of them raises, none appears in a passing test, and each is found by reading the signature or not at all.

It cuts the other way too, which is the cheaper half: a client whose timeout already defaults to ten seconds needs no wrapper setting one, so reading the defaults also stops you writing what is already there.

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

**Wait for the second error before there is a hierarchy.** A base class with exactly one subclass distinguishes nothing — every caller catching the base catches the subclass and vice versa — so it is the abstraction added before the second case, which the Avoid section rules out.
Start with one class named for what actually goes wrong (`SelectorError`, not `AppError` plus `SelectorError`), and introduce the base when a second error arrives and callers need to choose between broad and narrow.
The hierarchy above is what a library or an app with several failure modes grows into, not where it begins.

**Handle a library's exceptions with a decorator, not a `try` in every function.**
Where several functions convert the same library failures into the same error of yours, the `try`/`except`/`raise ... from` is identical in each and only the message differs.
Lift it once.
It belongs beside the error classes it raises, in the core, rather than with the adapters that apply it — `structure-python` has the reason and the package.

**The trigger is the repetition, not the message.**
Parameters worth naming are the *best* case, not the entry condition, so a constant message still earns the decorator — a layer of parsers each taking one `document` and raising the same error of yours is the duplication this removes, however little there is to interpolate.
The tell that it was missed is a `try` at the top of every function in a layer, all catching the same types and raising the same one.

Format the message against the decorated function's **own parameters**, so it can name what the caller asked for without the function taking an argument its work never touches:

```python
def handle[**P, T](
    *kinds: type[Exception], report: type[Exception], message: str
) -> collections.abc.Callable[
    [collections.abc.Callable[P, T]], collections.abc.Callable[P, T]
]:
    """Return a decorator raising one of your errors in place of a library's.

    :param kinds: The exception types to handle.
    :param report: The exception type to raise instead.
    :param message: A format string over the decorated function's parameters.
    :returns: The decorator.
    """

    def decorate(
        work: collections.abc.Callable[P, T],
    ) -> collections.abc.Callable[P, T]:
        """Return the function with its library failures reported as ours."""
        signature = inspect.signature(work)

        @functools.wraps(work)
        def run(*a: P.args, **k: P.kwargs) -> T:
            """Do the work, and say whose fault it is in your own terms."""
            try:
                return work(*a, **k)
            except kinds as failure:
                bound = signature.bind(*a, **k)
                bound.apply_defaults()
                raise report(
                    f"{message.format(**bound.arguments)}: {failure}"
                ) from failure

        return run

    return decorate
```

```python
@handle(
    polars.exceptions.PolarsError,
    report=HoldingsError,
    message="Could not read the holdings {name} published",
)
def get_holdings(name: str, *, get: Get = get_document) -> polars.DataFrame: ...
```

`typing.Concatenate` is not needed: `P` carries the whole signature, so the wrapped function keeps its own and the message reads any parameter by name.
The `[**P, T]` type parameters are PEP 695 syntax and need 3.12, which is the floor this skill assumes; below it, declare `P` and `T` as module-level `typing.ParamSpec`/`typing.TypeVar` instead.
Take the signature once at decoration time — binding it per call is the only cost, and it is what lets the message name an argument the body never mentions.

**Put the decorator on the function that knows what was asked for, not on the one that fails.**
The `try` would have gone around the parse, so that is where the decorator looks like it belongs — but the message formats over the *decorated* function's parameters, and the parser was given a document rather than a name.
Decorating it yields "the holdings file could not be read" with nothing to say which fund's, which is the failure a caller cannot act on.
Decorate the entry point that took the name and the same failure comes back naming it, because an exception raised deeper still passes through on its way out.
The example above is the shape: `@handle` sits on `get_holdings(name, ...)` and catches what the parse it calls throws.
This is the section's last rule applied to placement rather than to parameters — the boundary that holds the name is the boundary that reports.

**The one case the decorator cannot take is a report type that varies by caller.**
`report` is bound at decoration, so a function whose caller decides what a failure *means* — a 404 that is "no such thing" to one caller and "the publisher moved it" to every other — cannot express that through it.
Write one shared private converter taking the report type as an argument and call it from each entry point, which is still the one place deciding that the rule was asking for.
Reach for it only where the meaning genuinely differs; a message that differs is the decorator's case, not this one.

**A decorator is a rule about a call, not only about its exceptions.**
`handle` catches, so this section reads as exception machinery — but a decorator sees the arguments and the return value together, and both are places the same duplication collects.

- **Classifying an answer is a decorator.** Which status a service replied with is a branch on the *response*, not on an exception type, so the function raising a distinct error per outcome carries no `try` at all and lifts out of every adapter sharing that boundary.
- **Checking what came back against what was asked for is a decorator.** A source answering for four of the five symbols it was given has not failed in any way a `try` could see, and the comparison needs the arguments and the result in one place — which is what a decorator holds and a helper called from each function does not.

**Stacking `handle` is how one outcome means different things to different adapters.**
It converts whatever it is given, so it reinterprets your own errors as readily as a library's: a neutral "there is no such document" becomes "no such index" for the source that will try any name, and "the publisher moved it" for the issuer publishing a book you ship.
Put the narrow conversion **inside** the broad one — the inner decorator has already turned the neutral error into something the outer's `kinds` do not name, so the outer leaves it alone.
Reversed, the broad one catches first, the distinction is lost, and nothing says so.

That is not the case ruled out above: there the *caller* decides at runtime, so no report type can be bound at decoration; here each adapter decides once, which is exactly what decorating it records.

**The decorator converts a failure; it does not classify one.**
It maps a set of exception types onto a single error of yours, so it cannot say that one answer from a service means something different from another — that a 404 is "there is no such thing", a 503 is "ask again shortly" and a 401 is neither.
Where the caller's next move differs by *which* failure it was, that decision is a branch and it belongs at the one boundary that can see the raw outcome: raise a distinct error per outcome there, from a single function.
The two then compose rather than compete — the decorator handles the library exceptions that all mean the same thing (a connection that would not open, a document that would not parse), and the explicit raises cover the ones the caller has to tell apart.
A retry policy sitting outside that function is what consumes the distinction, which is the usual reason the distinction has to exist at all.

**Name the outcomes for who consumes them, and never by negation.**
Which errors you raise at that boundary is decided by the *consumers*, and there are always at least two: the caller, choosing what to tell the user, and the retry policy, choosing whether to ask again.
They cut differently — a caller may need only "no such thing" against "it went wrong", where retry needs "might work shortly" separated from "will never work" — so enumerate both before settling the classes, and expect siblings rather than a tree, since nothing wants the middle of the hierarchy.

A predicate written as a negation is where this goes wrong quietly.
"Retry unless it was a missing document" reads as the same rule and is not: it enrols every outcome nobody has thought of yet, so a refused credential and a forbidden path each wait out three backoffs before failing.
Name the retryable outcome and retry *that*, so anything new defaults to failing fast.

**Don't reach for a package.** The dedicated ones are abandoned — the four on PyPI run 40 to 100 downloads a month — and the popular neighbours solve other problems: `wrapt` and `decorator` help you *write* a decorator, `tenacity` and `backoff` retry, `returns` converts an exception into a `Result` and changes every caller.
`tenacity`'s `retry_error_cls` does translate on exhaustion, but the message it raises is a `repr` of a `Future`, and fixing that means subclassing `tenacity.RetryError` — coupling your domain error to the library the adapter exists to hide.

**Attach the context where the context already lives.**
A helper taking an identifier only to name it in an error message has an argument its work never touches — it cannot be called or tested without inventing one, and the parameter cannot be removed without editing every caller.
Let it raise plainly, and catch at the boundary that already holds the name: `fetch_holdings(name)` knows which fund it asked for, so `parse_csv(document)` does not need telling.
That also keeps one place deciding how a failure reads, rather than a message spelled slightly differently at each depth.

Let exceptions propagate to where they can be handled meaningfully — don't catch-and-continue to hide failures.
When re-raising with context, use `raise NewError(...) from original` to preserve the chain.
Reserve returning `None` for genuinely expected "not found" cases, and make it obvious in the type (`User | None`) and docstring.

## Idioms

- **Comprehensions** for simple transforms/filters; a plain loop once it needs multiple statements or gets hard to read.
Don't nest past two levels.
- **`pathlib.Path`** for filesystem work, not string paths.
A string path only looks simple: joining it means guessing at separators, and every question you then ask it — suffix, parent, does it exist — is a different `os.path` function, where `Path` carries them all as methods and handles the separator itself.
- **`urllib.parse.urljoin` for an address, not string concatenation.**
A URL carries the same trap a filesystem path does and one more: `base + path` guesses at the separator, so a base that gains or loses its trailing slash silently doubles or drops one, and the failure arrives as a 404 that reads as the publisher having moved the file.
`urljoin` knows what a scheme, an absolute path and a relative segment each mean.
The trap to know is that it reads the base as a *document*: a base missing its trailing slash loses its last segment, and a path carrying a leading one resets to the host — so hold the slash on the base and not on the path, which is also what keeps a table of paths readable.
- **Use a named method over an overloaded operator when both exist — especially when chaining off the result.** `path.joinpath("a/b").read_text()` reads left-to-right, where the operator form needs parens (`(path / "a/b").read_text()`) because attribute access binds tighter than `/`.
A named method also reads in evaluation order and says what a symbol only implies — `polars`'s `col.mul(2)`/`col.gt(0)` over `*`/`>` (see `use-polars`).
Keep operators where they're the plain idiom: arithmetic on numbers, and short expressions you don't chain off.
- **Context managers** (`with`) for anything with cleanup — files, locks, connections.
Write your own with `contextlib.contextmanager` when useful.
- **f-strings** for formatting.
Use `logging` with `%`-style lazy args (`logger.info("got %s", x)`) so the string isn't built when not logged.
- **EAFP over LBYL** (Easier to Ask Forgiveness than Permission, over Look Before You Leap) where it reads well — try the operation and handle the exception rather than pre-checking; avoids races and is often clearer.
- **Prefer a function returning a value over a hardcoded module global.** A function can later compute, parameterise, or override the value without callers changing; a bare global has to be torn out to extend.
This holds for a value that looks permanently fixed too — "it will never change" is what every constant is believed to be right up until it has to be parameterised, and by then the callers are written against the global.
The exceptions are names a tool or framework *requires* at module level — a `logging.getLogger(__name__)` module logger, a framework's app object, a test module's shared strategy or fixture data.
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
- **A fixed, known set is a lookup, not a mechanism.**
Several implementations of one interface look like the second case that justifies an abstraction, but the test is whether the set is *open*.
Something you ship, can enumerate today, and change only by editing your own code is **data** — and the code that reaches it is a lookup.
Build the registration machinery — a record per implementation, a sequence they are collected into, a key routing between them — when something outside your control has to join the set.
Four sources you wrote yourself are four calls behind one lookup, and the machinery only moves the four names from a place the type checker reads to a place it does not.
- **A single-use local variable** — inline the expression instead.
A name for a value used exactly once adds reading overhead without payoff.
Keep the name only when it meaningfully documents an otherwise opaque expression.
- **Hand-placed blank lines inside a function body** to group statements — keep the body contiguous and leave vertical spacing to the formatter.
The urge to separate chunks with whitespace usually means the function is doing too much, so extract a helper instead.
(Blank lines *between* definitions are the formatter's job.)
