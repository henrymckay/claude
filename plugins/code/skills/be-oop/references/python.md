# Be object-oriented in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.
Most "patterns" are lighter here than in Java or C++, so the collapsed forms below are the usual ones.

## Dataclasses

A `dataclass` holds an object's state; a stateful one is the exception to `write-python`'s frozen default, and says so by leaving `frozen` off:

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

- **`typing.Protocol`** — the default for an interface; its method stubs carry docstrings, since they are the contract.
  ```python
  import typing


  class Reader(typing.Protocol):
      """Anything that can be read as bytes."""

      def read(self) -> bytes:
          """Return the whole content."""
          ...
  ```
- **`abc.ABC` + `@abc.abstractmethod`** — *nominal* typing, enforced at instantiation; only when you own the hierarchy and want shared base code as well as the contract.
- **`@typing.override` on every overriding method**, as `write-python` requires.

## Mixins

A mixin shares behaviour across classes with no common base.
List it **left** of the base, so its methods win in the MRO (Method Resolution Order), and keep it to methods over the host's own interface, since a slotted host has no `__dict__` for a mixin to read:

```python
class OrderedByKeyMixin:
    """Order instances by the key the host defines."""

    def sort_key(self) -> tuple[int, ...]:
        """Return the key instances are ordered by."""
        ...

    def __lt__(self, other: typing.Self) -> bool:
        """Order by the key."""
        return self.sort_key() < other.sort_key()


class Version(OrderedByKeyMixin):
    """A release version that sorts by its parts."""

    ...
```

## Enums

`enum.StrEnum` for a closed set of names that crosses a boundary; a sum type of dataclasses once the variants carry data (see `be-functional/references/python.md`).

## Design patterns

Concrete versions of the collapsed forms in `SKILL.md`:

```python
import collections.abc
import enum


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
```

A **Singleton** is a module, or a value the composition root reads once and passes down (see `structure-python`); a cached reader is hidden state every test then shares.

For **Observer**, keep a list of callbacks and call them; for **Visitor**, use `functools.singledispatch` or `match` (see `be-functional`).
For **Adapter**, **Decorator**, **Composite** and **State**, a small class that wraps or holds state is the right tool — those don't collapse into a function.
