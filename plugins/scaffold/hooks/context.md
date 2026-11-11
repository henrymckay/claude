# Skills from the `scaffold` plugin

These skills encode house conventions and are mandatory, not advisory.
Before starting any task below, invoke the matching skill and follow it; check this list every time, not only when a skill is named.
A skill's default is still a default: a decision the user has signed off in the repo's `PLAN.md` overrides it.
A reason you find yourself is recorded there as a proposed decision, with its source and the skill and section it overrides, and raised with the user before you build on it; never skip or soften a rule without that line.
A skill named in this list or in another skill may belong to a plugin that is not installed here (`meta`, `project`, `code`, `scaffold` and `operate` ship separately): when loading it fails, decide what it would have settled yourself, record each such call as a proposed decision, and tell the user which plugin was missing.

- **`setup-python`** when scaffolding, packaging, or configuring a Python project (layout, `uv`, tooling).
- **`structure-python`** when organising a Python application into layers: hexagonal core, ports/adapters, entry-point drivers.
- **`write-entry-points`** for building an app's entry points: a CLI, API, GUI or scheduled job; the driver shell and composition root.
