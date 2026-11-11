---
name: store-data
description: >-
  Where a project's data lives and how it is written and read —
  hive-partitioned Parquet for pipeline output, read by Polars in code and
  queried across the tree by DuckDB; DuckLake or Delta Lake once a write
  spans partitions, corrects rows or must read an earlier state, and what
  each costs; MotherDuck when another machine or a phone chat must reach it,
  with the DuckDB client it accepts; SQLite for small single-writer state,
  Postgres only for a multi-writer service, and no ORM; the data directory
  and its tree, named in the plan's terms; the store as a write port and a
  read port over a Parquet adapter and a MotherDuck adapter; one file per
  partition, its columns in alphabetical order and its timestamps UTC,
  overwritten atomically so a re-run is idempotent, and an empty day stored
  as an empty partition; the raw archive, the quarantine and the run
  manifest; metrics recomputed whole, compacting only once measured, and
  testing a store on a temporary directory. Use whenever deciding where a
  project's output goes, writing a store adapter, choosing between Parquet,
  a table format, DuckDB, SQLite or Postgres, laying out a data directory,
  writing or scanning Parquet, deciding what to keep when a row or an item
  fails, recording what a run did, or sharing data with another machine or a
  hosted dashboard — even if the user just says "save the results", "where
  should this live" or "add a database". Targets Polars 2.x and DuckDB 2.x.
  Layers on structure-python (the store is an adapter) and use-polars;
  run-unattended reads the manifest and holds the lock, write-sql covers the
  SQL written against the store, and secure-project decides which data may
  leave the machine.
---

# Store data

Where a project's data lives, how it is written so a re-run is safe, and how it is read back.
The store is a driven adapter in `structure-python`'s terms, the frames it moves obey `use-polars`, `run-unattended` reads the manifest it keeps, `write-sql` covers the SQL written against it, and `secure-project` decides which of its data may leave the machine.
Three mistakes account for most lost data: appending on a re-run, so a retried night doubles its rows; writing a file in place, so a crash leaves a half-file every later scan trips over; and discarding the raw response, so a parser fix cannot reach history.

**In an existing project, ask first.** Where a repo already has a store, check with the user whether to keep it or apply this layout, and prefer this layout unless they choose to keep theirs.

## Pick the engine

Each pick is the default for its need; a `PLAN.md` decision overrides it, and a measurement (a scan that takes seconds to plan, a query that no longer fits one machine) goes under Decisions as proposed and is raised with the user before the layout changes.

- **Hive-partitioned Parquet** for pipeline output — `records/source=<s>/day=<d>/part.parquet`, scanned as one table.
A single DuckDB file would be simpler to hand around, but it is one writer's binary blob: a crash mid-write risks the whole table where Parquet risks one day, and nothing but DuckDB can read it.
- **A table format — DuckLake or Delta Lake — once a write must change several partitions as one, correct rows in place, or read the store as it stood on an earlier date** (Pick a table format).
- **Polars to read the tree in code**, and **DuckDB for a question across it** — `read_parquet` over the whole tree at a SQL prompt, or a view for a question asked often (Read).
The read port is Polars because the core speaks frames; DuckDB earns its place where a person asks something no operation answers, joining and aggregating every partition without writing an operation for a one-off.
- **MotherDuck** when more than one machine, or a phone chat, must reach the data: the same SQL over `duckdb.connect("md:<db>")`, with the token in the environment as `motherduck_token` (lower case, per MotherDuck's docs).
It is an outside service, so private or personal data goes there only under a plan decision naming it (`secure-project`).
**Pin `duckdb` to the client versions MotherDuck accepts**, which its docs list: 1.4.1 to 1.5.6 on 2026-11-12, when a 2.0 client's `motherduck` extension refused to load ("not yet supported by MotherDuck").
1.5.6 ships wheels up to Python 3.14 only, so until MotherDuck accepts 2.0 a project that reaches it sets `requires-python` below `setup-python`'s floor, recorded as a proposed decision naming that pin.
Syncing Parquet to a bucket is the alternative and costs a sync step and credentials on every reader.
- **SQLite** for small single-writer app state — a watermark table, a key-value cache — through the stdlib `sqlite3`.
A JSON file is the alternative and loses atomic updates the moment two fields change together.
- **Postgres** only for a multi-writer service; it earns a server to run, so a `PLAN.md` decision names it.

**No ORM.** Frames cross the boundary as frames: `polars.read_database` with a `sqlite3` connection, `write_database(..., engine="adbc")` with `adbc-driver-sqlite` installed — the default `sqlalchemy` engine refuses without `pandas`.

## Pick a table format

**Hive-partitioned Parquet stays the default for one writer's output**: any reader reads it correctly with no catalog or log, Write a partition's atomic rename makes a re-run safe, and a new column costs `missing_columns="insert"` at the read.
A table format earns its place when the plan needs what the tree cannot give by hand — several partitions or tables changed as one, rows corrected in place, the store as it stood on an earlier date, or more than one writer — and every format leaves files that read true only through it: a replaced day's old file stays on disk until cleaned up, and a plain Parquet scan of both trial tables returned the old rows beside the new.

- **DuckLake pairs best with DuckDB and MotherDuck.** A catalog database — a DuckDB or SQLite file beside the data, Postgres for several writers, or MotherDuck — records the table, and the data is Parquet under a hive-style path (`ATTACH 'ducklake:catalog.ducklake' AS lake (DATA_PATH 'data/')`, then `ALTER TABLE ... SET PARTITIONED BY (day)`).
A day is replaced by `DELETE` then `INSERT` in one transaction, which is one snapshot; a column is added without rewriting a file; `AT (VERSION => n)` reads an earlier snapshot.
The read port queries it through DuckDB and hands the result over with `.pl()`, or `.pl(lazy=True)` for a `LazyFrame`, so the core still receives frames and its tests use a DuckLake under `tmp_path`.
The costs: the catalog is part of the data, backed up with the files, and a DuckDB-file catalog admits one writing process at a time; a write under ten rows is kept in the catalog, not a file, unless the attach sets `DATA_INLINING_ROW_LIMIT 0`; old files stay until `ducklake_expire_snapshots` and `ducklake_cleanup_old_files` run; and Polars has no reader of its own.
With MotherDuck holding the catalog the back-up moves there, but the client pin above applies and data on MotherDuck's own storage is not reachable from your compute, only data in your bucket (MotherDuck's docs, read, not run).
- **Delta Lake through `deltalake`** where Polars or an engine other than DuckDB must write the table: no catalog, since the log sits in the table's folder; Polars reads and writes it (`scan_delta`; `write_delta` with `mode="overwrite"` and a `predicate` in `delta_write_options` replacing one day, `schema_mode="merge"` adding a column); DuckDB reads it with `delta_scan` and appends but cannot delete or update; MotherDuck only reads it.
The costs are a dependency and an `optimize` and `vacuum` routine.
- **Iceberg** needs a REST catalog before DuckDB will write it, so it earns its place only where a platform already serves one.

Pick DuckLake with a local catalog where every reader goes through DuckDB, Delta where a Polars or non-DuckDB writer needs the same guarantees, and record either as a decision with the need that earned it.
Checked 2026-11-12 by running DuckDB 2.0.0 with DuckLake 1.1, deltalake 1.6.6 and Polars 2.1.0 in throwaway scripts.

## Lay out the data directory

Runtime data lives outside the repo and the package, in one directory the settings resolve once at the composition root:

```python
class Settings(pydantic_settings.BaseSettings):
    """Where the tool keeps its data, overridable per machine."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="MYAPP_")

    data_dir: pathlib.Path = platformdirs.user_data_path("myapp")
```

`MYAPP_DATA_DIR` overrides the platform default (`~/Library/Application Support/myapp` on macOS, `~/.local/share/myapp` on Linux), which is what a test, a second checkout and a scheduler each need; a test sets it with `monkeypatch.setenv("MYAPP_DATA_DIR", str(tmp_path))` before the settings are built.
Settings mechanics are in `write-entry-points`' Python reference; `platformdirs` is the dependency that names the default.

```text
<data_dir>/
  items.csv         user-editable list of what to fetch (see structure-python, Configuration)
  raw/              what each source sent, one file per page, as sent
  records/          the parsed, validated output, one schema for every source
  rejected/         the quarantine: rows that failed validation and items that failed, with a reason
  metrics.parquet   derived numbers, recomputed whole
  runs.parquet      the run manifest
  alerts.json       the last state each source alerted on (see send-messages)
  logs/
  .lock             the overlap lock (see run-unattended)
```

A tiny tool with one output is one Parquet file at the root; grow the tree when a second source or a second kind of output arrives.

**The tree's names are placeholders for the plan's Terms**: a project whose items are stations keeps `stations.csv` with a `station` column and calls `records/` what it holds (`readings/`), with no decision needed to say so.

**A second kind of record with its own schema gets its own tree beside the first**, each named for its dataset and keeping the `source=<s>/day=<d>` partitions, while `raw/` and `rejected/` gain a leading `dataset=<name>` level and the manifest a `dataset` column, so the quarantine and the manifest each stay one table.
Two schemas under one `records/` fail the scan that reads it as one table (`SchemaError` on the first column the files don't share).

**The store is two ports**, since its writer and its readers differ (`structure-python`, Declare a port): a write port, `port.Sink`, taking what a fetch returned, the manifest row and the metrics; and a read port, `port.Store`, answering records over a range, the metrics and the manifest.
The API and the dashboard take only `port.Store`, so a stray write from either is a type error.
`adapt/parquet.py` satisfies both over the tree: a frozen dataclass holding `data_dir`, built by the composition root, writing records, rejected rows, raw pages, metrics and the manifest row, so the fetch adapter never sees the directory.

**When `motherduck_token` is set, the root adds `adapt/motherduck.py`**, a second adapter satisfying both ports over `records`, `metrics` and `runs` tables, and hands the nightly both sinks, the tree first as the record, so a hosted dashboard and `status` read the manifest where they run.
A second target inside `parquet.py` would be less code, but the hosted dashboard needs a MotherDuck reader anyway, and keeping the network out of `parquet.py` keeps its tests to a temporary directory.
The load replaces the source's day in one transaction, the table's form of overwriting a partition, and a failed load raises after the tree is written, so the night exits 1 and a `fetch --day` re-run reloads it.
**`raw/` stays in the tree and is never loaded**; on a cloud runner it is uploaded as a workflow artifact kept seven days, long enough to re-parse a week after a parser fix, and is otherwise lost, since committing every page would grow the repository each night (`deploy-project`); a public repository's artifacts are readable by anyone signed in to GitHub, so there it holds public data only.

## Shape a stored table

**Order a stored table's columns alphabetically**: `frame.select(sorted(frame.columns))` in the adapter just before it writes, and the same order in a database table's definition.
A join or `with_columns` appends its column at the end, so without the sort one table's files carry whatever order each frame happened to be built in; with it, `polars.testing.assert_frame_equal`, which checks column order, compares a write with its read-back directly, and the plan's schema table, the file and `describe` list each column in one place.
The partition keys are the exception: they live in the path, not the file (Write a partition), and a scan appends them after the file's columns.

**Store every timestamp as a UTC datetime with its time zone** — `polars.Datetime("us", "UTC")`, `timestamp with time zone` to DuckDB — never a naive one, and a calendar day as a `Date`.
Polars raises `SchemaError` comparing a naive column with the core's aware values, and DuckDB compares a naive timestamp with an aware one in the session's time zone, so a query from a machine set to another zone is wrong by hours with no error (Polars 2.1, DuckDB 2.0).

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
A frame that arrives carrying them (the quarantine's does) has them dropped on write.

**An empty day is a stored partition.** A source whose every item answered with nothing (`structure-python`, Write an adapter) gets an empty `part.parquet` in the records schema and a manifest row with `rows=0`, so a dashboard shows a quiet day and `status` can judge the zero against what the source normally sends; only a source that didn't answer leaves no partition.

## Keep what the source sent

- **Archive the raw response** under `raw/source=<s>/day=<d>/page-NNN.json`, one file per page in the wire format it arrived in, before parsing.
A parser fix then re-parses history offline; without it the fix applies from tonight and every earlier day keeps the bug.
- **Quarantine rejected rows** under `rejected/` in the same partition layout, one row per rejected record **and** per failed item, in one schema: `reason` and `record` (the raw record as a string, or the item's name where nothing arrived), with `source` and `day` from the path.
Dropping them silently makes a schema change at the source look like a quiet day; the quarantine makes it a count, and one schema lets the whole tree be read as one table.
- **Write a run manifest**, `runs.parquet`: one row per source per run with `day`, `ended`, `failed_items`, `last_day`, `outcome`, `rejected`, `requests`, `rows`, `source` and `started`.
`rejected` counts every row under `rejected/` for the partition and `failed_items` the items among them that answered nothing, so `status` can tell a source that changed shape from one that lost an item; `requests` counts the pages archived, the answers a service counts against its daily cap, which the next process that day subtracts from it (`structure-python`, Write an adapter); `outcome` is an `enum.StrEnum` of `stored`, `partial` and `failed`, set as `run-unattended`'s Report the outcome says; `started` and `ended` are UTC timestamps, so a day filled late shows as a row started after its `day`, which `status` reports; and the `compute` stage writes its own row with `source="metrics"`.
A fetch that covers a range (`run-unattended`, Make a run rerunnable) writes one row with `day` the range's first day and `last_day` its last, equal to `day` on a one-day row, and files its raw pages and failed items under that first day.
It is small, so append by reading, concatenating and overwriting the file atomically; `run-unattended`'s `status` command reads it, and nothing else records that a night happened.
- **Store metrics as a full recompute** overwriting `metrics.parquet` from the records, until a timed check shows the recompute exceeding the nightly window; an incremental update is a second code path that drifts from the full one, so it is earned by that measurement and nothing else.
The file is long — `day`, `item`, `metric`, `value` — so a new metric is rows, not a column every reader must learn (`use-polars`).

## Read

**Scan the tree as `use-polars`' Eager vs lazy says**, with the filter on the partition columns, so only the partitions asked for are opened:

```python
readings = (
    polars.scan_parquet(data_dir / "records", hive_partitioning=True)
    .filter(polars.col("source").eq("weather"), polars.col("day").ge(start))
    .collect()
)
```

`hive_partitioning=True` adds `source` and `day` as columns, with `day` inferred as `Date` from `YYYY-MM-DD`; pass `hive_schema` when inference guesses wrong, such as a numeric-looking identifier that must stay a string.
Once a column has been added to the records, pass `schema=` naming every column with `missing_columns="insert"`, so the days written before it read as null; without both the scan raises `SchemaError` at the first file that holds the new column.

At a DuckDB prompt the same tree is a table: `read_parquet('<data_dir>/records/**/*.parquet', hive_partitioning = true)`.
Wrap the questions asked often in views in a local `.duckdb` file beside the data, and hand results back as frames with `.pl()` — which needs `pyarrow` installed, a dependency the Parquet path never needed.
A Polars frame in scope is queryable by name (`duckdb.sql("select * from readings")`), so a question asked of one in SQL costs no export step.
When a query belongs in SQL rather than Polars, where it is kept and how a documented one is tested are `write-sql`'s.

**Compact only when the file count hurts** — thousands of files, a scan whose planning is visible — and then by closed year: rewrite each year's days into `history/source=<s>/year=<y>/part.parquet`, keeping `day` as a column, and read `records` and `history` as a `polars.concat` of two scans.
Rewriting earlier is a second layout to maintain for a cost nobody has measured.

## Test the store

- **Exercise the real adapter on `tmp_path`** with a round-trip property: whatever frame is written is read back equal, through `polars.testing.assert_frame_equal`, including the partition columns and after a second write of the same day.
- **Give the core an in-memory fake** satisfying the same two ports — a dict keyed by source and day — so operations run with no filesystem.
- **Point every test's `data_dir` at `tmp_path`** through the environment override (Lay out the data directory), never the platform default, or a test run writes into the real store.

The shape of the tests is `write-tests`; the ports they share are Lay out the data directory's.
