# Package layers — each layer in detail

Part of `setup-python`'s package-layers architecture — see `SKILL.md` for the `code`/`data` split, the two rules (IO at the edge, imports inward), and the naming/qualified-access conventions these layers obey. This file walks each layer: what it holds, its module tree, and the specifics.

## transform — the pure core

The types and rules of the problem, plus the pure functions over them, depending on nothing outward.
Model data so illegal states can't be built (see `be-functional`).
Reads as a phrase where it's called: `transform.averages(readings)`.

```text
transform/
  __init__.py
  average.py
```

The domain types that model the problem — dataclasses and enums like a `Reading` or a `Scale` — live here too for a small app; split them into a dedicated `domain/` package (a noun) once they multiply, leaving the pure functions in `transform`. They're the domain's data, so they sit in the core, never in `port`.

## port — the seams

The *behavioural* interfaces the core needs the outside world to satisfy — `typing.Protocol`s or callable type aliases (`Fetch = collections.abc.Callable[[list[str]], dict[str, list[float]]]`).
A port names *what* the core needs, not *how*: `operate` depends on it, `adapt` implements it.
A noun, because it only defines.
Ports are interfaces, not data — the domain's own dataclasses and enums are *not* ports; they belong with the domain (see `transform` above), though a port's signature may reference them.

```text
port/
  __init__.py
  fetch.py
```

## operate — the use cases

The functions that orchestrate a whole task (`operate.report(stations, fetch)`): call `transform` for logic and a `port` for I/O, staying IO-free because the adapter is injected.
Imports `transform` and `port` only.

```text
operate/
  __init__.py
  report.py
```

Each use case is a module, re-exported in `operate/__init__.py` per the package-API rule above, so a driver calls `operate.report(...)`:

```python
from mypackage.code.operate.report import report

__all__ = ["report"]
```

## adapt — the driven adapters

The IO layer: concrete implementations of the ports, each adapting an outside system to what the core expects — `adapt`'s `httpx_.fetch` calls the weather service over HTTP and adapts its JSON response to the `Fetch` port.
Imports `transform`/`port` to conform to them; never imports `operate` or `drive`.
Library-coupled modules take trailing-underscore names.

```text
adapt/
  __init__.py
  httpx_.py
```

When the IO splits into the `extract`/`load` pair above, `load` means *persist to a store* — not on-screen presentation, which is a driver's job and belongs in `drive`.

## drive — the entry points

The driving side and composition root: the entry points (CLI, API, GUI, jobs) that start the program.
A driver imports both an operation and a concrete adapter and injects one into the other:

```python
from mypackage.code import operate
from mypackage.code.adapt import httpx_

operate.report(stations, fetch=httpx_.fetch)
```

The role packages, framework packages, and presentation a driver holds are covered under Entry points in `SKILL.md`.

```text
drive/
  cli/
  rich_/
  typer_/
```
