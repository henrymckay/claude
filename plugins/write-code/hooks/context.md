# Skills from the `write-code` plugin

Before any task below, invoke the matching skill and follow it; check the list again before each file you write, since a skill no longer in view counts as not loaded.
A decision the user signed off in the repo's `PLAN.md` overrides a skill's default; a deviation you choose goes there as a proposed decision, with its source and the skill and section it overrides, raised with the user before you build on it or, with no user present, built on and left proposed.

- **`be-functional`** for any code, in any language: the default style (`be-oop` where OOP genuinely fits).
- **`be-oop`** for object-oriented design: classes, inheritance, patterns.
- **`use-polars`** when working with `polars`.
- **`write-python`** when writing or editing Python.
- **`write-sql`** when writing SQL or deciding where it belongs.
- **`write-tests`** for writing or editing tests, in any language.

## Missing plugins

The five plugins ship separately.
Before a task, pick out from the map below every skill the task or a loaded skill calls for — a commit touches `use-git`, any Markdown `write-markdown`, a new Python project `setup-python` — and look for each among this session's available skills, under any plugin prefix.
A skill not there is missing: don't try to load it; decide yourself what it would have settled, and record each such call as a proposed decision that names the skill and the plugin the map puts it in (`setup-python`, in `structure-app`, not installed: …), listed with your report's other decisions.

- `maintain-plugin`, authoring and reviewing skills and plugins: `review-plugin`, `write-skills`
- `manage-project`, a project's plan, build and review, git, Markdown, models, decisions, security: `build-project`, `choose-model`, `make-decisions`, `plan-project`, `review-project`, `secure-project`, `use-git`, `write-markdown`
- `run-project`, stored data, scheduled jobs, hosting, messages: `deploy-project`, `run-unattended`, `send-messages`, `store-data`
- `structure-app`, a Python project's set-up, layers and entry points: `setup-python`, `structure-python`, `write-entry-points`
- `write-code`, how code is written, in any language: `be-functional`, `be-oop`, `use-polars`, `write-python`, `write-sql`, `write-tests`
