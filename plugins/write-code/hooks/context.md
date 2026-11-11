# Skills from the `write-code` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
Check it again before each file you write, since a long session drifts from it: a skill whose text is no longer in view, or that was loaded under a name this list no longer uses, counts as not loaded.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it — or, with no user present, built on and left proposed for their review (`plan-project`, Plan with no user present); never skip or soften a rule without that line.
A skill named in this list or in another skill may belong to a plugin that is not installed here (`maintain-plugin`, `manage-project`, `write-code`, `structure-app` and `run-project` ship separately): when loading it fails, decide what it would have settled yourself, record each such call as a proposed decision, and tell the user which plugin was missing.

- **`be-functional`** for any code, in any language: the default style (`be-oop` where OOP genuinely fits).
- **`be-oop`** for object-oriented design: classes, inheritance, SOLID, patterns.
- **`use-polars`** when working with `polars`.
- **`write-python`** when writing or editing Python.
- **`write-sql`** when writing SQL or deciding where it belongs: SQL against Polars, where a query lives, the engine's dialect, style, schema changes, testing a documented query.
- **`write-tests`** for writing or editing tests, in any language (`pytest` for Python).
