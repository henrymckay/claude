---
name: write-sql
description: >-
  The decisions around SQL in a project, whatever the engine — when a query is
  SQL and when it is Polars, never both for one result; where a query lives (a
  .sql file the package loads, a fenced block in the README when it is another
  project's read contract, a view for a question asked often); writing the
  dialect of the engine that runs it, a development dependency until an
  adapter queries with it, with pinned types, typed literals and named
  columns; the house style, formatted and linted by sqlfluff from the first
  .sql file; changing a stored schema without breaking its
  readers, and numbered forward-only migrations with no framework for a
  database; and running and linting every documented query in the suite
  against a tree the real store wrote. Load it
  before the first line of any SQL, even a query answered inline. Use whenever
  writing, editing or reviewing SQL, a .sql file, a view or a migration,
  setting up a SQL linter or formatter,
  choosing between SQL and a DataFrame, documenting a query in a README, or
  adding, renaming or retyping a stored column — even if the user just says
  "write a query", "query the parquet", "add a column" or "add a migration".
  Dialect-neutral decisions here; DuckDB 2.x specifics in
  references/duckdb.md.
  Layers on write-python, use-polars and write-tests; store-data picks the
  engine and lays out what a query reads, structure-python places a
  packaged .sql file, and setup-python wires the linter's hook.
---

# Write SQL

Where SQL belongs in a project, and how to write it so it stays true while the data under it changes.
It layers on `write-python` for the code that runs a query, `use-polars` for the frames it meets and `write-tests` for the test that runs it; `store-data` picks the engine and lays out what a query reads, `structure-python` places a packaged `.sql` file, and `setup-python` wires the linter's hook.
Three mistakes account for most SQL that goes wrong: one result computed in both SQL and Polars, which then disagree; a documented query nobody runs, broken by the next schema change and found by its reader; and a type left to inference — a partition column, a date literal — that the engine guesses differently from the code.

- **Wrong** — the README's query is pasted into a prompt once, returns rows, and breaks for its reader the month a column is renamed.
- **Right** — the suite runs the README's query against a tree the store wrote, so the rename fails a test in its own commit.

**Dialect-neutral here.** The DuckDB specifics live in references/duckdb.md.

**In an existing project, ask first.** Where a repo already has SQL in an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Choose SQL or Polars

- **A transform inside the package is Polars** (`use-polars`): a query held in a string is invisible to the type checker and the linter, so a renamed column is found when it runs, and it cannot be piped or tested a step at a time.
- **SQL earns its place where the reader or the data makes it the shorter path**:
  - a question asked at a prompt across the whole store, which no operation answers and none should be written for;
  - a query another project, language or person runs with nothing of yours installed — the store's read contract;
  - a query sent to a database that holds the data, which filters, joins and aggregates there and returns the answer, where reading its tables into frames moves every row to drop most of them.
- **Never compute one result both ways.** A figure the package derives in Polars and a documented query derives again agree until one of them changes; store the figure and have the query read it.
- **The engine is a development dependency until an adapter queries with it.** A prompt and the test below need it installed; the package imports it only once an adapter does.

## Keep each query in one place

- **A query the package runs is a `.sql` file in the package's data**, one statement a file, named for what it returns and loaded as `structure-python`'s Data says, except a statement that fits one line, which stays a string beside its call.
A file is highlighted, diffed and read as SQL; a multi-line string is none of these.
- **A documented query is a fenced `sql` block in the README**, complete as a reader would paste it — every option, the closing semicolon, and the path as the reader has it, from the repository root where the tree is committed there and from the data directory otherwise — with that directory and the engine's oldest working version named beside it.
Past a handful, each moves to `queries/<name>.sql` at the repository root and the README links to it.
- **A view's definition lives in one `views.sql`** beside the packaged queries, the one file holding several statements, each a `create or replace view`, re-run whole whenever it changes; which questions earn a view, and where the views are kept, are `store-data`'s Read.

## Write the engine's dialect

- **Write for the engine that runs the query, and use its own forms where they do the work** — reading a file tree, an as-of join.
A common subset written for an engine nobody runs costs the reader the clearer query and is tested against nothing.
- **In a stored or documented query, pin every type the engine would otherwise infer**: a column read from a path or an untyped file gets the type the store's schema gives it, declared in the query, and a timestamp keeps the time zone the schema gives it (`store-data`, Shape a stored table).
An inferred identifier of digits comes back a number, and the query and the code then disagree about one column with no error from either.
- **Give a date or timestamp a typed literal**, `date '2026-01-31'`.
Against a column that turned out to be text a typed literal fails the query, where a quoted string compares as text and `'2026-1-5'` matches nothing without a word.
- **Name every column in a stored or documented query**; `select *` is for a prompt.
A star's output changes when the table gains a column, and whatever read the result by position now reads the wrong one.

## Style

House preference: nothing observable turns on most of it, and one style keeps a diff to the change.
The linter below enforces each line, so a breach fails a commit rather than waiting for a reader.

- **Lower case** for keywords, functions and types; `snake_case` for names.
- **One clause a line, one selected column a line**, indented four spaces, commas trailing.
- **`as` on every alias**, column and table; engines reject some keyword-like aliases without it.
- **A table alias is a word**, `stations`, never a letter.
- **Group and order by name**, never by position.

```sql
with daily as (
    select
        station,
        day,
        avg(value) as mean_value
    from readings
    where day >= date '2026-01-01'
    group by station, day
)

select
    daily.station,
    stations.name as station_name,
    daily.day,
    daily.mean_value
from daily
inner join stations on daily.station = stations.station
order by daily.station, daily.day;
```

**Format and lint every `.sql` file with `sqlfluff` from the project's first one**, as a development dependency run by a pre-commit hook, configured so the style above is checked rather than remembered; under `setup-python`'s toolchain the hook is its to wire and the configuration sits in `pyproject.toml`, and elsewhere the same sections go in a `.sqlfluff` file:

```toml
[tool.sqlfluff.core]
dialect = "duckdb"
max_line_length = 88
rules = "core, AL06, AM06"

[tool.sqlfluff.rules."aliasing.length"]
min_alias_length = 3

[tool.sqlfluff.rules."ambiguous.column_references"]
group_by_and_order_by_style = "explicit"

[tool.sqlfluff.rules."capitalisation.keywords"]
capitalisation_policy = "lower"

[tool.sqlfluff.rules."capitalisation.identifiers"]
extended_capitalisation_policy = "lower"

[tool.sqlfluff.rules."capitalisation.functions"]
extended_capitalisation_policy = "lower"

[tool.sqlfluff.rules."capitalisation.literals"]
capitalisation_policy = "lower"

[tool.sqlfluff.rules."capitalisation.types"]
extended_capitalisation_policy = "lower"
```

- **`dialect` names the engine that runs the queries**; with the default `ansi` an engine's own forms fail to parse.
- **The core rules leave case "consistent"**, so the policies pin lower case; `AL06` makes a table alias a word and `AM06` rejects `group by 1`, neither of them core (sqlfluff 4.5).
- **`sqruff` is the alternative** when lint time is felt: on 200 files it took under a second where `sqlfluff` took thirteen (sqruff 0.44), at the cost of a pre-1.0 port that reads its own `.sqruff` file rather than `pyproject.toml`.
- **`sqlfmt` is not picked**: it packs a select's columns onto one line, which the style above rejects, and has no option to stop it (shandy-sqlfmt 0.32).
- **A fenced block in a README is beyond a file hook**, so the test that runs each documented query lints it too (Test a documented query).

## Change a schema

- **Adding a column is the one change readers survive**, and only readers that name their columns; files written before it hold none, so every read across old and new declares the whole schema and takes null for the old, or it fails or drops the column outright (the engine's option is in the reference; Polars' is in `store-data`, Read).
- **A rename, a retype or a drop is a new schema.** In a file tree, rewrite every partition in one backfill, in the commit that changes the code and the documented queries, since a tree holding two shapes fails the scan that reads it as one table; in a database, write a migration.
- **A database's schema changes only through numbered, forward-only migration files**, `migrations/0001_create_readings.sql`, each applied in one transaction with the number of the last one applied recorded in the database.
An undo is the next migration: a down script is the one path nobody runs until the day it matters.
- **No migration framework** until a second deployer or a served database earns one; the common ones arrive with an object-relational mapper the house does not use (`store-data`, Pick the engine).

## Test a documented query

**Every documented query runs in the suite**: one test takes each `sql` block from the README, or each file under `queries/`, runs it against a tree the real store adapter wrote to a temporary directory, from the directory its documented path starts at, and asserts on the rows that come back.
A schema change then fails that test in the commit that makes it; a query checked once by hand fails for its reader instead, some weeks later.

- **Lint each documented query in the same module** with `sqlfluff`'s Python API against the project's configuration, since the hook reads only `.sql` files.
- **Write the fixture tree through the store adapter**, never by hand, so the fixture changes shape when the store does.
- **Assert a query's answer where the contract promises one** — a join that must not multiply rows, a figure that must match the stored one — beside the shared check that each returns rows.
- **Test a packaged query through the adapter that runs it**, against a real database in memory or on a temporary path.
- **Apply every migration to an empty database as the fixture for those tests**, so a migration that fails or was edited after the fact fails the suite.

## Dialect specifics

Read the file for the engine that runs the query:

- **DuckDB** → references/duckdb.md (reading a hive-partitioned Parquet tree with pinned types, files of differing shape, integer sums, a view's path, the schema version, and the tests that run and lint the README's queries).

Add a new references/<dialect>.md when you write for another engine rather than adding its specifics to this file.
