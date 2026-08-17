# pandas → Polars migration

Translations and the traps that bite `pandas` users most.
The recurring theme: `polars` has **no index**, is **immutable**, and wants **expressions**, not row-wise Python.
(House style: `import polars`, qualified — no `as pl`.)

## Mindset shifts

| `pandas` habit | `polars` way |
|---|---|
| implicit row index, `.loc`/`.iloc` | no index — `.filter()` / `.select()` with expressions |
| `inplace=True`, column assignment mutates | every op returns a new frame; assign the result |
| `df.apply(fn, axis=1)` row-wise | column expressions; avoid per-row Python |
| chained boolean masks `df[df.a>0]` | `df.filter(polars.col("a").gt(0))` |
| `groupby().agg()` keeps index | `group_by().agg()` returns plain columns |
| `NaN` == missing | null (missing) and `NaN` (float) are distinct |

## Direct translations

| `pandas` | `polars` |
|---|---|
| `df[["a", "b"]]` | `df.select("a", "b")` |
| `df["c"] = df["a"] + df["b"]` | `df.with_columns(polars.col("a").add(polars.col("b")).alias("c"))` |
| `df[df["a"] > 0]` | `df.filter(polars.col("a").gt(0))` |
| `df.rename(columns={"a": "b"})` | `df.rename({"a": "b"})` |
| `df.sort_values("a", ascending=False)` | `df.sort("a", descending=True)` |
| `df.groupby("k")["v"].sum()` | `df.group_by("k").agg(polars.col("v").sum())` |
| `df["k"].value_counts()` | `df["k"].value_counts()`, returning a `DataFrame` |
| `df["x"].fillna(0)` | `polars.col("x").fill_null(0)` |
| `df.apply(lambda r: r.a * r.b, axis=1)` | `polars.col("a").mul(polars.col("b"))` |

The row-wise `apply` is the one to unlearn — there is no `polars` equivalent because the column expression *is* the answer.

## Interop

```python
polars.from_pandas(pdf)     # pandas -> Polars
df.to_pandas()              # Polars -> pandas
df.to_numpy()               # to numpy
```

**Switching mid-chain.** When you need a `pandas`-only operation inside a `polars` pipeline, drop to `pandas` and come straight back without breaking the chain — `.pipe(polars.from_pandas)` works because `pandas`'s `.pipe()` hands the frame to `polars.from_pandas`:

```python
result = (
    df                              # Polars
    .to_pandas()
    .some_pandas_only_op()          # pandas
    .pipe(polars.from_pandas)       # back to Polars
    .with_columns(polars.col("x").mul(2))
)
```

This materialises the data (a `LazyFrame` must be `.collect()`-ed first) and costs a conversion each way, so reserve it for genuine `pandas`-only needs.

Zero-copy where possible via Arrow, but converting back and forth in a hot loop defeats the purpose — convert once at the boundary.

## Reading and writing

```python
polars.read_csv("f.csv")        # eager
polars.scan_csv("f.csv")        # lazy
polars.read_parquet("f.pq")
polars.scan_parquet("f.pq")
df.write_csv("out.csv")
df.write_parquet("out.pq")      # prefer parquet: typed, compressed, columnar
```

Prefer `scan_*` + `.collect()` over `read_*` for anything nontrivial so the query optimiser can push work down and read only what's needed.

## When `pandas` is still fine

`polars` shines for larger data and pipeline-style transforms.
For tiny interactive pokes, or when a required library only speaks `pandas`, converting at the boundary is reasonable — just don't scatter conversions through a pipeline.
