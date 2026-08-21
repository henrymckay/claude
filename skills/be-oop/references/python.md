# Be object-oriented in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
The theme: Python gives you a lot for free (dataclasses, protocols, generators, modules), so most "patterns" are lighter here than in Java/C++.
Follow the `write-python` conventions in examples (qualified imports, annotate every function, docstrings).

## Dataclasses

Use `dataclasses` for objects that hold state — they generate `__init__`, `__repr__`, `__eq__`, and (with `order=True`) comparisons:

```python
import dataclasses


@dataclasses.dataclass
class Account:
    """A bank account."""

    owner: str
    balance: float = 0.0

    def deposit(self, amount: float) -> None:
        """Add funds to the balance."""
        self.balance += amount
```

Use `frozen=True` for immutable value objects and `slots=True` to save memory and reject stray attributes.

## `Protocol` vs ABC

- **`typing.Protocol`** — *structural* typing: any class with the right methods satisfies it, no inheritance needed.
Prefer this for interfaces (interface segregation and dependency inversion) — it's duck typing the type checker understands.
  ```python
  import typing


  class Reader(typing.Protocol):
      """Anything that can be read as bytes."""

      def read(self) -> bytes: ...
  ```
- **`abc.ABC` + `@abc.abstractmethod`** — *nominal* typing: subclasses must inherit and implement, enforced at instantiation.
Use when you own a hierarchy and want shared base code plus enforcement.

## Properties

Don't write Java-style getters/setters.
Expose a plain attribute, and upgrade to a `@property` only when you need computation or validation:

```python
import math


class Circle:
    """A circle."""

    def __init__(self, radius: float) -> None:
        """Create a circle of the given radius."""
        self.radius = radius

    @property
    def area(self) -> float:
        """Area, computed on access."""
        return math.pi * self.radius**2
```

## Constructors and namespacing

- **`@classmethod`** for alternative constructors (`Account.from_json(...)`).
- **`@staticmethod`** for a function that lives in the class's namespace but needs no instance — though a module-level function is often simpler.

## Dunder methods

Implement the protocols the language uses: `__repr__` (dataclasses give you this), `__eq__`/`__hash__`, `__iter__`/`__next__` for iteration, `__enter__`/`__exit__` for context managers (or `contextlib.contextmanager`), `__call__` to make an instance callable.

## Mixins

A mixin is a plain class inherited for one focused capability, listed **left** of the base so its methods take precedence in the method-resolution order:

```python
class AsDictMixin:
    """Add a dict view of an object's public attributes."""

    def as_dict(self) -> dict[str, object]:
        """Return the public attributes as a dict."""
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}


class Widget(AsDictMixin):
    """A widget that can render itself as a dict."""

    ...
```

Keep a mixin behaviour-only and stateless (no `__init__`) so several combine cleanly.

## Enums

`enum.Enum` for a closed set of named constants — a sum type (see `be-functional`, "Algebraic data types and pattern matching").

## Design patterns

Concrete versions of the simpler forms listed in `SKILL.md`:

```python
import functools
import typing


# Strategy / Command → a function parameter
def process(data: list[int], strategy: typing.Callable[[list[int]], int]) -> int:
    """Apply a pluggable strategy to the data."""
    return strategy(data)


# Factory → a function
def make_client(env: str) -> Client:
    """Build the client for an environment."""
    return {"prod": ProdClient, "dev": DevClient}[env]()


# Singleton → a module (imported once), or a cached factory
@functools.cache
def get_settings() -> Settings:
    """Return the single, lazily-built settings object."""
    return Settings.load()
```

For **Observer**, keep a list of callbacks and call them; for **Visitor**, use `functools.singledispatch` or `match` (see `be-functional`).
For **Adapter** / **Decorator** / **Composite** / **State**, a small class that wraps or holds state is the right tool — those don't collapse into a function.
