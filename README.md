# 🤖 claude

Six [Claude Code](https://code.claude.com/docs) plugins that let Claude plan, design, build, review and run a project from a short prompt.
They settle in advance the decisions that recur across projects, so Claude neither asks nor re-decides them.
When a skill steers Claude wrong, the gap is filed and a sweep fixes it.

[`PLAN.md`](PLAN.md) holds the aim, the decisions and what is left out on purpose.

## 📦 Plugins

Each plugin installs on its own and names any skill it needs from a plugin you left out.

- **`manage-project`** — a project's life from a loose conversation to a reviewed build.
  - [`plan-project`](plugins/manage-project/skills/plan-project) drafts one `PLAN.md` and asks one batch of questions.
  - [`build-project`](plugins/manage-project/skills/build-project) builds it milestone by milestone behind a gate that runs the product.
  - [`review-project`](plugins/manage-project/skills/review-project) reviews against the plan and the skills, then fixes what it finds.
  - [`retire-project`](plugins/manage-project/skills/retire-project) tears a project down from its records, confirming each removal.
  - [`choose-model`](plugins/manage-project/skills/choose-model) runs each stage on the right model and records its cost.
  - [`make-decisions`](plugins/manage-project/skills/make-decisions) settles an open question from the nearest precedent.
  - [`secure-project`](plugins/manage-project/skills/secure-project) keeps private data and credentials where their class allows, and says how to set Claude Code's own permission controls and sandbox.
  - [`use-git`](plugins/manage-project/skills/use-git) sets branching and [Conventional Commits](https://www.conventionalcommits.org).
  - [`write-markdown`](plugins/manage-project/skills/write-markdown) writes Markdown for humans and for models.
- **`design-project`** — what a project shows and holds, settled before it is built.
  - [`design-interface`](plugins/design-project/skills/design-interface) sets one house look and a bar for every surface: screen, alert, command line, API, README.
  - [`design-pipeline`](plugins/design-project/skills/design-pipeline) shapes each table's grain, loads and freshness, daily or intraday.
- **`write-code`** — how the code itself is written, whatever the toolchain.
  - [`be-functional`](plugins/write-code/skills/be-functional) is the default style.
  - [`be-oop`](plugins/write-code/skills/be-oop) is object-oriented design where it fits.
  - [`write-python`](plugins/write-code/skills/write-python) covers typing, naming and the error model.
  - [`write-typescript`](plugins/write-code/skills/write-typescript) does the same for TypeScript, React and Cloudflare Workers.
  - [`write-sql`](plugins/write-code/skills/write-sql) decides where SQL belongs, with a [DuckDB](https://duckdb.org) reference.
  - [`write-tests`](plugins/write-code/skills/write-tests) covers tests in any language, with `pytest` for Python and Vitest for TypeScript.
  - [`use-polars`](plugins/write-code/skills/use-polars) covers idiomatic [`polars`](https://pola.rs).
- **`structure-app`** — a Python application's set-up and shape.
  - [`setup-python`](plugins/structure-app/skills/setup-python) scaffolds with [`uv`](https://docs.astral.sh/uv), `ruff`, `pyright` and `pytest`.
  - [`structure-python`](plugins/structure-app/skills/structure-python) lays out a pure core behind ports and adapters.
  - [`write-entry-points`](plugins/structure-app/skills/write-entry-points) builds the CLI, API, dashboard or scheduled job, with the toolchain for a TypeScript front end or Worker.
- **`run-project`** — a project in the real world.
  - [`store-data`](plugins/run-project/skills/store-data) decides where data lives: Parquet, DuckDB, MotherDuck or SQLite.
  - [`run-unattended`](plugins/run-project/skills/run-unattended) runs a job nobody watches.
  - [`deploy-project`](plugins/run-project/skills/deploy-project) picks a free or near-free host for each artefact.
  - [`send-messages`](plugins/run-project/skills/send-messages) decides how a job reaches you.
- **`maintain-plugin`** — keeping plugins like these healthy, yours or anyone's.
  - [`write-skills`](plugins/maintain-plugin/skills/write-skills) sets how a skill is named, described and structured.
  - [`review-plugin`](plugins/maintain-plugin/skills/review-plugin) works through skill feedback and checks a plugin for drift.

## 🛠️ Install

Install any subset, pinned to the newest release tag.

```bash
claude plugin marketplace add "henrymckay/claude#$(git ls-remote --tags --refs --sort=-version:refname https://github.com/henrymckay/claude.git 'v*' | head -n 1 | cut -d/ -f3)"
claude plugin install manage-project@henrymckay
claude plugin install write-code@henrymckay
```

Where plugins cannot be installed, symlink them instead.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s "$PWD/claude/skills" ~/.claude/skills
ln -s "$PWD/claude/instructions/symlinked.md" ~/.claude/CLAUDE.md
```

> [!WARNING]
> Never link `skills/` on a machine with the plugins installed.
> Both together load every skill twice.

With symlinks, merge the `Stop` entry of `maintain-plugin`'s [`hooks.json`](plugins/maintain-plugin/hooks/hooks.json) into `~/.claude/settings.json`.

## 🎛️ Configure

- **Feedback** — `claude plugin configure maintain-plugin` sets `feedback` to `issues` (the default), `file` or `off`.
  Use `file` on a machine whose work must not reach a public tracker.
- **`CLAUDE.md`** — only your own rules with the plugins installed, since each plugin prints its skill list into every session and subagent, like the owner's [`installed.md`](instructions/installed.md); with symlinks, [`symlinked.md`](instructions/symlinked.md) adds the skill list, plugin map and feedback rule.

## 🧩 Companions

From Anthropic's [official marketplace](https://github.com/anthropics/claude-plugins-official); each skill using one works without it.

- **`skill-creator`** tests a skill with and without it and tunes its description, for `write-skills`.
- **`plugin-dev`** checks hooks, manifests, agents and commands, for `review-plugin`.
- **`commit-commands`** runs the commit and pull request flows `use-git` sets conventions for.
- **`pyright-lsp`**, **`typescript-lsp`** and **`claude-security`** for type errors and security.

Beyond these, `plan-project` looks for an outside plugin where no skill here covers a project's language or domain, and proposes it for you to install.

## 🔁 Feedback and sweeps

1. **Feedback** — when a skill steers Claude wrong, Claude files an issue labelled `skill-feedback` on the plugin's repository.
   A `Stop` hook sends Claude back if it forgot.
2. **Sweep** — [`review-plugin`](plugins/maintain-plugin/skills/review-plugin) works through the open issues, runs every drift check, and ends with a read-only review on the top model.
   It runs weekly, or when you say "review the skills".
3. **Pull request** — each sweep lands as one pull request whose body is its report.

Each plugin's `evals/` holds a casual prompt that should fire each skill, and, where a neighbour could claim one, a prompt that should not.
Pass `--trust-plugin` only for a plugin whose source you have read.
Add `--scaffold --allow-tools Write` in `manage-project` and `write-code`, whose mid-task cases start from a prepared folder.

```bash
cd plugins/write-code
claude plugin eval . --ablation none --no-publish --trust-plugin
```

## 🧪 Trial builds

The trigger suites show a skill loads; a trial build shows it steers well.
A trial is meant to run as a Claude Code cloud session given only the trial's repository, with the house plugins loaded by a pinned start-up hook ([`build-project`'s set-up](plugins/manage-project/skills/build-project/references/unattended.md)).
The control build of 2026-11-22 ran three that way, one prompt with all, none and two of the plugins.
Its work is to come back as a branch, and your reading of the diff decides whether it is finished; a sweep then works through the build's feedback.
[`PLAN.md`](PLAN.md)'s `Next` list orders them.

## 📄 Licence

[MIT](LICENSE).
