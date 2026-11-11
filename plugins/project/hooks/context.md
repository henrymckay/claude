# Skills from the `project` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it; never skip or soften a rule without that line.
A skill named in this list or in another skill may belong to a plugin that is not installed here (`meta`, `project`, `code`, `scaffold` and `operate` ship separately): when loading it fails, decide what it would have settled yourself, record each such call as a proposed decision, and tell the user which plugin was missing.

- **`build-project`** when building a project from its `PLAN.md`: milestone by milestone, gating each before it is ticked.
- **`plan-project`** before building a new project or a new input, output or interface: the `PLAN.md`.
- **`review-project`** when reviewing, auditing or fixing a project: against its `PLAN.md`, the skills, correctness, tests and modernity.
- **`use-git`** for any `git` operation: committing, branching, PRs, history (Conventional Commits; no `Co-authored-by` / "Generated with" footers).
- **`write-markdown`** for any Markdown, for humans or LLMs: READMEs, docs, `SKILL.md`, `CLAUDE.md`, prompts.
