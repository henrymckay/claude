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
from
    read_parquet(
        'data/readings/**/*.parquet',
        hive_partitioning = true,
        hive_types = { 'source': varchar, 'day': date },
        union_by_name = true
    )
where day >= date '2026-01-01';
```

- **`hive_types` names every partition key.** Inference reads a key of digits, `region=42`, as `BIGINT`; pinned, a path that will not cast raises `Unable to cast` instead of changing the column's type.
- **`union_by_name = true` on any tree whose files may differ.** Without it the first file's columns are the table's, and a column added later is absent from every row with no error.
- **A typed literal fails as a binder error** when the column is text: `Cannot compare values of type VARCHAR and type DATE`.
- **Cast an integer `sum`**: it is `HUGEINT`, which reaches Polars as `Decimal(38, 0)`; write `sum(quantity)::bigint`.

## Keep each query in one place

**A view stores its path as written and resolves it from the working directory of whoever queries it**: a relative one works at the prompt that made it and raises `No files found` anywhere else.
So `views.sql` names the tree by a placeholder, and the composition root puts the data directory's absolute path there before running the file — the one value formatted into SQL, from settings, never from input.

## Change a schema

DuckDB has no `user_version` pragma (that is SQLite's): keep the number in a one-row `schema_version` table, updated inside the migration's own transaction so a failed statement rolls both back.

## Test a documented query

For a tree committed in the repository, where the documented paths start at its root:

```python
ROOT = pathlib.Path(__file__).parents[2]
SQL_BLOCK = re.compile(r"```sql\n(.*?)```", flags=re.DOTALL)
QUERIES = SQL_BLOCK.findall((ROOT / "README.md").read_text())


@pytest.mark.parametrize("query", argvalues=QUERIES)
def test_when_documented_query_runs_then_rows_come_back(
    query: str, stored_tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(stored_tree)
    assert duckdb.sql(query).fetchall()


@pytest.mark.parametrize("query", argvalues=QUERIES)
def test_when_documented_query_is_linted_then_it_keeps_the_style(query: str) -> None:
    assert not sqlfluff.lint(query, config_path=str(ROOT / "pyproject.toml"))
```

`stored_tree` is the fixture that writes a few partitions through the real store adapter under `tmp_path` and returns it; `duckdb` and `sqlfluff` sit in the development dependency group, and `parents[2]` is the repository root from `tests/suite/`.
Without `config_path`, `sqlfluff.lint` checks against the `ansi` dialect and its default rules, so a query in the house style fails on rules the project never chose (sqlfluff 4.5).
Fence every query as `sql`: a block in another fence language — `duckdb`, a bare fence — is one the test misses.
