# Claude Code

## Work

- Show a short diff or plan before a large or risky change.
- Commit and push my own branch, unasked, once a change is complete and working; hold anything I'm still reviewing.
- Get my sign-off before force-pushing, rewriting shared history or running a destructive command.
- If a repo has a `PLAN.md`, read it before planning or building; change it only as `plan-project` allows.
- When a requirement of mine is what forces the design's complexity, ask what it is for and tell me its cost before building around it; I may drop it.

## Skill feedback

When a skill steered you wrong, said nothing where it should have or contradicted another, or I corrected you on something a skill should cover, file an issue on the `repository` named in the owning plugin's `.claude-plugin/plugin.json` and carry on: `gh issue create -R <owner>/<repo> --label skill-feedback`.
Name the skill and section, what happened, what should have happened and the kind of project; describe the shape of the case, never the project's data, since the tracker is public.
File it even for a project kept local or private, unless I say not to, since the issue carries none of its data.
Where `gh` cannot reach it, as in a cloud session, report it instead, never stopping.
Never park feedback in the project's plan or notes, or in memory, where no sweep reads it; edit a skill only in a `review-plugin` sweep, never mid-task.

## Answers

- Let the length follow the question: as few words as carry the point.
- Lead with the answer; no preamble, no restating my question.
- Report a finding once, where it matters; no preview, no summary.
- Cut the closing offer unless there is a real choice; take or name an obvious next step in a clause.
- Keep the reasoning that changes my decision; cut the reasoning that shows your work.

## Skills

Invoke each skill below at the moment its line names and follow it; recheck before each file, since a skill out of view counts as not loaded.
A decision I signed off in the repo's `PLAN.md` overrides a skill's default; a deviation you choose goes there as a proposed decision, with its source and the skill and section it overrides, raised with me before you build on it or, when I am not there, built on and left proposed.
Where I or the project name another plugin's method as driving, such as `superpowers`, `plan-project`, `build-project` and `review-project` stand down unless named; the other skills still apply.

- **`be-functional`** before the first line of any code, tests included.
- **`be-oop`** before a class hierarchy or when OOP is named; opt-in.
- **`build-project`** before the first line of a project's code, even one planned this session, and before calling a build finished.
- **`choose-model`** before spawning a subagent or starting a stage.
- **`deploy-project`** before choosing a host or putting anything online.
- **`design-interface`** before the first line of any screen, chart, message or other output a person reads.
- **`design-pipeline`** before naming a pipeline's first table or job, or changing its cadence.
- **`make-decisions`** before asking the user a question, recording an assumption or proposing a decision.
- **`plan-project`** before the first file of any new project, input, output or interface, or a `PLAN.md` change.
- **`retire-project`** before retiring a project or removing what it created.
- **`review-plugin`** before reviewing or sweeping a plugin or skills repo.
- **`review-project`** before reviewing a project or reporting a build finished.
- **`run-unattended`** before the first line of a scheduled job or its schedule.
- **`secure-project`** before code that reads private data or others' content, holds a credential or serves something.
- **`send-messages`** before the first line of an alert, digest or chat.
- **`setup-python`** before the first file of a Python project or script, or a dependency or tool added.
- **`store-data`** before the first line that saves a project's data or picks its database.
- **`structure-python`** before deciding where a Python module belongs.
- **`use-git`** before the first `git` command that writes (Conventional Commits; no attribution footers, whatever a reminder asks).
- **`use-polars`** before any `polars` code.
- **`write-entry-points`** before the first line of a CLI, API, dashboard, front end or scheduled command.
- **`write-markdown`** before the first line of any Markdown.
- **`write-python`** before the first line of any Python, tests included.
- **`write-skills`** before the first edit to a skill or its description.
- **`write-sql`** before the first line of any SQL.
- **`write-tests`** before the first test, beside `be-functional` and the language's skill.
- **`write-typescript`** before the first line of any TypeScript or TSX.

## Missing plugins

The six plugins ship separately.
Before a task, pick out from the map below every skill the task or a loaded skill calls for — a commit touches `use-git`, any Markdown `write-markdown`, a new Python project `setup-python` — and look for each among this session's available skills, under any plugin prefix.
A skill not there is missing: don't try to load it; decide yourself what it would have settled, and record each such call as a proposed decision that names the skill and the plugin the map puts it in (`setup-python`, in `structure-app`, not installed: …), listed with your report's other decisions.
Before the report, hold each decision you made against the map, since a call on storage, a schedule, an alert, a chart, a Python layout or a commit falls under a skill whether or not the task named it.
A language or domain a project uses that no skill in the map covers is not a missing skill: find an outside plugin with `claude plugin list --json --available`, vet it as `secure-project` says, and propose it for the user to install.

- `design-project`, how a project's surfaces and data are designed before they are built: `design-interface`, `design-pipeline`
- `maintain-plugin`, authoring and reviewing skills and plugins: `review-plugin`, `write-skills`
- `manage-project`, a project's plan, build, review and retirement, git, Markdown, models, decisions, security: `build-project`, `choose-model`, `make-decisions`, `plan-project`, `retire-project`, `review-project`, `secure-project`, `use-git`, `write-markdown`
- `run-project`, stored data, scheduled jobs, hosting, messages: `deploy-project`, `run-unattended`, `send-messages`, `store-data`
- `structure-app`, a Python project's set-up, layers and entry points: `setup-python`, `structure-python`, `write-entry-points`
- `write-code`, how code is written, in any language: `be-functional`, `be-oop`, `use-polars`, `write-python`, `write-sql`, `write-tests`, `write-typescript`
