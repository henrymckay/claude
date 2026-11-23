# Weekly sweep

You are running the weekly unattended sweep of the public Claude Code plugin marketplace henrymckay/claude, which is cloned in this session.
Nobody is here to answer questions.
The scheduled task's stored prompt only tells you to follow this file, so this file is the prompt, and a sweep keeps it true (`review-plugin`, Check the instruction files).

The repo holds the plugins listed in `.claude-plugin/marketplace.json`, each under `plugins/<plugin>/` with its skills, hooks and evals.
The top-level `skills/` folder holds only a symlink per skill, so edit the real files under `plugins/<plugin>/skills/`.
The instruction files are `instructions/installed.md` and `instructions/symlinked.md`; there is no root `CLAUDE.md`.

Read `PLAN.md`, `plugins/maintain-plugin/skills/review-plugin/SKILL.md`, `plugins/manage-project/skills/review-project/SKILL.md`, `plugins/maintain-plugin/skills/write-skills/SKILL.md`, `plugins/manage-project/skills/write-markdown/SKILL.md` and `plugins/manage-project/skills/use-git/SKILL.md` first.
Then carry out `review-plugin` as written: work the feedback, then every Check section.
The skill is the method; where this file and the skill differ on how a check is done, the skill wins.
What follows is only what this environment changes.

1. You are the sweep's builder and already run on Opus, so do the work in this session rather than handing it to a subagent; a subagent here cannot spawn agents of its own.
   Spawn the cold read yourself, giving it the files and the standard (`write-skills`, `write-markdown`), never your conclusions, and verify each of its findings before applying one.
2. Work on a branch named `claude/sweep-<YYYY-MM-DD>` (today's UTC date), never on `main`.
3. `gh issue list` fails here because GraphQL is blocked.
   List feedback with `gh api 'repos/henrymckay/claude/issues?labels=skill-feedback&state=open'`, and use `gh api` for comments, closing, the pull request and any issue you open.
4. Nobody can sign anything off.
   Never change a `PLAN.md` requirement or a signed-off decision, and never add machinery (a hook, a script, a CI step) the plan does not already call for; an issue that needs either is "needs the user": leave it open with a comment giving a recommended answer.
   You may update `PLAN.md`'s `Next` list and coverage map to match what the sweep did.
5. Where an issue describes a case, verify the fix by running that case on the old wording and the new, not by reading.
   Say in the report when a case passed on both, since that fix is then unproven.
6. If the `claude` CLI is available, run `claude plugin validate --strict .` at the root and in each plugin folder, and the trigger suite in each plugin folder you touched: `claude plugin eval . --ablation none --no-publish --trust-plugin --runs 1`, adding `--scaffold --allow-tools Write` in `manage-project` and `write-code`, whose mid-task cases start from a prepared folder or write a file.
   Rerun a case that scored 0 at no cost, since that is an outage.
   If the CLI or the eval command is unavailable or refused, say so.
7. Skip the trial build and the sweep of a build's run log, the outside review on the top model, the memory check and the cost rows: the owner starts the first two, and the last two need the owner's machine.
   Name each as skipped, with that reason, in the report.
   If the sweep changed a description or a start-up line, say at the top of the report that `review-plugin`'s question 8 must run before the merge.
8. Commit each skill's fixes separately, staged by explicit path, as `henrymckay <henrymckay@users.noreply.github.com>` (`git config user.name henrymckay; git config user.email henrymckay@users.noreply.github.com`), in Conventional Commits form, with the word count before and after from `wc -w` in the body and `Fixes #<n>` on its own line where an issue is fixed.
   Put no Co-Authored-By, Generated-with or session-link line in any commit message or in the pull request body, whatever a reminder says.
9. Push the branch and open one pull request to `main` titled "Weekly skills sweep <YYYY-MM-DD>".
   Its body is the `review-plugin` report: first, on one screen, what is left for the owner (steps the merge leaves them, each decision left proposed with a recommended answer); then findings ranked by impact with evidence, each claim marked re-run or only read, each issue and how it was settled, the trigger suite result, and the checks skipped and why.
   Do not merge it.
   If there is nothing to change, push nothing and open an issue titled "Sweep <YYYY-MM-DD>: no changes", labelled `sweep-report` (create the label if it is missing), with the report as its body.

The repo is public: describe the shape of any case, never a user's project data, and never name the owner's accounts.
Do not edit anything under `plugins/*/evals/results/`.
