# 🤖 Claude Code

Personal [Claude Code](https://claude.com/claude-code) skills and global instructions.
Symlink them into `~/.claude` so they apply everywhere.

## ✏️ `CLAUDE.md`

[`CLAUDE.md`](CLAUDE.md) holds the cross-project instructions loaded into every repo.

- When to commit and push, and when to hold off.
- Which skill to invoke, and when.

## 📦 Skills

Verb-first skills that encode consistent working conventions.

- [`be-functional`](skills/be-functional) defines language-agnostic functional programming paradigms.
- [`be-oop`](skills/be-oop) defines language-agnostic object-oriented paradigms.
- [`setup-python`](skills/setup-python) scaffolds a Python project with [`uv`](https://docs.astral.sh/uv/), [`ruff`](https://docs.astral.sh/ruff/), [`pyright`](https://microsoft.github.io/pyright/), and [`pytest`](https://docs.pytest.org/).
- [`use-git`](skills/use-git) defines a `git` workflow from branching to [Conventional Commits](https://www.conventionalcommits.org).
- [`use-polars`](skills/use-polars) covers idiomatic [`polars`](https://pola.rs) from expressions to [`pandas`](https://pandas.pydata.org) migration.
- [`write-markdown`](skills/write-markdown) covers writing Markdown for humans and LLMs.
- [`write-python`](skills/write-python) defines in-code Python conventions for style and structure.

## 🛠️ Set up

Clone the repo.
Symlink the authored files into `~/.claude`.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Symlink `agents/` and `commands/` the same way once added.

> [!TIP]
> Reinstall any plugins separately.
> They live outside the repo under `~/.claude/plugins`.
> From the [marketplace](https://github.com/anthropics/claude-plugins-official), `skill-creator`, `pyright-lsp`, and `commit-commands` pair well with these skills.

## 📚 Learn more

- Pick the right [extension](https://code.claude.com/docs/en/features-overview) for a job, whether `CLAUDE.md`, a skill, a hook, or a plugin.
- A [skill](https://code.claude.com/docs/en/skills) loads only when relevant, so it's cheap on context.
- [`CLAUDE.md`](https://code.claude.com/docs/en/memory) loads every session, so keep it to continuous rules under 200 lines.
- Claude Code reads config from `~/.claude` and a project's [`.claude/`](https://code.claude.com/docs/en/claude-directory).
- These skills follow the [Agent Skills](https://agentskills.io) open standard.
- Install prebuilt skills and [plugins](https://code.claude.com/docs/en/discover-plugins) from the [official marketplace](https://github.com/anthropics/claude-plugins-official) with `/plugin`.

## 🤝 Contribute

Only the authored files belong in the repo:

- `skills/`.
- `CLAUDE.md`.
- `agents/` and `commands/`, once added.

> [!WARNING]
> Never commit Claude Code's runtime state.
> Its sessions, history, and caches must stay local to `~/.claude`.
