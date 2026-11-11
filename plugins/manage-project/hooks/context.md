# Skills from the `manage-project` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
Check it again before each file you write, since a long session drifts from it: a skill whose text is no longer in view, or that was loaded under a name this list no longer uses, counts as not loaded.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it — or, with no user present, built on and left proposed for their review (`plan-project`, Plan with no user present); never skip or soften a rule without that line.
A skill named in this list or in another skill may belong to a plugin that is not installed here (`maintain-plugin`, `manage-project`, `write-code`, `structure-app` and `run-project` ship separately): when loading it fails, decide what it would have settled yourself, record each such call as a proposed decision, and tell the user which plugin was missing.

- **`build-project`** when building a project from its `PLAN.md`: milestone by milestone, gating each before it is ticked.
- **`choose-model`** when starting a stage, spawning a subagent or asked about cost: the model and effort ladder.
- **`make-decisions`** before asking the user a question, recording an assumption or proposing a decision: the nearest answered precedent, cited, and what still goes to the user.
- **`plan-project`** before building a new project or a new input, output or interface: the `PLAN.md`.
- **`review-project`** when reviewing, auditing or fixing a project: against its `PLAN.md`, the skills, correctness, tests and modernity.
- **`secure-project`** when a project holds data that is not public, a credential or an account with money in it, or serves something: the data's class, where it may go, secrets, access, the audit.
- **`use-git`** for any `git` operation: committing, branching, PRs, history (Conventional Commits; no `Co-authored-by` / "Generated with" footers).
- **`write-markdown`** for any Markdown, for humans or LLMs: READMEs, docs, `SKILL.md`, `CLAUDE.md`, prompts.
