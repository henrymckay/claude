# Report answers

What a build working from the brief should arrive at, and the wrong turns to watch for.
Nothing here is stated in the brief: each item is something the skills should produce.

## The shape

Two more shapes, and both are core.

| shape | one row is | how it is reached |
|---|---|---|
| counts | one count on a candle | rung 3, unchanged |
| aligned | a ticker, day, timeframe and count | map each candle's counts onto the days it covers |
| wide | a ticker on a day | `pivot` timeframe and count kind out together |

**Widening is not presentation.** A pivot changes what a row represents, and a change of grain is a seam, so it belongs to a transform even though a table is what made you want it.
Presentation starts where the result stops being data and becomes a `Table`.
The test is what a second entry point would do: an API serving the same report wants the same pivot and a completely different renderer.

**Alignment is a containment join, nothing more.** A weekly count attaches to a weekly candle and has to be spread across the days that candle covers before it can sit beside a daily count on the same row.
Nothing is reconstructed as of a past date — there is no "the weekly candle as it stood last Wednesday", so there is no per-date rebuild and none of the machinery that would make one fast.
A previous run spent its whole core design on that machinery, for a requirement nobody wanted.

**Filtering is not a seam.** It drops rows without changing what a row is.
It earns its own function by being independently useful, not because the flow demands one, and it comes last, since the bounds are set on columns that only exist once the frame is wide.

## The filter is generic over columns

One function, bounding a named column, knowing nothing about setups — and the date is just another column it bounds.
Two mechanisms for the same operation, a date bounded by its own parameters beside a general filter for everything else, means the general one was not general enough.

The option surface is the driver's problem, not the filter's: parse each bound pair straight to the value the core needs.
A record per accepted phrasing, or a condition and operator tree over domain concepts, is modelling the input grammar rather than the problem.

## The date bound does double duty

The date filters the final frame, but it also decides how much history to fetch, and the count needs a warm-up run of candles before the earliest date asked about or the first counts come out wrong.
So the edge derives a fetch window from the same bounds the core later filters on, plus a margin.

Deriving that window is the driver's job.
The filter stays generic and knows nothing about warm-up, and the core cannot ask for data it was not given.
Size the margin from evidence — measure how far back a pending countdown actually reaches over real data — rather than guessing, and prefer an unbounded fetch to a margin that is too small, because too small fails silently.

## Two readers, one command

`rich` drops colour by itself when standard output is not a terminal, which is not enough: a boxed table is still unparseable, so the plain form is a second render rather than the same one unstyled.
Logs go to standard error, or they land in the middle of piped data — `RichHandler` builds its own stdout console unless told otherwise.

## Wrong turns

- **Optimising before there is a correct simple version.** Anticipating that rebuilding weekly candles per as-of date is slow, and inventing a carry-the-state-forward trick that then dictates the function's signature.
An optimisation that changes what a function takes has leaked into the interface.
- **Hand-rolling `pivot`.** A `reduce` over per-timeframe joins is `pivot` spelled out the long way.
- **A filter DSL**, where the requirement is bounds on a named column.
- **Dates as their own type hierarchy.** A latest/on/span sum type, when a date is a column like any other and "latest" is a default bound of today.
- **Filtering the dates before counting**, which starves the run counter of the history it needs.
The bound selects rows at the end and sizes the fetch at the start, and does nothing in between.
- **Widening in the renderer**, which puts a change of grain in the driver and leaves a second entry point to repeat it.
- **A `--format` flag that only changes colour**, leaving the piped output as unparseable as the pretty one.
