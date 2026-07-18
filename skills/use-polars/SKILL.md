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

# Using Polars

Polars is fast and correct when you work *with* its model: **expressions** evaluated inside **contexts**, over eager `DataFrame`s or lazy `LazyFrame`s.
Most mistakes come from writing pandas habits in Polars syntax.
This file is the mental model; reach into `references/` for concrete recipes.

> Targets **Polars 1.x**. Verify version-specific method names against the
> installed version if something doesn't resolve.
>
> Import convention (house style): `import polars` and qualify — `polars.col(...)`
> — not the conventional `import polars as pl`. See the write-python skill.

## The mental model

**Expressions** describe a computation on columns — `polars.col("a") + polars.col("b")`, `polars.col("x").sum()`.
They're lazy descriptions, run in parallel by the engine, and are the heart of Polars.
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
    .filter(polars.col("amount") > 0)
    .with_columns(
        (polars.col("amount") * polars.col("rate")).alias("value"),
        polars.col("name").str.to_uppercase().alias("name_up"),
    )
    .group_by("category")
    .agg(polars.col("value").sum().alias("total"))
    .sort("total", descending=True)
)
```

**Prefer one fluent method chain.** Build pipelines by **chaining contexts** end to end rather than assigning intermediate frames to variables between steps — a single chain reads as one transformation and stays one query the optimizer can work on.
Wrap it in parentheses for multi-line readability, and don't break the chain without a real reason (reusing an intermediate, or debugging).
Within a context, compute multiple columns in a single `with_columns` rather than many sequential calls — the engine parallelizes expressions within one context.

## Eager vs lazy — prefer lazy for pipelines

- **Eager** (`polars.read_csv`, `df.select(...)`) runs immediately.
  Fine for small data and quick interactive work.
- **Lazy** (`polars.scan_csv`, `df.lazy()`) builds a query plan and only executes on `.collect()`.
  The optimizer can push filters down, prune columns, and stream — so lazy is the default for real pipelines and large files.

```python
result = (
    polars.scan_parquet("events/*.parquet")   # lazy: nothing read yet
    .filter(polars.col("ts") >= start)
    .group_by("user_id")
    .agg(polars.len().alias("n"))
    .collect()                                # execute the optimized plan
)
```

For data bigger than memory, use the streaming engine: `.collect(engine="streaming")` (the older `.collect(streaming=True)` is deprecated).

## Key habits (and pandas traps)

- **No index.** There's no implicit row index and no `.loc`/`.iloc` — select and filter with expressions.
- **Immutable.** Every operation returns a *new* frame; there's no `inplace=`.
  Assign the result.
- **Don't use `.map_elements`/Python loops** for per-row work — express it with column expressions.
  Row-wise Python callbacks kill Polars' performance.
- **Select before compute.** Only pull the columns you need; with lazy frames the optimizer does this for you.
- **`when/then/otherwise`** for conditional columns: `polars.when(cond).then(a).otherwise(b)`.
- **Namespaces** for typed ops: `.str`, `.dt`, `.list`, `.struct`.

## Naming dataframes

Name a frame by its **contents**, not its type: `customers`, `orders`, `trades` — not `df` or `df_customers`.
The type hint (and the Polars API you're calling) already says it's a `DataFrame`/`LazyFrame`, so a `df_` prefix is redundant Hungarian notation.
Reserve a bare `df` (or `frame`) for the cases where the contents genuinely aren't known: a generic placeholder in an example, or a **generic function** that operates on any frame — e.g. a `.pipe()` helper like `def map_round_2dp(df: polars.DataFrame) -> polars.DataFrame`.

## Naming `.pipe()` UDFs: map / amap / bind

When you factor pipeline steps into functions used with `.pipe()`, name them by their functional shape so a reader knows what each does at a glance.
On the surface all three are `DataFrame -> DataFrame`, so the prefix signals **intent**, not the type signature.

- **`map_`** (functor map) — a pure transform of the frame alone, behaviour fixed: `frame.pipe(map_round_2dp)`.
- **`amap_`** (applicative map) — combines the frame with one or more **independently provided** inputs in a **fixed** way; the operation does *not* branch on the data: `customers.pipe(amap_join_orders, orders)`.
- **`bind_`** (monadic bind) — the operation **chosen depends on the frame's own data**: you inspect the contents and branch.
  E.g. attach FX rates by looking at which currencies are actually present and joining only those tables: `trades.pipe(bind_attach_fx, rate_tables)`.

The line between `amap_` and `bind_` is exactly the one between applicative and monad: **an applicative step's behaviour is fixed regardless of the values inside; a bind step's behaviour depends on the materialised data.**
That has teeth in Polars — `map_`/`amap_` are pure plan transforms and stay **lazy**, whereas `bind_` usually has to **materialise** (collect/inspect) the data to decide what to do, breaking laziness.
So reach for `bind_` only when the logic genuinely must see the data; prefer `map_`/`amap_` to keep the query lazy and optimizable.

## Reference cookbooks

Read the relevant file for detail and worked examples:

- `references/expressions.md` — the expression API: selection, conditionals, aggregations, window functions (`.over`), joins, string/date ops.
- `references/pandas-migration.md` — pandas → Polars translations and the gotchas that bite most often.
