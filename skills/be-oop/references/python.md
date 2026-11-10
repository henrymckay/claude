# Be object-oriented in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
Python gives a lot for free — dataclasses, protocols, generators, modules — so most "patterns" are lighter here than in Java or C++.

## Dataclasses

A `dataclass` holds an object's state and generates `__init__`, `__repr__` and `__eq__`; a stateful one is the exception to `write-python`'s frozen default, and says so by leaving `frozen` off:

```python
import dataclasses
import decimal


@dataclasses.dataclass(slots=True, kw_only=True)
class Account:
    """A bank account whose balance changes over time."""

    owner: str
    balance: decimal.Decimal = decimal.Decimal(0)

    def deposit(self, amount: decimal.Decimal) -> None:
        """Add funds to the balance."""
        self.balance += amount
```

Money is `decimal.Decimal`, never `float` (see `write-python`); `slots=True` rejects a stray attribute and saves memory.

## `Protocol` vs ABC

- **`typing.Protocol`** — *structural* typing: any class with the right methods satisfies it, no inheritance needed; the default for an interface.
  ```python
  import typing


  class Reader(typing.Protocol):
      """Anything that can be read as bytes."""

      def read(self) -> bytes: ...
  ```
- **`abc.ABC` + `@abc.abstractmethod`** — *nominal* typing, enforced at instantiation; only when you own the hierarchy and want shared base code as well as the contract.
- **`@typing.override` on every overriding method**, so a renamed base method fails type-checking instead of silently leaving the override unreached.

## Mixins

A mixin shares behaviour across classes with no common base.
List it **left** of the base, so its methods win in the MRO (Method Resolution Order):

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

## Enums

`enum.StrEnum` for a closed set of names that crosses a boundary; a sum type of dataclasses once the variants carry data (see `be-functional/references/python.md`).

## Design patterns

Concrete versions of the collapsed forms in `SKILL.md`:

```python
import collections.abc
import enum
import functools


# Strategy / Command → a function parameter
def process(
    data: list[int], strategy: collections.abc.Callable[[list[int]], int]
) -> int:
    """Apply a pluggable strategy to the data."""
    return strategy(data)


class Environment(enum.StrEnum):
    """Where the client runs."""

    DEV = "dev"
    PROD = "prod"


# Factory → a function over a closed set
def make_client(env: Environment) -> Client:
    """Build the client for an environment."""
    return {Environment.PROD: ProdClient, Environment.DEV: DevClient}[env]()


# Singleton → a cached read of immutable settings, called from the composition root
@functools.cache
def read_settings() -> Settings:
    """Return the settings, read once."""
    return Settings.load()
```

For **Observer**, keep a list of callbacks and call them; for **Visitor**, use `functools.singledispatch` or `match` (see `be-functional`).
For **Adapter**, **Decorator**, **Composite** and **State**, a small class that wraps or holds state is the right tool — those don't collapse into a function.
