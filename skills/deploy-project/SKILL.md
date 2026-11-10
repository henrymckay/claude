---
name: deploy-project
description: >-
  Where each artefact of a project runs in the cloud and how it gets there at
  zero or near-zero cost — the nightly pipeline as a GitHub Actions schedule
  in the project's own repository, writing to MotherDuck and committing a
  Parquet copy back, Modal when a job outgrows a runner; MotherDuck Lite with
  one token per consumer, R2 past 10 GB; a Shiny dashboard on Posit Connect
  Cloud Free from a public repo, shinylive on GitHub Pages when it needs no
  secret, Streamlit Community Cloud when the app is Streamlit or must be
  private; an API on Render only once a second consumer earns one, Cloud Run
  when the wake matters; a static site from the same workflow; what changes
  for a private repository; secrets in each platform's own store; the hosts
  ruled out as dead or no longer free; and re-reading the vendor's plan page
  before relying on a limit. Use whenever deploying, hosting or publishing a
  pipeline, dashboard, API or site, choosing a free tier or cloud host,
  writing a workflow that runs in the cloud, or filling a plan's Runs on
  section — even if the user just says "put this online", "host the
  dashboard", "run it in the cloud" or "is there a free tier for this". Facts
  checked 2026-11-10; the two workflow files are in
  references/github-actions.md. Layers on run-unattended (what the job does
  unwatched), store-data (the store and its tokens), write-entry-points (the
  drivers deployed) and setup-python (uv, Docker and CI); plan-project's Runs
  on section records the choice.
---

# Deploy a project

Where each artefact of a project runs once it leaves the laptop, and how it gets there, on hosts that cost nothing or nearly nothing.
It builds on `run-unattended` (what the job does unwatched), `store-data` (the store), `write-entry-points` (the drivers deployed) and `setup-python` (`uv`; no Docker or CI until earned, and this skill earns the workflow); `plan-project`'s Runs on section records each choice with the date its tier was checked.
Three mistakes account for most deployments that die quietly: a free tier that changed or vanished after the plan was written, so the job stops the day the credit runs out; a secret bundled into a static app, which the browser hands to anyone who opens the network tab; and a public-repository assumption on a private project, where Pages and Connect Cloud Free refuse to publish.

**In an existing project, ask first.** Where a repo already deploys somewhere, check with the user whether to keep it or apply these picks, and prefer these unless they choose to keep theirs.

## Decide what runs where

Give each artefact its own host; one platform for everything costs the free tier of every piece that platform is second-best at.
Each pick is a default a `PLAN.md` decision overrides.

- **Pipeline** — a GitHub Actions `schedule` workflow in the project's own repository.
- **Data** — MotherDuck Lite, `store-data`'s pick for data another machine must reach.
- **Dashboard** — Shiny for Python on Posit Connect Cloud Free.
- **API** — a Render free web service, once a second consumer earns one.
- **Static site** — GitHub Pages, published by the same nightly workflow.

**A private repository changes three of these.** Actions includes $12 of minutes a month on the Free plan (2,000 Linux 2-core minutes), enough for a nightly job; Pages and Connect Cloud Free take public repositories only, so the dashboard moves to Streamlit Community Cloud's one private app or Connect Cloud Basic at $19 a month; MotherDuck and Render are unaffected.

**None of these needs a Docker image**; each installs from `uv.lock` or a `requirements.txt`, and a `Dockerfile` is earned by Cloud Run or another container platform, as `setup-python` says.

A weather project, say, fetches yesterday's observations each night into MotherDuck, keeps a Parquet copy in its repository and shows a seven-day chart on a Shiny dashboard; nothing else reads the store, so it has no API.

## Run the pipeline

**Schedule the nightly command as an Actions workflow in the project's repository**, `uv sync --locked` then `uv run myapp-cli nightly`; the file is in `references/github-actions.md`.
A public repository runs it free; a job must finish inside six hours, and the cron fires on the default branch only, at most every five minutes, and late under load, so pick a minute other than `:00` and let `run-unattended`'s day rule set the hour.

- **Write to MotherDuck and commit a date-partitioned Parquet copy back** with `stefanzweifel/git-auto-commit-action` under `permissions: contents: write`.
The copy is the backup, and the push is repository activity, so GitHub does not disable the schedule after sixty days without a commit; a push made with `GITHUB_TOKEN` triggers no workflow, so it cannot loop.
- **Commit one small file per night, never a growing one.** GitHub warns at 50 MiB a file and blocks at 100 MiB, a repository should stay well under 1 GB, and a rewritten file makes every clone carry every version.
- **Set a spend limit on a private repository**, or the schedule stops silently the day the included minutes run out.
- **Move the job to Modal when it needs more than six hours, more memory than a 2-core runner, or retries and logs outside GitHub**: `@app.function(schedule=modal.Cron("0 2 * * *", timezone=...))`, deployed by `modal deploy` from an Action holding its two tokens; Starter includes $30 of compute a month and five crons, and the cost is a second platform with its own secrets and logs.
- **Vercel's Hobby cron is not a pipeline host**: once a day at most, up to 59 minutes late, 300 seconds a function, non-commercial only.

## Hold the data

**Stay on MotherDuck Lite**, $0 for 10 GB and 10 CU-hours a month on Pulse instances, with its two service accounts: a read/write token for the pipeline and a read-scaling token for the dashboard and the API, so a leaked dashboard token reads but never writes.
`store-data` has the connection and the `motherduck_token` variable; past the quota it bills pay-as-you-go ($0.60 a CU-hour, $0.04 a GB-month).

- **Move cold data to Cloudflare R2 when the store outgrows 10 GB**: 10 GB free with free egress, read into DuckDB or Polars over `httpfs` with an S3 key pair; the cost is a second credential on every reader.
- **Neon or Supabase only for a multi-writer service**, `store-data`'s Postgres case: Neon's free tier scales to zero after five idle minutes, Supabase's pauses after an idle week, so the first reader pays a wake.

## Serve the dashboard

**Publish the Shiny app to Posit Connect Cloud Free from a public GitHub repository**, with the read-scaling token as a secret variable set at publish and read with `os.getenv`.
Its GitHub App republishes on every push from a committed `requirements.txt`, so export one with `uv export --format requirements-txt --no-emit-project --no-hashes > requirements.txt` whenever `uv.lock` changes, or the app runs last month's dependencies.
Usage-credit enforcement on the Free plan began in November 2026 and its limits could not be verified, so read connect.posit.cloud/plans before relying on it; Basic at $19 a month adds private repositories and scheduled publishing.

- **shinylive on GitHub Pages when the dashboard needs no secret and its data fits in the site.** `uvx shinylive export app site` builds a bundle the nightly workflow publishes (`references/github-actions.md`).
It runs in the browser on Pyodide — pure-Python wheels only, so `pandas` with `pyarrow` or DuckDB-wasm and never `polars`, `pyodide.http.pyfetch` in place of `urllib`, about 13 MB on first load — and the whole bundle, data included, goes to the viewer, so it holds no token; the nightly job writes a small pre-aggregated Parquet or CSV into `site/` for a same-origin fetch.
- **Streamlit Community Cloud when the app is Streamlit or must be private at $0**: unlimited public apps and one private one, `uv.lock` read directly, secrets as TOML through `st.secrets`, sleep after twelve idle hours, a cap of about 2.7 GB.
Plotly Cloud Free (ten Dash apps, three private viewers) has no GitHub integration, so every change is published by hand.

## Serve an API

**Add no API while the dashboard reads the store directly** (`write-entry-points`); a second consumer — another app, a phone chat, a partner — earns one.

- **Render's free web service** once it is earned: auto-deploy on push from `render.yaml`, the read-scaling token as an environment variable, start command `uv run uvicorn mypackage.code.drive.api:app --host 0.0.0.0 --port $PORT`.
It gives 750 instance hours a month and, per a secondary source, 5 GB of bandwidth since August 2026; it spins down after fifteen idle minutes and takes about a minute to wake, which the first request pays.
- **Google Cloud Run when a one-minute wake is unacceptable**: 2 million requests, 180,000 vCPU-seconds and 360,000 GiB-seconds free a month and cold starts of seconds, deployed with `google-github-actions/auth@v3` and `deploy-cloudrun@v3` from `source: ./` with secrets from Secret Manager through the action's `secrets:` input; the cost is a billing account and the project's one container image.
- **Koyeb** (one free 512 MB service, waking in seconds, against a $29 card hold) and **Vercel's** FastAPI preset (Hobby, non-commercial only) are the remaining free hosts.

## Publish a static site

**Publish a static site from the same nightly workflow**, a `site/` directory sent through `actions/upload-pages-artifact` and `actions/deploy-pages`, so the data and the page showing it are never from different nights.
Pages serves a public repository on the Free plan and a private one only on Pro, up to 1 GB a site and a soft 100 GB a month.

## Keep secrets per consumer

- **One token per consumer, so a leak is scoped**: the pipeline's read/write token, the dashboard's and API's read-scaling token; a token shared by all three is rotated everywhere when one leaks.
- **Repository secrets for Actions**, set with `gh secret set NAME` and read as `${{ secrets.NAME }}`; environment secrets need Pro or Team on a private repository.
- **Each other host's own store for the rest** — Connect Cloud's secret variables, Streamlit's TOML, Render's environment variables, Cloud Run's Secret Manager — never a committed file (`use-git`: rotate it), never a static bundle.

## Re-check the tiers

Free tiers moved several times between 2024 and 2026; every figure above was read from the vendor's page on 2026-11-10.
**Before relying on a limit, read the vendor's plan page and record the date beside the pick in Runs on**; the weekly `review-plugin` sweep re-checks the picks in this skill.

Ruled out on that date, so a search does not re-propose them: Ploomber Cloud (shut 2025-10-31) and Deta Space (sunset 2024-10-17); Fly.io (no free tier, a card for a $1 trial) and Railway (a trial, then $1 a month of credit); Hugging Face Spaces (Gradio, Docker and Streamlit Spaces need PRO at $9 a month since mid-2026); PythonAnywhere (the free tier expires monthly and blocks most outbound hosts); Netlify (no Python functions); and shinyapps.io (no secrets, sunset for Connect Cloud in 2027).
