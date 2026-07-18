# Claude Code skills

Personal [Claude Code](https://claude.com/claude-code) skills and configuration, version-controlled and symlinked into `~/.claude` so they work across every repo and machine.

## 📦 Skills

Verb-first skills that encode my coding conventions.

| Skill | Purpose |
|---|---|
| `use-git` | Git workflow: branches, atomic commits, Conventional Commits, rebase vs merge. |
| `setup-python` | Scaffold a Python project: `src/` layout, `uv`, `ruff`, `pyright`, `pytest`. |
| `write-python` | In-code Python conventions: typing, docstrings, imports, idioms. |
| `be-functional` | Functional style in any language: purity, immutability, composition. |
| `be-oop` | Object-oriented design done well: composition, SOLID, patterns. |
| `use-polars` | Idiomatic Polars: expressions, lazy execution, pandas migration. |
| `write-markdown` | Markdown for humans and LLMs, with audience-specific rules. |

## 🔗 How it works

Symlink `skills/` into `~/.claude/skills`, and Claude Code loads every skill as a personal skill in all repos.

```bash
ln -s /path/to/claude/skills ~/.claude/skills
```

The same pattern extends to other authored config if you add it.

```text
~/.claude/skills   -> repo/skills
~/.claude/agents   -> repo/agents      # optional, if you add agents/
~/.claude/commands -> repo/commands    # optional, if you add commands/
```

## 🚫 What stays local

Machine-local runtime state must never go in git or iCloud.
Keep `~/.claude` itself a normal local directory and symlink only the authored folders.

- Session and history state.
  - `sessions/`, `projects/`, `history.jsonl`.
- Caches and installed state.
  - `shell-snapshots/`, `cache/`, `plugins/`, `file-history/`.

## ➕ Add a skill

1. Create `skills/<name>/SKILL.md`.
2. Fill in the `name` and `description` frontmatter.
   - The `description` drives auto-invocation, so be specific about what it does and when to use it.
3. Write the instructions in the body.
4. Invoke it explicitly any time with `/<name>`.

Copy an existing skill such as `skills/use-git/SKILL.md` as a starting template.

## 💻 On a new machine

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
```
