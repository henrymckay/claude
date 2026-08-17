---
name: use-polars
description: >-
  How to write correct, idiomatic Polars (the Python DataFrame library) — the
  expression API, lazy vs eager execution, and the mental-model shifts coming
  from pandas. Use whenever working with Polars DataFrames/LazyFrames, writing
  data transformations or analytics in Polars, converting pandas code to
  Polars, or debugging Polars queries — even if the user only says "polars",
  "pl.", or names a .parquet/.csv workflow they want done with it. Targets
  Polars 1.x. Detailed cookbooks live in references/. Polars-specific; the
  general write-python conventions still apply on top.
---

# Use Polars

`polars` is fast and correct when you work *with* its model: **expressions** evaluated inside **contexts**, over eager `DataFrame`s or lazy `LazyFrame`s.
Most mistakes come from writing `pandas` habits in `polars` syntax.
This file is the mental model; reach into `references/` for concrete recipes, and `write-python`'s general conventions apply on top.

**In an existing project, ask first.** Where a codebase already has an established `polars` style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

Targets `polars` 1.x.
Verify version-specific method names against the installed version if something doesn't resolve.

Import convention (house style): `import polars` and qualify — `polars.col(...)` — not the conventional `import polars as pl`.

## The mental model

**Expressions** describe a computation on columns — `polars.col("a").add(polars.col("b"))`, `polars.col("x").sum()`.
They're lazy descriptions, run in parallel by the engine, and are the heart of `polars`.
You almost never loop over rows.

**Contexts** are where expressions run:

- `.select(...)` — pick/compute columns (result has only what you select).
- `.with_columns(...)` — add/replace columns, keep the rest.
- `.filter(...)` — keep rows matching a boolean expression.
- `.group_by(...).agg(...)` — aggregate per group.

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

**Prefer one fluent method chain.** Build pipelines by **chaining contexts** end to end rather than assigning intermediate frames to variables between steps — a single chain reads as one transformation and stays one query the optimiser can work on.
Wrap it in parentheses for multi-line readability, and don't break the chain without a real reason (reusing an intermediate, or debugging).
Within a context, compute multiple columns in a single `with_columns` rather than many sequential calls — the engine parallelises expressions within one context.

**Prefer expression methods to operator symbols.** Write `polars.col("a").mul(polars.col("b"))` and `polars.col("x").gt(0)`, not `*` and `>`.
The method form chains without wrapping parentheses and reads consistently with the rest of the expression API (`.sum()`, `.alias()`, `.over()`).
Arithmetic and comparison operators all have method equivalents: `.add`, `.sub`, `.mul`, `.truediv`, `.floordiv`, `.mod`, `.pow`, and `.gt`, `.ge`, `.lt`, `.le`, `.eq`, `.ne`.
This also sidesteps the precedence trap — `polars.col("a").gt(0) & polars.col("b").gt(0)` needs no inner parentheses, where the operator form does.
Keep the boolean combinators `&`, `|`, `~` as operators, though — their method spellings (`.and_`, `.or_`, `.not_`) read worse and they are near-universal for combining masks.

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

## Stay in the dataframe

**If data is a dataframe, or you're doing dataframe-shaped work, do it *in* `polars` — don't drop to Python lists and loops.**
When another library hands you a frame (a `pandas` result from `yfinance`, an API), convert it once with `polars.from_pandas` and keep going with expressions.
Pulling columns out to Python lists and looping, comprehending, or `functools.reduce`-ing over them throws away the engine's speed and the query optimiser, and it's the most common way people accidentally leave `polars`.
Comparing a column to an earlier row, running a count, grouping by a key — that is all expression work, so it belongs in the frame.

**Keep every group in one long-form frame — don't split it up.**
Stack all groups (all tickers, all users, all categories) into a single frame and compute across them together, rather than holding a frame per group and looping.
Most work is plain column expressions that apply to every group in one pass — element-wise maths, filters, `when/then` — with **no `.over` at all**.
Reach for `.over(group)` only where an operation must respect group boundaries: a `.shift`, a cumulative, a rank, or a per-group window.
Even sequential per-group logic stays in the one frame that way — a consecutive-run length or reset-on-change counter is a change flag, a `cum_sum` to number the runs, and a cumulative count within each run, all `.over(group)`, not a Python accumulator (see the run-length recipe in `references/expressions.md`).
Splitting into per-group sub-frames and looping is the same mistake as looping rows one at a time, a level up.

## Habits and `pandas` traps

- **No index.** There's no implicit row index and no `.loc`/`.iloc` — select and filter with expressions.
- **Immutable.** Every operation returns a *new* frame; there's no `inplace=`.
Assign the result.
- **Don't use `.map_elements`/Python loops** for per-row work — express it with column expressions.
Row-wise Python callbacks kill `polars`'s performance.
- **Select before compute.** Only pull the columns you need; with lazy frames the optimiser does this for you.
- **`when/then/otherwise`** for conditional columns: `polars.when(cond).then(a).otherwise(b)`.
- **Namespaces** for typed ops: `.str`, `.dt`, `.list`, `.struct`.

## Name dataframes

Name a frame by its **contents**, not its type: `customers`, `orders`, `trades` — not `df` or `df_customers`.
The type hint (and the `polars` API you're calling) already says it's a `DataFrame`/`LazyFrame`, so a `df_` prefix is redundant Hungarian notation.
Reserve a bare `df` (or `frame`) for the cases where the contents genuinely aren't known: a generic placeholder in an example, or a **generic function** that operates on any frame — e.g. a `.pipe()` helper like `def map_round_2dp(df: polars.DataFrame) -> polars.DataFrame`.

## Name `.pipe()` UDFs

When you factor pipeline steps into UDFs (user-defined functions) used with `.pipe()`, name them by their functional shape so a reader knows what each does at a glance.
The map/bind vocabulary is `be-functional`'s — this is its composition and monad guidance applied to frames.
On the surface all three are `DataFrame -> DataFrame`, so the prefix signals **intent**, not the type signature.

- **`map_`** (functor map) — a pure transform of the frame alone, behaviour fixed: `frame.pipe(map_round_2dp)`.
- **`amap_`** (applicative map) — combines the frame with one or more **independently provided** inputs in a **fixed** way; the operation does *not* branch on the data: `customers.pipe(amap_join_orders, orders)`.
- **`bind_`** (monadic bind) — the operation **chosen depends on the frame's own data**: you inspect the contents and branch.
E.g. attach FX rates by looking at which currencies are actually present and joining only those tables: `trades.pipe(bind_attach_fx, rate_tables)`.

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

## Reference cookbooks

Read the relevant file for detail and worked examples:

- `references/expressions.md` — the expression API: selection, conditionals, aggregations, window functions (`.over`), joins, string/date ops.
- `references/pandas-migration.md` — `pandas` → `polars` translations and the gotchas that bite most often.
