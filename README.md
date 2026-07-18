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

- The [right extension for a job](https://code.claude.com/docs/en/features-overview) ranges from `CLAUDE.md` to skills, hooks, and plugins.
- A skill's body loads only when it's relevant, so [reference material in a skill](https://code.claude.com/docs/en/skills) costs almost nothing until used.
- `CLAUDE.md` loads in full every session, so keep it to [always-on rules under ~200 lines](https://code.claude.com/docs/en/memory).
- Claude Code reads the same file types from `~/.claude` and a project's [`.claude/` directory](https://code.claude.com/docs/en/claude-directory).
- These skills follow the [Agent Skills](https://agentskills.io) open standard, so they work in other AI tools too.
- [Prebuilt skills and plugins](https://code.claude.com/docs/en/discover-plugins) install from a marketplace with `/plugin`.
- [Anthropic's official marketplace](https://github.com/anthropics/claude-plugins-official) is a curated directory of high-quality plugins.

## 🤝 Contribute

Only the authored files belong in the repo:

- `skills/`.
- `CLAUDE.md`.
- `agents/` and `commands/`, once added.

> [!WARNING]
> Never commit Claude Code's runtime state.
> Its sessions, history, and caches must stay local to `~/.claude`.
