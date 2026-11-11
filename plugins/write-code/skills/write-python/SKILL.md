---
name: write-python
description: >-
  In-code conventions for writing Python that a formatter can't decide —
  typing (the frozen dataclass as the record, Literal, StrEnum, NewType,
  Protocol, override, assert_never), aware UTC datetimes and Decimal money,
  docstrings, comments, imports and the trailing underscore on a
  library-coupled module, re-exports, naming, call-site argument style, member
  ordering, simplicity, the one error model (raise from the app's error
  package, convert or classify at an adapter's seam, decide what the user sees
  in a driver, nothing caught in the core, X | None only for a lookup miss),
  sync by default, and idioms, with what to avoid. A rule that bends carries
  its exception. Load it before the first line of any
  Python, even a one-off function answered inline. Use whenever writing,
  editing, refactoring or reviewing Python code, even if the user doesn't
  mention "conventions", "style", or "clean code". Targets the Python floor
  setup-python sets, 3.15 today. Formatting and linting are delegated to ruff
  and type-checking to pyright in strict mode; this skill covers only the
  judgement calls they can't make. The baseline for all Python: be-functional,
  be-oop and write-tests layer on it; for project structure see
  structure-python, for packaging and tooling setup-python.
---

# Write Python

The judgement calls that make Python readable — the decisions a formatter or linter can't make.
It is the baseline that `be-functional`, `be-oop` and `write-tests` layer on; project structure lives in `structure-python`, packaging and tooling in `setup-python`.
Three habits account for most of what goes wrong: importing names instead of modules, leaving a function unannotated or undocumented, and reaching for a class or abstraction before a second case calls for one.

**In an existing project, ask first.** Where a codebase already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Formatting

`ruff` formats, sorts imports and lints; `pyright` type-checks.
Don't restate or fight them, and don't hand-format what `ruff format` fixes on pre-commit — wrapping, quotes, the trailing comma it adds when a line splits — since the hook will undo it and the diff gains noise.

**The magic trailing comma is the one formatting decision that is yours.** `ruff format` collapses a call or collection onto one line where it fits, unless a trailing comma after the last element pins it open one-per-line.
Use it for consistency within a module: if some calls of a kind run down the page because they were long, give the short ones the comma too, so the difference doesn't look meaningful and adding an argument is a one-line diff.

## Typing

**Annotate every function** — every argument and the return value, public and private alike — so `pyright` checks every call site.
**Don't annotate local variables**; let inference work, and add a hint only where it genuinely can't.

- **Accept the most general type, return a concrete one**: take `collections.abc.Iterable`, return `list`.
- **`typing.Any`** only for a genuinely unspecified type.
- **A record is a frozen dataclass** — `@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)` — once the record is warranted (see `be-functional`); `kw_only` makes construction follow the Arguments rule, and an object whose changing state is the model leaves `frozen` off (see `be-oop`).
`pydantic` models only where data crosses a trust boundary — a request body, a settings source, a response being parsed — since validation at every layer is paid at every layer; `typing.NamedTuple` only where an API requires tuple semantics; never `attrs`.
- **Name a closed set of modes as a type**: `typing.Literal[...]` for a few string modes inside the code, `enum.StrEnum` once the set crosses a boundary or needs behaviour, a sum type of frozen dataclasses once the variants carry data (see `be-functional`).
- **`typing.NewType` for an identifier that must not mix** with another of the same base type (`UserId`, `OrderId`), so `pyright` catches the swap.
- **`typing.TypedDict` only for a JSON shape before `pydantic` parses it**; past that boundary it is a dataclass.
- **`typing.Protocol` for a structural interface** rather than an ABC (Abstract Base Class) hierarchy, and **`typing.override`** on every overridden method, so a renamed base method fails type-checking instead of silently detaching the override.
- **End every `match` over a sum type with `case _: typing.assert_never(value)`**, which makes a forgotten variant a type error rather than a missing return.
- **A type that spans a line becomes a PEP 695 `type` alias**, so names stay qualified and the signature stays readable (see Convert with a decorator).
- **Write for the floor `setup-python` sets**, today 3.15, except in a library published for others, which keeps the floor its users need: annotations are deferred, so no `from __future__ import annotations` and no quoted forward references; `warnings.deprecated` marks a deprecation; `copy.replace`, not `dataclasses.replace`, updates a record, since it works for any type with `__replace__`.

## Time and money

- **Aware datetimes only, in UTC inside the core**; attach a `zoneinfo.ZoneInfo` only where a person reads the value, and use `datetime.date` for a calendar day.
A naive value a library hands back is converted at the adapter, once, so a local-time conversion never hides in the core.
The same holds on disk: a stored timestamp column keeps its UTC zone (`store-data`, Shape a stored table).
Never `pytz`, `arrow` or `pendulum`; the stdlib covers it, and inside a frame the temporal dtypes do.
- **Money is `decimal.Decimal` or integer minor units in domain types, never `float`**; in a frame, `polars.Decimal` where the operations support it, else `Float64` rounded only at presentation, with a dependency test pinning the precision (see `write-tests`).

## Docstrings

**Every module, class, and public or module-level private function gets a docstring**, in reStructuredText field-list style, a `Protocol` method included, since the stub is the whole contract; a closure nested inside a function does not, since its name and position already say what it does and `ruff`'s `D` rules never ask, and nor does a test, which `setup-python`'s `per-file-ignores` exempt for the same reason (see `write-tests`):

```python
def fetch_forecast(city: str, *, days: int = 3) -> polars.DataFrame:
    """Return the daily forecast for a city.

    :param city: The city's name, as the weather service spells it.
    :param days: How many days ahead to cover.
    :returns: One row per day, with high and low temperatures in Celsius.
    :raises ForecastError: If the service has no forecast for the city.
    """
```

- **Types stay out** — the annotations carry them, so no `:type:` or `:rtype:`.
- **Summary line in the imperative**: "Return the forecast", not "Returns…" or the noun phrase "The forecast"; `ruff`'s `D401` flags the rest.
- **A summary line and its fields is the whole docstring.** A prose sentence between them must be earned by a fact neither the signature nor the body can state — a unit, a side effect, an invariant the caller must respect.
- **A module docstring is one line** saying what the module is for.
- **Say what the signature doesn't.** A trivial function still gets a docstring, but a restatement of its name is wasted.
- **Design reasoning goes elsewhere.** Why the code changed belongs in the commit message, and behaviour a user meets in the README; a docstring holding the design is a wall a caller scrolls past to find what comes back.

`ruff`'s pydocstyle (`D`) rules enforce presence under the `pep257` convention, which checks that docstrings exist but not the field-list style (see `setup-python`).

## Comments

Write self-documenting code instead of `#` comments: a name, a named constant or a small helper carries the meaning and cannot drift out of sync the way a comment does.
Where a genuine *why* remains — a workaround, a subtle invariant — put it in the docstring.
Reserve `#` for tooling directives and the PEP 723 script header; in a config file (`pyproject.toml`, pre-commit) a one-line comment beside an odd setting is read when the setting is, where an explanation in the docs drifts.

**A suppression names what it suppresses** — `# noqa: D103`, `# type: ignore[arg-type]`, never bare.
A bare `# noqa` disables every rule on the line, including rules added later, so the line silently stops being checked.
A `typing.cast` written to quiet the checker is a suppression that doesn't admit it; unless it narrows a genuinely wider type, restructure until the checker agrees.

## Imports

**Import modules, not names, and qualify at every use** — `import polars` then `polars.DataFrame`, never `from polars import DataFrame`.
Every name then shows where it comes from and none can collide.
This applies to the standard library too: `import pathlib` → `pathlib.Path`, `import collections.abc` → `collections.abc.Iterable`.
For a deep internal path, bind the nearest useful module (`from mypackage import db`, then `db.session`).

- **Import a submodule explicitly.** `import polars` does not bind `polars.testing` — a package exposes only the submodules it imports itself — so write both lines when you use both.
- **Don't rename with `as`**, including the popular aliases: `import polars`, not `import polars as pl`.
Where a clash forces a rename, derive it from the true name (`import numpy as numpy_`).
A redundant alias (`from .users import find as find`) renames nothing — it marks a re-export (see Public API).
- **Name a module coupled to a third-party library with a trailing underscore** — `polars_.py`, `typer_.py`, `httpx_.py` — so it marks the coupling without shadowing the library.
It stays a module until a second file is needed, then becomes a package of the same name (`httpx_/`), so no import changes shape; an empty `__init__.py` package wrapping one module is a directory nobody opens.
- **Fix a circular import by restructuring** — merge the two modules or extract the third they both need — not with a function-local import.

## Public API

**Mark a re-export with a redundant alias — `from .users import find as find` — not `__all__`.**
A name imported into `__init__.py` for callers is unused in that file, so `ruff` flags it as a leftover unless something marks it deliberate.
The alias is what the typing spec defines as an explicit re-export, so `pyright` reads it the same way; `__all__` duplicates the import list and drifts from it, and a blanket `per-file-ignores` hides genuinely stale imports.
A module that only defines its own names needs no marker.

## Naming

**Name a function `verb_noun`, and pick the verb so the noun names the half that varies:**

- **Transfer** (`read`, `write`, `fetch`, `load`, `get`, `send`) — the noun is the thing moved: `fetch_orders`.
- **Transformation** (`parse`, `convert`, `render`, `serialise`) — the noun is the source format, since the target is the return annotation: `parse_csv`.
- **Derivation** (`find`, `pick`, `build`, `derive`) — the noun is the result: `build_index`.

Refine it with these rules:

- **A preposition names the other side** where that is what varies: `load_from_cache` beside `load_from_disk`.
Don't add one where nobody would misread the plain name.
- **An adjective can be the qualifier** when the verb selects a subset: `keep_active(users)`, `drop_empty(rows)`.
- **Don't repeat what the parameters say.** `parse_csv(document: str)` names the format, because `parse_document` would repeat the parameter; `resolve(names, catalogue)` needs no noun at all.
But a parameter supplies the noun only when it *is* the noun: `get(url)` gets a document *from* a URL, so it is `get_document(url)`.
The test is whether verb and parameter read as a sentence — "resolve the names" does, "get the url" doesn't.
- **Judge against the siblings.** In a module holding `fetch_orders`, `read_orders` and `parse_orders`, the shared noun says nothing; name each for what distinguishes it.
- **A bare noun promises a cheap value, not work.** `_settings()` reads like an attribute and gets called wherever convenient; anything touching the network, disk, clock or a cache takes a verb (`_read_settings()`), so its cost shows at every call site.
- **A type stays a noun** even when the thing it names does work: a port is `Orders`, the function satisfying it `fetch_orders` (see `structure-python` on ports).
- **A domain prefix goes in front of the finished name**, never in place of the verb: `use-polars`'s `map_keep_active`.
- **Don't repeat the namespace**: `user.name`, not `user.user_name`; the qualifier carries the context.
- **Decorators and context managers are imperative too** — `@handle(...)`, `with report():`, never `@handled`.
They are the functions whose bodies a call site can't see, so their names most need to say what they do.

Packages and modules:

- **A package that acts takes a verb** (`transform/`, `adapt/`, `drive/`); one that holds definitions takes a noun (`domain/`, `port/`).
- **Separate words with underscores**, in packages too, overriding PEP 8's discouragement: `unit_price`, not `unitprice`.
A name is read far more often than typed.
Spell it as the thing is called, not as a domain name runs it together.
- **Take the shortest name the surrounding package leaves unambiguous**: a source inside `adapt/` is `weather`, not `weather_source`.
- **Name an adapter for what it reads**, not whose data it is: the mirror you download from is what breaks and changes under you, not the project whose releases it republishes.
- **One library serving many sources gets a module per source** — `adapt/weather.py`, `adapt/tides.py` — sharing the library package (`adapt/httpx_/`): the trailing underscore names the coupling, and the source module names what it reads.

## Arguments

**Name every argument at the call site except the subject** — the thing the function's name already announces.
A positional value is readable only to someone who knows the signature, so each unnamed argument past the first sends the reader to another file.

```python
# Wrong: what do True and 30 mean?
render(rows, True, 30)

# Right: the subject is bare; everything after it says what it is.
render(rows, table=True, width=30)
```

- **A variable already spelled like the parameter needs no label**: `revenue(quantity, unit_price)`, not `revenue(quantity=quantity, …)`.
The rule bites on literals, expressions and mismatched names.
- **A boolean or bare number is never the subject**, except as the operand of an operator method (`.gt(0)`, `.add(1)`).
- **Put a `*` in the signature** before everything optional or modal, so the language enforces the naming and those parameters can be reordered later without breaking callers: `def fetch_user(user_id: int, *, include_archived: bool = False) -> User`.

Two limits: a keyword binds callers to the parameter's name, so renaming it breaks a published API; and positional-only builtins (`len`, `abs`) raise `TypeError` if named.

## Ordering

Order alphabetically so every name has one predictable place.

- **Module level and class members: dunders, then private names, then public names**, each group alphabetical.
A definition is then met before the public functions that call it, and the underscore already tells a scanner which block to skip.
- **Execution order outranks the sort**: a base class precedes its subclasses.
- **Arguments alphabetically**, in definitions and keyword call sites, after `self`/`cls` and the language's own constraints, except in a pipeline module, where parameters follow the data flow the functions were derived from (see `be-functional`, Derive functions from the data flow), and never where order carries meaning.
- Carve-outs: a script's `main` may sit conventionally, and grouped constants stay at the top.

Place a new definition in its slot, but don't reshuffle an existing file — the diff noise and broken `git blame` outweigh the tidiness.

## Simplicity

**Take the simplest solution**: the language and standard library before custom code or a dependency, except where `setup-python` names a house pick over the stdlib, such as `typer` over `argparse`; complexity only when a concrete need forces it.

**Once a library is in play, use its features rather than hand-rolling around them.** Before writing validation, grouping, reshaping, retries or serialisation, check its API — a mature library already names any standard manipulation.
Confirm the feature exists, though; a genuine gap is fine to fill.

**Read every field of a record a library returns before deriving one.** The publisher knows what you can't compute — which address is primary, which identifier canonical, which row current — and a derived version works for most rows and is silently wrong for the rest.
Print one whole record first; where a field answers the question, take it.

**Write the fallback for an absent field.** It is present on every record you looked at, which is why the fallback gets dropped.
Reach for it with `.get`, since one record missing the key would otherwise raise for the whole batch.
Fall back to the next-best field of the same kind **only where the direct one is absent** — preferring the fallback when it looks more complete replaces right answers with plausible ones.
Where no field answers, leave the value empty rather than guessing.

**Decide every default of a call you make.** A default is someone else's choice for a different caller, and the harmful ones are silent and plausible: a timestamp converted to local time, a fetch that quietly returns one page when given no limit, a progress bar writing to a channel the driver owns.
None raises or fails a test; reading the signature is the only way to find them.
It also stops you re-setting what is already the default.

**Measure behaviour the documentation doesn't state.** Whether a range end is inclusive, how a coarser period aligns, what an empty input returns — run the call on two inputs that differ in the way you will rely on, and write the rule from what came back.
The tell is that you are about to write a docstring or branch stating how a library behaves without having watched it.
Keep the measurement as a dependency test (see `write-tests`).

## Error handling

**Raise from the application's own `error/` package** (see `structure-python`), and catch in two places only.
An adapter converts a library's failure, or classifies an item's outcome, at its seam (Convert with a decorator, Classify outcomes), so nothing third-party crosses into the core; a driver decides what the user sees, and its top-level `except Exception` logs and exits.
Nothing in the core catches: a `try` there hides a failure the driver was built to report.
**Return `X | None` only for a lookup miss the caller always branches on**, visible in the signature; every other awkward case raises, and no `Result` library is used, since it changes every caller's shape to carry what an exception carries for free.

**Wait for the second error before building a hierarchy**, unless a retry policy or a caller must already tell outcomes apart, in which case name the siblings on day one (see Classify outcomes).
A base with one subclass distinguishes nothing, since catching either catches both.
Start with one class named for what goes wrong (`ForecastError`), and add a base when a second arrives and callers need to choose broad or narrow.
When you do, expect siblings under one base rather than a deep tree — nothing catches the middle of one.

**Attach context where it already lives.** A helper that takes an identifier only to name it in an error has a parameter its work never touches.
Let it raise plainly, and convert at the boundary that holds the identifier — `fetch_forecast(city)` knows the city, so the parser it calls needn't.

### Convert with a decorator

**When several functions convert the same library failures into the same error of yours, lift the `try` into one decorator.**
The trigger is the repetition — a `try` atop every function in a layer, catching the same types and raising the same error — not whether the message has anything to interpolate.
Format the message over the decorated function's own parameters, so it can name what the caller asked for:

```python
type Decorator[**P, T] = collections.abc.Callable[
    [collections.abc.Callable[P, T]], collections.abc.Callable[P, T]
]


def handle[**P, T](
    *kinds: type[Exception],
    message: str = "",
    report: collections.abc.Callable[[str], BaseException],
) -> Decorator[P, T]:
    """Return a decorator answering a failure in your own terms.

    :param kinds: The exception types to handle.
    :param message: A format string over the decorated function's parameters.
    :param report: How to answer, returning the exception to raise instead.
    :returns: The decorator.
    """

    def decorate(
        work: collections.abc.Callable[P, T],
    ) -> collections.abc.Callable[P, T]:
        signature = inspect.signature(work)

        @functools.wraps(work)
        def run(*a: P.args, **k: P.kwargs) -> T:
            try:
                return work(*a, **k)
            except kinds as failure:
                bound = signature.bind(*a, **k)
                bound.apply_defaults()
                said = message.format(**bound.arguments)
                raise report(
                    f"{said}: {failure}" if said else str(failure)
                ) from failure

        return run

    return decorate


@handle(httpx.HTTPError, message="No forecast for {city}", report=ForecastError)
def fetch_forecast(city: str, *, days: int = 3) -> polars.DataFrame:
    """Return the daily forecast for a city."""
```

- **`report` returns the exception to raise**, so an exception class satisfies it unchanged and a driver can pass its own function that prints the message and returns the exit to raise — one decorator for adapters and drivers, and with an empty `message` the driver gets the failure's own text.
That responder is presentation, so it lives with the driver's output, not beside the error classes.
- **Decorate the function that knows what was asked for**, not the one that fails: on the parser the message has only a document to name; on `fetch_forecast(city)` it names the city, and the parser's exception still passes through.
- **Stack to reinterpret.** `handle` converts your own errors as readily as a library's, so a neutral `AbsentError` can become "no such city" in one adapter and "the service moved it" in another.
Put the narrow conversion inside the broad one; reversed, the broad one catches first and the distinction vanishes silently.
- **A meaning that varies by caller can't be bound at decoration.** Write one private converter taking the error type as an argument and call it from each entry point.
- **No package does this well.** The dedicated ones are abandoned, and the popular neighbours solve other problems (`tenacity` retries, `returns` changes every caller to a `Result`).

`P` carries the whole signature, so no `typing.Concatenate` is needed; the `type` alias keeps the return annotation to one line.

### Classify outcomes

**A decorator is a rule about a call, not only its exceptions.** It sees the arguments and the return value together, so two more repeated checks lift the same way:

- **Classifying a response** — raising a distinct error per status — is a branch on the answer, not an exception type, so it needs no `try`.
- **Checking the result against the request** — a source answering for four of the five keys it was asked for — needs arguments and result in one place.

Lift either only when a second function needs the same check; on one function a decorator is indirection.

**Converting is not classifying.** `handle` maps many exception types onto one error; where the caller's next move depends on *which* failure it was (a 404 is "no such thing", a 503 "try again shortly"), raise a distinct error per outcome at the one boundary that sees the raw response.

**Name outcomes for their consumers, never by negation.** There are usually two consumers — the caller deciding what to tell the user, and the retry policy deciding whether to ask again — and they cut differently, so enumerate both before choosing the classes.
"Retry unless it was missing" enrols every outcome nobody thought of, so a refused credential waits out three backoffs; name the retryable outcome and retry only that, so anything new fails fast.

## Sync and async

The core is synchronous and pure; `async` lives only inside a driver or adapter whose framework or fan-out requires it, and never reaches a signature the core calls.
A `fastapi` handler stays a plain `def` unless it awaits something, since the framework runs a plain `def` in a worker thread.
Test async code through the `anyio` pytest plugin, which `fastapi` already depends on, not `pytest-asyncio`.

## Idioms

- **A function over a module global**, even for a value that looks permanent, so it can later compute or take a parameter without callers changing — except a `typing.Final` constant, and a name a tool requires at module level (a `logging.getLogger(__name__)` logger, a framework's app object).
- **A named method over an operator when chaining** is a preference: `path.joinpath("a").read_text()` reads left to right where `(path / "a").read_text()` needs parentheses, and `polars` says the same for `col.gt(0)` (see `use-polars`); operators stay for plain arithmetic and short unchained expressions.
- **One branch shape per function.** An early return and a conditional expression say the same thing, so mixing them looks meaningful; two branches read well as a conditional expression, three or more as early returns.
- **`urllib.parse.urljoin`, not concatenation, for URLs.** `urljoin` treats the base as a document: keep the trailing slash on the base and none on the path, or it drops the base's last segment or resets to the host.
- **Tabular data stays in a dataframe** — compute in expressions across one long frame rather than looping over lists or groups (see `use-polars`); `iter_rows` appears only where a driver renders rows for a person, never in a transform.
- **Measure before optimising** — `pyinstrument` on the real input — and only against a budget the plan sets (see `plan-project`); a hot path guessed at is usually the wrong one.

## Avoid

- **Any abstraction** (factory, base class, config layer) **before a second case**.
- **Registration machinery for a closed set.** Implementations you ship, can enumerate and change only by editing your code are data reached by a lookup; build registries only when code outside your control must join the set.
- **A single-use local variable**, unless its name documents an otherwise opaque expression or is the *when* of a test (see `write-tests`).
- **Blank lines inside a function body** to group statements, except between the beats of a short function that would otherwise split into one-line functions; past that the urge means the function should be split.
