---
name: deploy-project
description: >-
  Where each artefact of a project runs in the cloud at little or no cost,
  picked from the data's class — a scheduled pipeline on GitHub Actions, a
  dashboard as a static site or on a free host, an API once earned, private
  data kept on the owner's machine. Use whenever deploying, hosting or
  publishing a pipeline, dashboard, API or site, or choosing a free tier —
  even if the user just says "put this online" or "host the dashboard". Not
  for a job on the user's own machine, which is run-unattended's.
---

# Deploy a project

Where each artefact of a project runs once it leaves the laptop, and how it gets there, on hosts that cost nothing or nearly nothing.
It builds on `run-unattended` (what the job does unwatched), `store-data` (the store), `write-entry-points` (the drivers deployed), `send-messages` (the alert) and `setup-python` (`uv`; no Docker or CI until earned — this skill earns the nightly workflow, not a CI one); `secure-project` classes the data each host is picked from, and `plan-project`'s Runs on records each choice with the date its tier was checked.
Three mistakes account for most deployments that die quietly: a free tier that changed or vanished after the plan was written, so the job stops the day the credit runs out; a secret bundled into a static app, which the browser hands to anyone who opens the network tab; and a public default applied to private data, which then lands in a public repository's history or on a host anyone can open.

**In an existing project, ask first.** Where a repo already deploys somewhere, check with the user whether to keep it or apply these picks, and prefer these unless they choose to keep theirs.

## Decide what runs where

Give each artefact its own host; one platform for everything costs the free tier of every piece that platform is second-best at.
Each pick is a default a `PLAN.md` decision overrides, and each is for public data from a public repository: **read the data's class first** (`secure-project`).

- **Pipeline** — a GitHub Actions `schedule` workflow in the project's own repository, started by a Cloudflare Worker instead where a run must start within minutes of its slot (Run the pipeline).
- **Data** — MotherDuck Lite, `store-data`'s pick for data another machine must reach.
- **Dashboard** — a static build on GitHub Pages, or the API serving it once it needs a server (Serve the dashboard).
- **API** — an edge function on Cloudflare Workers, once a second consumer or a requirement earns one (Serve an API).
- **Static site** — GitHub Pages, published by the same nightly workflow.

**Private or personal data stays on the owner's machine** unless a plan decision names a host for it, and so does licensed data whose terms allow personal use only (`secure-project`, Decide where each class may go): the pipeline under `run-unattended`'s scheduler, its credential in the keychain at a fixed address a venue's IP allow-list can name, the store in the data directory, and the dashboard reached from the owner's phone over Tailscale.
`tailscale serve 8000` (8001 for a Dash or Shiny app) shares the port with their own devices only, and the guard then accepts the machine's Tailscale name too (`secure-project`, Guard what is served); the Personal plan is free for up to six users.
Nothing runs or answers while the machine sleeps, which the catch-up window and the dashboard's staleness cover; hosting it instead — a static build behind Cloudflare Access, or MotherDuck behind a hosted app — sends every row to outside services, which `secure-project` allows only under a signed-off decision naming them.

**A private repository holding public data changes two of these.** Actions includes $12 of compute a month on the Free plan (about 2,000 Linux 2-core minutes), enough for a nightly job; GitHub Pages serves a private repository only on Pro, so the static dashboard goes to Cloudflare Pages by direct upload from the workflow (`wrangler pages deploy`, its token a repository secret), which takes no repository at all; MotherDuck and the API hosts are unaffected.

**None of these needs a Docker image**; each installs from `uv.lock` or a `requirements.txt`, and a `Dockerfile` is earned by Cloud Run or another container platform, as `setup-python` says.

## Run the pipeline

**Schedule the nightly command as an Actions workflow in the project's repository**, `uv sync --locked --no-dev` then `uv run --no-dev myapp-cli nightly --log-level info` (`run-unattended`, Schedule it); the file is in `references/github-actions.md`.
A public repository runs it free; a job must finish inside six hours, and the cron fires on the default branch only, at most every five minutes, with no promised start: GitHub's docs say a scheduled run can be delayed under load, that the start of every hour is such a time and that some queued runs may be dropped (docs.github.com, Events that trigger workflows, read 2026-11-20).
**Read that as hours, not minutes**: on a new public repository the first scheduled runs of two workflows started eight to nine hours after their slots, at minutes away from `:00`, and a community report from 2026-07 shows a new repository's daily run eight to fourteen hours late for a week, with moving the minute changing nothing (github.com/orgs/community/discussions/201738).
So pick a minute other than `:00` and let `run-unattended`'s day rule set the hour, which serves a nightly whose freshness allows a day, and ask the plan how late each run may start (`design-pipeline`, State the freshness) before taking this pick.

- **Trigger the workflow from outside when a run must start within minutes of its slot** — an hourly fetch at a few minutes' lag, an alert due within the hour: a Cloudflare Worker on Cron Triggers calls the workflow's `workflow_dispatch` endpoint with a fine-grained token for the one repository, and the run stays on the free runner (`references/github-actions.md`, Trigger on time).
Workers Free allows five Cron Triggers an account, as often as every minute, 10 ms of CPU an invocation, the wait on the request excluded, and 50 subrequests; Cloudflare promises no firing accuracy either, and a changed trigger takes up to 15 minutes to take effect, missing runs meanwhile (developers.cloudflare.com, Workers limits and Cron Triggers, read 2026-11-20).
A dispatched run still queues for a runner, eleven minutes on average at the worst of one 2026 incident (githubstatus.com), so measure the first day's starts against their slots before calling the lag met.
- **Its alternatives**, each read 2026-11-20: cron-job.org, free under fair use, every minute, a 30-second timeout and a POST with a header, with no punctuality promise and a job switched off after 25 failures; AWS EventBridge Scheduler, 14 million invocations a month free with at-least-once delivery, and Google Cloud Scheduler, three jobs free a billing account, each a new cloud account with a card; and on the owner's machine, launchd or systemd, on time while it is awake (`run-unattended`, Schedule it).
- **An intraday job commits no data per run**: a run an hour is 24 commits a day, each rewriting the day's files into every clone's history, so it writes to the hosted store and commits a day's closed partitions once a day, or nothing.
- **Write to MotherDuck and commit the data tree back** — the night's `records/` and `rejected/` partitions, `metrics.parquet`, `runs.parquet` and `alerts.json` — with `stefanzweifel/git-auto-commit-action` under `permissions: contents: write`.
The tree is the backup and the next night's input, and the push is repository activity, so GitHub does not disable the schedule, as it does a public repository's after sixty days without activity; a push made with `GITHUB_TOKEN` triggers no workflow, so it cannot loop.
- **Commit one date-partitioned file per source a night, and rewrite whole only files that stay small**: GitHub warns at 50 MiB a file and blocks at 100 MiB, a repository should stay well under 1 GB, and every clone carries every version of a rewritten file; once `metrics.parquet` passes a few MiB, stop committing it and let the site job run `compute` before it exports.
- **The data commits land on `main`**, since the data tree is not code and nothing reviews a night's rows; record that as a `PLAN.md` decision, which `use-git`'s branch rule defers to.
- **Once an alert is earned, the workflow covers what the driver cannot**: an `if: failure()` step for a failed install or commit, and a `status` workflow for a night that never ran (`send-messages`, Decide what deserves a message).
- **Call the pipeline deployed only once the schedule itself has fired**: a run dispatched by hand shows the job works, not that the cron starts it, so after the first scheduled time `gh run list --workflow nightly.yml --event schedule --limit 1` must list a run, `--event workflow_dispatch` at a slot's time for one the Worker starts, and until it does the report lists that check as owed.
- **Set a spend limit on a private repository**, or the schedule stops silently the day the included minutes run out.
- **Move the job to Modal when it needs more than six hours, more memory than a 2-core runner, or retries and logs outside GitHub**: `@app.function(schedule=modal.Cron("0 2 * * *", timezone=...))`, deployed by `modal deploy` from an Action holding its two tokens; Starter includes $30 of compute a month and five crons, and the cost is a second platform with its own secrets and logs.
- **Vercel's Hobby cron is not a pipeline host**: once a day at most, up to 59 minutes late, 300 seconds a function, non-commercial only, and its Cron Jobs are being moved to a new Schedules feature (re-read 2026-11-19).

## Hold the data

**Stay on MotherDuck Lite** for data its class lets leave the machine, $0 for 10 GB and 10 CU-hours a month on Pulse instances, with its two service accounts: one with a read/write token for the pipeline, and one for the API, given a restricted share of the database, which attaches read-only, so a leaked token reads but never writes.
Read-scaling tokens are a Business-plan feature, and Lite refuses to create one (motherduck.com/docs/about-motherduck/billing/pricing, 2026-11-18; the refusal and the share attached by a service account were seen in a trial build, not in the docs); a reader that needs no live read takes exported files and no token.
`store-data` has the connection and the `motherduck_token` variable; past the quota it bills pay-as-you-go ($0.60 a CU-hour, $0.04 a GB-month, in the US regions).

- **Move cold data to Cloudflare R2 when the store outgrows 10 GB**: 10 GB free with free egress, read into DuckDB or Polars over `httpfs` with an S3 key pair; the cost is a second credential on every reader.
- **Neon or Supabase only for a multi-writer service**, `store-data`'s Postgres case: Neon's free tier scales to zero after five idle minutes, Supabase's pauses after an idle week, so the first reader pays a wake.

## Serve the dashboard

**Publish a public dashboard as a static build on GitHub Pages**, from the nightly workflow's site job (Publish a static site): the web front end over files (`write-entry-points`, Dashboard), always on, waking nothing and costing nothing.
**A static build shows what was exported when it was built, so it does not meet a requirement that the dashboard read a hosted store live**; that requirement earns an API the page calls (Serve an API), and is never traded for the static pick without the user (`plan-project`, step 4).
**A dashboard that needs a server runs where its data's class allows**: public, behind the API; private, on the owner's machine over Tailscale (Decide what runs where).

Dash's and Shiny's vendor clouds are no hosting advantage over a static build; the free host for each technology, read on 2026-11-12:

| Technology | Free host | Awake | Monthly cap | Repository | Private viewers |
|---|---|---|---|---|---|
| Static web front end | GitHub Pages | always; no cold start | 1 GB a site, 100 GB of traffic (soft) | public on the Free plan | none: a Pages site is public |
| Static web front end | Cloudflare Pages | always; no cold start | 20,000 files, 25 MiB a file, 500 builds | any, or a direct upload | Cloudflare Access, free to 50 users |
| API with the front end | Render web service | sleeps after 15 idle minutes, about a minute to wake | 750 instance hours | GitHub; private repositories unverified | none built in: a token per consumer (`secure-project`) |
| Dash | Plotly Cloud Free | resumes when opened (since 2025-12-19); wake time unpublished | 10 apps, a 10-credit trial, then $1 a credit | publish from Dash's dev tools or a folder | 3 listed, though the same page lists private apps as a Pro feature |
| Shiny | Posit Connect Cloud Free | billed while served; idle behaviour unpublished | 20 credits, at 1.75 an hour for its 1 CPU and 4 GB: about 11 served hours | public only | none (link sharing is the $59 Enhanced plan) |

- **Posit Connect Cloud enforces the Free plan's credits from the first usage period starting on or after 2026-11-01**, though its plans page still says limits are not enforced; past the allowance the app stops until the next period (docs.posit.co/connect-cloud, Usage).
- **Cloudflare's static assets answer a Range request with the whole file**, `200` rather than `206`, so a browser reader that fetches Parquet by range downloads every byte there; keep each file to a few megabytes (developers.cloudflare.com, Workers static assets, billing and limitations; whether Pages behaves the same is unverified).
- **Dash and Shiny also run on Render's free web service**, `app.server` under `gunicorn` or the Shiny app under `uvicorn`, with the same sleep and wake.
- **Cloudflare Access protects a Pages preview with a toggle**; the production site needs an Access application on its hostname, best a custom domain (unverified beyond the docs' Known issues), and private data reaches it only under a signed-off decision naming Cloudflare (`secure-project`).
- **shinylive on Pages** remains for an existing Shiny app with no secret: `uvx shinylive export app site`, Pyodide in the browser, pure-Python wheels only (`pandas` with `pyarrow`, never `polars`), about 13 MB on first load.

## Serve an API

**Add an API only once a second consumer — another app, a phone chat, a partner — or a requirement a static build cannot meet earns one**, such as a live read of a hosted store; until then the dashboard reads files (`write-entry-points`).

**Prefer a host on an account the user already holds**, found in their instruction file or memory, else asked once; a new account is a cost the plan states, since the accounts a first project opens are the ones later projects reuse.
**A host that needs a payment card is not ruled out**: report the card as a fact, with whether usage can charge it unasked and whether a hard cap exists, and let the user decide.

- **Cloudflare Workers Free for a small read-only API over a hosted store**: 100,000 requests a day, past which requests fail rather than bill, 10 ms of CPU a request and no virtual machine to cold-start; written in TypeScript, reaching MotherDuck through its Postgres endpoint (`pg.<region>-aws.motherduck.com`, the `pg` driver under `nodejs_compat`); the same account's KV (1 GB, 100,000 reads and 1,000 writes a day) and D1 (5 GB, 5 million rows read a day) also fail rather than bill, while R2 bills past 10 GB-months. The cost is a second language beside the Python core, which does not run there.
- **Render's free web service for an API that runs the Python core**: auto-deploy on push from `render.yaml`, the token as an environment variable, start command `uv run uvicorn mypackage.code.drive.api:app --host 0.0.0.0 --port $PORT`; its minute-long wake (the table above) is wrong behind a page with a speed budget, and it has 5 GB of outbound bandwidth a month.
- **Google Cloud Run when the Python core must answer in seconds**: 2 million requests, 180,000 vCPU-seconds and 360,000 GB-seconds free a month, deployed with `google-github-actions/auth@v3` and `deploy-cloudrun@v3` from `source: ./` with secrets from Secret Manager, private by default behind IAM, the access control an API over private data needs; it needs a billing account, and a budget only alerts unless set as a spend cap, which is unverified for Cloud Run.
- **Vercel Hobby** runs Python functions, generally available since 2026-10-15, 300 seconds each, for personal or non-commercial use only; **Koyeb's** one free 512 MB service requires a card.

**Keep a public API's traffic from becoming database spend**: a closed set of fixed queries with no caller SQL, each answer cached until the next run writes, and the host's daily request cap as the bound (`secure-project`, Guard what is served).

## Publish a static site

**Publish a static site from the same nightly workflow**, a second job that `needs:` the nightly, sending a `site/` directory through `actions/upload-pages-artifact` and `actions/deploy-pages`, so the data and the page showing it are never from different nights.
The `github-pages` environment the first deploy creates has refused a deploy from any branch but the default in a trial build (GitHub's docs only recommend that rule), so a check on the live site runs after the merge (`build-project`, Gate it).

## Keep secrets per consumer

- **Repository secrets for Actions**, set with `gh secret set NAME` and read as `${{ secrets.NAME }}`; environment secrets need Pro or Team on a private repository.
- **Each other host's own store for the rest** — Workers' secrets, Render's environment variables, Cloud Run's Secret Manager, Connect Cloud's secret variables — never a committed file or a static bundle (`secure-project`).
- **List each host account, what was created on it and each secret by name in the project's `DEPENDENCIES.md`** as it is created, so the owner can see every account the project holds open and retire it from one list.

## Re-check the tiers

Every figure above not marked otherwise was read from the vendor's page on 2026-11-11, the dashboard hosts on 2026-11-12, and MotherDuck and the API hosts on 2026-11-18, and all were re-read on 2026-11-19, unchanged wherever the page still states them, with the schedulers under Run the pipeline read on 2026-11-20; Connect Cloud's Free credit amount and Plotly Cloud's resume date are no longer on a current page.
**Before relying on a limit, read the vendor's plan page and record the date beside the pick in Runs on**; each `review-plugin` sweep of this plugin re-checks the picks in this skill.

Ruled out on that date, so a search does not re-propose them: Ploomber Cloud (shut 2025-10-31) and Deta Space (sunset 2024-10-17), both from secondary sources; Fly.io (no free tier, a $1 seven-day trial, re-read 2026-11-18) and Railway (a trial, then $1 a month of credit); Hugging Face Spaces (Gradio and Docker Spaces need a paid plan, re-read 2026-11-18); Deno Deploy (sunset in April 2027, read 2026-11-18); PythonAnywhere (the free tier expires monthly); Netlify (no Python functions, re-read 2026-11-18); and shinyapps.io (no secrets, its free accounts move to Connect Cloud on 2027-01-28).
