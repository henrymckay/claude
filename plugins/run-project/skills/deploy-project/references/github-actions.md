# GitHub Actions workflows

The principles are in `SKILL.md`; these are the two workflow files, both scheduled after 02:00 UTC at an off-peak minute and both installing the project with `uv`.
They live in the repo under `.github/workflows/` and run on the default branch only; `workflow_dispatch` lets you run either by hand after a miss.
Both commit the data tree and publish logs and artifacts to the repository, so they serve public data only (`SKILL.md`, Decide what runs where).
What the nightly command does once it runs is `run-unattended`'s; the launchd and systemd units for a machine you own are in its `references/schedulers.md`.

## Nightly pipeline and site

`.github/workflows/nightly.yml`: fetch yesterday, write it through the store to the data tree and MotherDuck, commit the tree's new files back, then build the shinylive site from the stored metrics and publish it to Pages.
Enable Pages once in the repository's settings with GitHub Actions as the source, or the deploy job fails with no site to deploy to.

```yaml
name: nightly
on:
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:
concurrency:
  group: data
jobs:
  nightly:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.3.3
        with:
          enable-cache: true
      - run: uv sync --locked --no-dev
      - id: day
        run: echo "day=$(date -u -d yesterday +%F)" >> "$GITHUB_OUTPUT"
      - id: run
        run: uv run --no-dev myapp-cli nightly --log-level info
        env:
          MYAPP_DATA_DIR: ${{ github.workspace }}/data
          MYAPP_NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
          motherduck_token: ${{ secrets.MOTHERDUCK_WRITE_TOKEN }}
      - if: ${{ !cancelled() }}
        uses: stefanzweifel/git-auto-commit-action@v7
        with:
          commit_message: "chore(data): store ${{ steps.day.outputs.day }}"
          file_pattern: data/records data/rejected data/metrics.parquet data/runs.parquet data/alerts.json
      - if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v7
        with:
          name: raw-${{ steps.day.outputs.day }}
          path: data/raw
          retention-days: 7
      - if: failure() && steps.run.outcome != 'failure'
        run: >-
          curl --fail --silent
          -H "Title: nightly failed outside the run"
          -H "Priority: urgent"
          -d "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
          "https://ntfy.sh/$NTFY_TOPIC"
        env:
          NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
  site:
    needs: nightly
    if: ${{ !cancelled() }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.ref_name }}
      - uses: astral-sh/setup-uv@v10.3.3
        with:
          enable-cache: true
      - run: uv sync --locked --no-dev
      - run: uvx shinylive export app site
      - run: mkdir -p site/data
      - run: uv run --no-dev myapp-cli export metrics --format parquet --output site/data/metrics.parquet
        env:
          MYAPP_DATA_DIR: ${{ github.workspace }}/data
      - uses: actions/upload-pages-artifact@v5
        with:
          path: site
  deploy:
    needs: site
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

- `cron` is UTC unless a `timezone` key is set.
- `concurrency` without `cancel-in-progress` queues an overlapping run instead of killing the one in flight, the same policy as the lock; the status workflow shares the group, so the two never commit at once.
- The runner has no data directory of its own, so `MYAPP_DATA_DIR` points `store-data`'s tree into the checkout, where last night's commits already hold the records `compute` reads, and with `motherduck_token` set the store also loads the night into MotherDuck.
- The commit takes the night's `records/` and `rejected/` partitions, one new file each per source, plus `metrics.parquet`, `runs.parquet` and `alerts.json`, rewritten whole; keep them out of `.gitignore` or the commit is empty.
`raw/` and `logs/` are never committed: the pages go up as the artifact `store-data` keeps, and the log is the run's own.
- `if: ${{ !cancelled() }}` on the commit and the upload keeps a partial night, which exits 1, from losing what it stored.
- The `if: failure()` step and its `NTFY_TOPIC` secret are added once an alert is earned (`run-unattended`, Report the outcome); it skips a failed run step, which the driver alerts on itself (`send-messages`).
- `permissions: contents: write` is what lets `GITHUB_TOKEN` push; the push triggers no workflow, not even another workflow's `push` trigger.
- `site` runs on `!cancelled()`, so a partial night still publishes what it stored.
Its checkout names `ref: ${{ github.ref_name }}`, because the default is the commit the run started from, which lacks the data the nightly job just pushed.
- `export metrics` reads the store, never a source, so the site job needs no token and the bundle holds only the exported file.
- `app/` is the browser app's own directory, separate from the package: it runs on Pyodide, so it cannot import a package that depends on `polars`, and it reads `data/metrics.parquet` by a same-origin `pyodide.http.pyfetch`; after changing it, run the workflow by hand rather than waiting a night.
- `pages: write` and `id-token: write` are what `deploy-pages` needs; the `github-pages` environment is created by the first deploy and shows the site's URL on the run.
- Pin the action versions as the uv docs show (`@<sha> # vN`) once the workflow is stable; the tags above are the current majors, except `setup-uv`, which has published no major tag since v8, so `@v10` resolves to nothing and the job fails at setup — it takes a full version (checked 2026-11-10).

## Status

`.github/workflows/status.yml`, added once an alert is earned (`run-unattended`, Report the outcome): read the committed manifest a few hours after the nightly and alert when a source has gone stale, since a nightly that never fired cannot say so itself.

```yaml
name: status
on:
  schedule:
    - cron: "43 7 * * *"
  workflow_dispatch:
concurrency:
  group: data
permissions:
  contents: write
jobs:
  status:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.3.3
        with:
          enable-cache: true
      - run: uv sync --locked --no-dev
      - run: uv run --no-dev myapp-cli status --alert
        env:
          MYAPP_DATA_DIR: ${{ github.workspace }}/data
          MYAPP_NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
      - if: ${{ !cancelled() }}
        uses: stefanzweifel/git-auto-commit-action@v7
        with:
          commit_message: "chore(data): record alert state"
          file_pattern: data/alerts.json
```

- It reads `runs.parquet` from the checkout, so it needs no MotherDuck token, and commits `alerts.json` back so tomorrow's run alerts only on a change (`send-messages`).
- A stale source exits 1, so the run fails and GitHub's own mail reports it (`run-unattended`, Report the outcome).
