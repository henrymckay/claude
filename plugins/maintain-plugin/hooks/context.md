# Skills from the `maintain-plugin` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
Check it again before each file you write, since a long session drifts from it: a skill whose text is no longer in view, or that was loaded under a name this list no longer uses, counts as not loaded.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it — or, with no user present, built on and left proposed for their review (`plan-project`, Plan with no user present); never skip or soften a rule without that line.

- **`review-plugin`** when reviewing a Claude Code plugin or skills repo: `review-project` plus drift across skills, instructions, README, wiring and memory.
- **`write-skills`** when authoring or editing a skill: its name, description, opening, structure, and the skill/reference split.

## Missing plugins

The five plugins ship separately.
Before a task, pick out from the map below every skill the task or a loaded skill calls for — a commit touches `use-git`, any Markdown `write-markdown`, a new Python project `setup-python` — and look for each among this session's available skills, under any plugin prefix.
A skill not there is missing: don't try to load it; decide yourself what it would have settled, and record each such call as a proposed decision that names the skill and the plugin the map puts it in (`setup-python`, in `structure-app`, not installed: …), listed with your report's other decisions.

- `maintain-plugin`, authoring and reviewing skills and plugins: `review-plugin`, `write-skills`
- `manage-project`, a project's plan, build and review, git, Markdown, models, decisions, security: `build-project`, `choose-model`, `make-decisions`, `plan-project`, `review-project`, `secure-project`, `use-git`, `write-markdown`
- `run-project`, stored data, scheduled jobs, hosting, messages: `deploy-project`, `run-unattended`, `send-messages`, `store-data`
- `structure-app`, a Python project's set-up, layers and entry points: `setup-python`, `structure-python`, `write-entry-points`
- `write-code`, how code is written, in any language: `be-functional`, `be-oop`, `use-polars`, `write-python`, `write-sql`, `write-tests`
