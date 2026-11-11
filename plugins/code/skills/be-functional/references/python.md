# Be functional in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
Python isn't a pure functional language, so aim for *pragmatic* functional without fighting the language.

## Immutability

- **Frozen dataclasses** for records, in `write-python`'s shape:
  ```python
  import copy
  import dataclasses


  @dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
  class Point:
      """An immutable 2-D point."""

      x: int
      y: int


  p = Point(x=1, y=2)
  p2 = copy.replace(p, x=10)
  ```
- **`copy.replace`** updates a record (see `write-python`); `d | {k: v}` a mapping.

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

The `case _: assert_never` arm is what makes a new variant a type error at every `match` that forgot it; without it `pyright` reports only a possibly missing return, and only when the function returns a value.

**`match` vs `functools.singledispatch`** — both dispatch on type, so choose by who owns the cases.
Use `match` for a **closed** set of variants you own (you get exhaustiveness checking); use `singledispatch` when the operation should stay **open** to new types that register their own handler from elsewhere, without editing the function.
For plain boolean conditions, `if`/`elif` still wins over both.
Neither is right where every branch only *returns a value* for its case — that is the lookup `SKILL.md` describes, written as an `enum.StrEnum` or a dict literal in the core, or as a data file when it is reference data someone will correct (see `structure-python`, Data).
For dispatch on **more than one argument's type** the stdlib has nothing; `plum` does it well typed, at the cost of a dependency and a dispatch at every call, so reach for it only where `match` on a tuple of the arguments would not read.

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
`toolz.curry` composes more freely, but `toolz` ships no type hints, so every curried or composed function comes out `Unknown` and `write-python`'s annotate-everything rule is defeated on exactly the functions hardest to read; reach for it only where that cost is paid knowingly.
- **A named function over `compose`.** `get_one` as a two-line `def` is typed, documented and greppable; `toolz.compose(take_one, functools.partial(get_many, n=1))` is none of those.
Keep any composition shallow enough to read; the aim is expressive building blocks, not point-free cleverness.
- **`functools.cache`** memoises a pure function, with three traps: an unhashable argument (a frame) raises, a method leaks `self` into the cache, and the cache is hidden state the tests then share.
- **Tabular data's declarative form is a dataframe expression**, not a comprehension over extracted columns — see `use-polars`.

## Inject impure dependencies

In a layered application the core takes an ambient effect — environment, clock, randomness — with **no default**, and the driver passes the real thing (see `structure-python`):

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

The stdlib covers composition, immutability and dispatch; each library below earns its place only for the case named.

- **`toolz`** — a sequence helper the stdlib lacks (`partition_all`, `sliding_window`, `groupby` into a dict without pre-sorting); untyped, so never for currying or composition.
- **`plum`** — multiple dispatch on more than one argument's type where `match` on the tuple would not read.
- **`pyrsistent`** — persistent collections with structural sharing for repeated functional updates to large structures; frozen dataclasses remain the record.
- **No `Result` library** (`returns` and the like): `write-python`'s error model is exceptions raised from `error/` and answered in drivers, with `X | None` for a lookup miss.
