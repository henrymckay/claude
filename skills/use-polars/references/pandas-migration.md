# pandas → Polars migration

Translations and the traps that bite pandas users most. The recurring theme:
Polars has **no index**, is **immutable**, and wants **expressions**, not
row-wise Python. (House style: `import polars`, qualified — no `as pl`.)

## Mindset shifts

| pandas habit | Polars way |
|---|---|
| implicit row index, `.loc`/`.iloc` | no index — `.filter()` / `.select()` with expressions |
| `inplace=True`, column assignment mutates | every op returns a new frame; assign the result |
| `df.apply(fn, axis=1)` row-wise | column expressions; avoid per-row Python |
| chained boolean masks `df[df.a>0]` | `df.filter(polars.col("a") > 0)` |
| `groupby().agg()` keeps index | `group_by().agg()` returns plain columns |
| `NaN` == missing | null (missing) and `NaN` (float) are distinct |

## Direct translations

```python
# select columns
df[["a", "b"]]                        -> df.select("a", "b")

# new column
df["c"] = df["a"] + df["b"]           -> df.with_columns((polars.col("a") + polars.col("b")).alias("c"))

# filter rows
df[df["a"] > 0]                       -> df.filter(polars.col("a") > 0)

# rename
df.rename(columns={"a": "b"})         -> df.rename({"a": "b"})

# sort
df.sort_values("a", ascending=False)  -> df.sort("a", descending=True)

# groupby aggregate
df.groupby("k")["v"].sum()            -> df.group_by("k").agg(polars.col("v").sum())

# value_counts
df["k"].value_counts()                -> df["k"].value_counts()   # returns a DataFrame

# fillna
df["x"].fillna(0)                     -> polars.col("x").fill_null(0)

# apply row-wise (AVOID) — express instead
df.apply(lambda r: r.a * r.b, axis=1) -> (polars.col("a") * polars.col("b"))
```

## Interop

```python
polars.from_pandas(pdf)     # pandas -> Polars
df.to_pandas()              # Polars -> pandas
df.to_numpy()               # to numpy
```

**Switching mid-chain.** When you need a pandas-only operation inside a Polars
pipeline, drop to pandas and come straight back without breaking the chain —
`.pipe(polars.from_pandas)` works because pandas' `.pipe()` hands the frame to
`polars.from_pandas`:

```python
result = (
    df                              # Polars
    .to_pandas()
    .some_pandas_only_op()          # pandas
    .pipe(polars.from_pandas)       # back to Polars
    .with_columns(polars.col("x") * 2)
)
```

This materialises the data (a `LazyFrame` must be `.collect()`-ed first) and
costs a conversion each way, so reserve it for genuine pandas-only needs.

Zero-copy where possible via Arrow, but converting back and forth in a hot loop
defeats the purpose — convert once at the boundary.

## Reading/writing

```python
polars.read_csv("f.csv")     / polars.scan_csv("f.csv")        # eager / lazy
polars.read_parquet("f.pq")  / polars.scan_parquet("f.pq")
df.write_csv("out.csv")
df.write_parquet("out.pq")   # prefer parquet: typed, compressed, columnar
```

Prefer `scan_*` + `.collect()` over `read_*` for anything nontrivial so the
query optimizer can push work down and read only what's needed.

## When pandas is still fine

Polars shines for larger data and pipeline-style transforms. For tiny
interactive pokes, or when a required library only speaks pandas, converting at
the boundary is reasonable — just don't scatter conversions through a pipeline.
