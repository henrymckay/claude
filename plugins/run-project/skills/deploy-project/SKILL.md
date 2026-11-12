---
name: deploy-project
description: >-
  Where each artefact of a project runs in the cloud and how it gets there at
  little or no cost, picked from the data's class — the nightly pipeline as a
  GitHub Actions schedule writing to MotherDuck and committing the data tree
  back, with a status workflow for a night that never ran and Modal when a job
  outgrows a runner; MotherDuck Lite with one token per consumer; a public
  dashboard as a static build on GitHub Pages, or Cloudflare Pages from a
  private repository, with the free host and its limits for each dashboard
  technology (static, an API, Dash, Shiny); an API on Render only once a second consumer earns
  one, Cloud Run when the wake matters; private data kept on the owner's
  machine and its dashboard reached over Tailscale; what changes for a
  private repository; secrets in each platform's own store; the hosts ruled
  out; and re-checking a tier before relying on it. Use whenever deploying,
  hosting or publishing a pipeline, dashboard, API or site, choosing a free
  tier or cloud host, writing a workflow that runs in the cloud, or filling a
  plan's Runs on section — even if the user just says "put this online", "host
  the dashboard", "run it in the cloud" or "is there a free tier for this".
  The two workflow files are in references/github-actions.md. Layers on run-unattended, store-data,
  write-entry-points, send-messages and setup-python; secure-project classes
  the data the hosts are picked from, and plan-project's Runs on section
  records the choice.
---

# Deploy a project

Where each artefact of a project runs once it leaves the laptop, and how it gets there, on hosts that cost nothing or nearly nothing.
It builds on `run-unattended` (what the job does unwatched), `store-data` (the store), `write-entry-points` (the drivers deployed), `send-messages` (the alert) and `setup-python` (`uv`; no Docker or CI until earned — this skill earns the nightly workflow, not a CI one, so the suite still runs where the code is written); `secure-project` classes the data each host is picked from, and `plan-project`'s Runs on section records each choice with the date its tier was checked.
Three mistakes account for most deployments that die quietly: a free tier that changed or vanished after the plan was written, so the job stops the day the credit runs out; a secret bundled into a static app, which the browser hands to anyone who opens the network tab; and a public default applied to private data, which then lands in a public repository's history or on a host anyone can open.

**In an existing project, ask first.** Where a repo already deploys somewhere, check with the user whether to keep it or apply these picks, and prefer these unless they choose to keep theirs.

## Decide what runs where

Give each artefact its own host; one platform for everything costs the free tier of every piece that platform is second-best at.
Each pick is a default a `PLAN.md` decision overrides, and each is for public data from a public repository: **read the data's class first** (`secure-project`).

- **Pipeline** — a GitHub Actions `schedule` workflow in the project's own repository.
- **Data** — MotherDuck Lite, `store-data`'s pick for data another machine must reach.
- **Dashboard** — a static build on GitHub Pages, or the API serving it once it needs a server (Serve the dashboard).
- **API** — a Render free web service, once a second consumer earns one.
- **Static site** — GitHub Pages, published by the same nightly workflow.

**Private or personal data stays on the owner's machine** unless a plan decision names a host for it, and so does licensed data whose terms allow personal use only (`secure-project`, Decide where each class may go): the pipeline under `run-unattended`'s scheduler, its credential in the keychain at a fixed address a venue's IP allow-list can name, the store in the data directory, and the dashboard served from the same machine and reached from the owner's phone over Tailscale (`tailscale serve 8000` shares the dashboard's port (8001 for a Dash or Shiny app) with their own devices only, and its guard then accepts the machine's Tailscale name as well as loopback (`secure-project`, Guard what is served); the Personal plan is free for up to six users).
Nothing runs or answers while the machine sleeps, which the catch-up window and the dashboard's staleness cover; hosting it instead — a static build behind Cloudflare Access, or MotherDuck behind a hosted app — sends every row to outside services, which `secure-project` allows only under a signed-off decision naming them.

**A private repository holding public data changes two of these.** Actions includes $12 of compute a month on the Free plan (about 2,000 Linux 2-core minutes), enough for a nightly job; GitHub Pages serves a private repository only on Pro, so the static dashboard goes to Cloudflare Pages by direct upload from the workflow (`wrangler pages deploy`, its token a repository secret), which takes no repository at all; MotherDuck and Render are unaffected.

**None of these needs a Docker image**; each installs from `uv.lock` or a `requirements.txt`, and a `Dockerfile` is earned by Cloud Run or another container platform, as `setup-python` says.

## Run the pipeline

**Schedule the nightly command as an Actions workflow in the project's repository**, `uv sync --locked --no-dev` then `uv run --no-dev myapp-cli nightly --log-level info` (`run-unattended`, Schedule it); the file is in `references/github-actions.md`.
A public repository runs it free; a job must finish inside six hours, and the cron fires on the default branch only, at most every five minutes, and late under load, so pick a minute other than `:00` and let `run-unattended`'s day rule set the hour.

- **Write to MotherDuck and commit the data tree back** — the night's `records/` and `rejected/` partitions, `metrics.parquet`, `runs.parquet` and `alerts.json` — with `stefanzweifel/git-auto-commit-action` under `permissions: contents: write`.
The tree is the backup and the next night's input, and the push is repository activity, so GitHub does not disable the schedule, as it does a public repository's after sixty days without activity; a push made with `GITHUB_TOKEN` triggers no workflow, so it cannot loop.
- **Commit one date-partitioned file per source a night, and rewrite whole only files that stay small.** GitHub warns at 50 MiB a file and blocks at 100 MiB, a repository should stay well under 1 GB, and a rewritten file makes every clone carry every version; the manifest stays small, but once `metrics.parquet` passes a few MiB, stop committing it and let the site job run `compute` before it exports.
- **The data commits land on `main`**, since the data tree is not code and nothing reviews a night's rows; record that as a `PLAN.md` decision, which `use-git`'s branch rule defers to.
- **Once an alert is earned, the workflow covers what the driver cannot**: an `if: failure()` step for a failed install or commit, and a `status` workflow for a night that never ran (`send-messages`, Decide what deserves a message).
- **Set a spend limit on a private repository**, or the schedule stops silently the day the included minutes run out.
- **Move the job to Modal when it needs more than six hours, more memory than a 2-core runner, or retries and logs outside GitHub**: `@app.function(schedule=modal.Cron("0 2 * * *", timezone=...))`, deployed by `modal deploy` from an Action holding its two tokens; Starter includes $30 of compute a month and five crons, and the cost is a second platform with its own secrets and logs.
- **Vercel's Hobby cron is not a pipeline host**: once a day at most, up to 59 minutes late, 300 seconds a function, non-commercial only.

## Hold the data

**Stay on MotherDuck Lite** for data its class lets leave the machine, $0 for 10 GB and 10 CU-hours a month on Pulse instances, with its two service accounts: a read/write token for the pipeline and a read-scaling token for the dashboard and the API, so a leaked dashboard token reads but never writes.
`store-data` has the connection and the `motherduck_token` variable; past the quota it bills pay-as-you-go ($0.60 a CU-hour, $0.04 a GB-month).

- **Move cold data to Cloudflare R2 when the store outgrows 10 GB**: 10 GB free with free egress, read into DuckDB or Polars over `httpfs` with an S3 key pair; the cost is a second credential on every reader.
- **Neon or Supabase only for a multi-writer service**, `store-data`'s Postgres case: Neon's free tier scales to zero after five idle minutes, Supabase's pauses after an idle week, so the first reader pays a wake.

## Serve the dashboard

**Publish a public dashboard as a static build on GitHub Pages**, from the nightly workflow's site job: the web front end over files (`write-entry-points`, Dashboard), its data the small Parquet files an `export` command writes beside the page.
It is always on, wakes nothing and costs nothing, and the data and the page are always from the same night.
**A dashboard that needs a server runs where its data's class allows**: public, as the API serving the built front end on Render (Serve an API); private, on the owner's machine over Tailscale (Decide what runs where).

Dash and Shiny each have a vendor cloud with a free plan, and neither is a hosting advantage over a static build; the free host for each technology, read on 2026-11-12:

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
- **Streamlit Community Cloud** sleeps after twelve hours without traffic and is ruled out as a technology (`write-entry-points`); its one private app is no longer the private route.

## Serve an API

**Add no API while the dashboard reads the store directly** (`write-entry-points`); a second consumer — another app, a phone chat, a partner — earns one.

- **Render's free web service** once it is earned: auto-deploy on push from `render.yaml`, the read-scaling token as an environment variable, start command `uv run uvicorn mypackage.code.drive.api:app --host 0.0.0.0 --port $PORT`.
It gives 750 instance hours a month and 5 GB of outbound bandwidth; it spins down after fifteen idle minutes and takes about a minute to wake, which the first request pays.
- **Google Cloud Run when a one-minute wake is unacceptable**: 2 million requests, 180,000 vCPU-seconds and 360,000 GiB-seconds free a month and cold starts of seconds, deployed with `google-github-actions/auth@v3` and `deploy-cloudrun@v3` from `source: ./` with secrets from Secret Manager through the action's `secrets:` input, and private by default behind IAM, the access control an API over private data needs; the cost is a billing account and the project's one container image.
- **Koyeb** (one free 512 MB service, waking in seconds, against a $29 card hold) and **Vercel's** FastAPI preset (Hobby, non-commercial only) are the remaining free hosts.

## Publish a static site

**Publish a static site from the same nightly workflow**, a second job that `needs:` the nightly, sending a `site/` directory through `actions/upload-pages-artifact` and `actions/deploy-pages`, so the data and the page showing it are never from different nights.
Pages serves a public repository on the Free plan and a private one only on Pro, up to 1 GB a site and a soft 100 GB a month.

## Keep secrets per consumer

- **Repository secrets for Actions**, set with `gh secret set NAME` and read as `${{ secrets.NAME }}`; environment secrets need Pro or Team on a private repository.
- **Each other host's own store for the rest** — Render's environment variables, Cloud Run's Secret Manager, Connect Cloud's secret variables — never a committed file or a static bundle (`secure-project`).

## Re-check the tiers

Every figure above not marked otherwise was read from the vendor's page on 2026-11-11, and the dashboard hosts on 2026-11-12.
**Before relying on a limit, read the vendor's plan page and record the date beside the pick in Runs on**; each `review-plugin` sweep of this plugin re-checks the picks in this skill.

Ruled out on that date, so a search does not re-propose them: Ploomber Cloud (shut 2025-10-31) and Deta Space (sunset 2024-10-17), both from secondary sources; Fly.io (no free tier, a $1 seven-day trial) and Railway (a trial, then $1 a month of credit); Hugging Face Spaces (Gradio and Docker Spaces need a paid plan, re-read 2026-11-12); PythonAnywhere (the free tier expires monthly); Netlify (no Python functions); and shinyapps.io (no secrets, its free accounts move to Connect Cloud on 2027-01-28).
