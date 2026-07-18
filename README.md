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

## 🔗 Set up

Clone the repo.
Symlink each authored piece into `~/.claude`.
Claude Code then loads it in every repo.

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills    ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
# optional, once you add them:
# ln -s /path/to/claude/agents   ~/.claude/agents
# ln -s /path/to/claude/commands ~/.claude/commands
```

> [!NOTE]
> Reinstall any Claude Code plugins separately.
> They live outside this repo, under `~/.claude/plugins`.

## 🚫 Keep runtime state local

> [!CAUTION]
> Never symlink all of `~/.claude`.
> Never commit its runtime state.
> Symlink only the authored files above.

This machine-local state stays out of `git` and iCloud:

- Session and history state.
  - `history.jsonl`, `projects/`, `sessions/`.
- Caches and installed state.
  - `cache/`, `file-history/`, `plugins/`, `shell-snapshots/`.

## ➕ Add a skill

1. Create `skills/<name>/SKILL.md`.
2. Fill in the `name` and `description` frontmatter.
   - The `description` drives auto-invocation.
     Be specific about what it does and when to use it.
3. Write the instructions in the body.
4. Invoke it explicitly any time with `/<name>`.

Copy an existing skill such as `skills/use-git/SKILL.md` as a starting template.
