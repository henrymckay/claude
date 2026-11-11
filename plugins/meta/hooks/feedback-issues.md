
# Skill feedback

When a skill from any plugin steered you wrong, said nothing where it should have, or contradicted another skill, or the user corrected you on something a skill should cover, file an issue and carry on: `gh issue create -R <owner>/<repo> --label skill-feedback`.
The repository is the one the user's `CLAUDE.md` names for skill feedback, else the `repository` in the owning plugin's `.claude-plugin/plugin.json`, two folders above the skill's own.
Name the skill and section, what happened, what should have happened, and the kind of project.
Describe the shape of the case, never the project's data: the tracker may be public.
Record skill corrections there, not in memory, and edit a skill only in a `review-plugin` sweep, never mid-task.
