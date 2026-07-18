# 🤖 Claude Code

Personal [Claude Code](https://claude.com/claude-code) skills and global instructions.
Symlinked into `~/.claude` so they apply everywhere.

## 📦 Skills

Verb-first skills that encode a consistent set of coding conventions.

- `be-functional` defines language-agnostic functional programming paradigms.
- `be-oop` defines language-agnostic object-oriented paradigms.
- `setup-python` scaffolds a Python project with [`uv`](https://docs.astral.sh/uv/), [`ruff`](https://docs.astral.sh/ruff/), [`pyright`](https://microsoft.github.io/pyright/), and [`pytest`](https://docs.pytest.org/).
- `use-git` defines a `git` workflow from branching to [Conventional Commits](https://www.conventionalcommits.org).
- `use-polars` covers idiomatic [`polars`](https://pola.rs) from expressions to [`pandas`](https://pandas.pydata.org) migration.
- `write-markdown` covers writing Markdown for humans and LLMs.
- `write-python` defines in-code Python conventions for style and structure.

## 🧠 Global instructions

`CLAUDE.md` holds cross-project guidance Claude Code loads in every repo.
It sets:

- Working style.
- `git` policy.
- Coding preferences.
- Index of the skills above.

## 🛠️ Set up

Clone the repo.
Symlink the authored files into `~/.claude`.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Symlink `agents/` and `commands/` the same way once you add them.

> [!TIP]
> Reinstall any Claude Code plugins separately.
> They live under `~/.claude/plugins`, outside the repo.

## 🧹 Keep the repo clean

Only the authored files belong in the repo:

- `skills/`.
- `CLAUDE.md`.
- `agents/` and `commands/`, once added.

> [!CAUTION]
> Never commit Claude Code's runtime state.
> Its sessions, history, and caches must stay local to `~/.claude`.
