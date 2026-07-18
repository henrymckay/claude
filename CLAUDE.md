# Global instructions

Personal, cross-project guidance for Claude Code.
Applies in every repo.
Keep project-specific rules in that project's own `CLAUDE.md` instead.

## Working style

- Be concise; lead with the answer, then the reasoning if needed.
- Git: follow the `use-git` skill.
  Commit and push your own branch without waiting to be asked once a change is complete and working; hold off on anything I'm still actively reviewing or iterating.
  Force-pushing, rewriting shared history, and destructive commands need explicit sign-off.
- Prefer showing a short diff/plan before large or risky changes.

## Coding preferences

- Match the conventions of the surrounding code.

## Skills — consult these proactively

These personal skills carry my conventions.
Consult the relevant one *before* acting, not only when explicitly asked — their descriptions sit in a passive menu and are easy to skip on routine work.

- Any git operation (commit, branch, PR, history) → follow **`use-git`**.
  In particular: Conventional Commits format, and **no `Co-Authored-by` / "Generated with" footers** on commit messages.
- Writing or editing Python → **`write-python`**.
- Starting a new Python project or packaging → **`setup-python`**.
- Functional-style code, in any language → **`be-functional`**.
- Object-oriented design (classes, inheritance, SOLID, patterns) → **`be-oop`**.
- Any Markdown, human- or LLM-facing (README, docs, SKILL.md, CLAUDE.md, prompts) → **`write-markdown`** — it separates universal rules from audience-specific ones.
- Working with Polars → **`use-polars`**.
