# Be object-oriented in Python

The language-agnostic principles are in `SKILL.md`; this is how they land in Python.

## Dataclasses

A stateful object is a `dataclass` with `frozen` left off, the exception to `write-python`'s frozen default:

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

## `Protocol` vs ABC

- **`typing.Protocol`** — the default for an interface.
  ```python
  import typing


  class Reader(typing.Protocol):
      """Anything that can be read as bytes."""

      def read(self) -> bytes:
          """Return the whole content."""
          ...
  ```
- **`abc.ABC` + `@abc.abstractmethod`** — *nominal* typing, enforced at instantiation; only when you own the hierarchy and want shared base code as well as the contract.

## Mixins

A mixin shares behaviour across classes with no common base.
List it **left** of the base, so its methods win in the MRO (Method Resolution Order), keep it to methods over the host's own interface, and give it an empty `__slots__`, or a `slots=True` host silently gains a `__dict__` through it:

```python
import dataclasses
import typing


class OrderedByKeyMixin:
    """Order instances by the key the host defines."""

    __slots__ = ()

    def sort_key(self) -> tuple[int, ...]:
        """Return the key instances are ordered by."""
        raise NotImplementedError

    def __lt__(self, other: typing.Self) -> bool:
        """Order by the key."""
        return self.sort_key() < other.sort_key()


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Version(OrderedByKeyMixin):
    """A release version that sorts by its parts."""

    major: int
    minor: int

    def sort_key(self) -> tuple[int, ...]:
        """Return the major and minor numbers."""
        return (self.major, self.minor)
```

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

A `functools.cache` reader is no **Singleton**: it is hidden state every test then shares.
