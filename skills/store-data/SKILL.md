---
name: store-data
description: >-
  Where a project's data lives and how it is written and read —
  hive-partitioned Parquet for pipeline output, DuckDB to query it, MotherDuck
  when another machine or a phone chat must reach it, SQLite for small
  single-writer state, Postgres only for a multi-writer service, and no ORM;
  the data directory, its environment override and its tree; one file per
  partition, overwritten atomically so a re-run is idempotent; the
  raw-response archive, the rejected-row quarantine, the run manifest and
  recomputed metrics; scanning lazily from Polars or DuckDB and compacting
  only once measured; and testing a store on a temporary directory with an
  in-memory fake for the core. Use whenever deciding where a project's output
  goes, writing a store adapter, choosing between Parquet, DuckDB, SQLite or
  Postgres, laying out a data directory, writing or scanning Parquet,
  recording what a run did, or sharing data with another machine — even if the
  user just says "save the results", "where should this live" or "add a
  database". Targets Polars 2.x and DuckDB 2.x. Layers on structure-python
  (the store is an adapter) and use-polars; run-unattended reads the manifest
  and holds the lock.
---

# Store data

Where a project's data lives, how it is written so a re-run is safe, and how it is read back.
The store is a driven adapter in `structure-python`'s terms, the frames it moves obey `use-polars`, and `run-unattended` reads the manifest it keeps.
Three mistakes account for most lost data: appending on a re-run, so a retried night doubles its rows; writing a file in place, so a crash leaves a half-file every later scan trips over; and discarding the raw response, so a parser fix cannot reach history.

**In an existing project, ask first.** Where a repo already has a store, check with the user whether to keep it or apply this layout, and prefer this layout unless they choose to keep theirs.

## Pick the engine

Each pick is the default for its need; a `PLAN.md` decision overrides it, and a measurement (a scan that takes seconds to plan, a query that no longer fits one machine) goes under Decisions as proposed and is raised with the user before the layout changes.

- **Hive-partitioned Parquet** for pipeline output — `records/source=<s>/day=<d>/part.parquet`, scanned as one table.
A single DuckDB file would be simpler to hand around, but it is one writer's binary blob: a crash mid-write risks the whole table where Parquet risks one day, and nothing but DuckDB can read it.
- **DuckDB** to query the Parquet locally — `read_parquet` over the tree, with views for the questions asked often.
Loading into Polars and filtering there works for one frame; DuckDB joins, aggregates and prunes partitions across the whole tree without a materialising step.
- **MotherDuck** when more than one machine, or a phone chat, must reach the data: the same SQL over `duckdb.connect("md:<db>")`, with the token in the environment as `motherduck_token` (lower case, per MotherDuck's docs).
Syncing Parquet to a bucket is the alternative and costs a sync step and credentials on every reader.
- **SQLite** for small single-writer app state — a watermark table, a key-value cache — through the stdlib `sqlite3`.
A JSON file is the alternative and loses atomic updates the moment two fields change together.
- **Postgres** only for a multi-writer service; it earns a server to run, so a `PLAN.md` decision names it.

**No ORM.** Frames cross the boundary as frames: `polars.read_database` with a `sqlite3` connection, `write_database(..., engine="adbc")` with `adbc-driver-sqlite` installed — the default `sqlalchemy` engine refuses without `pandas`.

## Lay out the data directory

Runtime data lives outside the repo and the package, in one directory the settings resolve once at the composition root:

```python
class Settings(pydantic_settings.BaseSettings):
    """Where the tool keeps its data, overridable per machine."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="MYAPP_")

    data_dir: pathlib.Path = platformdirs.user_data_path("myapp")
```

`MYAPP_DATA_DIR` overrides the platform default (`~/Library/Application Support/myapp` on macOS, `~/.local/share/myapp` on Linux), which is what a test, a second checkout and a scheduler each need.
Settings mechanics are in `write-entry-points`' Python reference.

```text
<data_dir>/
  items.csv         user-editable list of what to fetch (see structure-python, Data)
  raw/              what each source sent, as sent
  records/          the parsed, validated output
  rejected/         rows that failed validation, with a reason
  metrics.parquet   derived numbers, recomputed whole
  runs.parquet      the run manifest
  logs/
  .lock             the overlap lock (see run-unattended)
```

A tiny tool with one output is one Parquet file at the root; grow the tree when a second source or a second kind of output arrives.

## Write a partition

**Overwrite the day's partition; never append to it.** The nightly command's unit of work is one source for one day, so re-running it must produce the same tree: with append, the retry after a half-failed night stores every row twice and no later query can tell.

**One file per partition, named by you, written atomically.** Write to a temporary file in the partition's directory and `os.replace` it onto `part.parquet`; the rename is atomic on the same filesystem, so a reader sees the old file or the new one and never a torn one, and a crash leaves only a temp file to sweep.

```python
def write_partition(frame: polars.DataFrame, partition: pathlib.Path) -> None:
    """Replace the partition's file so a re-run leaves the same tree."""
    partition.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False, dir=partition, suffix=".parquet"
    ) as tmp:
        frame.write_parquet(tmp.name)
    os.replace(tmp.name, partition / "part.parquet")
```

`write_parquet(path, partition_by=[...])` and `sink_parquet(polars.PartitionBy(...))` build the same `key=value` tree in one call and earn their place for a one-off bulk load; both name the files themselves (`00000000.parquet`), so a re-run that produces fewer chunks leaves the old ones in place, and neither renames atomically.

**Keep the partition keys out of the file.** `source` and `day` are read from the path on scan; when the file also holds a `day` column the scan keeps the file's copy and drops the path's, so `day` comes back as a string and a filter on a date matches nothing.

## Keep what the source sent

- **Archive the raw response** under `raw/source=<s>/day=<d>/` in the wire format it arrived in, before parsing.
A parser fix then re-parses history offline; without it the fix applies from tonight and every earlier day keeps the bug.
- **Quarantine rejected rows** under `rejected/` in the same partition layout, with a `reason` column.
Dropping them silently makes a schema change at the source look like a quiet day; the quarantine makes it a count.
- **Write a run manifest**, `runs.parquet`: one row per source per run with `source`, `day`, `rows`, `rejected`, `started`, `ended` and `outcome`.
It is small, so append by reading, concatenating and overwriting the file atomically; `run-unattended`'s `status` command reads it, and nothing else records that a night happened.
- **Store metrics as a full recompute** overwriting `metrics.parquet` from the records, until a timed check shows the recompute exceeding the nightly window; an incremental update is a second code path that drifts from the full one, so it is earned by that measurement and nothing else.

## Read

**Scan lazily and collect once**, pushing the filter down so only the partitions asked for are opened:

```python
readings = (
    polars.scan_parquet(data_dir / "records", hive_partitioning=True)
    .filter(polars.col("source").eq("weather"), polars.col("day").ge(start))
    .collect()
)
```

`hive_partitioning=True` adds `source` and `day` as columns, with `day` inferred as `Date` from `YYYY-MM-DD`; pass `hive_schema` when inference guesses wrong, such as a numeric-looking identifier that must stay a string.

In DuckDB the same tree is a table: `read_parquet('<data_dir>/records/**/*.parquet', hive_partitioning = true)`.
Wrap the questions asked often in views in a local `.duckdb` file beside the data, and hand results back as frames with `.pl()` — which needs `pyarrow` installed, a dependency the Parquet path never needed.
A Polars frame in scope is queryable by name (`duckdb.sql("select * from readings")`), so a transform written in SQL costs no export step.

**Compact only when the file count hurts** — thousands of files, a scan whose planning is visible — and then by closed year: rewrite each year's days into `history/source=<s>/year=<y>/part.parquet`, keeping `day` as a column, and read `records` and `history` as a `polars.concat` of two scans.
Rewriting earlier is a second layout to maintain for a cost nobody has measured.

## Test the store

- **Exercise the real adapter on `tmp_path`** with a round-trip property: whatever frame is written is read back equal, through `polars.testing.assert_frame_equal`, including the partition columns and after a second write of the same day.
- **Give the core an in-memory fake** satisfying the same port — a dict keyed by source and day — so operations run with no filesystem.
- **Point every test's `data_dir` at `tmp_path`** through the settings override, never the platform default, or a test run writes into the real store.

The shape of the tests is `write-tests`; the port they share is `structure-python`'s Declare a port.
