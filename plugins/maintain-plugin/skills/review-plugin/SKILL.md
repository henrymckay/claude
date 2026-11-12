---
name: review-plugin
effort: high
description: >-
  How to review a Claude Code plugin, a marketplace of several, or a repo
  serving as one, for drift — the checks a skills repo needs on top of
  review-project: its skill feedback first, from GitHub issues or a feedback
  file, each settled as fixed, already covered, won't fix or needs the user
  and each case run before and after the fix, with a trial build's
  transcripts read for skills that never loaded; then every drift check,
  whatever the brief names — word counts of the skills and the top-level
  files against the last sweep, each description against its body,
  overfitted examples and rules Claude follows unprompted, duplicates and
  contradictions, dead cross-references, trigger overlap, every code block
  and library claim re-run, the instruction files, README and PLAN.md judged
  whole and rewritten rather than patched, the manifests, hooks, symlinks
  and trigger suites, and memory; landed as one pull request whose report
  lists each check and the net words. Use after a run of skill edits, when
  skill feedback has piled up, or whenever the user asks to review, audit,
  tidy or sweep skills, a plugin or a Claude repo, theirs or one whose
  source they can read, even if they just say "check the skills for drift",
  "tidy up my skills" or "work through the skill feedback". Layers on
  review-project, which runs the cold read, the fixes and the report, and on
  write-skills and write-markdown, the standard it checks against.
---

# Review the plugin

A review of a Claude Code plugin, a marketplace of several, or a repo serving as one — skills, instruction files, wiring and memory — after edits made one at a time during other work.
It takes whatever plugin source it is pointed at: the checkout it runs in, a path, or a repository to clone.
Where the user can push, it fixes and commits; where they cannot, it stops at the report and offers it as an issue or a pull request from a fork, since another owner's conventions may be deliberate.
It runs `review-project` with the skills as the code under review and adds the checks below, judging against `write-skills` and `write-markdown` rather than restating them.
Three mistakes account for most drift: a description no longer matching the body it introduces, a rule stated in two skills that then contradict, and a rule or example overfitted to the project that prompted it.
**Run every check below in every sweep, whatever the brief names.** A sweep briefed as "settle these issues" that settles them and stops leaves the drift no issue reported, such as a README still describing a folder the plan has removed.

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

Where an issue describes a case, verify the fix by running that case — a throwaway prompt or script — not by reading the new wording, and run it on the old wording first where that is cheap: a case that fails before and passes after shows the fix did the work, and one that already passed shows the rule was covered and went unapplied.
**Read a trial build's transcripts** where they are on the machine, for a skill that should have loaded and never did, and a stage served by the wrong model; cite each finding's file and line, and file it as feedback, since a session that skipped a skill never reports the gap itself.
Several reports against one skill mean its structure is wrong; rework the skill rather than patching each report.
**Promote a decision that recurs.** Where feedback, or a plan the sweep can read, shows one decision made again by precedent from another project, or proposed alike in two, make it the owning skill's default with its reason (`make-decisions`), so the next project finds it in the skill instead of re-deciding it.

## Land it as one pull request

Work on one branch and open one pull request carrying the report as its body, whether the sweep runs as a scheduled task or in a session, so the user reviews every skill change in one place before it reaches an install.
Who merges is the plan's decision; without one, the user does.

## Take an inventory

Count the words in every `SKILL.md` and reference, skipping folders synced in by other tools, and in the README, `CLAUDE.md`, `PLAN.md` and each context file.
Compare each against its neighbours and against the counts the last sweep recorded in its commit messages and report.
A skill that grew while its neighbours held steady is where to look first; a top-level file that grew is a finding in itself, since each fix adds a sentence and nobody restructures the whole.

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
Where they also map each plugin of a marketplace to its skills, so a plugin installed alone can name what it lacks, the map is identical in every copy and matches the plugin folders.
- **Judge the README, `CLAUDE.md`, `PLAN.md` and each context file whole against `write-markdown`**, for length and organisation as well as truth, never only the lines a fix touched.
A file patched sweep after sweep reads as drip-fed even when every line is true; rewrite it whole from what the repo is today rather than adding to it.
- **Hold each always-on file to a word budget**, the plan's or one the sweep sets and records there; an addition to it says in its commit what it removed, and a file over budget is a finding.
`CLAUDE.md` and the context files carry no defaults (see `write-markdown`).
- **The README is true**: it lists every skill as its skill describes itself, and its setup, configuration and feedback sections hold against the repo and the plan; a section describing something a `PLAN.md` decision, proposed or signed off, removes is a finding even while the thing still exists.
- **`PLAN.md`'s Decisions agree with the skills both ways**; a decision a skill contradicts, or a skill default the plan overrides without saying so, is a finding.

## Check the wiring

- **Every manifest validates**: `claude plugin validate` on the marketplace and on each plugin, with every plugin folder listed in `marketplace.json` and every skill in exactly one plugin.
- **Each hook runs**: execute the session-start script and read what it prints; a prompt hook is checked by the case that should trip it.
- **Every symlink resolves**, into `~/.claude` and from a top-level `skills/` folder into the plugins, or is dangling on purpose.
- **`.gitignore` covers what should never be committed**: editor folders, caches, OS files, folders synced in by other tools.
- **No sync-conflict copies** (`name 2.ext` from iCloud and the like) sit in the tree.
- **Each trigger suite passes**, run from every plugin folder the sweep touched: `claude plugin eval . --ablation none --no-publish --trust-plugin`.
`--trust-plugin` stands in for the trust prompt no unattended run can answer, so pass it only for a plugin whose source the sweep has read; a case scoring 0 at no cost with an API or timeout note never reached the model, so rerun it rather than reword its description.
- **The feedback wiring works**: the `skill-feedback` label exists on the plugin's repository and `gh issue list` runs authenticated (`gh api` where GraphQL is blocked).

## Check memory

- **Delete a memory that restates a skill rule.** Two copies drift, and memory loses because it is per-machine.
- **Promote a correction the user keeps repeating** into the skill it belongs to, then delete the memory.

## Adapt review-project

- **Correctness is the claims.** Re-run every code block and library claim as `write-skills` requires, including in skills nobody edited; a release since the last review can remove an API or change a default, making a skill wrong without anything failing.
Read every free-tier limit and price a skill quotes against the vendor's plan page too, and update the date beside it, since tiers move without a release.
- **Hold the sweep on Opus** as `choose-model`'s Hold a stage on its model says, by handing it to a subagent briefed as the sweep's own.
- **Brief the cold read** with `write-skills` and `write-markdown` as the standard, asking for duplicates, contradictions, dead pointers and description gaps; it runs on `sonnet`, as does a gap probe, and only a trigger grader or a hook on `haiku` (see `choose-model`).
- **Commit each skill's fixes separately, with its word count before and after**, taken from `wc` at commit time, not from memory, on every commit that touches a skill; the next inventory reads it, and one skill's fixes are read together, which is why this overrides review-project's commit per fix.
- **Flag in the report every rule cut by the default test, generalised, or left for the user**, so the user can restore or settle one.
- **State the net words across skills and references, and each top-level file's count before and after**; justify any growth, since a sweep that only adds leaves the next reader more to read.
- **List every check in the report as done, with what it found, or skipped, with why** — one line each for the README, `CLAUDE.md` and each context file — so a check left out shows as a gap rather than passing unseen.
