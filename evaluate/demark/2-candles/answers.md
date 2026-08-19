# Candles answers

What a build working from the brief should arrive at, and the wrong turns to watch for.
Nothing here is stated in the brief: each item is something the skills should produce.

## The shape

A second source, and the first shape the core genuinely owns.

| shape | one row is | how it is reached |
|---|---|---|
| symbols | one symbol | rung 1, unchanged |
| candles | a ticker's candle in one timeframe | fetch each timeframe directly |

**There is no resample step.** `yfinance` serves daily, weekly and monthly, so the adapter returns one long frame already carrying a timeframe column, and Yahoo's own week and month alignment is used rather than a reinvented one.
Deriving coarser candles from dailies is a transform the problem does not need, and it adds a seam that then has to be threaded through every later rung.

**Timeframe is a column, not something the caller stitches together.** The adapter makes one call per interval because the API has no other shape, concatenates them itself, and hands back a single frame.
A `concat` over a comprehension is only the per-group-loop mistake when the groups are computation; here each group is its own network call.

## What should not exist yet

- **Still no `operate/`.** Two adapters and a driver do not make a use case; the driver wiring a fetch to a writer is the whole of it.
- **A `port/` is arguable and not yet earned.** Nothing pure is calling outward — the driver calls the adapter directly and passes plain data on.
Introducing it now is defensible; introducing it *and* an `operate` layer is scaffolding ahead of need.
- **No date range, no filtering, no counts.** The brief asks for candles.

## The adapter boundary

This is where `pandas` meets `polars` and the rung is mostly judged on it.

- Convert at the boundary and never reach back into the original frame.
- The one thing that must happen in `pandas` is dissolving an index `polars` cannot represent — `yfinance` returns a `MultiIndex` on the columns, so a `stack` and a `reset_index` are forced, and everything after them is an expression.
- `polars.from_pandas` needs `pyarrow` for anything beyond plain numpy-backed columns.
- The adapter declares its own output shape and returns it whatever happens, including when the download comes back empty or `None`, so no later code branches on what the library felt like returning.
- `auto_adjust=False` keeps the close split-adjusted but not dividend-adjusted, which is the brief's requirement; `Adj Close` is the dividend-adjusted one and is not what a chart shows.

## Verification

Pin the `yfinance` behaviours the adapter leans on, in a dependency test kept apart from your own and marked slow because it hits the network: the column `MultiIndex` and its level names, that stacking the ticker level yields one row per candle, and that a weekly candle is stamped at the week's start.

## Wrong turns

- **Resampling dailies into weeks and months**, a transform invented for a problem the data source already solves.
- **A call per timeframe stitched together by the caller**, leaving the core to concatenate what the adapter should have returned whole.
- **A leaky adapter**: tidying in `pandas` past what the `MultiIndex` forces, reaching back into the original frame mid-chain, typing the incoming frame as `object` with a `# type: ignore`, or letting the upstream's empty shape reach the core.
- **Reading stdin only when a flag says so.** Taking a path where one is named and standard input otherwise is what makes the two commands compose.
