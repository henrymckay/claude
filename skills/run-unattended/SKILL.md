---
name: run-unattended
description: >-
  The operational side of a job that runs on a schedule with nobody watching —
  which day a nightly run fetches, the overlap lock, no silent catch-up and
  backfill by range, exit codes and a partial fetch, the status command as the
  health check and no notification in v1, logs and their rotation, picking the
  scheduler (a launchd agent on macOS, a systemd timer on Linux, GitHub
  Actions in the cloud) and what each does with a missed run, invoking the
  environment through uv, secrets outside the unit file, keeping an API or
  dashboard alive, and deploying with a clone and uv sync. Use whenever
  scheduling a nightly or periodic job, writing a plist, timer or workflow,
  deciding what a job does when a night is missed or a source fails, adding a
  status or health command, choosing where a job's logs go, or keeping a
  service running — even if the user just says "run this every night", "cron
  this", "make it restart" or "why did last night not run". Layers on
  write-entry-points (the job driver) and store-data (the manifest); the
  plist, timer and workflow files are in references/schedulers.md.
---

# Run unattended

How a job behaves when a scheduler, not a person, starts it.
The driver itself is `write-entry-points`' Jobs; the manifest it writes and the data directory it locks are `store-data`'s; this skill covers what happens between the two when nobody is watching.
Three mistakes account for most quiet failures: a slow night overlapping the next so two runs write one partition; a job that repairs missed nights silently, so nobody learns the machine was off; and a unit file that works in the shell and fails under the scheduler, whose environment has no `PATH` worth the name and no `.env`.

**In an existing project, ask first.** Where a repo already has a scheduler and run conventions, check with the user whether to keep them or apply these, and prefer these unless they choose to keep theirs.

## Name the day

**The nightly command fetches yesterday in UTC and nothing else**; a `--day` option overrides it for a re-run.
Compute it from the UTC clock, not the local one, and schedule the run after midnight **UTC**: at 00:30 British Summer Time it is still yesterday in UTC, so "yesterday" comes out as the day before and a day is skipped every summer.

```python
def yesterday(now: datetime.datetime) -> datetime.date:
    """Return the last complete UTC day, whichever zone the clock is in."""
    return now.astimezone(datetime.UTC).date() - datetime.timedelta(days=1)
```

Size the hour from when the source publishes, not from midnight: a feed that posts yesterday's figures at 06:00 is empty at 02:00, and an empty answer stores as a quiet day (see `structure-python`, Write an adapter).

## Make a run rerunnable

- **Lock the data directory with `fcntl.flock` on `<data_dir>/.lock`**, taken non-blocking at the top of the job and held to the end.
The kernel releases it when the process dies, where a PID file outlives a crash and blocks every later run until someone deletes it; `fcntl` is Unix-only, which the house targets are.
- **When the lock is held, log one line and exit 0.** The run in progress is the one that counts; a non-zero exit would make the scheduler record a failure and a restart policy fire a third copy.

```python
@contextlib.contextmanager
def held(path: pathlib.Path) -> collections.abc.Iterator[None]:
    """Hold the overlap lock for the block, or raise if another run has it."""
    with path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
```

The second holder gets `BlockingIOError`; catch it in the driver, where the exit code is decided.

- **Never catch up on missed nights inside the nightly command.** A job that notices a gap and fills it hides that the machine was off, and a gap of a month becomes a surprise bulk fetch against someone else's rate limit.
Expose `fetch --from --to` for backfill, and let `status` report the gap.
- **Make backfill the same code path** as the nightly, called once per day, so a day fetched late lands in the same partition as a day fetched on time.

## Report the outcome

- **Exit `0` when every source stored, `1` when any failed, `2` for a usage or configuration error** — a missing token, a bad option.
A scheduler and a shell both branch on non-zero; the split between 1 and 2 tells a reader of the log whether to look at the source or at the machine.
- **A partial fetch stores what arrived**, lists the failed sources on standard error and exits 1.
Discarding the good sources because one failed turns one outage into a full missed night.
- **The run manifest is the record**: one row per source per run, as `store-data` lays it out.
A log line is not a record — nothing queries it.
- **`status` reads the manifest and exits 1 when any source is stale**, printing which and since when; it is the health check, so anything that can run a command can watch the job.
Define stale per source from how often it publishes, with a default of two missed nights.
- **No notification in v1**, and say so in the README: the exit code, the manifest and a dashboard that shows its own staleness are the signals.
A mail or chat hook is earned by the first outage nobody noticed, and then costs a credential on the machine; record it under Decisions when it is.

## Log

- **Write the job's log to `<data_dir>/logs/` through a `TimedRotatingFileHandler`** rolling at `midnight` with a `backupCount`, or let the scheduler capture standard error (`StandardErrorPath`, the journal, the workflow log) and install no file handler.
Doing both writes every line twice; an unrotated `FileHandler` grows until the disk is full.
- **Keep `RichHandler` for a terminal**: its colour codes are noise in a file.
- **Emit JSON lines only behind a collector** that indexes them; for a file a person reads, the timestamped plain format in `write-entry-points`' Logging is the one to grep.

## Schedule it

**Pick the scheduler by platform**, since each is already running there: a launchd agent in `~/Library/LaunchAgents` on macOS, a systemd user timer in `~/.config/systemd/user` on Linux, a `schedule` workflow on GitHub Actions when the job has no machine of its own.
`cron` runs everywhere but fires into a bare environment with no log capture and no missed-run handling, which is the work the other three do for you.
The files are in `references/schedulers.md`; the unit lives in the repo under `deploy/` with its install line in the README, so a new machine is a copy and one command.

- **Invoke through the project's environment**: `uv run --project /path/to/repo --frozen myapp-cli nightly`, with `uv` by absolute path — the scheduler's `PATH` lacks the shell's additions.
`--frozen` runs what is locked instead of re-resolving against the network every night.
- **Set environment variables in the unit; put secrets in a file the unit points at** — a `.env` the settings read, `EnvironmentFile=` on systemd, repository secrets on Actions — never in the unit, which is committed under `deploy/`.
- **Know what each does with a missed run.** launchd runs a missed `StartCalendarInterval` on wake, merging several into one; systemd does so only with `Persistent=true`; Actions skips it, delays under load, and disables the schedule after sixty days without activity in a public repository.
Each is a gap `status` reports, not a job to repair.

**Keep a service alive with a second unit**, `KeepAlive` or `Restart=on-failure`, one process per service; the dashboard reads the store, so a missed night shows there as staleness without the job and the dashboard sharing a process.

## Deploy

Clone the repository and `uv sync --frozen --no-dev`; the scheduler's `uv run` then finds the environment and installs nothing.
Docker earns its place only when the target is a container platform; on a machine you own it adds an image to rebuild for every dependency bump, and the store ends up in a volume nobody can find.
On Actions, `astral-sh/setup-uv` then `uv sync --locked` is the equivalent, failing the run when the lockfile is behind `pyproject.toml` instead of resolving silently.
