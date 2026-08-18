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

- [`be-functional`](skills/be-functional) defines a language-agnostic functional style, with Python idioms via [`toolz`](https://toolz.readthedocs.io/) and [`plum`](https://beartype.github.io/plum/).
- [`be-oop`](skills/be-oop) defines language-agnostic object-oriented design.
- [`setup-python`](skills/setup-python) scaffolds and configures a Python project with [`uv`](https://docs.astral.sh/uv/), [`ruff`](https://docs.astral.sh/ruff/), [`taplo`](https://taplo.tamasfe.dev/), [`pyright`](https://microsoft.github.io/pyright/), [`pytest`](https://docs.pytest.org/) and house-pick libraries for common tasks.
- [`structure-python`](skills/structure-python) structures a Python application into hexagonal layers of a pure core behind ports, driven adapters and entry-point drivers over a `code`/`data`/`tests` layout.
- [`use-git`](skills/use-git) defines a `git` workflow from branching to [Conventional Commits](https://www.conventionalcommits.org).
- [`use-polars`](skills/use-polars) covers idiomatic [`polars`](https://pola.rs) from expressions to [`pandas`](https://pandas.pydata.org) migration.
- [`write-entry-points`](skills/write-entry-points) builds an app's entry points as thin shells over the pure core, whether a [`typer`](https://typer.tiangolo.com/) CLI, [`fastapi`](https://fastapi.tiangolo.com/) API, [`shiny`](https://shiny.posit.co/py/) GUI or scheduled job.
- [`write-markdown`](skills/write-markdown) covers writing Markdown for humans and LLMs (Large Language Models).
- [`write-python`](skills/write-python) defines in-code Python conventions for style and structure.
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
  - `opusplan` to plan on Opus and execute on Sonnet.
- **Effort.** `/effort` sets reasoning depth from `low` to `max`.
  Raise it for a hard bug or design decision, lower it for routine edits.
- **Speed.** `/fast` toggles faster output on Opus at a higher per-token cost.
- **Output style.** `/output-style` swaps Claude's behavioural preset, e.g. Default, Proactive, Explanatory or a custom one.
- **Permissions.** `Shift+Tab` cycles permission mode (`default`, `plan`, `acceptEdits`, `auto`, `bypassPermissions`).
  It controls how much Claude does before checking in.

## 🎯 Evaluate

Test how the skills guide a build, then fix what let a bad one through.
Point Claude at a `brief.md` and have it build from the skills alone, grade itself against `answers.md`, then fix every divergence at source.
A design it should have reached is the skill's fault.
A requirement it could never have known is the brief's.

- [`demark`](evaluate/demark) produces and displays DeMark counts for stock tickers across timeframes.

## 📚 Learn more

- Pick the right [extension](https://code.claude.com/docs/en/features-overview) for a job, whether `CLAUDE.md`, a skill, a hook or a plugin.
- A [skill](https://code.claude.com/docs/en/skills) loads only when relevant, so it's cheap on context.
- [`CLAUDE.md`](https://code.claude.com/docs/en/memory) loads *every session*, so keep it to always-on rules under 200 lines.
- Claude Code reads config from `~/.claude` and a project's [`.claude/`](https://code.claude.com/docs/en/claude-directory).
- These skills follow the [Agent Skills](https://agentskills.io) open standard.
- Install prebuilt skills and [plugins](https://code.claude.com/docs/en/discover-plugins) from the [marketplace](https://github.com/anthropics/claude-plugins-official) with `/plugin`.

## 🤝 Contribute

Contribute **only** `agents/`, `commands/`, `rules/`, `skills/` and `CLAUDE.md`.

> [!WARNING]
> **Never** commit Claude Code's runtime state.
> Its sessions, history and caches must stay local to `~/.claude`.
