---
name: use-polars
description: >-
  How to write correct, idiomatic Polars (the Python DataFrame library) — the
  expression API, lazy vs eager execution, keeping every group in one
  long-form frame instead of looping, ordering a window with order_by rather
  than a prior sort, a reverse cumulative for every later row, calendar
  windows against row windows and the defaults to pin, joining without
  silently multiplying rows, join_asof within groups, the silent traps around
  nulls, NaN and dtypes, naming frames and pipe steps, and the mental-model
  shifts coming from pandas. Load it before the first line of any Polars code,
  even a snippet answered inline. Use whenever working with
  Polars DataFrames or LazyFrames, writing data transformations or analytics
  in Polars, converting pandas code to Polars, joining or reshaping between
  long and wide, writing a rolling or windowed computation, or reading a query
  plan — even if the user only says "polars", "pl.", or names a .parquet/.csv
  workflow they want done with it. Targets Polars 2.x. Layers on write-python
  (its import and naming rules, and the method-over-operator preference) and
  be-functional's map/bind vocabulary.
---

# Use Polars

`polars` is fast and correct when you work with its model: **expressions** evaluated inside **contexts**, over eager `DataFrame`s or lazy `LazyFrame`s.
This targets `polars` 2.x, with `write-python` on top — its import rule included, so `polars.col(...)`, never `pl`, except in an external snippet being quoted — and frame functions named from `be-functional`'s map/bind vocabulary.
Three mistakes account for nearly all that goes wrong: leaving the frame for Python lists and loops, looping over groups instead of stacking them into one frame, and letting `pandas` habits or types leak past the boundary.

**In an existing project, ask first.** Where a codebase already has an established `polars` style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## The mental model

**Expressions** describe a computation on columns — `polars.col("a").add(polars.col("b"))` — and **contexts** (`.select`, `.with_columns`, `.filter`, `.group_by(...).agg(...)`, `.over`) run them in parallel inside the engine; you never loop over rows.

- **`group_by` order is arbitrary** unless `maintain_order=True`, which costs speed; sort the result instead where only the end needs determinism.
- **An aggregation can take a condition**: `polars.col("v").filter(polars.col("v").gt(0)).sum()`.

**Order a window with `order_by=`, not a `.sort` ahead of it.** `.shift`, every cumulative and `.first`/`.last` read row order, so an unsorted input gives a wrong answer and nothing raises; `.over(group, order_by="time")` fixes the order inside the window whatever the frame's order, where a `.sort` before it is undone by the next join and nothing says so.
`join_asof` is the exception: it has no `order_by`, so both frames are sorted on `on` (see Stay in the frame).

**A time window is `rolling_*_by`; a row window is `rolling_*`.** `rolling_mean_by("ts", window_size="3d")` covers three calendar days whether they hold three rows or none, where `rolling_mean(window_size=3)` averages the last three rows wherever they fall; `min_samples` (default `1`) decides whether a short window reports or returns null, and `closed` (default `"right"`) which end the window includes.
Pin all three with a dependency test (see `write-tests`).
A per-item window is `rolling_mean_by("day", window_size="7d", min_samples=7).over("item", order_by="day")`: each item runs over its own days whatever the frame's order, `min_samples` equal to the window leaves the first six days null rather than a mean of fewer, and a calendar window over a gap leaves the missing days unfilled — no row appears for them, and a day whose window spans the gap is null (Polars 2.1).

**Address a class of columns with `polars.selectors`.** `polars.selectors.numeric().fill_null(value=0)` resolves against the real schema when the query runs, so it covers the column added next month; a hand-listed set is pinned to the day it was written.
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

**Write one fluent method chain.** Chain contexts end to end in parentheses rather than binding intermediate frames: it reads as one transformation, and on an eager frame each bound intermediate is materialised in full.
Compute several columns in one `with_columns`, which the engine parallelises.
A chain opening with a function — `polars.concat(...)`, `polars.read_csv(...)` — is still a chain; that unannounced start is where most single-use intermediates come from.

**Keep control flow inside the chain.** An `if` that inspects the frame splits one transformation into branches each needing a test; use `when/then/otherwise` for values and `.filter` for rows.
An empty input rarely needs its own path — the chain returns an empty frame with the right schema, where an early return duplicates the schema somewhere it can drift.
Where a column may be absent from a genuinely open schema, `polars.selectors.by_name("a", "b", require_all=False)` avoids the `if`; where the caller knows the columns, require them.

**Expression methods over operators**, `write-python`'s preference: `.mul`, `.gt`, `.eq` and the rest also dodge the precedence trap in `polars.col("a") > 0 & polars.col("b") > 0`; an operator stays where precedence is unambiguous inside a one-line expression, and `&`, `|`, `~` are always operators, since their method spellings read worse.

**Name a column with `.alias()`, not a keyword argument.** The keyword form (`with_columns(total=...)`) belongs to the context, so the name is lost when the expression moves into a helper or a second context; `.alias()` travels with it, and spells names Python can't, like `total (£)`.

## Silent traps

Each of these returns a plausible frame rather than raising.

**Give a windowed step its own column before windowing it again.** A second `.over()` chained onto an already-windowed expression discards the inner partition.
A single `.over()` is fine however much precedes it.

```python
# Wrong: the .over("session") is discarded; cum_sum runs within the user.
frame.with_columns(
    polars.col("amount").cum_sum().over("session").first().over("user").alias("first")
)

# Right: one .over() per expression, each result carried in a column.
frame.with_columns(
    polars.col("amount").cum_sum().over("session").alias("running")
).with_columns(polars.col("running").first().over("user").alias("first"))
```

**An empty `pivot` loses its value columns.** With no rows there is nothing to spread, so only the index columns return and a later `select` raises `ColumnNotFoundError` only when a filter empties the frame.
Restore the shape without branching: `polars.concat([pivoted, empty], how="diagonal")`, where `empty` is a zero-row frame declaring the full schema.

**`NaN` compares false against everything, null included.** A ratio against a group aggregate — `polars.col("x").truediv(polars.col("x").max().over("g"))` — yields `NaN` where the maximum is zero, and every later filter on that column silently drops the row; decide the zero case with `when` where you divide.

**A comparison with null is null, not false**, so `.filter` drops the row; `.eq_missing()` is the null-safe form, counting two nulls equal.

**`.sum()` of an all-null column is `0`; `.mean()` is null.**

**Declare a dtype wherever you didn't choose the contents.** An empty list or an all-`None` column infers `Null`, not an empty `String`, so `concat`, a join or any `.str` method against it raises.
The type also varies by input: a field present for some records and absent for others infers `Int64` in one batch and `Null` in the next, and the two won't concatenate.
Declare the **widest** type the column can hold, on anything built from a response.
For a one-column frame, `polars.Series("id", ids, dtype=polars.String).to_frame()` states name and type once each.

## Unlearn `pandas`

- **Convert at the boundary and never reach back.** Convert another library's frame with `polars.from_pandas` at once; tidying in `pandas` first does the work in the weaker API and leaks its types into your signatures.
- **Pass `include_index=True` when the index means something** — the default drops it silently.
- **Flatten a column `MultiIndex` before converting** (`.stack(level=..., future_stack=True)`), the one `pandas` call with no `polars` equivalent.
- **Install `pyarrow`** for `from_pandas` beyond plain numpy-backed columns.

## Eager vs lazy

A real pipeline is lazy from the scan and collected once:

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

**Keep every group in one long-form frame**, computed across together; most work is plain column expressions with no `.over` at all.
Reach for `.over(group)` only where an operation must respect group boundaries — a shift, a cumulative, a rank.
Even sequential per-group logic stays in the frame: a run length is a change flag, a `cum_sum` numbering the runs, and a count within each run.

```python
runs = frame.with_columns(
    polars.col("state")
    .ne(polars.col("state").shift(n=1))
    .fill_null(value=True)
    .cum_sum()
    .over("group", order_by="order")
    .alias("run_id")
).with_columns(
    polars.int_range(start=1, end=polars.len().add(1))
    .over("group", "run_id", order_by="order")
    .alias("run_len")
)
```

`.fill_null(value=True)` makes each group's first row start a run; without it the comparison against a null shift is null, so that row's `run_id` is null and it drops out of every window keyed on it.
The `order_by` on each `.over` is what makes `.shift` and `.cum_sum` read the rows in order; the frame itself is never sorted.

**A cumulative over every later row is the same window read backwards**: `reverse=True` on the cumulative under the same ascending `order_by`, after a `shift(n=-1)` that leaves the row itself out.

```python
remaining = payments.with_columns(
    polars.col("amount")
    .shift(n=-1, fill_value=0)
    .cum_sum(reverse=True)
    .over("account", order_by="day")
    .alias("still_to_come")
)
```

`fill_value` is the operation's identity, 0 for a sum and 1 for a product; a bare shift leaves each group's last row null, where the answer is that nothing is still to come.

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
With `by=` pass `check_sortedness=False`, since the engine cannot check order within groups and otherwise warns on every call however the frames are sorted:

```python
priced = orders.sort("time").join_asof(
    rates.sort("time"),
    by="currency",
    check_sortedness=False,
    on="time",
    strategy="backward",
)
```

## Declare what a join must do

A join's failures all return an ordinary-looking frame.

- **Pass `validate=`** (`"1:1"`, `"1:m"`, `"m:1"`) so a duplicated key raises instead of silently multiplying rows.
- **Pass `coalesce=True` on a full join**, or the result carries `k` and `k_right` and `k` is null on every right-only row.
- **A null key matches nothing, not even null.** Fill it first where null is a real category.

## Name frames and steps

**Name a frame by its contents** under `write-python`'s naming rules — `customers`, never `df_orders`, since the type already says it's a frame — keeping `frame` for a generic function's parameter.

**Prefix every frame-to-frame function by its functional shape**, the map/bind vocabulary of `be-functional`:

- **`map_`** — transforms the frame alone: `frame.pipe(map_round_2dp)`.
- **`amap_`** — combines it with independently supplied inputs in a fixed way: `customers.pipe(amap_join_orders, orders)`.
- **`bind_`** — chooses what to do from the frame's own data: `orders.pipe(bind_attach_rates, rate_tables)` joins only the currencies present.

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
Where it genuinely takes a frame and returns a column, an eager ungrouped frame needs nothing special — `frame.with_columns(weighted_mean(frame).alias("weighted_mean"))`.
A `LazyFrame` or per-group application needs a struct and `map_batches`, which calls Python once per batch and stays vectorised (unlike `map_elements`):

```python
frame.with_columns(
    polars.struct("price", "quantity")
    .map_batches(
        lambda s: s.struct.unnest().pipe(weighted_mean), return_dtype=polars.Float64
    )
    .over("store")
    .alias("weighted_mean")
)
```

- **Name the struct's columns, never `polars.struct("*")`**, which defeats projection pushdown and reads every column of the scan.
- **Pass `return_dtype`**, or the engine calls your function on fabricated rows to learn its type, failing at schema resolution if it rejects them.
- **Filter before it**: the optimiser can't push a later filter past it.

The reverse also works: one expression can return several columns as an aliased `polars.struct(...)`, then `.unnest()` — one pass instead of one per column.
