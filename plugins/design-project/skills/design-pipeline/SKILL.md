---
name: design-pipeline
description: >-
  How to design a data pipeline and its tables before the store and schedule
  are picked — each table's grain and key, raw to clean to derived layers,
  idempotent loads, open against final records, when each fact was known,
  freshness, rebuilds and the contract readers rely on. Load it before naming
  a pipeline's first table or job, or changing how often one runs — even if
  the user just says "make it update hourly". Not for where data is saved,
  which is store-data's.
---

# Design the pipeline

The design side of a data pipeline: what each table holds, how data moves from what the source sent to what a reader sees, how fresh each table must be and what each run costs, decided in the plan before the store and the schedule are picked.
It sits beside `design-interface`, which designs the surfaces that show the data, and feeds `plan-project`'s Data flow and Outputs; the mechanics it hands off are `store-data`'s (the engine, the layout, atomic partition writes, the raw archive, the quarantine, the run manifest), `run-unattended`'s (naming the period, the lock, catch-up, the stale threshold), `deploy-project`'s (the host and the scheduler), `write-sql`'s (the mechanics of a schema change) and `send-messages`' (which events are sent).
Three mistakes account for most pipelines that have to be redesigned: tables built around one complete day fetched once, so a move to intraday data touches every table and every job; a table whose grain was never declared, so a forming record beside its final version, or two intervals in one table, read as duplicate rows; and freshness never stated, so the cadence, the scheduler and the stale alert are picked by habit and the alert fires a day late or on a run that was merely slow.

- **Wrong** — `usage` holds whatever each run fetched; a run every five minutes appends the current hour's running total each time, so the hour has twelve rows by its close, a report sums the half-formed ones, and the daily alert threshold calls a healthy feed stale.
- **Right** — `usage_1h` is declared as one row per meter per hour, keyed by both; the hour still forming lives apart and is replaced each run; the plan says hours are stored within ten minutes of their close while the source publishes, and the scheduler, the threshold and the dashboard's age all follow from that line.

**In an existing project, ask first.** Where a repo already has a pipeline design or a modelling convention, check with the user whether to keep it or apply this skill, and prefer this skill unless they choose to keep theirs.

## Declare the grain

**Write each table's grain as one sentence before its columns** — `one row per meter per hour, by the hour's start in UTC` — and make the key exactly the grain's columns, in the plan's schema table (`plan-project`, Outputs).
The grain is what a row *is*; a table whose grain is unwritten takes whatever each run produced, and its duplicates are found by a reader's total, not by a constraint (Kimball Group, Grain, read 2026-11-20).

- **One grain per table, never two.** Totals by the hour and by the day are two tables (`usage_1h`, `usage_1d`), since a reader who forgets to filter an `interval` column sums each day twice; one table keyed by `interval` as well earns its place only where many intervals are served through one route, and every query against it names the interval.
- **Store the finest grain the plan needs, and derive the coarser from it** where the coarse figure is the aggregate of the fine ones: a day's total is the sum of its hours, its peak the highest hourly peak.
**Fetch the coarse figure as well where the source's own differs from the aggregate** — a cut-off, a correction or a session boundary the hours do not carry — and record which table came from where; compare the two on a sample before trusting a derivation.
- **The key's time is the period's start in UTC**, with the period's length in the table's name or grain, never its end or a local time (`store-data`, Shape a stored table).

## Layer the data

Data moves through three layers, each a set of tables with declared grains:

- **Raw** — what the source sent, as sent, kept so a parser fix reaches history (`store-data`, Keep what the source sent).
- **Clean** — typed, validated and de-duplicated at its grain, one schema across sources: `store-data`'s `records`, the rejects quarantined.
- **Derived** — every figure computed from clean data: an aggregate, a signal, a coarser interval, a metric.

These are the medallion architecture's bronze, silver and gold, which Databricks calls a recommended practice rather than a requirement, and dbt's sources, staging and marts (docs.databricks.com, Medallion architecture; docs.getdbt.com, How we structure our dbt projects; both read 2026-11-20); the house uses the plain names, which say what each holds.

- **A derived table is recomputed whole from clean data**, stored as `store-data`'s metrics are (Keep what the source sent), or left a view where every reader can wait for its query; it turns incremental only once a full recompute is measured too slow for the run.
- **Every derived table can be rebuilt from clean data alone, and never holds a hand edit**, so a rule change is a rebuild (Rebuild a derived table) rather than an archaeology of patched rows.

## Load idempotently

**Every load writes by key, so a repeated or overlapping fetch is a no-op**: the same key with the same values leaves the same stored row, a re-run after a crash rewrites what it wrote, and two runs over one period store it once.

- **Fetch from the watermark less a lookback window**, unless the source re-serves its whole history cheaply, which `run-unattended`'s Make a run rerunnable fetches whole.
- **Derive the watermark from what is stored** — the last final period in the clean table, or the manifest's `last_day` — never from a separate counter, which can say a period was loaded that a failed write lost.
- **Size the lookback to the source's late arrivals and revisions**, at least one period: each run re-fetches it and rewrites it by key, which is how a late record or a corrected value arrives, as dbt's microbatch strategy re-processes its `lookback` batches (docs.getdbt.com, Incremental microbatch, read 2026-11-20).
- **Write by key in the store's own form**: replace the partitions the fetch covers in a file tree (`store-data`, Write a partition); in a database, `insert or replace` against a primary key, de-duplicating the batch first, since DuckDB applies one row per key within a statement and does not promise it is the last (duckdb.org, Insert, 2.0, read 2026-11-20); in DuckLake, which has no primary keys, a delete then an insert of the affected keys in one transaction.
- **Append only to a table whose grain is an event that happens once** — a sent message, a run — keyed by a stable id, so even there a retry finds its row.

## Keep open and final records apart

**A record whose period has not ended is open, and it is never stored as if it were final**: the current hour's total changes on every run until the hour closes, and a reader who takes it for a closed one charts a dip that is not there, fires a false alert or tests a rule on data that did not exist yet.

- **Hold the open record apart from the final ones**: in a file tree, one small file per table holding only the forming periods, replaced whole each run, while each period is written into its partition once it closes; in a database or table format, the same table with an `is_final` column, the open row replaced each run and a final row replaced only by a revision.
- **A period is final once it has ended and a settle margin has passed** — the source's own delay in publishing the closed figure, measured, not assumed — and the run that sees that writes it final.
- **Every reader says which it reads**: history, alerts and any test of a rule against history read final records only; a screen may show the forming one beside them, drawn apart (`design-interface`), and an API marks it (`is_final: false`).
- **A revision to a final record is recorded, never silent**: the run inside the lookback that finds a changed value rewrites it, counts it in the manifest and, where readers act on history, keeps the old version (Record when each fact was known).

## Record when each fact was known

**Store two times on every clean row**: the event's own time — the period's start — and `ingested_at`, when this pipeline stored that version, both in UTC (`store-data`, Shape a stored table).
The first answers "what happened when", the second "since when have we known it", and only the second shows a late arrival, a revision or a run that stored yesterday's data this morning.

- **Keep every version, not only the latest, where the plan must answer "what did we know then"** — a rule tested against history, an alert judged after the fact, an audit: a revision becomes a new row with the same grain and a later `ingested_at`, so a versioned table's key is its grain plus `ingested_at` and the load writes by that key, and an as-of read takes, per grain, the latest version stored by the time asked.
Overwriting a corrected figure, or testing a rule on today's corrected history, gives it knowledge it could not have had, the commonest look-ahead error.
- **A derived event records the `ingested_at` of the inputs it was computed from**, so re-evaluating it later is checked against what was known when it fired.
- **A table format's time travel is a mechanism, not this record**: DuckLake reads a table `AT (VERSION => n)` until its snapshots are expired, and Delta keeps 30 days of log and seven of deleted files by default (ducklake.select, Time travel; docs.delta.io; both read 2026-11-20), so a history that must outlive the retention keeps its versions as rows.
- **Where nothing reads the past as it was, keep `ingested_at` and overwrite**; a public series the source rarely revises needs no versions until a revision is seen.

## State the freshness

**Write each published table's freshness into the plan as a requirement**: how soon after its period closes it must be stored, and during which hours or calendar — `hourly totals stored within 10 minutes of each hour's close, while the source publishes`, `daily figures by 07:00 UTC on business days`.
Everything time-bound in the design is sized from that line, so nothing is picked by habit:

- **The lag budget is a sum, each part checked**: the source's own delay in publishing, the scheduler's lateness, the run's length, and any publish step after it, such as a static site's deploy; a part that alone exceeds the budget is a design change, not a tuning.
- **The cadence** is at most half the lag the plan allows, so a run that fails or starts late still leaves the next inside it; the average added delay of polling is half the interval.
- **The scheduler** is one whose lateness fits the budget (`run-unattended`, Schedule it).
- **The stale threshold and the watch** follow from the period and the scheduler's lateness (`run-unattended`, Report the outcome), and count only the hours the source publishes in, so its closed hours and weekends are quiet, and a run outside those hours writes no data, only its manifest row (`run-unattended`, Name the day).
- **Every surface shows the age** against this line (`design-interface`).
- **Poll until the lag must be under about a minute or the source only pushes**; then a stream earns its place, at the cost of an always-on process, which a scheduled job is not (`run-unattended`, Schedule it).

dbt's source freshness (`warn_after`, `error_after`) is the same idea as configuration, for a project on dbt (docs.getdbt.com, freshness, read 2026-11-20).

## Rebuild a derived table

**A changed rule rebuilds the range it affects from clean data, through the backfill path, and swaps it in whole** — partitions replaced atomically, or one transaction in a table format — never patches rows in place, which leaves a table that matches neither rule.

- **Version the rule**: a `rule_version` in the derived table or the manifest, raised with the change, so a reader and `status` can tell which rows the new rule made and a half-finished rebuild shows.
- **Run it as the nightly's own code over a range** (`run-unattended`, Make a run rerunnable), so a rebuilt day equals a day computed on time.
- **A rebuild sends nothing**: events it finds for the past are stored, not pushed (`send-messages`, Alert on events the job finds).

## Publish the contract

**Every table another reader relies on — the API, the dashboard, a documented query, another project — has a contract in the plan's Outputs**: the grain sentence, each column with its type, unit and meaning, the key, the time zone, open and final semantics, the freshness line, and a version.

- **Adding a column is safe; renaming, retyping or dropping one breaks the contract**, as dbt's model contracts also count it (docs.getdbt.com, Model contracts, read 2026-11-20).
Where every reader is in the repository, a breaking change lands with its backfill and its readers in one commit (`write-sql`, Change a schema); where a reader you cannot update relies on it, publish the new version beside the old, announce when the old one goes, and remove it then.
- **The contract is tested, not only written**: the documented queries run in the suite against a store the real adapter wrote (`write-sql`, Test a documented query), and a contract test asserts the grain's key is unique.
- **A formal contract file** (the Open Data Contract Standard, 3.1 in December 2025, read 2026-11-20 at bitol.io) earns its place once readers outside the project's owner rely on the data.

## Size the cost of each run

**Multiply the cost of one run by the runs in a month before picking the cadence**, and write the figure into Runs on (`plan-project`), since a design that is free once a day can exceed a free tier at 24 or 288 runs a day:

- **Hosted minutes**: GitHub rounds each job up to the whole minute, so 24 runs a day of a one-job pipeline is at least 720 minutes a month, free on a public repository and a third of a private Free plan's allowance (docs.github.com, Actions billing, read 2026-11-20).
- **Metered queries**: MotherDuck's Pulse bills at least one CU-second per query, so a run's query count times its runs is the floor against Lite's ten CU-hours a month (motherduck.com, Pricing, read 2026-11-20).
- **Small files**: each run's write is a file, and thousands of small files slow every scan; write closed periods into their day's or month's partition, and compact a table format's files on a schedule (`store-data`, Read; DuckLake's `ducklake_merge_adjacent_files`, ducklake.select, read 2026-11-20).
- **Commits**: what an intraday job may commit to its repository is `deploy-project`'s (Run the pipeline).

## Daily and intraday side by side

| Question | Daily batch | Hourly at a few minutes' lag |
|---|---|---|
| Grain | one row per item per day | one row per item per hour, start in UTC |
| Open record | none: yesterday is closed | the current hour, kept apart and replaced each run |
| Load | yesterday plus the catch-up window | the watermark less a lookback of at least one hour, by key |
| Freshness line | stored by a stated hour, business days | within minutes of each close, during the source's hours |
| Cadence | once a day | every few minutes during those hours, a no-op outside them |
| Scheduler | Actions `schedule` | a trigger with a firing promise in minutes, or a machine that is awake |
| Stale after | a day plus a margin (`run-unattended`) | an hour plus a margin, counting open hours only |
| Cost to check | rarely matters | minutes, queries and files times hundreds of runs a month |
