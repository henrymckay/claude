---
name: use-polars
description: >-
  How to write correct, idiomatic Polars (the Python DataFrame library) — the
  expression API, lazy vs eager execution, keeping every group in one long-form
  frame instead of looping, joining without silently multiplying rows, the
  silent traps around nulls, dtypes and windows, naming frames and pipe steps,
  and the mental-model shifts coming from pandas. Use whenever working with
  Polars DataFrames or LazyFrames, writing data transformations or analytics in
  Polars, converting pandas code to Polars, joining or reshaping between long
  and wide, or reading a query plan — even if the user only says "polars",
  "pl.", or names a .parquet/.csv workflow they want done with it. Targets
  Polars 2.x. Polars-specific; the general write-python conventions still apply
  on top.
---

# Use Polars

`polars` is fast and correct when you work with its model: **expressions** evaluated inside **contexts**, over eager `DataFrame`s or lazy `LazyFrame`s.
This targets `polars` 2.x, and `write-python` applies on top — including its import rule, so `import polars` and `polars.col(...)`, never `import polars as pl`.
Three mistakes account for nearly all that goes wrong: leaving the frame for Python lists and loops, looping over groups instead of stacking them into one frame, and letting `pandas` habits or types leak past the boundary.

**In an existing project, ask first.** Where a codebase already has an established `polars` style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## The mental model

**Expressions** describe a computation on columns — `polars.col("a").add(polars.col("b"))` — and run in parallel inside the engine; you never loop over rows.
**Contexts** run them, sorted by what they do to the frame's shape:

- **Keep the shape** — `.select` returns only what it computes, `.with_columns` adds or replaces columns, `.filter` drops rows.
- **Change the grain** — `.group_by(...).agg(...)` collapses to one row per group.
Group order is arbitrary unless `maintain_order=True`, which costs speed; sort the result instead where only the end needs determinism.
An aggregation can take a condition: `polars.col("v").filter(polars.col("v").gt(0)).sum()`.
- **Change the layout** — `.join` widens by key, `.pivot` spreads a key's values into columns, `.unpivot` turns columns into rows, `.explode` splits a list column.
- **Aggregate without collapsing** — `.over(group)` computes within a partition and writes the answer onto every row.
- **Factor out a step** — `.pipe(fn)` hands the frame to a function without breaking the chain.

**`.sort` is a correctness requirement, not presentation.** `.shift`, every cumulative, `.first`/`.last` and `join_asof` read the current row order, so an unsorted input gives a wrong answer and nothing raises.

**Address a class of columns with `polars.selectors`.** `polars.selectors.numeric().fill_null(0)` resolves against the real schema when the query runs, so it covers the column added next month; a hand-listed set is pinned to the day it was written.
**Rename by rule the same way**: `frame.rename(to_snake_case)` applies to whatever arrives, where a `{...}` dict silently misses a new field — keep the dict for a few renames that follow no rule.

```python
revenue = (
    orders.filter(polars.col("amount").gt(0))
    .with_columns(polars.col("amount").mul(polars.col("rate")).alias("value"))
    .group_by("category")
    .agg(polars.col("value").sum().alias("total"))
    .sort("total", descending=True)
)
```

**Write one fluent method chain.** Chain contexts end to end in parentheses rather than binding intermediate frames: it reads as one transformation and stays one query for the optimiser.
Compute several columns in one `with_columns`, which the engine parallelises.
A chain opening with a function — `polars.concat(...)`, `polars.read_csv(...)` — is still a chain; that unannounced start is where most single-use intermediates come from.

**Keep control flow inside the chain.** An `if` that inspects the frame splits one transformation into branches each needing a test; use `when/then/otherwise` for values and `.filter` for rows.
An empty input rarely needs its own path — the chain returns an empty frame with the right schema, where an early return duplicates the schema somewhere it can drift.
Where a column may be absent from a genuinely open schema, `polars.selectors.by_name("a", "b", require_all=False)` avoids the `if`; where the caller knows the columns, require them.

**Use expression methods, not operators**: `.mul`, `.add`, `.truediv`, `.gt`, `.eq` and the rest chain without wrapping parentheses and dodge the precedence trap in `polars.col("a").gt(0) & polars.col("b").gt(0)`.
Keep `&`, `|`, `~` as operators — their method spellings read worse.

**Name a column with `.alias()`, not a keyword argument.** The keyword form (`with_columns(total=...)`) belongs to the context, so the name is lost when the expression moves into a variable, a helper or a second context; `.alias()` travels with it, and also spells names Python can't, like `total (£)`.

## Silent traps

Each of these returns a plausible frame rather than raising.

**Give a windowed step its own column before windowing it again.** A second `.over()` chained onto an already-windowed expression discards the inner partition.
A single `.over()` is fine however much precedes it.

```python
# Wrong: the .over("run") is discarded; cum_sum runs within the segment.
frame.with_columns(
    polars.col("q").cum_sum().over("run").first().over("segment").alias("opened")
)

# Right: one .over() per expression, each result carried in a column.
frame.with_columns(polars.col("q").cum_sum().over("run").alias("counted")).with_columns(
    polars.col("counted").first().over("segment").alias("opened")
)
```

**An empty `pivot` loses its value columns.** With no rows there is nothing to spread, so only the index columns return and a later `select` raises `ColumnNotFoundError` only when a filter empties the frame.
Restore the shape without branching: `polars.concat([pivoted, empty], how="diagonal")`, where `empty` is a zero-row frame declaring the full schema.

**Null is not `NaN`.** `.fill_null` and `.fill_nan` are different calls, and `.drop_nulls` leaves `NaN`.
A ratio against a group aggregate — `polars.col("x").truediv(polars.col("x").max().over("g"))` — yields `NaN` where the maximum is zero, which then compares false against everything; decide the zero case with `when` where you divide.

**A comparison with null is null, not false**, so `.filter` drops the row; `.eq_missing()` is the null-safe form, counting two nulls equal.

**`.sum()` of an all-null column is `0`; `.mean()` is null.** Check which you hand a reader.

**Declare a dtype wherever you didn't choose the contents.** An empty list or an all-`None` column infers `Null`, not an empty `String`, so `concat`, a join or any `.str` method against it raises.
The type also varies by input: a field present for some records and absent for others infers `Int64` in one batch and `Null` in the next, and the two won't concatenate.
Declare the **widest** type the column can hold, on anything built from a response.
For a one-column frame, `polars.Series("id", ids, dtype=polars.String).to_frame()` states name and type once each.

## Unlearn `pandas`

- **No index** — no `.loc`/`.iloc`; select and filter with expressions.
- **Immutable** — every operation returns a new frame; there is no `inplace=`.
- **Select before compute** — or go lazy and let the optimiser prune.
- **Convert at the boundary and never reach back.** Convert another library's frame with `polars.from_pandas` at once; tidying in `pandas` first does the work in the weaker API and leaks its types into your signatures.
- **Pass `include_index=True` when the index means something** — the default drops it silently.
- **Flatten a column `MultiIndex` before converting** (`.stack(level=..., future_stack=True)`), the one `pandas` call with no `polars` equivalent.
- **Install `pyarrow`** for `from_pandas` beyond plain numpy-backed columns.

## Eager vs lazy

- **Eager** (`polars.read_csv`, `frame.select`) runs immediately — fine for small, interactive work.
- **Lazy** (`polars.scan_csv`, `frame.lazy()`) builds a plan that runs on `.collect()`, pushing filters down and pruning columns — the default for real pipelines.

```python
result = (
    polars.scan_parquet("events/*.parquet")
    .filter(polars.col("ts").ge(start))
    .group_by("user_id")
    .agg(polars.len().alias("n"))
    .collect()
)
```

- **Larger than memory**: `.collect(engine="streaming")`.
- **Several queries**: `polars.collect_all([a, b])` shares scans between them.
- **Write without materialising**: `.sink_parquet(path)`, not `.collect().write_parquet(path)`.
- **Read the plan with `.explain()`** rather than guessing: `PROJECT n/m COLUMNS` shows how many columns a scan reads, and where `FILTER` sits shows whether a predicate reached the scan.

**Lazy reads the top of a file whose bottom is broken.** `read_csv` parses the whole document in parallel chunks, so a stray quote far below kills it even with `n_rows`; `scan_csv(...).head(n).collect()` stops once it has `n` rows.
It still parses whole chunks, so it saves a large file but not a small one — and a committed fixture is too small to reproduce the failure, so test with a generated file.
Never repair it by slicing lines first: a quoted field may hold a newline, so the count silently comes out short.

## Stay in the frame

**Dataframe-shaped work stays in `polars`.** Pulling columns into lists and looping, comprehending or reducing throws away the engine and the optimiser; comparing to an earlier row, a running count and grouping are all expressions.
`.map_elements` is the same mistake under a `polars` name — a Python call per row.

**Keep every group in one long-form frame.** Stack all groups and compute across them together; most work is plain column expressions with no `.over` at all.
Reach for `.over(group)` only where an operation must respect group boundaries — a shift, a cumulative, a rank.
Even sequential per-group logic stays in the frame: a run length is a change flag, a `cum_sum` numbering the runs, and a count within each run.

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
        polars.int_range(1, polars.len().add(1))
        .over("group", "run_id")
        .alias("run_len")
    )
)
```

`.fill_null(True)` makes each group's first row start a run; without it the comparison against a null shift is null, so that row's `run_id` is null and it drops out of every window keyed on it.

**A grouping axis is data however it arrives** — rows from a fetch, a list the caller passed, or a set the problem fixes (three scenarios, four quartiles).
The closed set is easiest to miss, because it feels like structure.
The tells:

- a name repeated across columns (`low_total`, `high_total`);
- a function returning one column per member of a fixed set;
- `polars.concat([...])` around a comprehension building a frame per member.

Put the values in a small frame, `.join(axis, how="cross")`, and group by that axis alongside the rest; widen once at the end for display.
A comprehension building a *list of expressions* for one `with_columns` is fine — it stays one plan.

```python
# Wrong: a Python loop over scenarios, one frame each.
projected = polars.concat([project(sales, rate) for rate in rates])

# Right: the axis is a column, so one pass covers every scenario.
projected = sales.join(polars.DataFrame({"rate": rates}), how="cross").with_columns(
    polars.col("amount").mul(polars.col("rate").add(1)).alias("projected")
)
```

**Three exits are legitimate**, each at a boundary where no frame exists; say which you take in the docstring, or the next reader deletes it as a lapse:

- **IO** — one request per group because the API serves one at a time; concatenate inside the adapter and return one long frame.
- **Rendering** — a table, chart or response body, iterated once in the driver after all reshaping.
- **Decoding** — the comprehension turning nested records into a frame with a declared schema, once, in the adapter; a second comprehension after the frame exists is the lapse.

**Filter by another frame's keys with a semi join**: `frame.join(wanted, how="semi", on="id")` (or `"anti"` for non-matches).
Pulling `wanted["id"].to_list()` into `is_in` collects the other frame and stops a lazy query being lazy; passing a `Series` to `is_in` is deprecated.
A Python list you already hold is fine in `is_in`.

**Reshape so compared values share a row.** Values in different rows need a window or self-join; in different columns they are a plain expression.
Pivot mid-computation to compare across a key (this month against last), and unpivot back for anything uniform across series.
A chain of joins spreading a key is a hand-rolled `pivot`; per-column selects stacked with `concat`, a hand-rolled `unpivot`.

**Attach a coarser series to finer rows with `join_asof`**, `strategy="backward"` for "the last row at or before this one", both frames sorted on `on`.
With `by=` it warns `Sortedness of columns cannot be checked when 'by' groups provided` on every call however the frames are sorted, so suppress exactly that message:

```python
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Sortedness of columns")
    priced = trades.sort("time").join_asof(
        rates.sort("time"), by="currency", on="time", strategy="backward"
    )
```

## Declare what a join must do

A join's failures all return an ordinary-looking frame.

- **Pass `validate=`** (`"1:1"`, `"1:m"`, `"m:1"`) so a duplicated key raises instead of silently multiplying rows.
- **Pass `coalesce=True` on a full join**, or the result carries `k` and `k_right` and `k` is null on every right-only row.
- **A null key matches nothing, not even null.** Fill it first where null is a real category.

## Name frames and steps

**Name a frame by its contents** — `customers`, `orders` — never `df` or `df_orders`; the type already says it's a frame.
Keep `frame` or `df` for a generic function or placeholder.

**Prefix every frame-to-frame function by its functional shape**, the map/bind vocabulary of `be-functional`:

- **`map_`** — transforms the frame alone: `frame.pipe(map_round_2dp)`.
- **`amap_`** — combines it with independently supplied inputs in a fixed way: `customers.pipe(amap_join_orders, orders)`.
- **`bind_`** — chooses what to do from the frame's own data: `trades.pipe(bind_attach_fx, rate_tables)` joins only the currencies present.

Name the function by `write-python`'s rules, then prefix it — `map_keep_active`, not `map_active`.
The `amap_`/`bind_` line has teeth: `map_` and `amap_` are plan transforms and stay lazy, where `bind_` must materialise to decide, so reach for it only when the logic must see the data.

**Pipe rather than nest.** `orders.pipe(map_keep_paid).pipe(map_total_by_month)` reads in run order with each step's shape visible; nested calls read inside out and hide that both are pipe steps.
Every frame-to-frame function takes a prefix whether or not today's caller pipes it.

**`.pipe` passes extra arguments**, which is how an `amap_` step gets its inputs: `frame.pipe(amap_attach_rates, rates)`.
Carry state as data in the frame (a column, a `struct`) rather than a mutable object the step writes to — that is a side effect, and on a `LazyFrame` it runs at plan-build time, not execution.

## Pipe expressions

`polars.Expr` has `.pipe` too, so an expression helper drops into any context: `polars.col("name").pipe(map_normalise)`.

- **Take a `polars.Expr`, never a column name**, so the same helper serves a literal (`polars.lit(x).pipe(map_normalise)`), another expression's output or a `when/then`.
- **Leave `.alias()` to the caller**, or the helper can't be used twice in one `select`.
- **Pass a second expression through the pipe**: `polars.col("code").pipe(amap_qualify, polars.col("region"))`, reading in data order.
- **Prefix with `map_` or `amap_`; `bind_` never arises**, since an expression is a description with no data to branch on.

## Run a frame function inside an expression

Ask first whether the function should simply be an expression.
Where it genuinely takes a frame and returns a column, an eager ungrouped frame needs nothing special — `frame.with_columns(vwap(frame).alias("vwap"))`.
A `LazyFrame` or per-group application needs a struct and `map_batches`, which calls Python once per batch and stays vectorised (unlike `map_elements`):

```python
frame.with_columns(
    polars.struct("price", "volume")
    .map_batches(lambda s: s.struct.unnest().pipe(vwap), return_dtype=polars.Float64)
    .over("symbol")
    .alias("vwap")
)
```

- **Name the struct's columns, never `polars.struct("*")`**, which defeats projection pushdown and reads every column of the scan.
- **Pass `return_dtype`**, or the engine calls your function on fabricated rows to learn its type, failing at schema resolution if it rejects them.
- **Filter before it**: the optimiser can't push a later filter past it.

The reverse also works: one expression can return several columns as an aliased `polars.struct(...)`, then `.unnest()` — one pass instead of one per column.
