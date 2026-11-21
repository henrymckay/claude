# GitHub Actions workflows

The principles are in `SKILL.md`; these are the two workflow files, both scheduled after 02:00 UTC at an off-peak minute and both installing the project with `uv`.
They live in the repo under `.github/workflows/` and run on the default branch only; `workflow_dispatch` lets you run either by hand after a miss.
Both commit the data tree and publish logs and artifacts to the repository, so they serve public data only (`SKILL.md`, Decide what runs where).
What the nightly command does once it runs is `run-unattended`'s; the launchd and systemd units for a machine you own are in its `references/schedulers.md`.

## Nightly pipeline and site

`.github/workflows/nightly.yml`: fetch yesterday, write it through the store to the data tree and MotherDuck, commit the tree's new files back, then build the web front end over files from the stored metrics and publish it to Pages.
Enable Pages once in the repository's settings with GitHub Actions as the source, or the deploy job fails with no site to deploy to.

```yaml
name: nightly
on:
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:
concurrency:
  group: data
permissions: {}
jobs:
  nightly:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
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
        uses: stefanzweifel/git-auto-commit-action@d0b01107b5db882071f96de5dd4b54961ea93f4c # v7.2.1
        with:
          commit_message: "chore(data): store ${{ steps.day.outputs.day }}"
          file_pattern: data/records data/rejected data/metrics.parquet data/runs.parquet data/alerts.json
      - if: ${{ !cancelled() }}
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
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
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
          ref: ${{ github.ref_name }}
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
        with:
          enable-cache: true
      - run: uv sync --locked
      - run: mkdir -p web/public/data
      - run: uv run myapp-cli export metrics --format parquet --output web/public/data/metrics.parquet
        env:
          MYAPP_DATA_DIR: ${{ github.workspace }}/data
      - run: cp data/runs.parquet web/public/data/runs.parquet
      - run: uv run npm --prefix web ci
      - run: uv run npm --prefix web run build -- --base "/${GITHUB_REPOSITORY#*/}/" --outDir ../site --emptyOutDir
        env:
          VITE_DATA: files
      - uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
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
        uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1
```

- `cron` is UTC unless a `timezone` key is set.
- `concurrency` without `cancel-in-progress` queues an overlapping run instead of killing the one in flight, the same policy as the lock; the status workflow shares the group, so the two never commit at once.
- The runner has no data directory of its own, so `MYAPP_DATA_DIR` points `store-data`'s tree into the checkout, where last night's commits already hold the records `compute` reads, and with `motherduck_token` set the store also loads the night into MotherDuck.
- The site job syncs the development group too, since `nodejs-wheel` is where `npm` comes from (`setup-python`); `VITE_DATA=files` builds the data module that reads the Parquet beside the page, and `--base` names the repository because a project site is served under `/<repository>/`, where assets built for `/` all answer 404.
- The commit takes the night's `records/` and `rejected/` partitions, one new file each per source, plus `metrics.parquet`, `runs.parquet` and `alerts.json`, rewritten whole; keep them out of `.gitignore` or the commit is empty.
`raw/` and `logs/` are never committed: the pages go up as the artifact `store-data` keeps, and the log is the run's own.
- `if: ${{ !cancelled() }}` on the commit and the upload keeps a partial night, which exits 1, from losing what it stored.
- The `if: failure()` step and its `NTFY_TOPIC` secret are added once an alert is earned (`run-unattended`, Report the outcome); it skips a failed run step, which the driver alerts on itself (`send-messages`).
- `permissions: {}` at the top withholds every scope, and each job asks for only its own: `contents: write` is what lets the nightly's `GITHUB_TOKEN` push, `contents: read` serves a job that commits nothing; the push triggers no workflow, not even another workflow's `push` trigger.
- `site` runs on `!cancelled()`, so a partial night still publishes what it stored.
Its checkout names `ref: ${{ github.ref_name }}`, because the default is the commit the run started from, which lacks the data the nightly job just pushed.
- `export metrics` reads the committed tree, never a source, so the site job needs no token and the bundle holds only the exported file.
- **Where MotherDuck is the store of record and no tree is committed**, the export needs the token, so it moves to the nightly job's last steps and reaches the site job as an artifact; the token then never shares a job with the install scripts `npm ci` runs:

```yaml
# last steps of the nightly job, in place of the commit
- run: uv run --no-dev myapp-cli export metrics --format parquet --output site-data/metrics.parquet
  env:
    motherduck_token: ${{ secrets.MOTHERDUCK_WRITE_TOKEN }}
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with:
    name: site-data
    path: site-data
# in the site job, in place of the export and the copy
- uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
  with:
    name: site-data
    path: web/public/data
```
- `web/` is the front end's own folder beside the package (`write-entry-points`, Dashboard); the site job ships the night's `metrics.parquet` and the manifest `runs.parquet` beside the page, so the dashboard shows its data's age from the same night.
- `pages: write` and `id-token: write` are what `deploy-pages` needs; the `github-pages` environment is created by the first deploy and shows the site's URL on the run.
- Each action is pinned to the commit of its current release, the tag as a comment, since a tag can be moved to other code and the nightly job holds a write token and a secret; re-resolve each from the action's latest release when updating (resolved 2026-11-18).
The site job's checkout keeps no credential (`persist-credentials: false`), since it pushes nothing and runs `npm ci`; the nightly and status checkouts keep theirs for the commit action, and the build reads the repository's name from the shell rather than expanding it into the script. `setup-uv` has published no major tag since v8, so `@v10` resolves to nothing: pin a full version.

## Status

`.github/workflows/status.yml`, added once an alert is earned (`run-unattended`, Report the outcome): read the committed manifest after the nightly, timed as `run-unattended`'s stale rule says, and alert when a source has gone stale, since a nightly that never fired cannot say so itself.

```yaml
name: status
on:
  schedule:
    - cron: "43 7 * * *"
  workflow_dispatch:
concurrency:
  group: data
permissions: {}
jobs:
  status:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
        with:
          enable-cache: true
      - run: uv sync --locked --no-dev
      - run: uv run --no-dev myapp-cli status --alert
        env:
          MYAPP_DATA_DIR: ${{ github.workspace }}/data
          MYAPP_NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
      - if: ${{ !cancelled() }}
        uses: stefanzweifel/git-auto-commit-action@d0b01107b5db882071f96de5dd4b54961ea93f4c # v7.2.1
        with:
          commit_message: "chore(data): record alert state"
          file_pattern: data/alerts.json
```

- It reads `runs.parquet` from the checkout, so it needs no MotherDuck token, and commits `alerts.json` back so tomorrow's run alerts only on a change (`send-messages`).
- A stale source exits 1, so the run fails and GitHub's own mail reports it (`run-unattended`, Report the outcome).
- Its offset after the nightly must exceed the stale margin plus the `schedule` event's own lateness, which on a new repository has run to hours, or a healthy late night reads as stale (`run-unattended`, Report the outcome); a job triggered on time (below) is watched by a trigger of its own.

## Trigger on time

For a job whose plan states a lag the `schedule` event cannot keep (`SKILL.md`, Run the pipeline): a Cloudflare Worker on Cron Triggers calls each workflow's `workflow_dispatch` endpoint, and the run itself stays on GitHub's runner.
It lives in `trigger/` beside the package, with its own `package.json`, deployed with `uv run npx wrangler deploy` from that folder (Node from the project's `nodejs-wheel`, `setup-python`), its token set once with `uv run npx wrangler secret put GITHUB_TOKEN`.

`trigger/wrangler.jsonc`:

```jsonc
{
  "name": "myapp-trigger",
  "main": "src/index.ts",
  "compatibility_date": "2026-11-01",
  "triggers": { "crons": ["4 * * * *", "34 * * * *"] },
  "secrets": { "required": ["GITHUB_TOKEN"] },
}
```

`trigger/src/index.ts`, whose `Env` is the one `wrangler types` generates from that configuration (`write-entry-points`' TypeScript reference):

```typescript
const REPOSITORY = "owner/myapp";
const WORKFLOWS: Readonly<Record<string, string>> = {
  "4 * * * *": "pipeline.yml",
  "34 * * * *": "status.yml",
};

export default {
  async scheduled(controller, env) {
    const workflow = WORKFLOWS[controller.cron];
    if (workflow === undefined) {
      throw new Error(`no workflow for ${controller.cron}`);
    }
    const response = await fetch(
      `https://api.github.com/repos/${REPOSITORY}/actions/workflows/${workflow}/dispatches`,
      {
        body: JSON.stringify({ ref: "main" }),
        headers: {
          Accept: "application/vnd.github+json",
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          "User-Agent": "myapp-trigger",
        },
        method: "POST",
      },
    );
    if (!response.ok) {
      throw new Error(
        `${workflow}: ${response.status} ${await response.text()}`,
      );
    }
  },
} satisfies ExportedHandler<Env>;
```

- `GITHUB_TOKEN` here is a fine-grained personal access token for the one repository with **Actions: read and write**, the permission the dispatch endpoint needs, and an expiry date, listed in `DEPENDENCIES.md` with its rotation date (`secure-project`); the Actions `GITHUB_TOKEN` of the same name exists only inside a run (docs.github.com, REST permissions for fine-grained tokens, 2026-11-20).
- Each workflow keeps `workflow_dispatch:` under `on:` and drops its `schedule:`, or keeps it at a later minute as a backstop where a doubled run is a no-op (the lock, `concurrency`).
- `controller.cron` is the expression that fired, so one Worker serves both workflows within Workers Free's five Cron Triggers an account; a thrown error marks the invocation failed in the Worker's logs, and the next watch reports the run that never started.
- After deploying, `gh run list --workflow pipeline.yml --event workflow_dispatch --json createdAt --limit 24` shows each run's start against its slot; record the worst delay under Verification.
- Type-checked with TypeScript 7.0.2 against the types wrangler 4.166.0 generates, under `write-typescript`'s compiler settings, and linted and formatted as its toolchain says (2026-11-21); not yet run against a live account.
