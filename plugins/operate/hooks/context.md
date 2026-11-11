# Skills from the `operate` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it; never skip or soften a rule without that line.

- **`deploy-project`** when a pipeline, dashboard, API or site must run in the cloud: the free-tier host per artefact and how it gets there.
- **`run-unattended`** when a job runs on a schedule with nobody watching: the day it fetches, the lock, catch-up, exit codes, `status`, logs, the scheduler unit.
- **`send-messages`** when a job or assistant must reach me: a failure alert, a digest with a chart, a two-way chat; which channel and what never to send.
- **`store-data`** when deciding where a project's data lives and how it is written and read: Parquet, DuckDB, MotherDuck, SQLite; the data directory, atomic partitions, the raw archive, quarantine and the run manifest.
