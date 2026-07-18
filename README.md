# Claude Code skills & config

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

## 🔗 Link it into `~/.claude`

Symlink each authored piece into `~/.claude`, and Claude Code picks it up in every repo.
Keep `~/.claude` itself a normal local directory — symlink only the tracked files below.

```bash
ln -s /path/to/claude/skills    ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
# optional, once you add them:
# ln -s /path/to/claude/agents   ~/.claude/agents
# ln -s /path/to/claude/commands ~/.claude/commands
```

The repo currently tracks `skills/` and `CLAUDE.md`; `agents/` and `commands/` follow the same pattern whenever you add them.

```text
~/.claude/skills    -> repo/skills
~/.claude/CLAUDE.md -> repo/CLAUDE.md
~/.claude/agents    -> repo/agents      # optional
~/.claude/commands  -> repo/commands    # optional
```

## 🚫 Keep runtime state local

Machine-local runtime state must never go in git or iCloud, so never symlink all of `~/.claude` — only the authored folders above.

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

## 💻 Set up on a new machine

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills    ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Reinstall any Claude Code plugins you rely on separately — they live outside this repo, under `~/.claude/plugins`.
