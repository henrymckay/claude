# Claude Code

## Work

- Show a short diff or plan before large or risky changes.
- Commit and push my own branch without being asked once a change is complete and working; hold off on anything I'm still reviewing or iterating.
- If a repo has a `PLAN.md`, read it before planning or building, and change it only as `plan-project` allows.
- When a skill steered you wrong, said nothing where it should have, or contradicted another skill, or I corrected you on something a skill should cover, file an issue and carry on: `gh issue create -R henrymckay/claude --label skill-feedback`.
Name the skill and section, what happened, what should have happened, and the kind of project.
The repo is public, so describe the shape of the case, never the project's data.
File skill corrections there, not in memory, and edit a skill only in a `review-plugin` sweep, never mid-task.
- Get my explicit sign-off before force-pushing, rewriting shared history, or running destructive commands.
- When a requirement I have given turns out to be the thing forcing the design's complexity, come back and ask what it is for before building around it, and tell me what it costs.
I may not want it once I know the price.

## Answers

- **Let the length follow the question.** Use as few words as carry the point; a small question gets a small answer.
- Lead with the answer.
No preamble, no restating my question back at me.
- Report a finding once, where it matters.
Don't preview it, state it, then summarise it.
- Cut the closing offer unless there is a real choice to make.
If the next step is obvious, take it or name it in a clause.
- Keep the reasoning that changes my decision, cut the reasoning that shows your work.

## Skills

These skills encode my conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it.
Their trigger descriptions sit in a passive menu that is easy to skip on routine work, so check this list every time — not only when I name a skill.
Once you have applied a convention a few times, keep checking for it rather than assuming it is handled.
A skill's default is still a default: a decision I have signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself goes under Decisions as proposed, with its source and the skill and section it overrides, and is raised with me before you build on it (see `plan-project`); never skip or soften a rule without that line.

- **`be-functional`** for any code, in any language: the default style (`be-oop` where OOP genuinely fits).
- **`be-oop`** for object-oriented design: classes, inheritance, SOLID, patterns.
- **`build-project`** when building a project from its `PLAN.md`: milestone by milestone, gating each before it is ticked.
- **`choose-model`** when starting a stage, spawning a subagent or asked about cost: the model and effort ladder.
- **`deploy-project`** when a pipeline, dashboard, API or site must run in the cloud: the free-tier host per artefact and how it gets there.
- **`plan-project`** before building a new project or a new input, output or interface: the `PLAN.md`.
- **`run-unattended`** when a job runs on a schedule with nobody watching: the day it fetches, the lock, catch-up, exit codes, `status`, logs, the scheduler unit.
- **`review-plugin`** when reviewing this Claude repo: `review-project` plus drift across skills, `CLAUDE.md`, README, wiring and memory.
- **`review-project`** when reviewing, auditing or fixing a project: against its `PLAN.md`, the skills, correctness, tests and modernity.
- **`send-messages`** when a job or assistant must reach me: a failure alert, a digest with a chart, a two-way chat; which channel and what never to send.
- **`setup-python`** when scaffolding, packaging, or configuring a Python project (layout, `uv`, tooling).
- **`store-data`** when deciding where a project's data lives and how it is written and read: Parquet, DuckDB, MotherDuck, SQLite; the data directory, atomic partitions, the raw archive, quarantine and the run manifest.
- **`structure-python`** when organising a Python application into layers: hexagonal core, ports/adapters, entry-point drivers.
- **`use-git`** for any `git` operation: committing, branching, PRs, history (Conventional Commits; no `Co-authored-by` / "Generated with" footers).
- **`use-polars`** when working with `polars`.
- **`write-entry-points`** for building an app's entry points: a CLI, API, GUI or scheduled job; the driver shell and composition root.
- **`write-markdown`** for any Markdown, for humans or LLMs: READMEs, docs, `SKILL.md`, `CLAUDE.md`, prompts.
- **`write-python`** when writing or editing Python.
- **`write-skills`** when authoring or editing a skill: its name, description, opening, structure, and the skill/reference split.
- **`write-tests`** for writing or editing tests, in any language (`pytest` for Python).
