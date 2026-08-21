---
name: use-polars
description: >-
  How to write correct, idiomatic Polars (the Python DataFrame library) — the
  expression API, lazy vs eager execution, keeping every group in one long-form
  frame instead of looping, naming frames and pipe steps, and the mental-model
  shifts coming from pandas. Use whenever working with Polars
  DataFrames/LazyFrames, writing data transformations or analytics in Polars,
  converting pandas code to Polars, reshaping between long and wide, or
  debugging Polars queries — even if the user only says "polars", "pl.", or
  names a .parquet/.csv workflow they want done with it. Targets Polars 1.x.
  Polars-specific; the general write-python conventions still apply on top.
---

# Use Polars

`polars` is fast and correct when you work *with* its model: **expressions** evaluated inside **contexts**, over eager `DataFrame`s or lazy `LazyFrame`s.
`write-python`'s general conventions apply on top.
Most mistakes come from writing `pandas` habits in `polars` syntax.
Three account for nearly all of them: leaving the frame for Python lists and loops, looping over groups instead of stacking them into one frame, and letting `pandas` types or habits leak past the boundary — each has its own section below.

**In an existing project, ask first.** Where a codebase already has an established `polars` style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

Targets `polars` 1.x.
Verify version-specific method names against the installed version if something doesn't resolve.

Import convention (house style): `import polars` and qualify — `polars.col(...)` — not the conventional `import polars as pl`.

## The mental model

**Expressions** describe a computation on columns — `polars.col("a").add(polars.col("b"))`, `polars.col("x").sum()`.
They're lazy descriptions, run in parallel by the engine, and are the heart of `polars`.
You never loop over rows.

**Contexts** are where expressions run.
A handful of methods carry nearly all the work, and they sort by what they do to the frame's shape:

- **Keep the shape.** `.select` picks and computes columns and returns only what you selected; `.with_columns` adds or replaces columns and keeps the rest; `.filter` drops the rows a boolean expression rejects.
- **Change the grain.** `.group_by(...).agg(...)` collapses rows to one per group, changing what a single row represents.
Group order is arbitrary unless you pass `maintain_order=True`, which costs speed — so where you only need determinism at the end, sort the result instead.
An aggregation takes a condition without a second pass: `polars.col("value").filter(polars.col("value").gt(0)).sum()` totals only the rows that qualify.
- **Change the layout.** `.join` widens a row by key, `.pivot` turns a key's values into columns, `.unpivot` turns columns back into rows (it was `melt` before 1.0), and `.explode` splits a list column into rows.
- **Aggregate without collapsing.** `.over` evaluates an expression within a partition and writes the answer back onto every row.
It is what keeps per-group work in one frame instead of a loop, and it carries the worst trap in the API — below.
- **Factor out a step.** `.pipe` hands the frame to a function and returns what comes back, so a named transform joins a chain without breaking it.

Three more you reach for constantly: `.sort`, `.unique` to drop duplicate rows, and `polars.concat` to stack frames.
**`.sort` is a correctness requirement, not presentation.** `.shift`, every cumulative, `.first`/`.last` and `join_asof` all read the frame in its current row order, so an unsorted input returns a wrong answer rather than an untidy one, and nothing raises.
Naming is `.alias`, conditionals are `when/then/otherwise` (`polars.when(cond).then(a).otherwise(b)`), and the typed **namespaces** — `.str`, `.dt`, `.list`, `.struct` — hold whatever is particular to a dtype.

**Where an expression applies to a *class* of columns, say the class — `polars.selectors`.** `polars.selectors.numeric()`, `.starts_with("bid_")`, `.by_dtype(...)` and `.exclude(...)` resolve against the frame's real schema when the query runs, so `frame.with_columns(polars.selectors.numeric().fill_null(0))` covers the column somebody adds next month without the call being touched.
Naming each column, or assembling the list in Python first, pins the set to what the schema held the day it was written.

Choosing the shape is most of the work — the expression API is the easy half.

```python
import polars

out = (
    df
    .filter(polars.col("amount").gt(0))
    .with_columns(
        polars.col("amount").mul(polars.col("rate")).alias("value"),
        polars.col("name").str.to_uppercase().alias("name_up"),
    )
    .group_by("category")
    .agg(polars.col("value").sum().alias("total"))
    .sort("total", descending=True)
)
```

**Write one fluent method chain.** Build pipelines by **chaining contexts** end to end rather than assigning intermediate frames to variables between steps — a single chain reads as one transformation and stays one query the optimiser can work on.
Wrap it in parentheses for multi-line readability, and don't break the chain without a real reason (reusing an intermediate, or debugging).
Within a context, compute multiple columns in a single `with_columns` rather than many sequential calls — the engine parallelises expressions within one context.

**Give a windowed step its own column before the next step windows it.** `.over()` does **not** compose: chaining a second `.over()` onto an expression that has already been windowed silently discards the inner partition and evaluates the whole expression inside the outer one.
There is no error and the result looks plausible — it is simply wrong, which makes this the most expensive trap in the API.
So materialise each windowed result into a column in its own `with_columns`, then window *that* column:

```python
# Wrong: the .over("run") is discarded and the cum_sum runs within the segment.
frame.with_columns(
    opened=polars.col("qualifies").cum_sum().over("run").first().over("segment")
)

# Right: one .over() per expression, each result carried in a column.
frame.with_columns(counted=polars.col("qualifies").cum_sum().over("run")).with_columns(
    opened=polars.col("counted").first().over("segment")
)
```

This is the one place the single-chain rule gives way, and only that far: the chain carries on, each window just gets its own `with_columns`.

A *single* `.over()` is the normal idiom and stays correct however much precedes it — `polars.col("close").shift(1).over("ticker")` and `polars.col("high").rolling_max(window_size=9).over("ticker")` are both right.
The trap is the **second** `.over()`, which throws away whatever partition the first one named — so `.rolling_max(9).over("ticker").first().over("segment")` is broken in exactly the same way.

**Python control flow is what usually breaks a chain.** An `if` that inspects the frame and rebinds it, or an early return for an empty input, splits one transformation into branches that each need their own test.
Keep the decision inside the chain — `when/then/otherwise` for a value, `.filter` for rows — or normalise the shape once where the data enters, so there is nothing left to branch on.
An empty input rarely deserves its own path: the same chain over an empty frame returns an empty frame with the right schema, where a hand-written early return duplicates that schema somewhere it can drift out of step.

**`pivot` is the exception that breaks that promise.** With no rows there are no values to spread into columns, so it returns the index columns alone and every column downstream code selects has vanished — a `ColumnNotFoundError` that only ever fires once a filter empties the frame.
Restore the shape without branching by concatenating the empty frame's schema back in: `polars.concat([pivoted, empty], how="diagonal")` fills the missing columns with nulls, where `empty` is a zero-row frame declaring the full schema.

**Use expression methods, not operator symbols.** Write `polars.col("a").mul(polars.col("b"))` and `polars.col("x").gt(0)`, not `*` and `>`.
The method form chains without wrapping parentheses and reads consistently with the rest of the expression API (`.sum()`, `.alias()`, `.over()`).
Arithmetic and comparison operators all have method equivalents: `.add`, `.sub`, `.mul`, `.truediv`, `.floordiv`, `.mod`, `.pow`, and `.gt`, `.ge`, `.lt`, `.le`, `.eq`, `.ne`.
This also sidesteps the precedence trap — `polars.col("a").gt(0) & polars.col("b").gt(0)` needs no inner parentheses, where the operator form does.
Keep the boolean combinators `&`, `|`, `~` as operators, though — their method spellings (`.and_`, `.or_`, `.not_`) read worse and they are near-universal for combining masks.

**Name a column with `.alias("x")`, not a `x=` keyword.** Write `.with_columns(polars.col("close").diff().alias("move"))`, not `.with_columns(move=polars.col("close").diff())`.
The keyword form is a feature of the *context*, so the name lives outside the expression and is lost the moment the expression moves — lifted into a variable, passed to a helper, put in a list built elsewhere, or reused in a second context.
`.alias()` travels with the expression, which is what lets expressions be composed at all.
It is also the only form that can name a column Python cannot spell, like `total (£)` or `2024`, so the keyword form quietly stops working on real data rather than at the point you chose it.
The rest of the API only knows `.alias()` — `.over()`, `.pipe()`, a bare `polars.col(...)` in a `sort` — so one spelling everywhere reads more consistently than two.

## Eager vs lazy

- **Eager** (`polars.read_csv`, `df.select(...)`) runs immediately.
Fine for small data and quick interactive work.
- **Lazy** (`polars.scan_csv`, `df.lazy()`) builds a query plan and only executes on `.collect()`.
The optimiser can push filters down, prune columns, and stream — so lazy is the default for real pipelines and large files.

```python
result = (
    polars.scan_parquet("events/*.parquet")   # lazy: nothing read yet
    .filter(polars.col("ts").ge(start))
    .group_by("user_id")
    .agg(polars.len().alias("n"))
    .collect()                                # execute the optimised plan
)
```

For data bigger than memory, use the streaming engine: `.collect(engine="streaming")` (the older `.collect(streaming=True)` is deprecated).

Two more lazy-execution habits: run several independent queries together with `polars.collect_all([frame_a, frame_b])` so the engine shares scans and work across them, and write a lazy frame straight to disk with `.sink_parquet(path)` rather than `.collect().write_parquet(path)`, which streams without materialising the whole frame.

**Read the plan with `.explain()` rather than guessing what the optimiser did.** Two lines answer most questions: `PROJECT n/m COLUMNS` says how many columns the scan actually reads, and where `FILTER` sits says whether the predicate reached the scan or is running after all the work.
It is how you check a claim about a query instead of trusting one — including the projection cost of `polars.struct("*")` below, which is visible there as the difference between reading two columns and reading every one.
Don't reach for `.profile()`: it is deprecated, having been built for the older in-memory engine, and its timings mislead under the streaming one.

## Stay in the dataframe

**If data is a dataframe, or you're doing dataframe-shaped work, do it *in* `polars` — don't drop to Python lists and loops.**
Pulling columns out to Python lists and looping, comprehending, or `functools.reduce`-ing over them throws away the engine's speed and the query optimiser, and it's the most common way people accidentally leave `polars`.
Comparing a column to an earlier row, running a count, grouping by a key — that is all expression work, so it belongs in the frame.
`.map_elements` is the same mistake with a `polars` method on it: it hands each value to a Python callback, so the engine runs single-threaded through the interpreter for every row.

**Convert at the boundary, and never reach back.** When another library hands you a frame (a `pandas` result from `yfinance`, an API), convert it with `polars.from_pandas` at the first opportunity and keep going with expressions.
Tidying in `pandas` first — resetting an index, renaming, reshaping — does the work in the weaker API and drags `pandas` types into your own signatures, while a `polars` chain that reaches back into the original frame for a column name or a shape has left the boundary open.
Convert, then let every decision after that be an expression.

**The one `pandas` call you cannot avoid is dissolving a column `MultiIndex`.** It has no `polars` equivalent, so flatten it *before* converting or the levels arrive as tuple column names you unpick by hand — a `.stack(level=..., future_stack=True)` and nothing else.
A **row** index needs no `pandas` call at all: `polars.from_pandas(frame, include_index=True)` brings every level across as a column, so a `.reset_index()` first is one more `pandas` operation doing what the converter already does.
Pass that argument whenever the index carries meaning, because the default **drops it silently** — convert a frame indexed by date and ticker without it and you get the values alone, with nothing to say which row is which.
The renaming, casting, selecting and filtering all belong on the `polars` side.
`polars.from_pandas` also needs `pyarrow` installed for anything beyond plain numpy-backed columns, so add it as a dependency when you convert.

**Keep every group in one long-form frame — don't split it up.**
Stack all groups (all tickers, all users, all categories) into a single frame and compute across them together, rather than holding a frame per group and looping.
Most work is plain column expressions that apply to every group in one pass — element-wise maths, filters, `when/then` — with **no `.over` at all**.
Reach for `.over(group)` only where an operation must respect group boundaries: a `.shift`, a cumulative, a rank, or a per-group window.
Even sequential per-group logic stays in the one frame that way — a consecutive-run length or reset-on-change counter is a change flag, a `cum_sum` to number the runs, and a cumulative count within each run, all `.over(group)`, not a Python accumulator:

```python
runs = (
    frame.sort("group", "order")
    .with_columns(
        polars.col("state")
        .ne(polars.col("state").shift(1).over("group"))
        .fill_null(True)
        .cum_sum()
        .over("group")
        .alias("run_id")
    )
    .with_columns(
        polars.int_range(1, polars.len().add(1)).over("group", "run_id").alias("run_len")
    )
)
```

`state` is whatever you are measuring runs of — for an up/down/flat run, `polars.col("close").sub(polars.col("close").shift(4).over("group")).sign()`.
Two `with_columns` rather than one because `run_len` windows on `run_id`, which is the rule above.
**`.fill_null(True)` is what makes the first row of each group start a run.** Comparing against a null yields null under three-valued logic, not `True`, so without it that row's `run_id` is null and it drops out of every window keyed on it — a silent hole at the head of every group.

**Splitting into per-group sub-frames and looping is the same mistake as looping rows one at a time, a level up.**

**Filter by membership with a semi join, not a list pulled out to Python.**
`frame.join(wanted, on="ticker", how="semi")` keeps the rows having a match and brings no columns across, and `how="anti"` keeps the rows having none.
The reflex — `frame.filter(polars.col("ticker").is_in(wanted.get_column("ticker").to_list()))` — collects the other frame to build the list, so a lazy query stops being lazy on that line and the optimiser loses sight of the second frame entirely.
Passing the `Series` rather than the list avoids the `to_list()` but is deprecated in recent 1.x as ambiguous against a list-typed column, so the join is the spelling with a future.
A Python list you already hold is still fine in `is_in`; it is reaching into another *frame* for one that costs you.

**A grouping key that arrives as an argument is still a group.** Whether an axis reaches you as rows already in the frame (a `ticker` column from a fetch), as a caller-supplied list (a set of timeframes, regions, or scenarios to compute over), or as a set the *problem itself* fixes (there are exactly three counts, four quartiles, two scenarios), it is the same thing to the computation, and all of them belong in the frame.

That last one is the easiest to miss, because a closed set feels like structure rather than data — three counts become three columns and three expressions, and the axis never appears.
Three tells: a name repeated across columns (`daily_setup`, `weekly_setup`), a function returning one column per member of a fixed set, and a `polars.concat([...])` wrapping a comprehension.
The first two are a wide frame that should be long, and going long collapses the near-copies into one pass with the axis as a column; the third is the per-group loop already, wearing a parameter as a disguise.
The comprehension is not itself the fault: one building a *list of expressions* for a single `with_columns` stays one plan and is fine, though `polars.selectors` usually says it better.
It is the one building a *frame per group* that is the loop.
Widen at the end, once, for whatever has to display in columns.
Put the values in their own small frame and `.join(other, how="cross")` where each applies to every row (a plain join where it's selective), then group by that axis alongside the rest: `.over(["ticker", "timeframe"])`.
`be-functional`'s "Derive functions from the data flow" has the general test for whether a parameter is really data.

**The tell is about computation, not IO.** A `concat` over a comprehension that makes *one call per group to the outside world* — a request per timeframe because the API serves one interval at a time, a read per partition file — is not this mistake, and there is no in-frame form of it because the rows do not exist yet.
Keep that concat inside the adapter, have it return a single long frame with the axis as a column, and the rule then holds for everything downstream.

**Rendering is the other legitimate exit.**
A frame becomes a `rich.Table`, a chart, an HTTP response body — and there is no in-frame form of that either, because the destination is not a frame.
Iterate at that boundary and nowhere earlier: reshape, filter and sort while it is still a frame, then leave it once, in the driver.

Both exits look identical to a reader scanning for `iter_rows`, so say which one you are taking in the docstring — otherwise the next person reads it as the lapse the rule warns about and deletes it.

```python
# Wrong: a Python loop over groups, one frame per timeframe.
counts = polars.concat([counted(prices, timeframe) for timeframe in timeframes])

# Right: the axis is a column, so a single pass covers every group.
counts = prices.join(
    polars.DataFrame({"timeframe": timeframes}), how="cross"
).with_columns(
    polars.col("close").diff().over(["ticker", "timeframe"]).alias("move")
)
```

**Reshape so the values you are comparing sit on one row.** `pivot` and `unpivot` change what a row represents, which decides what counts as an element-wise comparison: values in *different rows* need a window, a self-join or a shift, where the same values in *different columns* are a plain expression.
So pivot mid-computation when a comparison spans a key — one timeframe against another, this month against last — and unpivot back to long form for anything that must apply uniformly across every series.
Long form is the default because most work applies to every series alike; wide is what you reach for when the key itself is what you are comparing across, and what you pivot to once at the boundary where something needs columns to display.
Spreading a key across columns with a chain of joins is `pivot` hand-rolled, and stacking per-column selects with a `concat` is `unpivot` hand-rolled — reach for the named operation instead.

**Attach a coarser series to finer rows with `join_asof`.** `strategy="backward"` answers "the last row at or before this one" — a weekly candle against daily rows, a rate that changes on effective dates — and both frames must be sorted on the `on` key.
Passing `by=` then warns `Sortedness of columns cannot be checked when 'by' groups provided` on **every** call, sorted or not, and nothing done to the frames silences it: not sorting by the `by` columns first, not `set_sorted`.
So sort correctly and suppress that one message where the join happens, rather than widening the filter or living with the noise:

```python
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Sortedness of columns")
    aligned = dates.sort("date").join_asof(
        counts.sort("date"), by=["ticker", "timeframe"], on="date", strategy="backward"
    )
```

## Habits and `pandas` traps

- **No index.** There's no implicit row index and no `.loc`/`.iloc` — select and filter with expressions.
- **Immutable.** Every operation returns a *new* frame; there's no `inplace=`.
Assign the result.
- **Select before compute.** Only pull the columns you need; with lazy frames the optimiser does this for you.
- **Null is not `NaN`.** `polars` keeps missing (null) apart from float not-a-number (`NaN`), where `pandas` conflates them — so `.fill_null` and `.fill_nan` are different calls, and `.drop_nulls` leaves a `NaN` sitting in the frame.

**Build a one-column frame from a `Series`, not a dict and a schema.**
`polars.Series("symbol", tickers, dtype=polars.String).to_frame()` states the column's name and its type once each, where `polars.DataFrame({"symbol": tickers}, schema={"symbol": polars.String})` states the name twice — so a rename can update one and miss the other, and the frame comes back with a column nothing downstream selects.
Both give the same frame on an empty list, which is the case the schema was there for.
Keep the dict form for a genuine multi-column literal.

## Name dataframes

Name a frame by its **contents**, not its type: `customers`, `orders`, `trades` — not `df` or `df_customers`.
The type hint (and the `polars` API you're calling) already says it's a `DataFrame`/`LazyFrame`, so a `df_` prefix is redundant Hungarian notation.
Reserve a bare `df` (or `frame`) for the cases where the contents genuinely aren't known: a generic placeholder in an example, or a **generic function** that operates on any frame — e.g. a `.pipe()` helper like `def map_round_2dp(df: polars.DataFrame) -> polars.DataFrame`.

## Name `.pipe()` UDFs

When you factor pipeline steps into UDFs (user-defined functions) used with `.pipe()`, name them by their functional shape so a reader knows what each does at a glance.
The map/bind vocabulary is `be-functional`'s — this is its composition and monad guidance applied to frames.
On the surface all three are `DataFrame -> DataFrame`, so the prefix signals **intent**, not the type signature.
Name the function by `write-python`'s rules first and *then* prefix it — `map_keep_tradeable`, not `map_tradeable` — since the prefix says how the step behaves in a chain and the verb still has to say what it does.

- **`map_`** (functor map) — a pure transform of the frame alone, behaviour fixed: `frame.pipe(map_round_2dp)`.
- **`amap_`** (applicative map) — combines the frame with one or more **independently provided** inputs in a **fixed** way; the operation does *not* branch on the data: `customers.pipe(amap_join_orders, orders)`.
- **`bind_`** (monadic bind) — the operation **chosen depends on the frame's own data**: you inspect the contents and branch.
E.g. attach FX rates by looking at which currencies are actually present and joining only those tables: `trades.pipe(bind_attach_fx, rate_tables)`.

**The prefix covers everything `.pipe()` reaches, a core transform included.**
A domain name says what a step is *about*; the prefix says what it does to the frame, which is the half a reader of the chain cannot see.
So a transform written to sit in a chain is `map_keep_tradeable` from the start, and the domain name stays in the rest of it — the prefix is added to the name, not swapped for it.
And reach for `.pipe()` rather than nesting the calls.
Three transforms wrapped around one another read inside-out and put the last step first; the same three piped read in the order they run, and the prefixes let you see which of them can branch on the data before you open any of them.

The line between `amap_` and `bind_` is exactly the one between applicative and monad: **an applicative step's behaviour is fixed regardless of the values inside; a bind step's behaviour depends on the materialised data.**
That has teeth in `polars` — `map_`/`amap_` are pure plan transforms and stay **lazy**, whereas `bind_` usually has to **materialise** (collect/inspect) the data to decide what to do, breaking laziness.
So reach for `bind_` only when the logic genuinely must see the data; prefer `map_`/`amap_` to keep the query lazy and optimisable.

## Pass extra data through `.pipe()`

`.pipe(udf, *args, **kwargs)` hands the frame plus any extra arguments to the UDF, so you can thread additional data through a chain without breaking it — `frame.pipe(amap_attach_rates, rate_table)`.
Supplying **read-only** inputs this way is exactly the `amap_` pattern above, and it's clean.

A mutable **state object** the UDF reads *and writes* also works, but treat it with care:

- It's a **side effect** — it breaks the referential transparency the rest of the pipeline relies on, since a step's result now depends on hidden mutable state.
- On a `LazyFrame` the UDF runs at **plan-build time**, not at execution, so it can only record schema- or plan-level facts; writing a *data-derived* value forces a `.collect()` (the `bind_` case, breaking laziness).

Prefer carrying state **as data in the frame** — an extra column or a `struct` — so it flows through the query natively and stays lazy.
If it genuinely must live outside the frame, thread it explicitly with a plain function returning `(frame, state)` rather than a mutable side-channel.
Reserve a write-through state argument for pragmatic cases like collecting diagnostics, knowing it's impure and runs at build time.

## Run a frame function inside an expression

`.pipe()` works at frame level, so a function taking a whole frame and returning one column has nowhere to sit inside `with_columns`.
`polars.struct(...).map_batches(...)` is the way in: the struct packs the columns into one value per row, `map_batches` hands the whole `Series` to your function at once, and `.struct.unnest()` turns it back into a frame:

```python
frame.with_columns(
    polars.struct("close", "volume")
    .map_batches(lambda s: s.struct.unnest().pipe(vwap), return_dtype=polars.Float64)
    .over("ticker")
    .alias("vwap")
)
```

**Ask first whether it should be an expression at all**, because most frame-to-column functions are one and the wrapper only hides that.
Then note that an *eager, ungrouped* frame does not need this: `with_columns` accepts a `Series`, so `frame.with_columns(vwap(frame).alias("vwap"))` already works.
What earns the wrapper is the two cases that leave you without a frame to call: a **`LazyFrame`**, where no frame exists yet to hand over, and **per-group application**, where `.over("ticker")` runs the function within each partition instead of once over everything.

It is emphatically **not** `.map_elements`.
That one calls Python per row; this one calls it once per batch, so a body written in expressions stays vectorised — on two million rows it costs the same as the plain expression.
Three things to get right, each of which bites silently:

- **Name the columns the function reads, never `polars.struct("*")`.** The struct's members are what the query has to materialise, so `"*"` defeats projection pushdown: `struct("a", "b")` over a four-column scan reads two columns, `struct("*")` reads all four, and on a wide `.parquet` that is the whole file.
- **Pass `return_dtype`.** Without it the engine resolves the output type by *calling your function* on a fabricated two-row frame, so it runs an extra time on invented values — and a function that rejects them fails when the schema is resolved, nowhere near the call.
- **The optimiser cannot see through it.** A `.filter` written after the expression stays after it rather than pushing down to the scan, so filter first and map second where the order is yours to choose.

**A single expression can return several columns, too.** Build a `polars.struct(...)` of the aliased parts and `.unnest()` it, and one pass over the data yields the lot where a column each would have made a pass each — the same move as above, run the other way round.
