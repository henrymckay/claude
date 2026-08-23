# Screen symbols answers

The design a good build reaches, and the wrong turns that miss it.
None of it appears in the brief — each line is something the skills alone should produce.

## The shape

The rung the pivot was being saved for.

| shape | one row is | how it is reached |
|---|---|---|
| candles | a symbol's candle in one timeframe | the symbol build, unchanged |
| counts | one count on one candle | the demark build, unchanged |
| wide | a symbol on a day | `pivot` the indicator and interval out together |
| matches | a symbol on a day that passed | one predicate per condition, all conjoined |

**The pivot finally has a reason, and it is the one the demark answers named.**
A condition is a claim about a symbol, and the claims span timeframes, so they can only be conjoined once the values sit on one row.
Widening is a change of grain and therefore a seam: it belongs to `transform`, not to the renderer, and this is the build where a second driver would want the same pivot with a different render.

**The conditions are data, not code.**
Two conditions and nine are the same computation over a longer table, so they arrive as rows — a name, a lower bound and an upper bound — and become one `filter` over the wide frame.
`use-polars` has the general form: a set the caller supplies is an axis of the input, so it belongs in the frame and never in a comprehension building one predicate per condition.
The tell is a `functools.reduce` over `and_`, which is that loop with a fold on it.

**The pivot's columns come from the conditions, not from the data.**
Only the named indicators are wanted, so the projection is decided before the pivot rather than after — which also stops a screen over one condition materialising nine columns and discarding eight.

**An empty result keeps its schema.** `pivot` on a frame with no rows returns the index columns alone, so every condition column vanishes and the `filter` after it fails with `ColumnNotFoundError` — a bug that only ever fires on the day nothing matched, which is most days.
`use-polars` names the fix: concatenate a zero-row frame carrying the full schema, `how="diagonal"`.
That concatenation appends the restored columns rather than ordering them, so the alphabetical order the brief asks for is a `select` after it — the one place in the tool where the column order cannot come from a declared schema, because the columns are whatever was asked for.

## What this build declares

**No new port.** Screening needs candles, which `port.Candles` already provides — and that is the third build running to need nothing new, which is the evidence the ports were drawn at the right size.

**One operation**, `find_matches`, taking the symbols, the bounds and the conditions, calling the candles port, then the demark transform, then the pivot and the filter.

**A `transform` for the conditions themselves**, turning what the driver parsed into the frame the filter is built from — pure, and the only part with any subtlety in it.

**A reader, not a port, for `--load`.** Reading a file the tool itself wrote is IO, so it belongs at the edge; but it is not a *port*, because the core does not call outward for it — the driver reads the file and passes the frame in, exactly as it passes symbols in.
A build that invents `port.Saved` has made a port out of the driver's own input.

## What should not exist yet

- **No indicator registry.** Nine names from one indicator is a closed set the type checker can hold, which `write-python` calls data rather than a mechanism. The plugin system is for when something outside the code has to join the set.
- **No expression language.** The brief asks for a name and two bounds; an operator tree over domain concepts models the input grammar rather than the problem.
- **No caching.** `--load` is not a cache: the caller names the file, decides when it is stale, and can diff it. A cache decides all three for them and has to be invalidated.
- **No screen library, no saved screens, no naming a screen.** Three conditions on a command line is not a thing to be managed.

## The boundary

**`--where` enters the program twice, and only the driver knows the second use.**
The conditions say which timeframes matter, so they size the fetch as well as filtering the result — a screen on `daily_setup` alone has no business fetching monthly candles.
That derivation is the composition root's, exactly as the warm-up margin is: the filter stays generic and knows nothing about fetching, and the core cannot ask for data it was not given.

Both apply at once here, which is the trap — the fetch window is the date bounds *plus* warm-up, and the intervals are those the conditions name, and getting one right while missing the other is a screen that is quietly wrong rather than slow.

**`--load` reads what `-o` wrote, so the two are one decision.**
The saved form is the plain form, so it is read back with the same column names and dtypes it was written with, and a build that writes floats and reads strings has broken its own round trip.
Worth a test that writes a frame, reads it back, and asserts they match — the cheapest property test in the suite and the one that catches a schema drifting.

## The surface

**`--where` repeated is a conjunction, and nothing spells `or`.**
That is a real limit and the right one for this build: the brief asks for every condition to hold, and adding a disjunction means precedence, grouping and parentheses — the expression language ruled out above.
Two screens and `sort -u` is the honest answer until somebody asks otherwise.

**No condition at all is not an error, and it does not fall out on its own.**
`polars.all_horizontal([])` raises `ComputeError: cannot return empty fold because the number of output rows is unknown` — with no expressions there is nothing to infer a length from.
Seed the fold with `polars.lit(True)` and the one path then covers no conditions, one and nine alike.
The reflex is an `if` around the filter instead, which is exactly the Python control flow `use-polars` warns about: a branch that inspects the input and splits one transformation into two, each needing its own test.

**`--load` makes the group's own output an input**, which is what makes the surface composable rather than merely pipe-friendly — and it is the pair `write-entry-points` describes, where the stage boundary already exists so the file is writable at all.

**It is not `--file` under another name**, and a build that folds them together has broken both.
`--file` names a list of symbols and `--load` names a saved wide table: different shapes, and one supplies what the other has already consumed.
They are mutually exclusive, and the brief says to refuse rather than guess — which is the same instruction as reading standard input only when nothing was named, arriving from the other side.

**Where a good build should push back.** The columns depend on the options, which every earlier brief went out of its way to prevent, and this one asks for on purpose.
Saying so is right; the answer is that a screen's columns *are* the question asked, so a stable schema here would mean printing nine columns to answer about two.
A build that notices the tension and follows the brief has read it properly; one that quietly returns a fixed schema has not.

## Verification

- The default run touches no network: the counting is pure and the fetch is behind a port, so every case here is a fake away from being fast.
- **The empty screen is the case to write first**, since it is both the common result and the one the `pivot` schema bug hides in.
- A screen whose conditions name one timeframe must not fetch the others — assert on what the fake was asked for, which is the one place a spy earns its keep over a stub.
- Round-trip `-o` and `--load`: write, read, assert the frames match.
- The conjunction: a symbol passing one condition and failing another does not appear.

## Wrong turns

- **Filtering before pivoting**, which tests each condition against rows that cannot see the others, and quietly returns symbols matching *any* condition rather than all.
- **A predicate per condition, folded together in Python**, where the conditions are rows and the filter is one expression over them.
- **Pivoting everything and projecting after**, which materialises nine columns to answer about two.
- **Letting the empty result lose its schema**, so the screen that matched nothing raises instead of printing nothing.
- **Fetching every timeframe regardless of the conditions**, tripling the slowest part of the run to compute columns nobody asked for.
- **Deriving the fetch window from the dates but not the intervals**, or the reverse — both are half the composition root's job, and the half that is missing is invisible.
- **A `port` for `--load`**, turning the driver's own file into an outward call the core makes.
- **An `if` around the filter for the no-condition case**, where seeding the fold covers it with no branch at all.
- **An `or`, a `not`, or parentheses**, none of which the brief asks for and all of which need the grammar it rules out.
