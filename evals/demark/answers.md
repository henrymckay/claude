# demark — the answers

What a build working from the brief should arrive at, and the wrong turns to
watch for. Nothing here is stated in the brief: each item is something the
skills should produce.

## The shape of the core

Four shapes, three seams. Each seam is a change of entity or grain, or a point
where a new independent input enters — so each is one function.

| shape | one row is | how it is reached |
|---|---|---|
| candles | a ticker's candle in one timeframe | fetched at each timeframe, with high and low |
| counts | one count on that candle | count the runs and the countdowns |
| aligned | a ticker, day, timeframe and count | map each candle's counts onto the days it covers |
| wide | a ticker on a day | `pivot` timeframe and count kind out together |

**There is no resample step.** `yfinance` serves daily, weekly and monthly
directly, so the adapter returns one long frame already carrying a timeframe
column, and Yahoo's own week and month alignment is used rather than a
reinvented one. Deriving coarser candles from dailies is a transform the
problem does not need, and inventing it adds a seam that then has to be threaded
through everything downstream.

Filtering is **not** a fifth seam: it drops rows without changing what a row
is. It earns its own function because it is independently useful, not because
the flow demands one — and it comes last, since bounds are set on count
columns that only exist once the frame is wide.

**The middle function is the heart of it.** Given a long frame of candles — one
row per candle, covering every ticker and every timeframe at once — return a
long frame of counts, one per candle. It is expressible entirely in column and
window functions, and it needs nothing but its input.

There are **three** axes — ticker, timeframe, and which count (setup,
sequential, combo) — and all three are **columns**, never arguments. Where each
arrived from (a fetch, a flag, the problem statement) is irrelevant to how it is
modelled, and a loop over any of them is the same mistake.

Setup and the two countdowns share a shape: a condition per candle, then a run
or a tally over it. Write one counting function parameterised by the condition
column rather than three near-copies.

**Signed counts remove the direction column.** Sell positive, buy negative on
one continuum, so the sign carries the direction and the magnitude carries the
position in the count. The filter then needs no notion of direction, and
`Direction` survives only as a rendering concern — if it survives at all.

## The units

**Adapters** — the only code touching the outside world:

- Expand an index name or pattern to its constituent symbols (`pytickersymbols`).
- Fetch candles for symbols, over a date range, at each requested timeframe
  (`yfinance`). Timeframe is a column of the frame it returns, not something the
  caller stitches together from a call per timeframe.

**Transforms** — pure, dataframe in and dataframe out:

- Count: candles to counts, as above.
- Widen: `pivot` the timeframe column out to one column per timeframe, giving
  one row per ticker and date.
- Filter: keep rows where a named column meets a lower bound, an upper bound,
  or an equality. Generic over columns — it knows nothing about setups, and the
  date is just another column it bounds.

**Commands** — one per independently useful stage, over a shared tabular
format so they compose in a pipeline, plus a path that runs the lot in one call
for the common case.

## What earns a type

`Timeframe` and the count kind: both are values that appear *in the data*, so
they turn up across counting, widening and rendering. Plus one error class.
Direction is the sign of a count, not a type.

Nothing else. A record built by the parser at one site and destructured by one
consumer at the next is that function's arguments wearing a name — parse each
input phrasing straight to the value the core needs (a tuple of symbols, a
pair of bounds, a predicate) and the types disappear with it.

## Candles as a chart shows them

Chart semantics: every past candle is complete, and only the newest is in
progress. Fetching each timeframe directly gives exactly this — Yahoo's latest
weekly bar *is* the in-progress one, and every earlier bar is closed.

**Nothing is reconstructed as of a past date.** There is no "the weekly candle
as it stood last Wednesday", so there is no per-date rebuild, and none of the
machinery that would be needed to make one fast. A previous run of this brief
spent its whole core design on that machinery, for a requirement nobody wanted:
worth checking what a stated requirement is actually for before building around
it.

The one real seam here is alignment: a weekly count attaches to a weekly
candle, and has to be spread across the days that candle covers before it can
sit beside a daily count on the same row. That is a containment join, nothing
more.

## The date bound does double duty

The date is a filter on the final frame, but it also decides how much history
to fetch — and the count needs a warm-up run of candles before the earliest date
asked about, or the first counts come out wrong.
So the edge derives a fetch window from the same bounds the core later filters
on. Deriving that window is the driver's job, not the filter's: the filter stays
generic over columns and knows nothing about warm-up.

## Wrong turns

Each of these is a real failure from a previous run of this brief.

- **Looping over timeframes.** `concat([count(prices, tf) for tf in timeframes])`
  is a per-group Python loop, one level up from looping over rows.
- **Optimising before there is a correct simple version.** Anticipating that
  rebuilding weekly candles per as-of date is slow, and inventing a
  carry-the-state-forward trick that then dictates the function's signature.
  An optimisation that changes what a function takes has leaked into the
  interface.
- **Fusing the seams.** One function doing resample, count and align satisfies
  "prices in, counts out" while hiding every seam inside itself. Fixing the
  endpoints does not constrain the middle.
- **Hand-rolling `pivot`.** A `reduce` over per-timeframe joins is `pivot`
  spelled out the long way.
- **A filter DSL.** Building a condition/clause/operator AST over domain
  concepts, where the requirement is bounds on a named column.
- **Dates as their own type hierarchy.** A latest/on/span sum type, when a date
  is a column like any other and "latest" is a default bound of today.
- **Modelling the input grammar as types.** A dataclass per accepted phrasing
  of a target, a date and a filter — "make illegal states unrepresentable"
  aimed at CLI syntax rather than at core values.
- **One command with an option per stage**, so the index expansion and the
  filter are reachable only by running the whole pipeline.
- **Filtering the dates before counting.** Cutting to the requested days early
  starves the run counter of the history it needs; the bound selects rows at
  the end and sizes the fetch at the start, and does nothing in between.
- **A direction column beside the count.** It doubles the columns to pivot and
  forces the filter to understand setups; the sign of a signed count already
  says it.
- **Three counting functions.** Setup, sequential and combo differ in their
  per-candle condition, not in how a run is counted.
- **Resampling dailies into weeks and months.** A transform invented for a
  problem the data source already solves, which then has to be threaded
  through every function downstream.
- **A leaky adapter.** Tidying in `pandas` before converting, reaching back
  into the original frame for a column name mid-chain, typing the incoming
  frame as `object` with a `# type: ignore`, and branching in Python on the
  shape the upstream library happened to return.

## Verification

The count is fiddly and easy to get subtly wrong, so pin it against a
brute-force reference that rebuilds each series from scratch per date — slow,
obviously correct, and used only in the tests. Property tests over the
invariants (a run only ever increments or resets; buy and sell are never both
active) are worth more here than more examples.
