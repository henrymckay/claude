# DeMark counts answers

The design a good build reaches, and the wrong turns that miss it.
None of it appears in the brief — each line is something the skills alone should produce.

## The shape

Three new shapes, three seams, each a change of entity or grain.

| shape | one row is | how it is reached |
|---|---|---|
| candles | a symbol's candle in one timeframe | the candles build, unchanged |
| counts | one count on that candle | count the runs and the countdowns |
| aligned | a symbol, day, timeframe and count | map each candle's counts onto the days it covers |

**The counting function needs nothing but its input.** Given a long frame of candles covering every symbol and every timeframe at once, it returns a long frame of counts, and it is expressible entirely in column and window expressions.

There are **three** axes — symbol, timeframe and which count — and all three are **columns**, never arguments.
Where each arrived from is irrelevant to how it is modelled: a fetch, a flag, or the problem statement fixing that there are exactly three counts.
A loop over any of them is the same mistake, and three count *columns* produced by three near-identical expressions is that loop written wide.

Setup and the two countdowns share a shape: a condition per candle, then a run or a tally over it.
Write one counting function parameterised by the condition rather than three near-copies.

**The value column is a float, and that is a decision about the tool rather than about counts.**
A DeMark count is a whole number, so the type only makes sense once you know the brief means the column to hold an EMA or an RSI later and `cat` to stack them.
A build that narrows it to an integer because these particular values are whole has optimised away the one thing the column was widened for, and the next indicator finds two shapes that will not concatenate.

**Signed counts remove the direction column.** The sign carries the direction and the magnitude the position, so `Direction` never becomes a column or a type — it survives only as a rendering concern.

**`aligned` is what leaves the tool, so there is no fourth shape.**
The brief fixes the output long — five columns whatever the options — which deletes the pivot this rung would otherwise have needed and the argument about whose job it is.
That is the option surface deciding a core shape, and rightly: `--timeframe` means a wide frame's columns would depend on what was asked for, and a schema that varies with the flags is not a schema.

Nor does `--pretty` bring one back: the brief fixes it as the same rows and columns made readable, so there is no shape in this group for a renderer to change.
That is what makes the rule enforceable rather than a matter of taste — a pivot is a change of grain and therefore a seam, and a seam in a renderer is one a second entry point has to write again.

**Alignment is a containment join, nothing more.** A weekly count attaches to a weekly candle and has to be spread across the days that candle covers before it can sit beside a daily count on the same row.
Nothing is reconstructed as of a past date — there is no "the weekly candle as it stood last Wednesday", so there is no per-date rebuild and none of the machinery that would make one fast.
A previous run spent its whole core design on that machinery, for a requirement nobody wanted.

**The date bounds are not a seam.** They drop rows without changing what a row is, so they earn their own function by being independently useful rather than because the flow demands one, and they come last.
The selection the brief defers is a different thing entirely: it answers about a symbol rather than a row, so when it arrives it will change the grain and *will* be a seam.

## What this build declares

**`--load` needs a reader at the edge, and not a port.**
Reading candles the tool itself wrote is IO, so it belongs to the driver; it is not an outward call the core makes, so the core never learns about it.
The operation takes candles either way — fetched through the port, or read from the file — which is why one operation serves both paths and neither knows which happened.
That is the whole payoff of the operation taking candles rather than symbols, and it is why the option costs a branch in the driver and nothing anywhere else.

**No new port.** The counting is pure, so what this group needs from outside is candles, which `port.Candles` already gives it.
That is the test of whether the last build declared it well, and it passes only because the bounds and timeframes stayed on the port rather than being bound into an adapter one group had curried for itself.

**One operation, shared by all four commands**, because they differ by which counts reach the output rather than by what they do.
It takes symbols and the same bounds and timeframes `get_candles` takes, calls that port, and hands the frame to the counting transform.

**Nothing is left open here.** Both forms are long, the pivot belongs to the screening build, and the operation's signature follows from the brief without waiting on anything.

## What the build earns

**A `transform` layer with real computation in it**, and that is the only thing new here.

The first two builds already have a core, ports and an `operate`; what their core holds is reshaping, normalisation and a tradeability rule — work that is easy to check by eye.
This one is the first whose core can be *subtly* wrong: a run length that wraps a candle early, a countdown that survives a cancellation it should not.
That is what the reference implementation and the property tests below are for, and neither was worth building before there was something they could catch.

Nothing else is new.
The port and the operation this group needs are ones the last two builds already declared, and whether that is true is the real test of how well they were declared.

## What should not exist yet

Absent unless the brief asks for it: a caching layer, a configuration system, a plugin or registry mechanism for counts, and any abstraction over "indicators" of which DeMark is imagined to be the first.
Three counts named in a brief are three counts, not a family to build a framework around.

## The boundary

The date filters the final frame, but it also decides how much history to fetch, and the count needs a warm-up run of candles before the earliest date asked about or the first counts come out wrong.
So the edge derives a fetch window from the same bounds the core later filters on, plus a margin.

Deriving that window is the driver's job.
The filter stays generic and knows nothing about warm-up, and the core cannot ask for data it was not given.
Size the margin from evidence — measure how far back a pending countdown actually reaches over real data — rather than guessing, and prefer an unbounded fetch to a margin that is too small, because too small fails silently.

## The surface

`rich` drops colour by itself when standard output is not a terminal, which is not enough: a boxed table is still unparseable, so the plain form is a second render rather than the same one unstyled.
Logs go to standard error, or they land in the middle of piped data — `RichHandler` builds its own stdout console unless told otherwise.

`trade demark count`, the three per-count commands, `trade symbol get-candles` and `trade index get-symbols` each reach their own stage, so a caller can take any one of them without running the rest.
The three groups are three sub-applications under one root, and the third arrives by registering a fourth thing on the root rather than by editing what the first two exposed — which is the test of whether the second build nested them or merely prefixed them.
Every command spells a shared idea the same way — the file it writes to, the way symbols arrive — because a tool whose second command renames its first command's options is one nobody can use from memory.

The bounds are two options, not a pair of them per column, so the surface grows by a timeframe rather than by three flags a timeframe.
Thirty options each doing one job is what happens when comprehensiveness is pursued without brevity.

**Where a good build should push back.** The brief says the filtering is not here and says what it is for, which is an invitation to agree rather than to guess.
The argument worth making is *why* it cannot live here — a condition per timeframe and count is a claim about a symbol, and the symbol's rows are not on one row to be conjoined — which is the same reason the build after this one has to widen before it can screen.

## The window trap

The counts are sequential per series, which invites a Python state machine, and they do not need one — a setup is a run length, and a countdown is a tally within a segment, both window expressions over the whole frame.

The cancellation rules are what make it delicate: a rule that depends on the running count cannot be a window function, so measure the break against the most recently completed setup instead, which is knowable without it.

`.over()` does not compose.
Chaining a second one onto an already-windowed expression silently discards the inner partition and returns a plausible wrong answer, so each windowed step goes in its own column before the next one windows it.

## Bounding is generic over columns

One function, bounding a named column, knowing nothing about setups — and the date is just another column it bounds.
Two mechanisms for the same operation, a date bounded by its own parameters beside a general bound for everything else, means the general one was not general enough.
That rule is what the screening build is judged against when it gets there, and it is why guessing at it here is expensive: a mechanism built per condition cannot be made generic afterwards without changing every caller.

The option surface is the driver's problem, not the core's: parse each bound straight to the value the core needs.
A record per accepted phrasing, or a condition and operator tree over domain concepts, is modelling the input grammar rather than the problem.

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

- **A Python loop** over the candles, the symbols, the timeframes, or the counts.
- **Three counting functions.** Setup, sequential and combo differ in their per-candle condition, not in how a run is counted.
- **Three count columns instead of a count axis**, which is the same loop wearing a schema.
- **A direction column beside the count**, which doubles what has to be reshaped and forces every consumer to understand setups.
- **A cancellation rule expressed circularly**, depending on the countdown state it is supposed to end.
- **Chained `.over()`**, above — the failure is silent, so only the reference catches it.
- **Optimising before there is a correct simple version.** An optimisation that changes what a function takes has leaked into the interface.
- **Pivoting at all**, when the brief fixes both forms long.
- **Building the filtering anyway.** The brief puts it in the next build and says why: the thing wanted is a symbol satisfying several conditions across different rows, which bounds on one column cannot express.
Guessing at a mechanism here means the real one arrives as a breaking change to a published surface.
- **Dates as their own type hierarchy.** A latest/on/span sum type, when a date is a bound like any other and "latest" is a default of today.
- **Filtering the dates before counting**, which starves the run counter of the history it needs.
The bound selects rows at the end and sizes the fetch at the start, and does nothing in between.
- **Reshaping under `--pretty`**, which makes the readable form a different answer rather than the same one, so what you check by eye is never what a script receives.
- **A `--format` flag that only changes colour**, leaving the piped output as unparseable as the pretty one.
