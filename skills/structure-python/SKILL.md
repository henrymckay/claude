---
name: structure-python
description: >-
  How to structure a non-trivial Python application — the hexagonal
  (ports-and-adapters) layers of a pure core (domain types, logic, and use cases
  behind ports) and an outer edge (driven adapters for IO, entry-point drivers at
  a composition root), how to declare a port and write an adapter, plus where
  configuration, logging, runtime data assets and the test suite sit. Use when
  organising an app into layers, deciding where a module, entry point, IO
  adapter, data asset or test belongs, designing a port or an adapter's output,
  choosing whether a data file should be CSV or YAML, packaging data through
  importlib.resources, applying dependency injection, or laying out the
  code/data/tests directories — even if the user just says "structure this app",
  "where does this go", or "clean/hexagonal architecture". Layers on
  write-python and be-functional; for building the entry points themselves, see
  write-entry-points; for scaffolding, packaging and tooling, see setup-python.
---

# Structure a Python application

How to organise a non-trivial application — its layers, the boundaries between them, and where each module, adapter and asset belongs.
It sits above `write-python`'s in-code conventions and `be-functional`'s core/shell split; the drivers are built out in `write-entry-points`, and scaffolding and tooling live in `setup-python`.
Three mistakes account for most of what goes wrong: an import that points from the core outward, an adapter that hands on the library's own type instead of yours, and reference data left in code because it looked too small for a file.

**In an existing project, ask first.** Where a repo already has an established layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Code

All the Python lives in a `code/` package under the package root, split into layers; non-code assets sit in `data/` beside it (see [Data](#data)).

```text
mypackage/
  __init__.py
  code/
    __init__.py
    adapt/
    drive/
    operate/
    port/
    transform/
  data/
```

`code/` has two groups — a pure **core** holding the logic and an **edge** doing all the IO — in five standard packages, each a regular package with an `__init__.py` (`data/` is a plain resource tree):

- **`transform`** (core) — the problem's types and rules, and the pure functions over them.
Model data so illegal states can't be built (see `be-functional`); the domain's dataclasses and enums live here, moving to a `domain/` package once they multiply.
- **`port`** (core) — the *behavioural* interfaces the core needs the outside world to satisfy, as `typing.Protocol`s or callable aliases (`Fetch = collections.abc.Callable[[list[str]], polars.DataFrame]`).
A noun naming *what* the core needs, not how; see [Declare a port](#declare-a-port).
- **`operate`** (core) — one function per use case, orchestrating it: calling `transform` for logic and a port for IO, staying pure because the adapter is injected (`operate.report(stations, fetch=...)`).
Imports only `transform` and `port`, with at most one module per use case, each re-exported.
- **`adapt`** (edge) — concrete implementations of the ports, each adapting an outside system to what the core expects (`httpx_.fetch` calls the weather service and returns the `Fetch` frame).
Imports `transform` and `port`, never `operate` or `drive`; see [Write an adapter](#write-an-adapter).
- **`drive`** (edge) — the entry points and composition root: each imports an operation and a concrete adapter and injects one into the other (`operate.report(stations, fetch=httpx_.fetch)`), built out in `write-entry-points`.

Two rules hold it together:

- **IO lives only at the edge.** Network, filesystem, clock, randomness and external services are touched only by `adapt` and `drive`; the core is deterministic and side-effect-free.
Purity is about effects, not dependencies: the core uses computation libraries (`polars`, `numpy`) freely and avoids only the IO frameworks (`httpx`, `typer`, `fastapi`) — even in `polars`, `scan_csv` and `write_*` are edge.
- **Imports point inward.** The edge imports the core and never the reverse; a driver is the one place importing both an operation and an adapter.
Control flows outward through the injected port, so the operation *calls* the adapter without *importing* it (see `be-functional`).

**The names are a standard, not a fixed set.** What places a package is its group: add pure packages beside `transform` as the core grows (`domain`, `pricing`), and edge packages beside `adapt` as the IO grows (an `extract` and a `load`), each obeying its group's rules.

**Errors are a core package of their own, `error/`, importing nothing.** Every layer raises the app's exceptions and every driver catches them, so they can't live in `adapt`, which nothing inward may import.
The `handle` decorator that converts a library's failures into them (see `write-python`) sits in the same package, since its `report` is usually one of the classes beside it.

**Let it grow into the app.** A tiny tool is a module or two at the package root — no `code/`, no `data/`, no layers.
Introduce them once there is a real boundary to name: an external service, a second entry point, a second operation, assets to separate.

**Design the core's shape before the edge's.** A CLI's flags invite a design pass; the core's data shape rarely does, yet every adapter, operation and test is built on it and a second driver inherits it.
Settle it first, deriving it from the data flow (see `be-functional`).

**A module separates what is read separately.** Split a layer when a module would be worth opening on its own, never one module per function: following one call through three dozen-line files, re-exported by an `__init__.py` that exists to undo the split, is the tell.

**Make every member of a package the same kind.** A directory holding `noaa.py` beside `httpx_/` suggests the difference means something when it doesn't, so when one member must become a package, promote its siblings.

**Reach each package through one qualified name.** A package with one cohesive API re-exports it, so callers write `transform.averages(...)` or `port.Fetch`; a package of independent peers (adapters, `typer` modules) is reached module by module, `httpx_.fetch`.

**A re-export shadows its module.** Re-exporting `count` from `transform/count.py` binds `transform.count` to the function, so the module — and its private helpers, for a test — is no longer reachable by that name.
Where that bites, name the module for the shape it holds (`sequence.py` re-exporting `count`), which also keeps it from holding just one function.

### Declare a port

**Where two calls must come from the same place, make the port a `Protocol` and pass the adapter module to satisfy it.**
The test is whether the calls are **tied** — whether the answer to one decides who answers the next: a registry that lists stations and then fetches one of them, a store that reads what it wrote.
Pass `{"noaa": noaa}`, not `Source(list=noaa.list_stations, fetch=other.fetch)` — a record of callables type-checks as a chimera of two sources, where a module cannot be mixed with itself.
`pyright` accepts a module as satisfying a protocol, so nothing needs to be a class or inherit anything.

- **Know the cost.** PyCharm's checker and some others reject a module as a protocol, leaving a warning nothing clears; a port declaring `__call__`, or a callable alias, is satisfied by a plain function in every checker.
- **A shared library is not a tie.** A client answering three unrelated questions is one import and three ports; bundling them forces every test fake to implement all three.
Count the ties, not the imports — one adapter module still satisfies all three ports.
- **A protocol's member name is the contract**, so every adapter spells it the same; put what distinguishes implementations (cost, source) in the module name.

**A port's parameters are the domain's values, not the computation's container.**
A caller should *state* a request — `fetch(stations, *, end, start)` — not assemble one; typing a parameter `polars.DataFrame` makes every adapter and fake speak the frame library.
An axis of the answer, such as a timeframe, belongs as a column of what comes back, not a frame going in.
The tell is a signature that no longer reads as a sentence about the problem.

**Split the port the moment one adapter can only answer half of it.** A source answering any query can't enumerate what it offers; a write-only store can't be read.
Forced to satisfy the whole port, the adapter returns an empty frame, `None` or `NotImplementedError` — a lie that gets consumed, as when an empty catalogue concatenates into the real one and reads as "offers none".
Two ports let the composition root hand each operation only what it needs, and the type checker enforces the difference.

**An open source is a fallback, not a member of the set.** An adapter answering for any input either claims every name before the real sources are asked, or is consulted last anyway.
Make the order explicit: resolve against sources that state their names, and fall back to the open one only where none claimed it — which also makes it the only one able to call a name unknown.

**Route on a name the source states, not a position.** Where the core picks among adapters at runtime, carry the adapter's key in the data; an index into whatever sequence a driver built means nothing outside that call and can't be type-checked.

### Write an adapter

**An adapter declares its output shape and always returns it** — the same columns and types on a full response, an empty one, and absent values alike.
Normalise the library's quirks (`None` for a bad key, columns that vary with row count) once at the boundary, so nothing downstream branches on them; a branch on the upstream's shape past the adapter means it didn't finish its job.

**An absent value is a row; an absent answer is an error.** Nothing found for a query normalises into the declared empty shape.
A source that didn't answer — request failed, document wouldn't parse, file not where it's published — **raises**, because an empty frame says "there are none" and the caller can't tell that from "nobody told me".

**Split getting from making sense of.** Give retrieval and parsing a function each and let the port's function compose them: `return _parse(_get(_url(station)))`.
Retrieval is a few lines that never change; the parse is where the source's quirks accumulate, and kept separate it takes a saved response in a test with no stubbed fetch.

**Declare the columns from the source, not today's caller.** Carry every field the source publishes that the domain has a name for — dropping a column later is one line in the core, widening it means revisiting every adapter and test — but not fields the domain can't name.

**Return the narrowest type callers use.** Returning `httpx.Response` makes that library your internal API: callers reach for `.headers`, and swapping the library touches them all.
Return the text, rows or values, and a test fake becomes a function instead of a mock of someone else's class.

**Close the seam on every library the adapter uses.** A response that arrives and won't parse is the same event to the caller as one that never arrived, so catch the parser's exceptions at the same seam as the client's.
Ask what escapes when the service answers `200` with the wrong content — a login page, an error document — and if the answer names a third-party exception, the seam is open.

**Don't refilter what the core already rejects.** A filter in the adapter that duplicates a core rule is a second home for one judgement, and they drift; the tell is an adapter branch asking whether the filtering column is even present.
Filter at the edge only on what the source states and the value can't show.

**Move pure frame operations into the core.** A frame in, a frame out with no IO belongs in `transform`, whichever adapter first needed it; written generically ("take this column as the key"), it is shared and tested once rather than reimplemented per adapter.
The adapter keeps the *decision* — that this source spells a key its own way is knowledge about the source.
A `try` wrapped round the chain hides the pure part by making the reshape read as IO; lift the handling into a decorator and the frame-in, frame-out steps show.

**Purity misfires on a rendering intermediate.** Columns computed only for a renderer to consume and drop in the same breath are presentation — pure, and still the driver's.
Ask what a second driver would keep: it wants the reshape, not the colour.

**Share one reader per wire format**, with each adapter passing only what differs (columns, header rows to skip).
Wait for the second caller, and count what's really shared — where the library reads the format natively, two adapters may share one line, not worth a module.

**Give a convention several sources share its own edge member**, named for the convention (an identifier scheme, an exchange-code suffix), holding the rule and its table.
The core still mustn't know it exists, and it isn't a source, so it stays out of the mapping of adapters a driver can fetch from.

**Call services you don't own with a timeout and a user agent.** A request with no timeout hangs the program on someone else's outage; a library's default user agent gets refused unevenly by whatever fronts the service, so the same code works on two hosts and 403s on a third.
Identify the tool by name and version; a service that accepts only a browser string is a fact found by trying it, not a default.

**Recognise a publisher's unstated terms**, since all three look like your bug and none appears in a test:

- **A burst is throttled, not refused**: after enough requests the service answers `200` with an HTML page instead of the file.
The tell is a failure that follows the request count; retry the same call after a pause.
- **A rate is stated somewhere you haven't read**: a `Crawl-delay` in `robots.txt`, or a `429` past an API's per-minute cap.
Back off long enough to outlast the window; pace a walk you chose (paging through results) and leave a single requested fetch alone.
- **Some documents need cookies first**: the first request redirects to a consent page whose cookies the second needs.
Give the HTTP module an optional page to visit first, beside the timeout and user agent.

## Configuration

Configuration is input crossing the boundary, so it takes the same path as any IO.

- **Read and validate at the edge** into a typed object, usually a `pydantic-settings` model.
- **Inject inward.** An operation takes the values it needs as arguments, never a global `Settings` or `os.environ` — reading ambient config is IO.
- **Wire it at the composition root**, loaded once at startup and injected beside the adapters (concretely in `write-entry-points`).
- **A value only an adapter needs is read by that adapter** — a user agent, a connection string.
Threading it through the port makes every adapter accept a parameter some ignore; the core stays pure either way, since the rule is that *it* never reaches for ambient state.
- **Secrets take the same path**, from the environment or a secret store, never committed.

## Logging

Logging is output, configured at the edge but carried by convention rather than a port.

- **Configure once, at the composition root** — level, format, a `rich` `RichHandler` — matching the suite's session setup (see `write-tests`).
A library or core module calling `logging.basicConfig` hijacks its host.
- **Emit through `logging.getLogger(__name__)` everywhere**, the core included; with no handler installed a record vanishes, so module loggers don't cost the core its purity.
- **Configuring the root adopts every dependency's narration.** A library logging failures your adapter already handled now writes them to standard error above your one line.
Where that happens, set that library's logger level at the composition root, by name — adopting its records is then a decision.
- **The edge narrates; the core stays quiet.** Log requests, adapter calls and caught errors at the edge; the core returns its results and is pinned by tests.

## Data

Load runtime assets — SQL files, templates, reference tables — through `importlib.resources`, never a path built from `__file__`.
Keep them in one `data/` directory **mirroring the code layers**, so each path names its owner:

```text
mypackage/
  code/
  data/
    adapt/
      orders.sql
    drive/
      report.html
    transform/
      regions.csv
```

- `data/adapt/` holds what an adapter runs or reads about the outside world (queries, where each source publishes).
- `data/drive/` holds templates and static files a driver renders.
- `data/transform/` holds reference data the core computes over — loaded by the edge and passed in, since reading a file is IO.

**Reference data goes in `data/` however small.** A table is read rather than executed, and a file lets someone see all of it, diff one row and correct it without opening a module — and six rows today is thirty next year.

- **Normalise it**: a prefix every row repeats (a base URL) is one value, held once.
- **A translation between your vocabulary and a library's is a table too** — your word against their spelling — so it goes in `data/adapt/`, keeping the library's spelling from leaking into output.
- **A lookup's table is data, including method names it selects.** A name in a file escapes the type checker, so add one test asserting every name in the table resolves.

**Use CSV only for a genuine table, YAML for everything else.** A table has the same fields on every row and enough rows for a header to pay off.
Configuration sets scalars beside collections and nests, which CSV can't hold — the tell is a value that belongs with the data (a shared base URL) ending up in code:

```yaml
base-url: https://data.example.com/stations/
stations:
  LHR: heathrow.csv
  MAN: manchester.csv
```

Load with `yaml.safe_load`; YAML also takes comments, so the reason for a row survives beside it.

**Package data lives inside the package** (`src/mypackage/data/`), since only the package under `src/` ships; a repo-root `data/` beside `src/` and `tests/` is for data deliberately kept out of the wheel.
`hatchling` ships non-`.py` files under the package automatically.
**An app with no runtime assets has no `data/`** — don't scaffold an empty tree.

```python
from importlib import resources

query = resources.files("mypackage").joinpath("data/adapt/orders.sql").read_text()
```

## Tests

Tests live in `tests/`, never beside the source:

```text
tests/
  data/
  pytest_/
    __init__.py
    given.py
    then.py
    when.py
  suite/
    mypackage/
    packages/
```

- **`data/`** — files the tests load; never shipped.
- **`pytest_/`** — imported helpers, a package named for its coupling to `pytest`: fixtures in `given.py`, assertions in `then.py`, named actions in `when.py`; tests import `from pytest_ import then`.
- **`suite/`** — the cases: your code mirrored in `suite/mypackage/`, dependency-behaviour tests in `suite/packages/`.
It is not a package: `--import-mode importlib` collects files by path, so same-named test files in different directories coexist.

`setup-python`'s `pytest` settings serve this layout (`testpaths`, `pythonpath = ["tests"]`, `-p pytest_.given`); scaffold `given.py` up front, since `-p` fails without it.
How to write the tests is `write-tests`.
