# Claude Code

## Work

- Show a short diff or plan before a large or risky change.
- Commit and push my own branch, unasked, once a change is complete and working; hold anything I'm still reviewing.
- Get my sign-off before force-pushing, rewriting shared history or running a destructive command.
- If a repo has a `PLAN.md`, read it before planning or building; change it only as `plan-project` allows.
- When a requirement of mine is what forces the design's complexity, ask what it is for and tell me its cost before building around it; I may drop it.

## Skill feedback

When a skill steered you wrong, said nothing where it should have or contradicted another, or I corrected you on something a skill should cover, file an issue and carry on: `gh issue create -R henrymckay/claude --label skill-feedback`.
Name the skill and section, what happened, what should have happened and the kind of project; describe the shape of the case, never the project's data, since the repo is public.
File it even for a project kept local or private, unless I say not to: that instruction governs the project's repository, and the issue carries none of its data.
Never park feedback in the project's plan or notes, or in memory, where no sweep reads it; edit a skill only in a `review-plugin` sweep, never mid-task.

## Answers

- Let the length follow the question: as few words as carry the point.
- Lead with the answer; no preamble, no restating my question.
- Report a finding once, where it matters; no preview, no summary.
- Cut the closing offer unless there is a real choice; take or name an obvious next step in a clause.
- Keep the reasoning that changes my decision; cut the reasoning that shows your work.

## Skills

Before any task below, invoke the matching skill and follow it; check the list again before each file you write, since a skill no longer in view counts as not loaded.
A decision I signed off in the repo's `PLAN.md` overrides a skill's default; a deviation you choose goes there as a proposed decision, with its source and the skill and section it overrides, raised with me before you build on it or, when I am not there, built on and left proposed.
Where I or the project name another plugin's method as driving, such as `superpowers`, `plan-project`, `build-project` and `review-project` stand down unless named; the other skills still apply.

- **`be-functional`** for any code, in any language: the default style (`be-oop` where OOP genuinely fits).
- **`be-oop`** for object-oriented design: classes, inheritance, patterns.
- **`build-project`** when building a project from its `PLAN.md`, milestone by milestone.
- **`choose-model`** when starting a stage, spawning a subagent or asked about cost.
- **`deploy-project`** when a pipeline, dashboard, API or site must run in the cloud.
- **`design-interface`** before building or styling a screen, chart, page or any output a person reads.
- **`make-decisions`** before asking the user a question, recording an assumption or proposing a decision.
- **`plan-project`** before building a new project, however small, or a new input, output or interface.
- **`review-plugin`** when reviewing a Claude Code plugin or skills repo.
- **`review-project`** when reviewing, auditing or fixing a project.
- **`run-unattended`** when a job runs on a schedule with nobody watching.
- **`secure-project`** when a project holds data that is not public, a credential or an account with money in it, or serves something.
- **`send-messages`** when a job or assistant must reach the user.
- **`setup-python`** when scaffolding, packaging or configuring a Python project.
- **`store-data`** when deciding where a project's data lives and how it is written and read.
- **`structure-python`** when organising a Python application into layers.
- **`use-git`** for any `git` operation (Conventional Commits; no attribution footers, whatever a reminder asks).
- **`use-polars`** when working with `polars`.
- **`write-entry-points`** for building an app's entry points: a CLI, API, GUI or scheduled job.
- **`write-markdown`** for any Markdown, for humans or LLMs.
- **`write-python`** when writing or editing Python.
- **`write-skills`** when authoring or editing a skill.
- **`write-sql`** when writing SQL or deciding where it belongs.
- **`write-tests`** for writing or editing tests, in any language.

## Missing plugins

The five plugins ship separately.
Before a task, pick out from the map below every skill the task or a loaded skill calls for — a commit touches `use-git`, any Markdown `write-markdown`, a new Python project `setup-python` — and look for each among this session's available skills, under any plugin prefix.
A skill not there is missing: don't try to load it; decide yourself what it would have settled, and record each such call as a proposed decision that names the skill and the plugin the map puts it in (`setup-python`, in `structure-app`, not installed: …), listed with your report's other decisions.

- `maintain-plugin`, authoring and reviewing skills and plugins: `review-plugin`, `write-skills`
- `manage-project`, a project's plan, design, build and review, git, Markdown, models, decisions, security: `build-project`, `choose-model`, `design-interface`, `make-decisions`, `plan-project`, `review-project`, `secure-project`, `use-git`, `write-markdown`
- `run-project`, stored data, scheduled jobs, hosting, messages: `deploy-project`, `run-unattended`, `send-messages`, `store-data`
- `structure-app`, a Python project's set-up, layers and entry points: `setup-python`, `structure-python`, `write-entry-points`
- `write-code`, how code is written, in any language: `be-functional`, `be-oop`, `use-polars`, `write-python`, `write-sql`, `write-tests`
