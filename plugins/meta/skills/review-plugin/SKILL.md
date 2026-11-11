---
name: review-plugin
model: opus
effort: high
description: >-
  How to review a Claude Code plugin, a marketplace of several, or a repo
  serving as one, for drift — the checks a skills repo needs on top of
  review-project: working through its skill feedback, GitHub issues or a
  feedback file (fixed, already covered, won't fix, or needs the user), an
  inventory of word counts, each description against its body, bloat and
  overfitted examples, rules duplicated or contradicted across skills and
  across plugins, dead cross-references, trigger overlap, every code block and
  library claim re-run, the always-on instructions, PLAN.md and the README
  against the skills, the manifests, hooks, symlinks and feedback wiring, and
  auto-memory; run in a session or unattended as a scheduled task that opens
  one pull request, each skill's fixes committed with word counts and every
  cut rule flagged; on a plugin you cannot push to, the same review ends in a
  report, an issue or a pull request from a fork. Use after a run of skill
  edits, when skill feedback has piled up, or whenever the user asks to
  review, audit, tidy or sweep skills, a plugin or a Claude repo, theirs or
  one whose source they can read, even if they just say "check the skills for
  drift", "tidy up my skills" or "work through the skill feedback". Layers on
  review-project, which runs the cold read, the fixes and the report, and on
  write-skills and write-markdown, the standard it checks against.
---

# Review the plugin

A review of a Claude Code plugin, a marketplace of several, or a repo serving as one — skills, instruction files, wiring and memory — after edits made one at a time during other work.
It takes whatever plugin source it is pointed at: the checkout it runs in, a path, or a repository to clone.
Where the user can push, it fixes and commits; where they cannot, it stops at the report and offers it as an issue or a pull request from a fork, since another owner's conventions may be deliberate.
It runs `review-project` with the skills as the code under review and adds the checks below, judging against `write-skills` and `write-markdown` rather than restating them.
Three mistakes account for most drift: a description no longer matching the body it introduces, a rule stated in two skills that then contradict, and a rule or example overfitted to the project that prompted it.

- **Wrong** — the issue says a skill steered a build wrong; the sweep rewords the rule, reads it back, and closes the issue.
- **Right** — the sweep reruns the build step the issue describes against the new wording, and closes the issue only when that run comes out right.

## Work the feedback

Start from the open reports, since they record what a real run got wrong and the checks below only find what reading can: `gh issue list -R <owner>/<repo> --label skill-feedback`, the repository being the `repository` in the plugin's `.claude-plugin/plugin.json`.
Read `~/.claude/skill-feedback.md` as well where the machine records feedback to a file; settle each entry the same way and delete it once settled.
Verify each against the files, then settle it one of four ways:

- **Fixed** — in the skill that owns the rule, generalised as `write-skills` says, with `Fixes #<n>` in the commit message.
- **Already covered** — the rule exists but went unapplied, so sharpen its wording, its placement or the description that should have loaded it.
- **Won't fix** — no skill should cover it, with the reason in the closing comment.
- **Needs the user** — it would change a `PLAN.md` decision or settle policy; leave it open with a recommended answer, and never decide it in an unattended run.

Where an issue describes a case, verify the fix by running that case — a throwaway prompt or script — not by reading the new wording.
Several reports against one skill mean its structure is wrong; rework the skill rather than patching each report.

## Run unattended

As a scheduled task, work on a branch and open one pull request carrying the report as its body, so the user reviews the week's changes in one place; in a session, commit as the plan decides.

## Take an inventory

Count the words in every `SKILL.md` and reference, skipping folders synced in by other tools.
Compare each against its neighbours and against the counts the last review recorded in its commit messages; a file that grew while its neighbours held steady is where to look first.

## Check each skill

- **Description against body, both ways.** List what the description promises and what the body covers; drop promises the body doesn't keep and add what it grew to cover.
- **Overfitting.** Find names, data and edge cases from one project — its domain terms, a single incident turned into a rule — and restate them in a domain any reader knows, or cut them.
- **The default test** (see `write-skills`): for each rule, ask whether Claude would do it unprompted, and cut it if so.
Word counts miss this bloat; it reads as reasonable advice.

## Check across skills

- **Duplicates.** Grep for each load-bearing rule's key words across all skills; keep it where it belongs and point there from the rest.
- **Contradictions.** Read neighbouring skills side by side where they meet — a style skill and its counterpart, a skill and the one it layers on.
- **Plugin boundaries.** A skill that points at one in another plugin must still read correctly with that plugin absent, and a toolchain's commands stay in the skill that owns the toolchain, named elsewhere only as that skill's example.
- **Dead cross-references.** Every section or skill named in prose must still say what the pointer claims.
- **Trigger overlap.** Write a handful of prompts the user typically gives, plus a few casual phrasings, and say which descriptions claim each.
Two claiming one prompt need a sharper boundary; none claiming it needs a wider description.

## Check the instruction files

- **The always-on skill list matches the skills both ways**, and each entry agrees with that skill's description: the list is each plugin's `hooks/context.md`, printed at session start, and the owner's `CLAUDE.md` where the skills are symlinked instead of installed; where both exist they carry the same line for a skill.
- **`CLAUDE.md` carries no defaults** (see `write-markdown`).
- **The README lists every skill**, each described as its skill describes itself, and its other sections — setup, configuration, feedback, evaluation — are still true.
- **`PLAN.md`'s Decisions agree with the skills both ways**; a decision a skill contradicts, or a skill default the plan overrides without saying so, is a finding.

## Check the wiring

- **Every manifest validates**: `claude plugin validate` on the marketplace and on each plugin, with every plugin folder listed in `marketplace.json` and every skill in exactly one plugin.
- **Each hook runs**: execute the session-start script and read what it prints; a prompt hook is checked by the case that should trip it.
- **Every symlink resolves**, into `~/.claude` and from a top-level `skills/` folder into the plugins, or is dangling on purpose.
- **`.gitignore` covers what should never be committed**: editor folders, caches, OS files, folders synced in by other tools.
- **No sync-conflict copies** (`name 2.ext` from iCloud and the like) sit in the tree.
- **The feedback wiring works**: the `skill-feedback` label exists on the plugin's repository and `gh issue list` runs authenticated (`gh api` where GraphQL is blocked).

## Check memory

- **Delete a memory that restates a skill rule.** Two copies drift, and memory loses because it is per-machine.
- **Promote a correction the user keeps repeating** into the skill it belongs to, then delete the memory.

## Adapt review-project

- **Correctness is the claims.** Re-run every code block and library claim as `write-skills` requires, including in skills nobody edited; a release since the last review can remove an API or change a default, making a skill wrong without anything failing.
Read every free-tier limit and price a skill quotes against the vendor's plan page too, and update the date beside it, since tiers move without a release.
- **Brief the cold read** with `write-skills` and `write-markdown` as the standard, asking for duplicates, contradictions, dead pointers and description gaps; it runs on `sonnet`, as does a gap probe, and only a trigger grader or a hook on `haiku` (see `choose-model`).
- **Commit each skill's fixes separately, with its word count before and after**, taken from `wc` at commit time, not from memory, on every commit that touches a skill; the next inventory reads it, and one skill's fixes are read together, which is why this overrides review-project's commit per fix.
- **Flag in the report every rule cut by the default test, generalised, or left for the user**, so the user can restore or settle one.
