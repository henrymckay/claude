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

## 🛠️ Set up

Clone the repo, then symlink the authored files into `~/.claude`.
Claude Code loads them in every project.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Symlink `agents/` and `commands/` the same way once you add them.

> [!CAUTION]
> Symlink only the files above, never all of `~/.claude`.
> Its sessions, history, and caches must never be committed.

> [!NOTE]
> Reinstall any Claude Code plugins separately.
> They live outside this repo, under `~/.claude/plugins`.
