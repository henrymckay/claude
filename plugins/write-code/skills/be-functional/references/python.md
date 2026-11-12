# Be functional in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.

## Immutability

A record is `write-python`'s frozen dataclass, updated with `copy.replace`; a mapping updates with `d | {k: v}`.

## Algebraic data types and pattern matching

Model *product* types with frozen dataclasses and *sum* types with a `type` alias over variant classes (or an `enum.StrEnum` for a closed set of names), then destructure with `match` and close it with `assert_never`:

```python
import dataclasses
import math
import typing


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Circle:
    """A circle, by radius."""

    radius: float


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Square:
    """A square, by side length."""

    side: float


type Shape = Circle | Square


def area(shape: Shape) -> float:
    """Return a shape's area."""
    match shape:
        case Circle(radius=r):
            return math.pi * r**2
        case Square(side=s):
            return s * s
        case _:
            typing.assert_never(shape)
```

**`match` for a closed set of variants you own; `functools.singledispatch` where new types must register their own handler from elsewhere** (`SKILL.md`, Choose axis of change).
Where every branch only *returns a value*, write the lookup `SKILL.md` describes as an `enum.StrEnum` or a dict literal in the core, or as a data file when it is reference data someone will correct (see `structure-python`, Data).

## Specialise and compose

Write the **generic** function and derive variants from it, with the stdlib:

```python
import functools


def get_many(source: Source, *, n: int) -> list[Item]:
    """Fetch n items from a source."""
    return source.fetch(limit=n)


def get_one(source: Source) -> Item:
    """Fetch one item from a source."""
    return take_one(get_many(source, n=1))


get_pair = functools.partial(get_many, n=2)


def take_one(items: list[Item]) -> Item:
    """Return the first item."""
    return items[0]
```

- **`functools.partial`** binds arguments and keeps the type: `pyright` special-cases it, so `get_pair` is checked at every call.
`toolz.curry` composes more freely, but `toolz` ships no type hints, so every curried or composed function comes out `Unknown`; reach for it only where that cost is paid knowingly.
- **A named function over `compose`.** `get_one` as a two-line `def` is typed, documented and greppable; `toolz.compose(take_one, functools.partial(get_many, n=1))` is none of those.
- **`functools.cache`** memoises a pure function, with three traps: an unhashable argument (a frame) raises, a method leaks `self` into the cache, and the cache is hidden state the tests then share.
- **Tabular data's declarative form is a dataframe expression**, not a comprehension over extracted columns — see `use-polars`.

## Inject impure dependencies

In a layered application the core takes the effect with no default (`SKILL.md`, Functional core, imperative shell):

```python
import collections.abc
import datetime


def build_config(env: collections.abc.Mapping[str, str]) -> Config:
    """Build config from the settings the environment holds."""
    return Config(debug=env.get("DEBUG") == "1")


def stamp(now: datetime.datetime) -> str:
    """Return an ISO-8601 timestamp."""
    return now.isoformat()
```

A script with no layers may default to the real thing in place: `env: collections.abc.Mapping[str, str] = os.environ` (a live mapping, so one binding tracks the environment), and for a value re-read each call, `now: datetime.datetime | None = None` resolved with `if now is None`, never `now or …`, which treats any falsy value as absent.

## Libraries

The stdlib covers composition, immutability and dispatch; each library earns its place only for the case named.

- **`toolz`** — a sequence helper the stdlib lacks (`partition_all`, `sliding_window`, `groupby` into a dict without pre-sorting); untyped, so never for currying or composition.
- **`plum`** — dispatch on more than one argument's type, which the stdlib lacks, only where `match` on a tuple of the arguments would not read, since it costs a dispatch at every call.
- **`pyrsistent`** — persistent collections with structural sharing for repeated functional updates to large structures; frozen dataclasses remain the record.
- **No `Result` library** (`returns` and the like): `write-python`'s error model.
