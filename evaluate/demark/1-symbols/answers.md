# Index symbols answers

What a build working from the brief should arrive at, and the wrong turns to watch for.
Nothing here is stated in the brief: each item is something the skills should produce.

## The shape

One change of shape, so one seam and one pure function.

| shape | one row is | how it is reached |
|---|---|---|
| membership | an index and the symbols it holds | read the packaged dataset |
| symbols | one symbol | keep the ones the named indices list |

The dataset ships with the package, so the adapter reads it in one call and hands the core a plain mapping.
No network, no caching, nothing to inject beyond that mapping.

**A stock's home listing is a judgement the adapter makes.** The dataset gives several Yahoo symbols per stock, one per exchange, and its own bare `symbol` field matches the home one where that listing exists.
Prefer the match, fall back to the first, and keep the rule in the adapter — it is a fact about the data source, not about the domain.

## What should not exist yet

This is why this rung is run first, and it is the easiest thing to get wrong.

- **No `code/` and `data/` split, and no four-package hexagon.** One adapter, one transform and one command is a module or two at the package root.
`structure-python` says to introduce the layers once there is a real boundary to name, and one data source is not one.
- **No `port/`.** A port earns its place when a pure core must call outward without importing the adapter.
With one adapter and one caller, passing the mapping in as an argument *is* the dependency injection.
- **No `operate/`.** A use case that orchestrates a single transform is that transform.
- **No configuration or logging module** beyond what the brief asks for.

Scaffolding the full structure here is not preparing for later rungs, it is the over-engineering `structure-python` names — and it costs the later rungs nothing to introduce a layer at the moment it is earned.

## The entry point

The tool is one command, so the CLI is one command, and it obeys the Unix conventions from the start.

- Symbols to standard output by default, one per line, so it pipes.
- Diagnostics and errors to standard error, so the pipe carries symbols alone.
- A non-zero exit when a name resolves to nothing.
- A `--help` that explains the tool without a README.

An unknown index name is an error the user can act on, not a silent empty result — name the index that failed.

## Verification

The dataset is a dependency whose shape the adapter relies on, so pin what it actually returns in a dependency test kept apart from your own.
The home-listing rule is worth its own cases: a US stock whose bare symbol appears among its listings, and a foreign one where it does not.

## Wrong turns

- **Building the hexagon before there is anything to separate**, covered above.
- **A network call.** `pytickersymbols` ships its data; reaching for HTTP means the adapter was written before the library was read.
- **Returning the dataset's records outward.** The core wants symbols, so the adapter returns symbols — a dict of raw stock records crossing into the core is the library's shape leaking.
- **Silently dropping an unmatched name**, which turns a typo into an empty report much later.
