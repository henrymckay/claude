# DeMark counts answers

What a build working from the brief should arrive at, and the wrong turns to watch for.
Nothing here is stated in the brief: each item is something the skills should produce.

## The shape

Three new shapes, three seams, each a change of entity or grain.

| shape | one row is | how it is reached |
|---|---|---|
| candles | a ticker's candle in one timeframe | the candles build, unchanged |
| counts | one count on that candle | count the runs and the countdowns |
| aligned | a ticker, day, timeframe and count | map each candle's counts onto the days it covers |
| wide | a ticker on a day | `pivot` timeframe and count kind out together |

**The counting function needs nothing but its input.** Given a long frame of candles covering every ticker and every timeframe at once, it returns a long frame of counts, and it is expressible entirely in column and window expressions.

There are **three** axes — ticker, timeframe and which count — and all three are **columns**, never arguments.
Where each arrived from is irrelevant to how it is modelled: a fetch, a flag, or the problem statement fixing that there are exactly three counts.
A loop over any of them is the same mistake, and three count *columns* produced by three near-identical expressions is that loop written wide.

Setup and the two countdowns share a shape: a condition per candle, then a run or a tally over it.
Write one counting function parameterised by the condition rather than three near-copies.

**Signed counts remove the direction column.** The sign carries the direction and the magnitude the position, so `Direction` never becomes a column or a type — it survives only as a rendering concern.

**Widening is not presentation.** A pivot changes what a row represents, and a change of grain is a seam, so it belongs to a transform even though a table is what made you want it.
Presentation starts where the result stops being data and becomes a `Table`; an API serving the same report wants the same pivot and a different renderer.

**Alignment is a containment join, nothing more.** A weekly count attaches to a weekly candle and has to be spread across the days that candle covers before it can sit beside a daily count on the same row.
Nothing is reconstructed as of a past date — there is no "the weekly candle as it stood last Wednesday", so there is no per-date rebuild and none of the machinery that would make one fast.
A previous run spent its whole core design on that machinery, for a requirement nobody wanted.

**Filtering is not a seam.** It drops rows without changing what a row is.
It earns its own function by being independently useful, not because the flow demands one, and it comes last, since the bounds are set on columns that only exist once the frame is wide.

## What this build finally earns

The hexagon becomes worth its keep here, and not before.

- **A pure core**, because there is now real logic that must be testable without touching the network.
- **A `port`**, because an operation calls outward for candles while staying pure, so the driver injects the adapter.
- **An `operate`**, because fetching and counting is a task worth naming, and four commands share it.

Introducing all three *now* is right; having introduced them while the tool only expanded an index was not.

## The window trap

The counts are sequential per series, which invites a Python state machine, and they do not need one — a setup is a run length, and a countdown is a tally within a segment, both window expressions over the whole frame.

The cancellation rules are what make it delicate: a rule that depends on the running count cannot be a window function, so measure the break against the most recently completed setup instead, which is knowable without it.

`.over()` does not compose.
Chaining a second one onto an already-windowed expression silently discards the inner partition and returns a plausible wrong answer, so each windowed step goes in its own column before the next one windows it.

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

## Verification

The count is fiddly and easy to get subtly wrong, so pin it against a brute-force reference implementation — slow, obviously correct, written from the brief rather than from the code, and used only in the tests.
Agreement means something only because the two share no mechanism.

Property tests over the invariants are worth more than more examples.

- A run only ever steps on, wraps, or starts over.
- The two countdowns never point in opposite directions.
- Every count stays inside its stated range.

**Check the generator reaches the states under test.** Uniformly random prices almost never contain a nine-candle run, so an agreement property over them can pass a hundred examples having never once exercised a completed setup or a cancellation.
Bias the walk and measure where it lands before trusting the result.

## Wrong turns

- **A Python loop** over the candles, the tickers, the timeframes, or the counts.
- **Three counting functions.** Setup, sequential and combo differ in their per-candle condition, not in how a run is counted.
- **Three count columns instead of a count axis**, which is the same loop wearing a schema.
- **A direction column beside the count**, which doubles what has to be reshaped and forces every consumer to understand setups.
- **A cancellation rule expressed circularly**, depending on the countdown state it is supposed to end.
- **Chained `.over()`**, above — the failure is silent, so only the reference catches it.
- **Optimising before there is a correct simple version.** An optimisation that changes what a function takes has leaked into the interface.
- **Hand-rolling `pivot`.** A `reduce` over per-timeframe joins is `pivot` spelled out the long way.
- **A filter DSL**, where the requirement is bounds on a named column.
- **Dates as their own type hierarchy.** A latest/on/span sum type, when a date is a column like any other and "latest" is a default bound of today.
- **Filtering the dates before counting**, which starves the run counter of the history it needs.
The bound selects rows at the end and sizes the fetch at the start, and does nothing in between.
- **Widening in the renderer**, which puts a change of grain in the driver and leaves a second entry point to repeat it.
- **A `--format` flag that only changes colour**, leaving the piped output as unparseable as the pretty one.
