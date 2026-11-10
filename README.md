# 🤖 Claude Code

Personal [Claude Code](https://claude.com/claude-code) skills and global instructions.
**Symlink** them into `~/.claude` so they apply *everywhere*.

## ✏️ `CLAUDE.md`

[`CLAUDE.md`](CLAUDE.md) holds the cross-project instructions loaded into *every repo*.

- When to commit, push or hold off.
- How to answer concisely and directly.
- Which skill to invoke and when.

## 📦 Skills

Verb-first skills that encode consistent working conventions.
[`PLAN.md`](PLAN.md) records what the repo is for, its decisions and what is deliberately left out.

A project runs through three of them in turn:

1. [`plan-project`](skills/plan-project) drafts a `PLAN.md` from a loose conversation and asks one batch of questions.
2. [`build-project`](skills/build-project) builds it milestone by milestone, gating each before it is ticked.
3. [`review-project`](skills/review-project) reviews the result against the plan and the skills, then fixes what it finds.

The rest are the conventions those three apply.

- [`be-functional`](skills/be-functional) defines the default, language-agnostic functional style, with Python idioms via [`toolz`](https://toolz.readthedocs.io/) and [`plum`](https://beartype.github.io/plum/).
- [`be-oop`](skills/be-oop) defines language-agnostic object-oriented design.
- [`build-project`](skills/build-project) builds a planned project milestone by milestone, passing a quality gate before each is ticked.
- [`choose-model`](skills/choose-model) picks the model and effort for each stage of work, from Opus for planning and review to Haiku for graders, and how a skill or subagent sets its own.
- [`plan-project`](skills/plan-project) plans a project in one `PLAN.md` with standard sections, from numbered requirements to milestones.
- [`run-unattended`](skills/run-unattended) covers a job that runs on a schedule with nobody watching, from the lock and the missed night to the [`launchd`](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html), [`systemd`](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html) or [GitHub Actions](https://docs.github.com/en/actions) unit.
- [`review-plugin`](skills/review-plugin) extends `review-project` for this repo, from descriptions that no longer match their skills to rules duplicated across them.
- [`review-project`](skills/review-project) reviews a project against its plan, the skills, its tests and current releases, then fixes what it finds.
- [`setup-python`](skills/setup-python) scaffolds and configures a Python project with [`uv`](https://docs.astral.sh/uv/), [`ruff`](https://docs.astral.sh/ruff/), [`taplo`](https://taplo.tamasfe.dev/), [`pyright`](https://microsoft.github.io/pyright/), [`pytest`](https://docs.pytest.org/) and house-pick libraries for common tasks.
- [`store-data`](skills/store-data) decides where a project's data lives, from hive-partitioned [Parquet](https://parquet.apache.org/) queried with [DuckDB](https://duckdb.org/) or [MotherDuck](https://motherduck.com/) to atomic partitions, the raw archive and the run manifest.
- [`structure-python`](skills/structure-python) structures a Python application into hexagonal layers of a pure core behind ports, driven adapters and entry-point drivers over a `code`/`data`/`tests` layout.
- [`use-git`](skills/use-git) defines a `git` workflow from branching to [Conventional Commits](https://www.conventionalcommits.org).
- [`use-polars`](skills/use-polars) covers idiomatic [`polars`](https://pola.rs), from the expression API to keeping every group in one frame instead of looping.
- [`write-entry-points`](skills/write-entry-points) builds an app's entry points as thin shells over the pure core, whether a [`typer`](https://typer.tiangolo.com/) CLI, [`fastapi`](https://fastapi.tiangolo.com/) API, [`shiny`](https://shiny.posit.co/py/) GUI or scheduled job.
- [`write-markdown`](skills/write-markdown) covers writing Markdown for humans and LLMs (Large Language Models).
- [`write-python`](skills/write-python) defines in-code Python conventions, from typing and naming to error handling.
- [`write-skills`](skills/write-skills) defines house conventions for authoring a skill, from its name and description to its structure and the language-agnostic skill/reference split.
- [`write-tests`](skills/write-tests) defines language-agnostic testing conventions with a `pytest` reference for Python.

## 🛠️ Set up

Clone the repo.
Symlink the authored files into `~/.claude`.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Symlink `agents/`, `commands/` and `rules/` the same way once added.

> [!TIP]
> Reinstall any plugins separately.
> They live outside the repo under `~/.claude/plugins`.
> From the [marketplace](https://github.com/anthropics/claude-plugins-official), `skill-creator`, `pyright-lsp` and `commit-commands` pair well with these skills.

## 🎛️ Configure

Skills and `CLAUDE.md` shape *how* Claude approaches a task.
These per-session controls shape *which model* runs it, *how hard* it thinks and *how fast* it replies, independent of any skill.

- **Model.** `/model` picks the model for the session.
  - `haiku` for simple or high-volume tasks.
  - `sonnet` for daily work.
  - `opus` for complex reasoning.
  - `fable` for the hardest or longest tasks.
  - `best` for the most capable model available.
  - `opusplan` to plan on Opus and execute on Sonnet.
- **Effort.** `/effort` sets reasoning depth: `low`, `medium`, `high`, `xhigh` or `max`.
Raise it for a hard bug or design decision.
Lower it for routine edits.
- **Speed.** `/fast` toggles faster output on Opus at a higher per-token cost.
- **Output style.** `/output-style` swaps Claude's behavioural preset.
Default, Concise, Explanatory, Learning and Proactive ship with it.
A custom one can be added.
- **Permissions.** `Shift+Tab` cycles permission mode: `default`, `acceptEdits` and `plan`, then `bypassPermissions` and `auto` where enabled.
It controls how much Claude does before checking in.

## 🔁 Feed back

Claude files an [issue](https://github.com/henrymckay/claude/issues?q=label%3Askill-feedback) labelled `skill-feedback` whenever a skill steers it wrong during real work, as [`CLAUDE.md`](CLAUDE.md) requires.
A [`Stop` hook](hooks/stop-skill-feedback.json) backs the rule: at the end of each turn a small model reads the reply and, if a skill gap surfaced that was not filed, sends Claude back to file it.
Merge the file's `hooks` key into `~/.claude/settings.json` to install it.
[`review-plugin`](skills/review-plugin) works through the open issues first, fixing each in the skill that owns it, closing it with a reason, or leaving it open for a decision only you can make.
A weekly scheduled run of it opens one pull request with the sweep's report, so the week's skill changes are reviewed in one place.

The trigger suite under [`evaluate/triggers/`](evaluate/triggers) holds one casual prompt per skill with a grader that checks the skill fired.
Run it from the repo root to catch a description that has stopped triggering.

```bash
claude plugin eval . --ablation none --no-publish
```

## 🎯 Evaluate

Test how well the skills guide a build.
Have Claude build from a `brief.md` using the skills alone.
Then have it grade itself against `answers.md`.
Fix each divergence in the skill that let it through, or in the brief if the requirement was never stated.
Finish by bringing the build into line with those fixes.
Drive the whole run from [`prompt.md`](evaluate/prompt.md), with its three placeholders filled in.

Order every brief and every answers file the same way.

- Briefs open with the domain, then what varies about it, then how the input arrives.
- Briefs close with commands, output, options, examples and working style.
- Answers argue before they declare.
- Answers run shape, what the build earns, what should not exist yet, the declarations, the boundary, failure, the surface, verification and wrong turns.
- Omit a section a file has nothing to say about rather than padding it out.

Put each evaluation in its own folder, `evaluate/<name>/`, holding a `brief.md` and an `answers.md`.
None are checked in at present.
Chain builds, each carrying on from the last, so structure scaffolded too early shows up as a failure rather than a defensible choice.

## 📚 Learn more

- Pick the right [extension](https://code.claude.com/docs/en/features-overview) for a job, whether `CLAUDE.md`, a skill, a hook or a plugin.
- A [skill](https://code.claude.com/docs/en/skills) loads only when relevant, so it's cheap on context.
- [`CLAUDE.md`](https://code.claude.com/docs/en/memory) loads *every session*, so keep it to always-on rules under 200 lines.
- Claude Code reads config from `~/.claude` and a project's [`.claude/`](https://code.claude.com/docs/en/claude-directory).
- These skills follow the [Agent Skills](https://agentskills.io) open standard.
- Install prebuilt skills and [plugins](https://code.claude.com/docs/en/plugins/install) from the [marketplace](https://github.com/anthropics/claude-plugins-official) with `/plugin`.

## 🤝 Contribute

Contribute **only** `agents/`, `commands/`, `rules/`, `skills/` and `CLAUDE.md`.

> [!WARNING]
> **Never** commit Claude Code's runtime state.
> Its sessions, history and caches must stay local to `~/.claude`.
