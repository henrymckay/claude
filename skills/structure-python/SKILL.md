---
name: structure-python
description: >-
  How to structure a non-trivial Python application — the hexagonal
  (ports-and-adapters) layers of a pure core (domain types, logic, and use cases
  behind ports) and an outer edge (driven adapters for IO, entry-point drivers at
  a composition root), plus where runtime data assets and the test suite sit
  alongside the code. Use when organising an app into layers, deciding where a
  module, entry point, IO adapter, data asset, or test belongs, choosing whether
  a data file should be CSV or YAML, packaging data through importlib.resources,
  applying dependency injection, wiring configuration and logging through the
  edge, or laying out the code/data/tests directories — even if the user just
  says "structure this app", "where does this go", or "clean/hexagonal
  architecture". Layers on write-python and be-functional; for building the entry
  points themselves, see write-entry-points; for scaffolding, packaging, and
  tooling, see setup-python.
---

# Structure a Python application

How to organise a non-trivial application's code — the layers, the boundaries between them, and where each module, entry point, and asset belongs.
This is the macro structure that sits above `write-python`'s in-code conventions and `be-functional`'s core/shell split; for building the entry-point drivers, see `write-entry-points`; for scaffolding, packaging, and tooling, see `setup-python`.
Three mistakes account for most of what goes wrong: an import that points from the core outward, an adapter that hands on the outside library's own type instead of yours, and reference data left in code because it looked too small to be worth a file.

**In an existing project, ask first.** Where a repo already has an established layout, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Code

Under `mypackage/`, all the Python lives in a `code/` package, split into layers; the non-code assets sit in a `data/` directory beside it, mirroring those layers (see [Data](#data)).

```text
mypackage/
  __init__.py
  code/
    __init__.py
    adapt/
      __init__.py
    drive/
      __init__.py
    operate/
      __init__.py
    port/
      __init__.py
    transform/
      __init__.py
  data/
```

Structure `code/` as two groups: a pure **core** that holds the logic, and an outer **edge** that does all the IO — the ports-and-adapters (hexagonal) shape.
The five standard packages, each named for what it does (imperative verbs for the behavioural layers per `write-python`; `port`, a package of definitions, stays a noun):

- **`transform`** (core) — the problem's types and rules, and the pure functions over them, depending on nothing outward.
Model data so illegal states can't be built (see `be-functional`); the domain's dataclasses and enums live here too, splitting into a dedicated `domain/` package (a noun) once they multiply — never `port`.
Multiplying types are a prompt to check each still earns its place, not grounds for a package: a set of one-parser-to-one-consumer records is the input grammar modelled as types rather than a domain.
- **`port`** (core) — the *behavioural* interfaces the core needs the outside world to satisfy, as `typing.Protocol`s or callable aliases (`Fetch = collections.abc.Callable[[list[str]], dict[str, list[float]]]`).
A noun that names *what* the core needs, not *how* — `operate` depends on it, `adapt` implements it.
Interfaces, not data, so the domain's own types stay in `transform`; [Declare a port](#declare-a-port) has the shape to give one.
- **`operate`** (core) — the functions that orchestrate a whole task (`operate.report(stations, fetch)`), calling `transform` for logic and a `port` for IO and staying IO-free because the adapter is injected.
Imports `transform` and `port` only, and holds **at most** one module per use case — two commands means at most two modules — each re-exported so a driver calls `operate.report(...)`.
That is a ceiling rather than a quota: a helper two use cases share lives in whichever module it most belongs to, not in a third one of its own.
- **`adapt`** (edge) — concrete implementations of the ports, each adapting an outside system to what the core expects (`httpx_.fetch` calls the weather service over HTTP and adapts its JSON to the `Fetch` port).
Imports `transform`/`port` to conform to them, never `operate` or `drive`; library-coupled code takes a trailing-underscore package name (`httpx_/`), per `write-python`; [Write an adapter](#write-an-adapter) covers what one owes its callers.
- **`drive`** (edge) — the driving side and composition root: the entry points that start the program, each importing an operation and a concrete adapter, injecting the adapter into the operation (`operate.report(stations, fetch=httpx_.fetch)`), built out in `write-entry-points`.

`mypackage/`, `code/`, and every layer under `code/` is a regular package — each carries an `__init__.py` — which is what makes `from mypackage.code import operate` and the `importlib.resources.files("mypackage")` anchor resolve; `data/` is a plain resource tree, not a package.

Two rules hold it together:

- **IO lives only at the edge.** The edge — driven adapters like `adapt`, and the drivers under `drive` — is the only code that touches the outside world: network, filesystem, clock, randomness, external services.
The core (`transform`, `port`, `operate`) stays **pure** — deterministic and side-effect-free.
Purity is about side effects, not dependencies: the core uses third-party *computation* libraries freely (`polars` for dataframes, `numpy`), and only avoids the IO/delivery frameworks (`fastapi`, `httpx`, `uvicorn`, `typer`, `shiny`) whose job *is* IO.
(Even within `polars`, the transforms are core while `scan_csv`/`write_*` are edge.)
- **Imports point inward.** The edge imports the core; the core imports neither the edge nor anything outward.
A driver is the one place that imports both an operation and a concrete adapter, to wire them together.

Control flows the other way: a running operation calls *out* through a port to whichever adapter a driver injected.
Dependency injection is what lets the import arrow point in while control flows out — the operation *calls* the adapter without *importing* it.
That injection is the essential idea (see `be-functional`).

**The names are a standard, not a fixed set.** What fixes a package is which group it's in — set by the two rules — not that it's spelled exactly `transform` or `adapt`.
Add more pure packages beside `transform` as the core grows (a `domain`, a `pricing`), and more edge packages beside `adapt` as the IO grows — an `extract` for input and a `load` for output, say (where `load` means *persist to a store*, not the on-screen presentation a driver owns).
Each new core package obeys the core's rules (no IO; imported, never importing outward); each new edge package obeys the edge's (does its own IO, imports the core, is never imported by it).

**An app's errors are a core package of their own, and so is what raises them.**
The exception classes an app reports are neither a transform nor a domain record: every layer raises them and every driver catches them, so they sit beside `transform` in the core as an `error/` package.
What settles it is that the package imports **nothing** — not the HTTP client, not the frame library — which is exactly why both edges and every entry point can reach it, where a corner of `adapt` could not be imported inward at all.

The decorator converting a library's failures into them goes in that same package, not at the edge (see `write-python`).
Filing it with the adapters that apply it is the instinct, and it costs the arrangement its point: its `report` argument is one of the classes beside it, the two are read together, and moving it outward files the one thing every layer needs under the one layer nothing inward may import.
Name the module for the shape it holds rather than the function it exports, so `error.handle` stays free to be the function.

**Within a package, make every member the same kind.** A directory holding `ark.py` beside `httpx_/` tells a reader nothing by the difference — the shapes do not mark scope, importance or anything else, and the import path is identical either way.
So when one member has to become a package, promote its siblings too.
The payoff is that adding a second module to any of them is a one-file diff rather than a restructure, and `ls` of a layer reads as a list of peers.

**Let it grow into the app.** A tiny tool is a module or two at the package root (`mypackage/transform.py` + `mypackage/drive.py`) — no `code/`/`data/` split; introduce the `code/` wrapper, `data/`, and the layer packages only once there's a real boundary to name — an external service, a second entry point, more than one operation, assets to separate from code.
Don't scaffold the full set for a script (KISS, YAGNI).

**Design the core's shape before the edge's.** An entry point's interface — a CLI's flags, an API's schema — invites a design pass before it's built; the core's data shape rarely does, and it is the one that matters more.
A driver is cheap to replace and serves one presentation, where the core's shape is what every adapter, operation and test is then built on, and a second entry point inherits it wholesale.
So settle the core's shapes first — `be-functional`'s "Derive functions from the data flow" is how to arrive at them.

**A module separates what is read separately — never one module per function.**
A layer's modules exist so a reader can open the part they care about without the rest; where the whole layer is one sitting's reading, that is one module and the package holds nothing else.
The tell is following a single call and opening three files to do it, each holding a dozen lines — the split cost more than it saved, and the `__init__.py` re-exporting them exists only to undo it.
Split when a module would be worth reading on its own, and not before.

**Reach each package through one qualified name.** A package presenting a single cohesive API re-exports it in `__init__.py`, so callers import the package and qualify through it — `transform.averages(...)`, `operate.report(...)`, `port.Fetch` — never a bare `averages` or a stuttering `average.averages`.
A package of independent peers instead keeps them as separate modules you import and qualify directly — an adapter is `httpx_.fetch`, a `typer` module is `argument.stations()`.
Either way you import a *module* and reach its members qualified through it (see `write-python`).

**A re-exported member shadows the module it came from.** Re-exporting `count` out of `transform/count.py` binds the *function* to `transform.count`, so `from mypackage.transform import count` hands back the function and the module becomes unreachable by name — including from a test that wants to reach a private helper, and from a sibling module inside the same package.
That is the trade the re-export makes and it is usually the right one, since callers want the function.
Where it bites, name the module for the *shape* it holds rather than the one function it exports — `sequence.py` re-exporting `count`, `membership.py` re-exporting `symbols` — so the module name stays free.
Those are naming examples, not a target shape: each of those modules holds everything of its kind, and a module that genuinely exports one function is the split the rule above warns against.

### Declare a port

**Where two calls must come from the *same place*, make the port a `Protocol` and let the adapter module satisfy it.**
The test is whether the calls are **tied** — whether the answer to one decides who answers the next.
A source that lists what it offers and then expands one of them is tied, because you ask who claims a name and then ask *that* source for it; a store that reads and writes is tied to the thing it stores.
Declare the pair as a `typing.Protocol` and pass the adapter **module** where one is wanted: `{"ark": ark}`, not `Source(holdings=ark.fetch, names=ark.read)`.

**One library serving several calls is not that test.**
A client answering three unrelated questions — what a symbol costs, what it is, which ones exist — has one import and three ports, because nothing says the three must come from one place and a second source could answer any of them alone.
Bundling them buys nothing and charges for it at every seam: a fake for one call has to implement the other two, so a test that cares about descriptions grows a stub for search.
So count the *ties*, not the imports.
Where they are tied, one protocol; where they merely share a library, a port each — and one adapter module satisfies all of them at once, which is what makes the split free.
A module satisfies a structural protocol in `pyright` exactly as an instance does, extra keyword-only parameters and all, so nothing has to be a class — the `Protocol` is a type declaration and no adapter inherits from it.

Prefer it to a record of callables, which lets a caller build a chimera: `Source(holdings=ark.fetch, names=wedbush.read)` type-checks, and a module cannot be mixed with itself.
Prefer it to an abstract base class too, which buys the contract being checked in the adapter's own file at the price of a stateless class per adapter and a subclass per test fake.

The trade to know: a protocol's method name **is** the contract, so every adapter spells it the same.
That rules out naming implementations for what distinguishes them — no `fetch_holdings` beside `read_holdings` to mark which costs a network call — and it should: callers reach the port precisely because they do not care which one answers, and a contract whose name changes per implementation is not a contract.
Put the distinction in the module name, where `pytickersymbols_` already says the data ships with the package.

**A port's parameters are the domain's own values, not the container the core computes in.**
A port says what the core needs in the domain's words — a sequence of symbols, two dates, the timeframes wanted — so a caller *states* a request rather than assembling one.
Typing a parameter `polars.DataFrame` or `polars.Series` makes the frame library part of the contract every adapter and every fake has to speak, and it charges twice: a test double unpacks a frame before it can answer, and a second driver builds one before it can ask.

The pull toward the frame is real and comes from the right place.
"A value matched against the data element by element is input, not a parameter", and a grouping axis belongs in the frame — but both govern the **computation**, not the request.
A timeframe is an axis of the answer and belongs in a `timeframe` column of what comes back; it is not therefore a frame going in.

The tell is a signature that has stopped reading as a sentence about the problem: `get_candles(symbols, windows)` says nothing about dates, where `get_candles(symbols, *, end, start, timeframes)` *is* the request.
Keeping it that way also settles where a derivation lives: the port carries one pair of bounds for every timeframe asked for, so the fan-out into a request each happens in the adapter, and the pure rule it calls — which day a week begins on — stays in the core.

**Split the port the moment one adapter can only answer half of it.**
Bundling two calls into one protocol is right while every adapter has both to give, and wrong once one of them is *open* — a source answering for anything cannot enumerate what it offers, a write-only store cannot be read, a live feed cannot be replayed.
The forced answer is always an empty frame, a `None` or a `NotImplementedError`, each of them the adapter lying to satisfy a signature.
The lie stops being cosmetic where something *consumes* it: an empty catalogue concatenates into the real one, and the command listing it prints nothing for that source — read as "offers none" rather than "was never that kind of thing".
So make the two calls two ports and let the composition root hand each operation the one it needs, leaving the open adapter a member of one and not the other, which the type checker enforces where a convention would not.

**An open source is a fallback, not another member of the set.**
An adapter answering for *any* input cannot sit in the mapping beside the ones that know their own names: it either claims every name before a real source is consulted, or it is consulted last anyway — and if last, the mapping never decided.
Make the ordering explicit, resolving against the sources that state their names and reaching for the open one only where none claimed it, so the fallback is a step in the operation rather than an entry the lookup is taught to skip.
It splits the failures properly too: only the open source can call a name *unknown*, being the only one asked to try.

**Route on a name the source states, not a position it was given.**
Where the core picks between several adapters at runtime, the key belongs to the adapter — put it in the record and carry it in the data.
A position in whatever sequence the driver happened to build is meaningless away from that one call, so the frame carrying it cannot be logged, cached or tested on its own; and indexing back into the sequence is a lookup no type checker can check, where a missing key at least fails loudly.
It also removes a step: with the name in the record, collecting the catalogue and routing a name back to its source read the same way, and neither has to know how many sources there are.

### Write an adapter

**An adapter declares its own output shape and always returns it** — the same columns and types on a full response, an empty one, and a failure alike.
That is what stops the upstream library's own shape leaking inward: a client that answers `None` on a bad symbol, or a frame whose columns depend on how many rows came back, is normalised *once* at the boundary into the declared empty shape, so nothing downstream ever branches on which of those happened.
Normalising that absence is the one Python-level branch that belongs in an adapter; a branch on the upstream's shape anywhere past it means the adapter did not finish its job.

**The declared shape covers an absent value, not an absent answer.**
A row the upstream had nothing for, a field it left off, a response with no matches — all normalise into the declared shape, because the caller asked a question and got an answer meaning "none".
A source that did not answer at all is a different event: the request failed, the document would not parse, the table was not where it is published.
An adapter **raises** there rather than returning its empty shape, because an empty frame says "there are none" and the caller has no way to tell that apart from "nobody told me" — which is the silent partial result the whole design is meant to prevent.
A core rule that rejects a source's stray matter as well as its unwanted rows is doing its job, not overreaching — say so in its docstring, so the next reader does not add a filter upstream that duplicates it.

**Before an adapter drops a row, check whether the core rule already drops it.**
A publisher's own column saying which rows are cash reads as better evidence than a rule over the value, so filtering on it feels like diligence — but where the core rule rejects the same rows anyway, the filter is a second place one judgement lives, and the two drift the day a publisher renames the column or a range stops carrying it.
The tell is a branch in the adapter asking whether the column is even there: normalising an absent *value* is the adapter's job, but normalising an absent *filter* means the filter was never load-bearing.
Filter in the adapter only where the source states something the value cannot show — a flag beside an otherwise ordinary ticker marking the row an option over the holding rather than the holding — and leave everything the core rule can see for the core rule.

**Split an adapter into getting and making sense of.**
An adapter does two unrelated jobs — reaching the outside world, and turning what came back into the declared shape — so give each its own function and let the port's own function be the composition of them: `return _parse(name, _get(_url(name)))`.
The retrieval is a few lines that never change; the parse is where the source's quirks live and where the work grows, so leaving them fused means the port's function gets longer every time the publisher changes something, and the one line a reader wanted — what this adapter actually returns — sinks under it.

It is also what makes the parse testable on its own.
A saved response goes straight into `_parse` with no stub for the fetch, so the test that pins how a disclaimer row is handled says so directly instead of arriving through an injected client.

**Declare the shape from the source, not from today's caller.**
Which *columns* an adapter returns is a decision made once per source and inherited by every use case after it, so carry the fields the source publishes that the domain has a name for — not the projection the first caller happened to need.
The costs are asymmetric: dropping a column later is one line in the core, where widening means revisiting every adapter and every test that pins their shape.
This is not licence to carry everything: a field the domain cannot name is noise, and the point is to decide against the source rather than against one caller.

**Return the narrowest thing the callers actually use, not the richest thing the library handed you.**
That is about the *type*, not the columns — the two rules do not fight.
An adapter that returns `httpx.Response` has made that library's surface into your internal API: every caller can now reach for `.status_code`, `.headers` or `.json()`, and swapping the library touches all of them instead of the one function that was supposed to contain it.
Return the text, the rows, the values — whatever the callers read — and keep the library's own objects inside the module.
It is also what keeps the test seam cheap: a fake that returns a string is a function, where a fake that returns a `Response` is a mock of somebody else's class.

**An adapter's boundary is every library it uses, not just the remote one.**
The adapter exists so nothing inward depends on `httpx` — and the parser, the client library and the driver behind it are no different.
A response that arrives and will not parse is the same event to the caller as one that never arrived, so wrap both: catch the parser's exception at the same seam as the client's and raise your own.
The tell is easy to miss because the request is what you thought about.
Ask what escapes when the service answers 200 with the wrong content — a login page, an error document, yesterday's format — and if the answer names a third-party exception type, the seam is not closed.

**A pure frame operation belongs in the core, however edge-ish the code around it looks.**
An adapter fetches a document and decodes it — and from the moment it holds a frame it is doing core work.
A frame in, a frame out, no IO: that is `transform`'s, whichever layer happened to notice it was needed, and `adapt` imports it inward like anything else.
Write it generic enough to name without naming the publisher — "take this column as the symbol", "fill a lookup's misses" — and it is shared by every adapter that needs it and covered by the core's own tests.
Leave it in the adapters and three of them grow three versions of one reshape, none of which the core tests.

What stays in the adapter is the *decision*, not the operation: that ARK spells a ticker the Bloomberg way is knowledge about ARK, and moving it inward teaches the core about publishers.

**A `try` wrapped round the chain is what hides the pure part.**
Fusing the read, the reshape and the conversion of the library's failure into one block makes the reshape read as part of the IO, so it is never offered to the core and the next adapter meeting that format writes it again.
Lift the handling into a decorator (see `write-python`) and what is left is one chain whose middle steps are plainly frame in, frame out — at which point moving them inward is obvious rather than a judgement.
That is the decorator's second reason to exist: it is what keeps a parse one chain instead of statements naming an intermediate at every step.
So the adapter chooses which transforms to apply and with what arguments, and the core owns the transforms themselves.

**One reader per wire format, shared by every adapter that meets it.**
A CSV is a CSV whoever published it, so the reading lives once in the layer and each adapter passes only what differs — which columns, how many heading rows to skip.
Left in each adapter it becomes a set of near-copies, and a correction to the read reaches whichever ones you remember.
What is emphatically *not* shared is the shaping: how a ticker becomes a symbol is that publisher's own knowledge and stays put.
Wait for the second caller before extracting, and count what is actually shared — where the library reads the format natively, two adapters may have only the wrapper line in common, and a package holding one three-line function costs more than the duplication.

**A convention several publishers write in stays at the edge, named for the convention rather than for any of them.**
The moment a second source spells something the same way — an exchange code beside a ticker, an identifier scheme, a date format somebody's industry fixed — the shaping stops being one publisher's knowledge without becoming the domain's: the core still must not learn that such a convention exists.
So it earns its own member of the edge layer, named for what it is, holding both the rule and the reference table it reads.
Each adapter then says only that it writes in that convention, which is the one fact about it that is true.

That member is not a source, and the layer's own mapping should not pretend otherwise.
A package of interchangeable adapters names its members so every driver reads the same set (see `write-entry-points`), and what it names is the ones something can be *fetched from* — a shared convention, a shared reader, a settings module and the loader that reads the layer's own `data/` files are all members of the package, and none of them belongs in that mapping.

**An adapter calling a service you do not own states a deadline and identifies itself.**
A request with no timeout hangs the whole program on somebody else's outage, and there is no upper bound on how long that lasts.
A client sending its library's default user agent gets refused by whatever sits in front of the service — and refused *unevenly*, on the host behind a CDN and not the one serving from object storage, so the same code works against two publishers and 403s the third.
Both are one argument.
Neither shows up in a passing test, because the failure is somebody else's configuration on a day you were not looking.
Say who you are by default — a tool name and version is honest and is what a publisher checking its logs wants to see — but know that some services front-ended by a CDN refuse anything that is not a browser string.
That is a fact about one service, found by trying it, not a default to adopt everywhere.

**A publisher also decides how fast and on what terms you may ask, and says none of it in a status code.**
Three refusals arrive looking like your own bug, so recognise them rather than rediscovering them:

- **A burst is throttled, not refused.** Ask for a document too many times in a row and the service starts answering `200` with the *page* instead of the file — the same request that worked eleven times now returns HTML, and nothing in the response says why.
The tell is a failure that follows the request *count* rather than the request, so change one thing: retry the same call after a pause and see whether it comes back.
- **A rate is stated somewhere you have not read.** `robots.txt` may carry a `Crawl-delay`, and an API may cap requests per minute and answer `429` past it — worth retrying, but on a wait long enough to outlast the window rather than the seconds a transient error deserves.
Read the terms before tuning the backoff, or the retry exhausts inside the window it is waiting out.
A stated delay governs a *walk you decided on* — the ten pages an adapter fetches because a ranking is paginated, the file per fund a loop asks for — rather than the one document a person asked for, so pace the walk and leave the single request alone.
Say in the docs which you are doing, since the difference is invisible in the code and the cost of being wrong lands on somebody else's schedule.
- **A document is served only to a caller who already has the cookies.** A first request redirects to a consent or region page and the second, carrying what that page set, gets the file.
So retrieval takes an optional page to *visit first*, and it belongs in the HTTP module beside the timeout and the user agent — not in the adapter, which knows only which page.

None of the three shows up in a test, and all three make the adapter look broken on the day a publisher is busy.

## Configuration

Configuration is **input crossing the boundary**, so it takes the same path as any other IO: read at the edge, validated there, injected inward.

- **Read and validate at the edge.** An adapter reads the source — environment variables, a `.env` file, a settings file — and validates it into a typed object at the boundary, the way a DTO (Data Transfer Object) validates an API body.
A `pydantic-settings` model is the usual tool.
- **Inject inward; the core never reaches out.** An operation takes the values it needs as arguments (a `rate`, a `timeout`), never a global `Settings` object and never `os.environ` — reading ambient config is IO.
This is `be-functional`'s "inject the environment as a default argument" applied to the whole app.
- **Wire it at the composition root.** The driver loads the settings once at startup and injects them into operations beside the adapters — configuration and dependencies enter through the same seam.
The concrete `pydantic-settings` loading lives in `write-entry-points`.
- **A value only an adapter needs is read by that adapter, not threaded through the core.** Injection is for what the *operation* takes; a value the core never sees — the address an HTTP client identifies itself with, a connection string, a region — would otherwise have to enter through the port, which means every adapter behind that port accepts a parameter to satisfy the signature and the ones making no request ignore it.
That is the adapter lying to satisfy a contract, which "Declare a port" already rules out, so read it at the edge module that uses it and keep it out of the port entirely.
The core stays pure either way: the rule it must obey is that *it* never reaches for ambient state, not that no edge module may.
- **Secrets are configuration too** — the same path, from the environment or a secret store, validated at the boundary and never committed (see `use-git`).

## Logging

Logging is **output**, so like all IO it's configured at the edge — but it's pervasive, so it's carried by convention rather than a port.

- **Configure once, at the composition root.** The driver sets up the root logger and its handler at startup — level, format, a `RichHandler`; nothing else touches logging configuration.
A library or core module that calls `logging.basicConfig` hijacks its host, so configuration lives *only* in the driver (see `write-entry-points`), exactly as the suite configures it once per session (see `write-tests`).
- **Emit through a module logger.** Every module — the core included — logs through `logging.getLogger(__name__)`.
A logger is inert until the root configuration decides what to do with a record, so module loggers don't cost the core its purity under test: with no handler installed, a `debug` line simply vanishes.
- **The shell narrates; the core stays quiet.** The edge logs the IO and the boundaries it crosses — a request served, an adapter called, a job run, an error caught.
The core logs sparingly if at all: it *returns* its results, and its behaviour is pinned by tests rather than narrated in logs.
- **`rich`, and lazy.** Render through a `RichHandler` on the root logger, matching `write-tests`' session setup; write log lines with `logging`'s lazy `%` args, never f-strings (see `write-python`).
The concrete driver wiring lives in `write-entry-points`.

## Data

Load the non-code assets an app needs at runtime — SQL query files, HTML templates, static reference data — through `importlib.resources`, never a path built from `__file__` or the repo root.

Keep them all in one `data/` directory whose inside **mirrors the code layers**, so every asset's path names the layer that owns it — `data/` and `code/` are the two parallel trees under the package.
One place to manage, with ownership still explicit — only the layers that own assets need a directory:

```text
mypackage/
  code/
    adapt/
    drive/
    transform/
  data/
    adapt/
      orders.sql
    drive/
      report.html
    transform/
      regions.csv
```

- `data/adapt/` — SQL and other files a driven adapter runs.
- `data/drive/` — templates and static web files a driver renders.
- `data/transform/` — static reference data the core computes over; an edge still *loads* it and passes it in, keeping the core pure (reading a file is IO).

**Reference data goes in `data/` however small it is.**
A table of a URL per publisher, a suffix per exchange code or a rate per band is six rows today and thirty next year, and the size is never what decided it: a table is a table, it is read rather than executed, and a file is where someone can see the whole of it, diff a change to one row, and correct it without opening a module.
So put it in a file whether it is thirty rows or one value.
Normalise it as you would a table anywhere else: a prefix every row repeats — a base URL, a shared directory — is one value, so hold it once and keep the rows to what differs.
Six rows carrying the same sixty characters is six places to edit when the host moves, and the diff hides which part actually changed.

**A translation between your words and a library's is a table too.**
Every example above is a value per row of the domain's own data, so a mapping from your word to a dependency's argument reads as adapter mechanics rather than reference data and stays in a `match` or a dict in the module.
It is the same table: your name against their spelling, one row each, edited when the library changes and by nobody reading the code around it.
Put it in `data/adapt/` with the rest, so the one place the two vocabularies meet is a file somebody can open — and so the library's own spelling has one home rather than being free to leak into an output column.

**Choose the format by the data's shape: CSV only where it is naturally a table, YAML everywhere else.**
A table means every row carries the same fields and there are enough rows for a header to pay for itself — a suffix per exchange code, a rate per band.
Configuration is not that.
It sets a scalar beside a collection, it nests, and it lets one entry carry what another doesn't, none of which CSV has anywhere to put.

The tell that the format was wrong is a value that belongs with the data ending up in code instead.
Factor a shared base URL out of a CSV of paths, as above, and there is now nowhere in the file to put it, so it becomes a function and one publisher's settings are split across two places — where YAML holds both in the single file a reader opens to change either:

```yaml
base-url: https://assets.example.com/fund-documents/
funds:
  ARKF: ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv
  ARKK: ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv
```

A one-row CSV is the same mistake with the header still attached.
YAML also takes comments where CSV cannot, so the reason a row is there survives beside it.
Load with `yaml.safe_load` and build whatever frame the code wants from the result — the file's shape serves the person editing it, not the parser.

Which layer owns the knowledge decides which `data/` directory it sits in, and outside knowledge is the edge's.
Where each publisher serves its file is `data/adapt/`, read by the adapter that fetches them — not `data/transform/`, which would point the core at the outside world to keep the tables together.

Where `data/` sits follows whether the assets ship — the one place its level does *not* follow `tests/`.
Package data must live **inside the package** (`src/mypackage/data/`, as above) to be installed and reachable via `importlib.resources` — not a bare `src/data/`.
`src/` is only a source root: just the package beneath it ships, with the `src/` prefix stripped, so a sibling of the package is neither packaged nor reachable as `mypackage`'s data.
`tests/` can sit at the repo root precisely because it never ships.
Reserve a repo-root `data/` (a sibling of `src/` and `tests/`, mirroring the package the same way) for data that deliberately stays out of the wheel — large datasets, dev seed data.

**An app with no runtime assets has no `data/` at all.** The directory exists to hold files, so leave it out rather than committing an empty tree beside `code/` — a tool that computes over what it fetches and renders the result carries none.
The `code/`/`data/` pair is what the package looks like once both halves have contents, not a shape to scaffold ahead of need.

Reach a packaged asset by navigating from the package, not the filesystem:

```python
from importlib import resources

query = resources.files("mypackage").joinpath("data/adapt/orders.sql").read_text()
```

`hatchling` ships non-`.py` files under the package automatically, so a committed in-package `data/` needs no extra config; add `[tool.hatch.build.targets.wheel]` `artifacts` only for generated or git-ignored files.
All of this is distinct from `tests/data/` — test fixtures that never ship (see [Tests](#tests)).

## Tests

Tests live in `tests/`, never beside the source, split three ways:

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

- **`data/`** — data files the tests load.
- **`pytest_/`** — the imported helpers, as a package (`__init__.py`): fixtures in `given.py`, custom assertions in `then.py`, and action helpers in `when.py` where actions earn a name.
It's named `pytest_` (per `write-python`'s underscore rule) because it's all `pytest`-coupled — fixtures, and assertions written as bare `assert`s rather than `unittest`'s methods.
Tests import it as `from pytest_ import then`.
- **`suite/`** — the test cases: your code mirrored in `suite/<package>/`, and dependency-behaviour tests in `suite/packages/`.
Neither `suite/` nor its subdirectories is a package — `--import-mode importlib` (below) collects the test files by path with no `__init__.py`; only `pytest_/` needs one, because it's *imported* rather than collected.
Keep the test dirs non-packages: it's `pytest`'s recommendation for new projects, and path-based collection lets same-named test files in different directories coexist without clashing.

The `pytest` settings in `setup-python`'s `pyproject.toml` serve this layout:

- `testpaths = ["tests/suite"]` collects only the cases.
- `--import-mode importlib` avoids `sys.path` clashes from the `src/` layout and nested folders.
- `pythonpath = ["tests"]` with `-p pytest_.given` makes `pytest_` importable and loads its fixtures.
- `src = ["src", "tests"]` marks `tests/` a source root so isort files `pytest_` as first-party.

Scaffold `tests/pytest_/given.py` (with its `__init__.py`) up front — `-p pytest_.given` fails to load if the module is missing.

That is the *scaffold*; the `write-tests` skill covers how to write the tests themselves — the given/when/then shape, naming, fixtures, and the rest.
