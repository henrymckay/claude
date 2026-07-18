# 🤖 Claude Code

Personal [Claude Code](https://claude.com/claude-code) skills and global instructions.
Symlinked into `~/.claude` so they apply everywhere.

## 🧠 `CLAUDE.md`

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

## 📚 Learn more

`CLAUDE.md` holds always-on facts and conventions.
A skill packages a procedure that loads only when it's relevant.

- [Extend Claude Code](https://code.claude.com/docs/en/features-overview) compares `CLAUDE.md`, skills, hooks, and plugins so you know which to reach for.
- [Skills](https://code.claude.com/docs/en/skills) covers what a skill is and when to prefer one over `CLAUDE.md`.
- [Memory and `CLAUDE.md`](https://code.claude.com/docs/en/memory) covers what belongs in persistent instructions.
- [The `.claude` directory](https://code.claude.com/docs/en/claude-directory) maps out `~/.claude` and where each file loads from.
- [Agent Skills](https://agentskills.io) is the open standard these skills follow.
- [Discover plugins](https://code.claude.com/docs/en/discover-plugins) is how to find and install prebuilt skills and plugins.
- [Anthropic's official marketplace](https://github.com/anthropics/claude-plugins-official) is the curated plugin directory.

## 🤝 Contribute

Only the authored files belong in the repo:

- `skills/`.
- `CLAUDE.md`.
- `agents/` and `commands/`, once added.

> [!WARNING]
> Never commit Claude Code's runtime state.
> Its sessions, history, and caches must stay local to `~/.claude`.
