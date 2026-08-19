# Counts answers

What a build working from the brief should arrive at, and the wrong turns to watch for.
Nothing here is stated in the brief: each item is something the skills should produce.

## The shape

One new shape, and it is the heart of the tool.

| shape | one row is | how it is reached |
|---|---|---|
| candles | a ticker's candle in one timeframe | rung 2, unchanged |
| counts | one count on that candle | count the runs and the countdowns |

**The counting function needs nothing but its input.** Given a long frame of candles covering every ticker and every timeframe at once, it returns a long frame of counts, and it is expressible entirely in column and window expressions.

There are **three** axes — ticker, timeframe and which count — and all three are **columns**, never arguments.
Where each arrived from is irrelevant to how it is modelled: a fetch, a flag, or the problem statement fixing that there are exactly three counts.
A loop over any of them is the same mistake, and three count *columns* produced by three near-identical expressions is that loop written wide.

Setup and the two countdowns share a shape: a condition per candle, then a run or a tally over it.
Write one counting function parameterised by the condition rather than three near-copies.

**Signed counts remove the direction column.** The sign carries the direction and the magnitude the position, so `Direction` never becomes a column or a type — it survives only as a rendering concern, at the next rung.

## What this rung finally earns

The hexagon becomes worth its keep here, and not before.

- **A pure core**, because there is now real logic that must be testable without touching the network.
- **A `port`**, because an operation now calls outward for candles while staying pure, so the driver injects the adapter.
- **An `operate`**, because fetching and counting is a task worth naming, and four commands share it.

Introducing all three *now* is right; having introduced them at rung 1 was not.

## The window trap

The counts are sequential per series, which invites a Python state machine, and they do not need one — a setup is a run length, and a countdown is a tally within a segment, both of which are window expressions over the whole frame.

The cancellation rules are what make it delicate: a rule that depends on the running count cannot be a window function, so measure the break against the most recently completed setup instead, which is knowable without it.

`.over()` does not compose.
Chaining a second one onto an already-windowed expression silently discards the inner partition and returns a plausible wrong answer, so each windowed step goes in its own column before the next one windows it.

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

- **A Python loop over the candles**, or over the tickers, or over the timeframes.
- **Three counting functions.** Setup, sequential and combo differ in their per-candle condition, not in how a run is counted.
- **Three count columns instead of a count axis**, which is the same loop wearing a schema.
- **A direction column beside the count**, which doubles what has to be reshaped later and forces every consumer to understand setups.
- **A cancellation rule expressed circularly**, depending on the countdown state it is supposed to end.
- **Chained `.over()`**, above — the failure is silent, so it is only caught by the reference.
