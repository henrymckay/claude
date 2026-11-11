# Skills from the `maintain-plugin` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
Check it again before each file you write, since a long session drifts from it: a skill whose text is no longer in view, or that was loaded under a name this list no longer uses, counts as not loaded.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it — or, with no user present, built on and left proposed for their review (`plan-project`, Plan with no user present); never skip or soften a rule without that line.

- **`review-plugin`** when reviewing a Claude Code plugin or skills repo: `review-project` plus drift across skills, instructions, README, wiring and memory.
- **`write-skills`** when authoring or editing a skill: its name, description, opening, structure, and the skill/reference split.

## Missing plugins

The five plugins ship separately, so a skill that the task, this list or a loaded skill calls for may sit in one not installed here.
Before a task, check the skills it needs against the map below: one that is not among this session's available skills, under any plugin prefix, is missing — don't try to load it.
Decide yourself what it would have settled, record each such call as a proposed decision, and end your report by naming each missing skill and the plugin that holds it; when none is missing, say nothing of it.

- `maintain-plugin`: `review-plugin`, `write-skills`
- `manage-project`: `build-project`, `choose-model`, `make-decisions`, `plan-project`, `review-project`, `secure-project`, `use-git`, `write-markdown`
- `run-project`: `deploy-project`, `run-unattended`, `send-messages`, `store-data`
- `structure-app`: `setup-python`, `structure-python`, `write-entry-points`
- `write-code`: `be-functional`, `be-oop`, `use-polars`, `write-python`, `write-sql`, `write-tests`
