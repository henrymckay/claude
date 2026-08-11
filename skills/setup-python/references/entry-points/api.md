# API entry point — `fastapi` + `pydantic`

Part of `setup-python`'s Entry points — see `SKILL.md` for the shared role/framework pattern, `[project.scripts]` naming, and the core architecture.

`fastapi` for an HTTP API (see Reach-for libraries in `SKILL.md`), served with `uvicorn` and its models built on `pydantic`. Under `code/drive/`, a hollow `api/` role package re-exports the app and launcher, over two framework packages — `fastapi_/` for the routing and `pydantic_/` for the schemas — the way the CLI splits `typer_/` and `rich_/`:

```text
api/
  __init__.py   role, hollow: re-exports app and run
fastapi_/
  __init__.py   app = fastapi.FastAPI(); includes the router; run() launcher
  depend.py     factories returning a fastapi.Depends marker
  provide.py    the providers Depends calls — names the concrete adapter
  query.py      functions returning a configured fastapi.Query
  route.py      the path operations that call the core
pydantic_/
  __init__.py
  schema.py     the request/response models (BaseModel DTOs)
```

`schema.py` holds the boundary DTOs — the `pydantic.BaseModel`s FastAPI validates and serialises (a `Reading` with `station: str` and `average: float`). These are pydantic-coupled, so they live in a `pydantic_` package, not `fastapi_` — the `fastapi_` (routing) / `pydantic_` (data schemas) split parallels the CLI's `typer_` (parsing) / `rich_` (presentation); the schema *is* the API's presentation.

A DTO is **not** a domain type, even when their fields match. The schema is the external **contract**; the domain model is the internal truth; keep them separate so they evolve independently (API versioning vs domain logic) and untrusted input is validated at the boundary. Map between them in `route.py`, as `schema.Reading(...)` does below. Neither belongs in `port/`, which is protocols only; the domain types live in `transform`/`domain`.

Pydantic is best used at exactly this kind of **trust boundary** — validating and (de)serialising data as it crosses in or out: API bodies here, `pydantic-settings` for config from the environment, or parsing an external response inside an adapter. It's a data library, not an IO framework, so it's *allowed* in the pure core too — but there the data is already validated, so a plain frozen `dataclasses.dataclass` is the lighter default; reach for pydantic in the core only when you specifically want its validation or serialisation there. Enums are the one thing you never duplicate: pydantic accepts a stdlib `enum.Enum`, so a domain `Scale` is imported and referenced straight in a schema field; only a genuinely API-only enum (a sort order) lives in the driver.

**A model shared across layers moves inward, to the core.** `pydantic_` here holds *only* the API's own schemas. Because `adapt` never imports `drive`, the two edges can't share a boundary model — so a pydantic model you find yourself wanting in *both* `adapt` and `drive` isn't a boundary DTO, it's a **domain model**: put it in `transform`/`domain`, which both edges import inward (pydantic is fine there). Each boundary DTO otherwise stays with its own edge — the API's schemas in `drive/pydantic_`, an external service's shape in the `adapt` module that parses it — never hoisted into one shared edge package.

**FastAPI declares parameters exactly as Typer does** — the same author built both, and both read `typing.Annotated[T, marker()]`, the marker carrying the framework metadata. Typer's `Argument`/`Option` are FastAPI's `Query`, `Path`, `Body`, `Header` and `Depends`. So `fastapi_` mirrors `typer_`'s structure: where `typer_` splits factory functions across `argument.py` and `option.py`, `fastapi_` has **a module per request marker** — `query.py`, plus `path.py`/`body.py`/`header.py` as those markers are used — each holding functions that return a configured marker, one per parameter (`query.stations()`, read as `category.member`). `fastapi.Query` alone takes many arguments (validation, docs, deprecation), and an app has many query parameters, so `query.py` earns its place exactly as `argument.py` does.

```python
import fastapi


def stations() -> fastapi.params.Query:
    """The stations query parameter."""
    return fastapi.Query(description="Station IDs.")
```

`Depends` is the exception — not request-parameter config but **dependency injection** — and it needs *two* functions, which split by coupling. `depend.py` holds the marker factory (FastAPI-coupled, like `query.py`); `provide.py` holds the **provider** it wraps — the function that names the concrete adapter. `Depends(fn)` **calls `fn` and injects its return value**, so the provider *returns* the adapter — the factory passes the provider, `Depends(provide.fetch)`, never `Depends(httpx_.fetch)`, which would make FastAPI call the adapter itself as a dependency and parse its arguments as request inputs:

```python
import fastapi

from mypackage.code.drive.fastapi_ import provide


def fetch() -> fastapi.params.Depends:
    """Inject the temperature source."""
    return fastapi.Depends(provide.fetch)
```

`provide.py` is the **injection seam** — the driver's place for naming a concrete adapter. It imports no FastAPI (its signature is `-> port.Fetch`, its body returns `httpx_.fetch`); it lives inside `fastapi_` only because FastAPI is the sole caller — lift it to a shared `drive/provide.py` if a second driver ever needs the same wiring.

```python
from mypackage.code import port
from mypackage.code.adapt import httpx_


def fetch() -> port.Fetch:
    """Provide the temperature source adapter; overridden in tests."""
    return httpx_.fetch
```

Naming `httpx_` in `provide.py` doesn't leak it into the core: it's part of the driver — the **composition root** — so naming the one concrete adapter is its job. The invariant that holds is that `operate` imports only `port`; and even here the signature depends on the abstraction `port.Fetch` while only the body names `httpx_`.

`route.py`'s endpoints then receive the injected adapter as a parameter (where the CLI's `command.py` passes it by hand) and shape the core's result into the response models:

```python
import typing

import fastapi

from mypackage.code import operate, port
from mypackage.code.drive.fastapi_ import depend, query
from mypackage.code.drive.pydantic_ import schema

router = fastapi.APIRouter()


@router.get("/report")
def report(
    stations: typing.Annotated[list[str], query.stations()],
    fetch: typing.Annotated[port.Fetch, depend.fetch()],
) -> list[schema.Reading]:
    """Report the average temperature for each station."""
    averages = operate.report(stations, fetch=fetch)
    return [
        schema.Reading(station=station, average=average)
        for station, average in averages.items()
    ]
```

`fastapi_/__init__.py` builds the app, includes the router, and adds the launcher — an ASGI app isn't callable to start a server, so `run()` calls `uvicorn.run(app)`; `api/__init__.py` re-exports `app` and `run`:

```python
import fastapi
import uvicorn

from mypackage.code.drive.fastapi_ import route

app = fastapi.FastAPI()
app.include_router(route.router)


def run() -> None:
    """Launch the API server."""
    uvicorn.run(app)
```

Launch with `mypackage-api = "mypackage.code.drive.api:run"`, or serve directly with `uvicorn mypackage.code.drive.api:app`.
Because the adapter arrives through `Depends`, a test swaps it for a fake by overriding the provider — `app.dependency_overrides[provide.fetch] = lambda: fake_fetch` — the FastAPI-native seam, no patching.
