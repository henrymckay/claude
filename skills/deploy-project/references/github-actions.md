# GitHub Actions workflows

The principles are in `SKILL.md`; these are the two workflow files, both scheduled after 02:00 UTC at an off-peak minute and both installing the project with `uv`.
They live in the repo under `.github/workflows/` and run on the default branch only; `workflow_dispatch` lets you run either by hand after a miss.
What the nightly command does once it runs is `run-unattended`'s; the launchd and systemd units for a machine you own are in its `references/schedulers.md`.

## Nightly pipeline

`.github/workflows/nightly.yml`: fetch yesterday, write it to MotherDuck through the store, and commit the day's Parquet partition back.

```yaml
name: nightly
on:
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:
permissions:
  contents: write
concurrency:
  group: nightly
jobs:
  nightly:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
        with:
          enable-cache: true
      - run: uv sync --locked --no-dev
      - id: day
        run: echo "day=$(date -u -d yesterday +%F)" >> "$GITHUB_OUTPUT"
      - run: uv run myapp-cli nightly
        env:
          MYAPP_DATA_DIR: ${{ github.workspace }}/data
          motherduck_token: ${{ secrets.MOTHERDUCK_WRITE_TOKEN }}
      - uses: stefanzweifel/git-auto-commit-action@v7
        with:
          commit_message: "chore(data): store ${{ steps.day.outputs.day }}"
          file_pattern: data/records/**/*.parquet
```

- `cron` is UTC unless a `timezone` key is set; the shortest interval is five minutes, and firings slip under load, so nothing downstream should assume the minute.
- `concurrency` without `cancel-in-progress` queues an overlapping run instead of killing the one in flight, the same policy as the lock.
- The runner has no data directory of its own, so `MYAPP_DATA_DIR` points `store-data`'s tree into the checkout and the store adapter also loads the partition into MotherDuck; a workflow that writes only to a local path keeps nothing.
- `file_pattern` commits the day's `records/` partition and nothing else, so `raw/`, `logs/` and the manifest stay on the runner; keep `data/records/` out of `.gitignore` or the commit is empty.
- `permissions: contents: write` is what lets `GITHUB_TOKEN` push; the push triggers no workflow, so a `push` trigger on another workflow never sees it.
- Pin the action versions as the uv docs show (`@<sha> # vN`) once the workflow is stable; the tags above are the current majors (checked 2026-11-10).

## shinylive to GitHub Pages

`.github/workflows/site.yml`: export a pre-aggregated file from the store, build the browser app around it and publish the directory to Pages.
Enable Pages once in the repository's settings with GitHub Actions as the source, or the deploy step fails with no site to deploy to.

```yaml
name: site
on:
  schedule:
    - cron: "47 2 * * *"
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
        with:
          enable-cache: true
      - run: uv sync --locked --no-dev
      - run: uvx shinylive export app site
      - run: mkdir -p site/data
      - run: uv run myapp-cli report --format parquet > site/data/report.parquet
        env:
          motherduck_token: ${{ secrets.MOTHERDUCK_READ_TOKEN }}
      - uses: actions/upload-pages-artifact@v5
        with:
          path: site
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
```

- The schedule runs half an hour after the nightly, since the nightly's `GITHUB_TOKEN` push cannot trigger this workflow; folding both into one file with a `needs:` between the jobs is the alternative when the gap matters.
- `app/` is the browser app's own directory, separate from the package: it runs on Pyodide, so it cannot import a package that depends on `polars`, and it reads `data/report.parquet` by a same-origin `pyodide.http.pyfetch`.
- The report is written by the CLI's format option (`write-entry-points`) with the read-scaling token, which never leaves the runner; the bundle holds only the aggregated file.
- `pages: write` and `id-token: write` are what `deploy-pages` needs; `contents: read` is enough for the checkout.
- The `github-pages` environment is created by the first deploy and shows the site's URL on the run.
