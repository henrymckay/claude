# Write SQL in DuckDB

The dialect-neutral decisions are in `SKILL.md`; this is how they land in DuckDB 2.x.
Picking DuckDB, and handing a result back as a frame, are `store-data`'s.

## Write the engine's dialect

Read a hive-partitioned Parquet tree with every inferred type pinned and columns matched by name:

```sql
select
    station,
    day,
    value
from read_parquet(
    'data/readings/**/*.parquet',
    hive_partitioning = true,
    hive_types = {'source': varchar, 'day': date},
    union_by_name = true
)
where day >= date '2026-01-01';
```

- **`hive_types` names every partition key.** Inference reads `day=2026-01-31` as `DATE` and a key of digits, `region=42`, as `BIGINT`; pinned, a path that will not cast raises `Unable to cast` instead of changing the column's type.
- **`union_by_name = true` on any tree whose files may differ.** Without it the first file's columns are the table's, and a column added later is absent from every row with no error.
- **A typed literal fails as a binder error** when the column is text: `Cannot compare values of type VARCHAR and type DATE`.
- **Cast an integer `sum`**: it is `HUGEINT`, which reaches Polars as `Decimal(38, 0)`; write `sum(quantity)::bigint`.

## Keep each query in one place

**A view stores its path as written and resolves it from the working directory of whoever queries it**: a relative one works at the prompt that made it and raises `No files found` anywhere else.
So `views.sql` names the tree by a placeholder, and the composition root, which knows the data directory, puts its absolute path there before running the file — the one value formatted into SQL, and it comes from settings, never from input.

## Change a schema

DuckDB has no `user_version` pragma, which is SQLite's: a DuckDB file keeps the number in a one-row `schema_version` table, updated inside the migration's own transaction, which rolls the schema change back with it when a statement fails.

## Test a documented query

For a tree committed in the repository, where the documented paths start at its root:

```python
README = pathlib.Path(__file__).parents[2] / "README.md"
SQL_BLOCK = re.compile(r"```sql\n(.*?)```", flags=re.DOTALL)


@pytest.mark.parametrize("query", argvalues=SQL_BLOCK.findall(README.read_text()))
def test_when_documented_query_runs_then_rows_come_back(
    query: str, stored_tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(stored_tree)
    assert duckdb.sql(query).fetchall()
```

`stored_tree` is the fixture that writes a few partitions through the real store adapter under `tmp_path` and returns it; `duckdb` sits in the development dependency group, and `parents[2]` is the repository root from `tests/suite/`.
A query the README documents and this test has not run is the one a schema change breaks unseen, so a block in another fence language — `duckdb`, a bare fence — is a block the test misses: fence every query as `sql`.
