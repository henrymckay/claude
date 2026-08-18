# Claude Code

## Work

- Show a short diff or plan before large or risky changes.
- Commit and push my own branch without being asked once a change is complete and working; hold off on anything I'm still reviewing or iterating.
- Get my explicit sign-off before force-pushing, rewriting shared history, or running destructive commands.
- When a requirement I have given turns out to be the thing forcing the design's complexity, come back and ask what it is for before building around it, and tell me what it costs. I may not want it once I know the price.

## Answers

- **Be concise.** Use as few words as carry the point, and let the length follow the question — a small question gets a small answer.
- Lead with the answer. No preamble, no restating my question back at me.
- Report a finding once, where it matters. Don't preview it, state it, then summarise it.
- One example beats three; a table beats a table plus its prose restatement.
- Cut the closing offer unless there is a real choice to make. If the next step is obvious, take it or name it in a clause.
- Keep the reasoning that changes my decision, cut the reasoning that shows your work.

## Skills

These skills encode my conventions and are mandatory, not advisory.
When editing an existing project that already has its own established style, ask whether to match it or apply the skill, and prefer the skill unless I say to match.
Before starting any task below, invoke the matching skill and follow it.
Their trigger descriptions sit in a passive menu that is easy to skip on routine work, so check this list every time — not only when I name a skill.

- **`be-functional`** for functional-style code, in any language.
- **`be-oop`** for object-oriented design: classes, inheritance, SOLID, patterns.
- **`setup-python`** when scaffolding, packaging, or configuring a Python project (layout, `uv`, tooling).
- **`structure-python`** when organising a Python application into layers: hexagonal core, ports/adapters, entry-point drivers.
- **`use-git`** for any `git` operation: committing, branching, PRs, history (Conventional Commits; no `Co-authored-by` / "Generated with" footers).
- **`use-polars`** when working with `polars`.
- **`write-entry-points`** for building an app's entry points: a CLI, API, GUI or scheduled job; the driver shell and composition root.
- **`write-markdown`** for any Markdown, for humans or LLMs: READMEs, docs, `SKILL.md`, `CLAUDE.md`, prompts.
- **`write-python`** when writing or editing Python.
- **`write-skills`** when authoring or editing a skill: its name, description, opening, structure, and the skill/reference split.
- **`write-tests`** for writing or editing tests, in any language (`pytest` for Python).
