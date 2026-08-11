# Scheduled and event-driven jobs

Part of `setup-python`'s Entry points — see `SKILL.md` for the shared role/framework pattern, `[project.scripts]` naming, and the core architecture.

A cron run, a queue worker, a webhook handler, or a serverless function is a driver triggered by *time or events* rather than a person. It reads its trigger, runs an operation — injecting the adapters, the composition root's job — and writes the result through an output adapter (this is the ETL shape: `extract` in, `transform` in the core, `load` out); keep the trigger wiring thin so the work stays in the core.

**Default to no library.** The cleanest scheduler is *external* to the app — cron, a systemd timer, a Kubernetes `CronJob`, a cloud scheduler, or a serverless trigger — so the schedule lives in infrastructure, not code. The app just exposes a console script that runs once and exits. A job is `command.py` without the parsing: a thin composition root wiring a source and a sink around an operation.

```python
from mypackage.code import operate
from mypackage.code.adapt import httpx_, postgres_


def run() -> None:
    """Fetch the latest readings and store the daily averages."""
    operate.refresh(fetch=httpx_.fetch, store=postgres_.save)
```

`mypackage-job = "mypackage.code.drive.job:run"`, invoked by the external trigger. Reach for a library only when the trigger must live *inside* the process (see Reach-for libraries in `SKILL.md`):

- **In-process scheduling** (a long-running process firing work on a clock) → `apscheduler`, in an `apscheduler_/` package holding the scheduler.
- **A task queue** (events enqueue work, worker processes consume it) → `dramatiq` (a cleaner Celery) over a Redis/RabbitMQ broker, its actors in a `dramatiq_/` package.
- **Orchestration** (dependent steps, retries, backfills, observability) → `prefect` or `dagster`.

Whichever it is, the scheduler or broker is the shell; the work stays an operation over the pure core.
