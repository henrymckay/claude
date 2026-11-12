
# Skill feedback

When a skill from any plugin steered you wrong, said nothing where it should have or contradicted another, or the user corrected you on something a skill should cover, file an issue and carry on: `gh issue create -R <owner>/<repo> --label skill-feedback`.
The repository is the one the user's `CLAUDE.md` names for skill feedback, else the `repository` in the owning plugin's `.claude-plugin/plugin.json`, two folders above the skill's own.
Name the skill and section, what happened, what should have happened and the kind of project; describe the shape of the case, never the project's data, since the tracker may be public.
File it even for a project kept local or private, unless the user says not to: that instruction governs the project's repository, and the issue carries none of its data.
Never park feedback in the project's plan or notes, or in memory, where no sweep reads it; edit a skill only in a `review-plugin` sweep, never mid-task.
