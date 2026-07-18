# Polars expression cookbook

Worked recipes for the expression API. Assumes `import polars` (house style — no
`as pl`) and Polars 1.x. Expressions run inside contexts (`select`,
`with_columns`, `filter`, `group_by().agg()`).

## Selecting & referencing columns

```python
polars.col("a")                      # one column
polars.col("a", "b")                 # several
polars.col(polars.Int64)             # by dtype
polars.all()                         # every column
polars.exclude("id")                 # all but some
polars.col("^prefix_.*$")            # by regex
df.select(polars.col("a").alias("x"))
```

## Computed & conditional columns

```python
df.with_columns(
    (polars.col("a") + polars.col("b")).alias("sum"),
    polars.when(polars.col("score") >= 50)
      .then(polars.lit("pass"))
      .otherwise(polars.lit("fail"))
      .alias("result"),
)
```

Chain multiple `when/then` before the final `otherwise` for multi-branch logic.

## Filtering

```python
df.filter(polars.col("amount") > 0)
df.filter((polars.col("a") > 0) & (polars.col("b").is_not_null()))  # & | ~, parenthesize
df.filter(polars.col("cat").is_in(["x", "y"]))
```

## Aggregation

```python
df.group_by("category").agg(
    polars.len().alias("n"),                          # row count per group
    polars.col("value").sum().alias("total"),
    polars.col("value").mean().alias("avg"),
    polars.col("name").n_unique().alias("distinct_names"),
    polars.col("value").filter(polars.col("value") > 0).sum().alias("pos_total"),
)
```

`group_by(..., maintain_order=True)` if you need deterministic group order
(slower). Common reducers: `sum`, `mean`, `min`, `max`, `median`, `std`,
`first`, `last`, `count`, `n_unique`, `quantile`.

## Window functions with `.over`

Aggregate *without collapsing rows* — like a SQL window / pandas groupby-
transform:

```python
df.with_columns(
    polars.col("value").sum().over("category").alias("cat_total"),
    (polars.col("value") / polars.col("value").sum().over("category")).alias("share"),
    polars.col("value").rank().over("category").alias("rank_in_cat"),
)
```

## Joins

```python
a.join(b, on="id", how="inner")            # inner | left | full | semi | anti | cross
a.join(b, left_on="uid", right_on="id", how="left")
a.join_asof(b, on="ts", by="key")          # nearest-key temporal join
```

## String & date namespaces

```python
polars.col("name").str.to_uppercase()
polars.col("name").str.contains(r"^A")          # regex
polars.col("name").str.strip_chars()
polars.col("email").str.split("@").list.last()

polars.col("ts").dt.year()
polars.col("ts").dt.truncate("1d")              # floor to day
(polars.col("end") - polars.col("start")).dt.total_seconds()
```

## List & struct namespaces

```python
polars.col("tags").list.len()
polars.col("tags").list.contains("urgent")
polars.col("values").list.eval(polars.element() * 2)   # map within each list
df.group_by("k").agg(polars.col("v"))                  # -> a List column per group
```

## Reshaping

```python
df.pivot(values="v", index="row", on="col", aggregate_function="sum")
df.unpivot(index="id")                          # wide -> long (formerly melt)
df.explode("tags")                              # one row per list element
```

## Nulls

```python
polars.col("x").is_null(), polars.col("x").is_not_null()
polars.col("x").fill_null(0)
polars.col("x").fill_null(strategy="forward")
df.drop_nulls(subset=["x"])
```
Note: Polars separates null (missing) from `NaN` (float not-a-number) — they're
not the same, unlike pandas.
