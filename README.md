# 🤖 Claude Code

Personal [Claude Code](https://claude.com/claude-code) skills and global instructions, symlinked into `~/.claude` so they work in every repo and on every machine.

## 📦 Skills

Verb-first skills that encode a consistent set of coding conventions.

| Skill | Purpose |
|---|---|
| `be-functional` | Functional style in any language: purity, immutability, composition. |
| `be-oop` | Object-oriented design done well: composition, SOLID, patterns. |
| `setup-python` | Scaffold a Python project: `src/` layout, `uv`, `ruff`, `pyright`, `pytest`. |
| `use-git` | Git workflow: branches, atomic commits, Conventional Commits, rebase vs merge. |
| `use-polars` | Idiomatic Polars: expressions, lazy execution, pandas migration. |
| `write-markdown` | Markdown for humans and LLMs, with audience-specific rules. |
| `write-python` | In-code Python conventions: typing, docstrings, imports, idioms. |

## 🔗 Set up

Clone the repo, then symlink each authored piece into `~/.claude` so Claude Code loads it in every repo.

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
> Never symlink all of `~/.claude`, and never commit its runtime state.
> Symlink only the authored files above.

This machine-local state stays out of git and iCloud:

- Session and history state.
  - `history.jsonl`, `projects/`, `sessions/`.
- Caches and installed state.
  - `cache/`, `file-history/`, `plugins/`, `shell-snapshots/`.

## ➕ Add a skill

1. Create `skills/<name>/SKILL.md`.
2. Fill in the `name` and `description` frontmatter.
   - The `description` drives auto-invocation, so be specific about what it does and when to use it.
3. Write the instructions in the body.
4. Invoke it explicitly any time with `/<name>`.

Copy an existing skill such as `skills/use-git/SKILL.md` as a starting template.
