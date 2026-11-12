# 🤖 claude

Five [Claude Code](https://code.claude.com/docs) plugins that let Claude plan, build, review and run a project from a short prompt.
They settle in advance the decisions that recur across projects, so Claude neither asks nor re-decides them.
When a skill steers Claude wrong, the gap is filed and a sweep fixes it, so the plugins improve as they are used.

[`PLAN.md`](PLAN.md) holds the aim, the decisions and what is left out on purpose.

## 📦 Plugins

Each plugin installs on its own and names any skill it needs from a plugin you left out.

- **`manage-project`** — a project's life from a loose conversation to a reviewed build.
  - [`plan-project`](plugins/manage-project/skills/plan-project) drafts one `PLAN.md` and asks one batch of questions.
  - [`build-project`](plugins/manage-project/skills/build-project) builds it milestone by milestone behind a quality gate.
  - [`review-project`](plugins/manage-project/skills/review-project) reviews against the plan and the skills, then fixes what it finds.
  - [`choose-model`](plugins/manage-project/skills/choose-model) runs each stage on the right model and effort.
  - [`make-decisions`](plugins/manage-project/skills/make-decisions) settles an open question from the nearest precedent.
  - [`secure-project`](plugins/manage-project/skills/secure-project) keeps private data and credentials where their class allows.
  - [`use-git`](plugins/manage-project/skills/use-git) sets branching and [Conventional Commits](https://www.conventionalcommits.org).
  - [`write-markdown`](plugins/manage-project/skills/write-markdown) writes Markdown for humans and for models.
- **`write-code`** — how the code itself is written, whatever the toolchain.
  - [`be-functional`](plugins/write-code/skills/be-functional) is the default style.
  - [`be-oop`](plugins/write-code/skills/be-oop) is object-oriented design where it fits.
  - [`write-python`](plugins/write-code/skills/write-python) covers typing, naming and the error model.
  - [`write-sql`](plugins/write-code/skills/write-sql) decides where SQL belongs, with a [DuckDB](https://duckdb.org) reference.
  - [`write-tests`](plugins/write-code/skills/write-tests) covers tests in any language, with `pytest` for Python.
  - [`use-polars`](plugins/write-code/skills/use-polars) covers idiomatic [`polars`](https://pola.rs).
- **`structure-app`** — a Python application's set-up and shape.
  - [`setup-python`](plugins/structure-app/skills/setup-python) scaffolds with [`uv`](https://docs.astral.sh/uv), `ruff`, `pyright` and `pytest`.
  - [`structure-python`](plugins/structure-app/skills/structure-python) lays out a pure core behind ports and adapters.
  - [`write-entry-points`](plugins/structure-app/skills/write-entry-points) builds the CLI, API, dashboard or scheduled job.
- **`run-project`** — a project in the real world.
  - [`store-data`](plugins/run-project/skills/store-data) decides where data lives: Parquet, DuckDB, MotherDuck or SQLite.
  - [`run-unattended`](plugins/run-project/skills/run-unattended) runs a job nobody watches.
  - [`deploy-project`](plugins/run-project/skills/deploy-project) picks a free or near-free host for each artefact.
  - [`send-messages`](plugins/run-project/skills/send-messages) decides how a job reaches you.
- **`maintain-plugin`** — keeping plugins like these healthy, yours or anyone's.
  - [`write-skills`](plugins/maintain-plugin/skills/write-skills) sets how a skill is named, described and structured.
  - [`review-plugin`](plugins/maintain-plugin/skills/review-plugin) works through skill feedback and checks a plugin for drift.

## 🛠️ Install

Install any subset from the marketplace, pinned to the newest release tag.

```bash
claude plugin marketplace add henrymckay/claude#v0.2
claude plugin install manage-project@henrymckay
claude plugin install write-code@henrymckay
```

Each plugin prints its skill list at session start, so no `CLAUDE.md` is needed.

Where plugins cannot be installed, symlink them instead.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s "$PWD/claude/skills" ~/.claude/skills
ln -s "$PWD/claude/CLAUDE.md" ~/.claude/CLAUDE.md
```

> [!WARNING]
> Never link `skills/` on a machine with the plugins installed.
> Both together load every skill twice.

With symlinks, merge the `Stop` entry of [`hooks.json`](plugins/maintain-plugin/hooks/hooks.json) into `~/.claude/settings.json`.

## 🎛️ Configure

- **Feedback** — `claude plugin configure maintain-plugin` sets `feedback` to `issues` (the default), `file` or `off`.
  Use `file` on a machine whose work must not reach a public tracker.
- **`CLAUDE.md`** — with symlinks, it is the always-on file: the working rules, the skill list and the feedback repository.
- **Companions** — `skill-creator`, `commit-commands`, `pyright-lsp`, `claude-security` and `security-guidance` from the [official marketplace](https://github.com/anthropics/claude-plugins-official) pair well with these.

## 🔁 Feedback and sweeps

1. **Feedback** — when a skill steers Claude wrong, Claude files an [issue](https://github.com/henrymckay/claude/issues?q=label%3Askill-feedback) labelled `skill-feedback` on the plugin's repository.
   A `Stop` hook sends Claude back if it forgot.
2. **Sweep** — [`review-plugin`](plugins/maintain-plugin/skills/review-plugin) works through the open issues, then runs every drift check.
   It runs weekly as a scheduled task, or on demand when you say "review the skills".
3. **Pull request** — each sweep lands as one pull request whose body is its report, listing every rule it cut or changed.

Each plugin's `evals/` folder holds one casual prompt per skill, to show its description still triggers.
Pass `--trust-plugin` only for a plugin whose source you have read.

```bash
cd plugins/write-code
claude plugin eval . --ablation none --no-publish --trust-plugin
```

## 🧪 Trial builds

The trigger suites show a skill loads; a trial build shows it steers well.

1. Start a headless session in a new project folder with one prompt and nobody answering: `claude -p --permission-mode auto`.
2. Claude plans, builds and reviews the project in autonomous mode: it records its answers as assumptions and takes no outward action.
3. Read the transcript under `~/.claude/projects/` for skills that never loaded and stages on the wrong model.
4. The next sweep works through the feedback the build filed.

Two builds are done: a data pipeline and a dashboard over its store.
Next comes a public project deployed end to end, then one kept private on your own machine, then one over a real account with a read-only credential.

## 📄 Licence

[MIT](LICENSE).
