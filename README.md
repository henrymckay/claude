# claude

Personal Claude Code skills, shared across all my repos.

## How it works

The `skills/` directory is symlinked into `~/.claude/skills`, so every skill
here is available as a **personal skill** in every repo I work in.

```
ln -s /path/to/claude/skills ~/.claude/skills
```

## Layout

```
skills/<name>/SKILL.md   # reusable instructions, can auto-invoke (primary mechanism)
agents/<name>.md         # custom subagents
commands/<name>.md       # simple, explicitly-invoked slash commands (/name)
```

Each authored directory is symlinked into the matching `~/.claude/<dir>`:

```
~/.claude/skills   -> repo/skills
~/.claude/agents   -> repo/agents
~/.claude/commands -> repo/commands
```

Not symlinked (machine-local runtime state — never put in git/iCloud):
`sessions/`, `projects/`, `history.jsonl`, `shell-snapshots/`, `cache/`,
`plugins/`, `file-history/`, etc. Keep `~/.claude` itself a normal local dir.

File-based config you can optionally track later: `CLAUDE.md` (global
instructions), `keybindings.json`, and a sanitised copy of `settings.json`
(which also holds hooks/permissions/env).

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Fill in the frontmatter `name` and `description`. The `description` is what
   Claude matches against to decide when to auto-invoke — be specific about
   *what it does* and *when to use it*.
3. Write the instructions in the body.
4. Invoke explicitly any time with `/<skill-name>`.

Use any existing skill (e.g. `skills/use-git/SKILL.md`) as a template.

## On a new machine

```
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
```
