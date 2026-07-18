# Functional Python idioms

Concrete ways to apply the `be-functional` principles in Python.
Python isn't a pure functional language, so aim for *pragmatic* functional: pure logic, immutable data, and comprehensions/generators over manual loops — without fighting the language.

## Immutability

- **Tuples** and **`frozenset`** instead of lists/sets when the data shouldn't change.
- **Frozen dataclasses** for immutable records:
  ```python
  import dataclasses

  @dataclasses.dataclass(frozen=True, slots=True)
  class Point:
      """An immutable 2-D point."""

      x: int
      y: int

  p2 = dataclasses.replace(p, x=10)   # new value, original untouched
  ```
- **`typing.NamedTuple`** for lightweight immutable tuples with names.
- Don't mutate arguments.
  Return a new structure instead of editing in place (`sorted(xs)` not `xs.sort()`; comprehension not `for … .append()`).
- **Immutable dict updates** with `toolz`: `assoc`/`dissoc` (add/remove a key), `update_in`/`get_in` (nested update/lookup), `valmap`/`keymap`/`valfilter` (map or filter a dict) — each returns a **new** dict instead of mutating.

## Algebraic data types & pattern matching

Model *product* types with frozen dataclasses (above) and *sum* types with a union of variant classes (or an `enum.Enum` for a simple closed set), then destructure with `match`:

```python
import dataclasses
import math

@dataclasses.dataclass(frozen=True)
class Circle:
    """A circle, by radius."""
    radius: float

@dataclasses.dataclass(frozen=True)
class Square:
    """A square, by side length."""
    side: float

Shape = Circle | Square   # sum type: a shape is exactly one variant

def area(shape: Shape) -> float:
    """Return a shape's area."""
    match shape:
        case Circle(radius=r):
            return math.pi * r**2
        case Square(side=s):
            return s * s
```

`match` makes each case explicit, and a type checker can flag an unhandled variant when the union grows — prefer it to `isinstance` ladders.

**`match` vs `functools.singledispatch`** — both dispatch on type, so choose by who owns the cases.
Use `match` for a **closed** set of variants you own (you get exhaustiveness checking); use `singledispatch` when the operation should stay **open** to new types that register their own handler from elsewhere, without editing the function.
And for plain boolean conditions, a simple `if/elif` still wins over both.
For dispatch on **more than one argument's type**, the stdlib has nothing — reach for **`plum`** (annotation-driven multiple dispatch, well-typed and maintained; `multipledispatch` is a simpler older alternative), and only when `singledispatch`/`match` genuinely can't express it.

## Transformations over loops

- **Comprehensions** for map/filter in one readable expression:
  ```python
  names = [u.name for u in users if u.active]
  ```
- **Generator expressions** for lazy pipelines over large/streamed data — they don't materialize the whole sequence:
  ```python
  total = sum(x * x for x in numbers)
  ```
- Prefer comprehensions to `map`/`filter` with a `lambda` (usually clearer); `map(f, xs)` is fine when `f` is already a named function.

## functools & itertools

- **`functools.reduce`** for genuine folds, but reach for a comprehension or `sum`/`math.prod`/`any`/`all` first — they're clearer.
- **`functools.partial`** to specialize a function without a wrapper.
- **`functools.lru_cache` / `cache`** to memoize pure functions.
- **`functools.singledispatch`** for type-based dispatch instead of `if/elif`.
- **`itertools`**: `chain`, `groupby`, `accumulate`, `takewhile`/`dropwhile`, `islice`, `product`, `starmap` — composable building blocks for iterators.
- **`operator`** module (`operator.attrgetter`, `itemgetter`, `add`) gives named functions where you'd otherwise write a `lambda`.

## Composition & currying

Write **generic** functions and derive specific variants by currying or composing them, rather than hand-writing each variant.
`toolz` provides both cleanly — use it rather than rolling your own:

- **`toolz.curry`** — bind arguments to produce a new, more specific function.
  Prefer it to `functools.partial`: it auto-curries, works as a decorator, and composes cleanly (`partial` is fine when you want zero dependencies).
- **`toolz.compose`** / **`toolz.compose_left`** — chain functions into a new one (right-to-left, or left-to-right for readability).
- **`toolz.pipe(data, f, g, h)`** — thread a value through functions left-to-right; the most readable one-off pipeline.

```python
import toolz

@toolz.curry
def get_many(source: Source, n: int) -> list[Item]:
    """Fetch n items from a source."""
    ...

def take_one(items: list[Item]) -> Item:
    """Return the first item."""
    return items[0]

get_pair = get_many(n=2)                            # curry: bind an argument
get_one = toolz.compose(take_one, get_many(n=1))    # compose: chain steps
```

Keep compositions shallow enough to stay readable — the aim is expressive, reusable building blocks, not point-free cleverness for its own sake.

Other high-value `toolz` helpers: **`groupby(key, seq)`** (group into a dict of lists — no pre-sorting, unlike `itertools.groupby`), **`juxt(f, g)(x)`** → `(f(x), g(x))`, and **`do(effect, x)`** to run a side-effect mid-pipeline and return `x` unchanged.

## Pure core, effectful shell

Keep functions that compute/transform free of I/O; do the reading and writing at the call site:

```python
def summarize(rows: list[Row]) -> Summary:   # pure — easy to test
    """Reduce rows to a summary."""
    ...

def main() -> None:                           # shell — does the I/O
    """Load, summarize, and print the report."""
    rows = load(path)
    print(render(summarize(rows)))
```

## Injecting impure dependencies

Take impure inputs — environment, clock, randomness, handles — as arguments whose default is the real thing.
Deterministic and pure under test (pass explicit values), convenient in normal use (rely on the default):

```python
import collections.abc
import os

def build_config(env: collections.abc.Mapping[str, str] = os.environ) -> Config:
    """Build config, reading settings from the environment."""
    return Config(debug=env.get("DEBUG") == "1")
```

Tests call `build_config({"DEBUG": "1"})`; normal callers pass nothing.
(`os.environ` is a live mapping, so binding it once as the default still reflects the current environment.)

For a value that must be *re-read* each call — the clock, a fresh random — default to `None` and resolve inside, which also sidesteps the mutable-default trap:

```python
import datetime

def stamp(now: datetime.datetime | None = None) -> str:
    """Return an ISO-8601 timestamp, defaulting to the current UTC time."""
    now = now or datetime.datetime.now(datetime.UTC)
    return now.isoformat()
```

## Errors, functionally

For expected "no result" cases prefer returning `X | None` (or a small result type) over raising, and make it explicit in the signature.
Reserve exceptions for genuinely exceptional conditions.
If you want richer functional error handling (Result/Either types), the `returns` library provides it — but only adopt it if it genuinely earns its place; plain `X | None` covers most cases.

## Libraries

- **`toolz`** — curated functional helpers; the go-to for currying and composition (see above), plus `pipe`, `groupby`, `merge`, etc.
- **`cytoolz`** — a C reimplementation of `toolz`, near drop-in, much faster on hot paths.
- **`funcy`** — an alternative functional-utils library; a peer to `toolz`, not a replacement — pick whichever API you prefer.
- **`returns`** — Result/Maybe/IO containers for a stricter functional style.
- **`plum`** — multiple dispatch (on several argument types) via type annotations, for when `functools.singledispatch` isn't enough.
- **`pyrsistent`** — persistent immutable collections (especially an immutable map) with efficient structural-sharing updates; reach for it when you update collections repeatedly in a functional style.
  Prefer frozen dataclasses for typed records — they integrate better with pyright.

Beyond these, stdlib comprehensions + `functools`/`itertools` handle most cases; reach for a library when it genuinely simplifies things.
