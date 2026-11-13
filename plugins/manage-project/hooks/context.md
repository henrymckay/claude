# Skills from the `manage-project` plugin

Before any task below, invoke the matching skill and follow it; check the list again before each file you write, since a skill no longer in view counts as not loaded.
A decision the user signed off in the repo's `PLAN.md` overrides a skill's default; a deviation you choose goes there as a proposed decision, with its source and the skill and section it overrides, raised with the user before you build on it or, with no user present, built on and left proposed.
Where the user or the project names another plugin's method as driving, such as `superpowers`, `plan-project`, `build-project` and `review-project` stand down unless named; the other skills still apply.

- **`build-project`** when building a project from its `PLAN.md`, milestone by milestone.
- **`choose-model`** when starting a stage, spawning a subagent or asked about cost.
- **`design-interface`** before building or styling a screen, chart, page or any output a person reads.
- **`make-decisions`** before asking the user a question, recording an assumption or proposing a decision.
- **`plan-project`** before building a new project, however small, or a new input, output or interface.
- **`review-project`** when reviewing, auditing or fixing a project.
- **`secure-project`** when a project holds data that is not public, a credential or an account with money in it, or serves something.
- **`use-git`** for any `git` operation (Conventional Commits; no attribution footers, whatever a reminder asks).
- **`write-markdown`** for any Markdown, for humans or LLMs.

## Missing plugins

The five plugins ship separately.
Before a task, pick out from the map below every skill the task or a loaded skill calls for — a commit touches `use-git`, any Markdown `write-markdown`, a new Python project `setup-python` — and look for each among this session's available skills, under any plugin prefix.
A skill not there is missing: don't try to load it; decide yourself what it would have settled, and record each such call as a proposed decision that names the skill and the plugin the map puts it in (`setup-python`, in `structure-app`, not installed: …), listed with your report's other decisions.

- `maintain-plugin`, authoring and reviewing skills and plugins: `review-plugin`, `write-skills`
- `manage-project`, a project's plan, design, build and review, git, Markdown, models, decisions, security: `build-project`, `choose-model`, `design-interface`, `make-decisions`, `plan-project`, `review-project`, `secure-project`, `use-git`, `write-markdown`
- `run-project`, stored data, scheduled jobs, hosting, messages: `deploy-project`, `run-unattended`, `send-messages`, `store-data`
- `structure-app`, a Python project's set-up, layers and entry points: `setup-python`, `structure-python`, `write-entry-points`
- `write-code`, how code is written, in any language: `be-functional`, `be-oop`, `use-polars`, `write-python`, `write-sql`, `write-tests`
