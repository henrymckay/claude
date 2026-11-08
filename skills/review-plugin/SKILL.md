---
name: review-plugin
description: >-
  How to sweep your own Claude Code plugin, or a repo serving as one, for
  drift — its skills and references, CLAUDE.md, README, the symlinks wiring it
  into ~/.claude, and auto-memory — checking each description against its
  body, cutting bloat and overfitted examples, finding rules duplicated or
  contradicted across skills, getting an unanchored cold read, and testing
  every code and library claim. Use after a run of skill edits, or whenever
  the user asks to review, audit, tidy or sweep their skills, plugin or Claude
  repo, even if they just say "check the skills for drift" or "tidy up my
  skills". Not for reviewing an application's code or a third-party plugin.
  Layers on write-skills and write-markdown, the standard it checks against;
  use-git commits the fixes.
---

# Review the plugin

A sweep of your own Claude Code plugin, or a repo serving as one — skills, instruction files, wiring and memory — after edits made one at a time during other work.
It checks against `write-skills` and `write-markdown` rather than restating them, and commits through `use-git`.
Three mistakes account for most drift: a description no longer matching the body it introduces, a rule stated in two skills that then contradict, and a rule or example overfitted to the project that prompted it.

**In an existing project, ask first.** Where a repo already has its own conventions for its skills, check with the user whether to review against them or against `write-skills`, and prefer `write-skills` unless they choose to match.

## Take an inventory

Count the words in every `SKILL.md` and reference, skipping folders synced in by other tools.
Compare each against its neighbours and against the counts the last sweep recorded in its commit messages; a file that grew while its neighbours held steady is where to look first.

## Check each skill

- **Description against body, both ways.** List what the description promises and what the body covers; drop promises the body doesn't keep and add what it grew to cover.
- **Overfitting.** Find names, data and edge cases from one project — its domain terms, a single incident turned into a rule — and restate them in a domain any reader knows, or cut them.
- **The default test.** For each rule, ask whether Claude would do it unprompted, and cut it if so.
Word counts miss this bloat; it reads as reasonable advice.
Keep corrections, house picks and non-obvious traps.

## Check across skills

- **Duplicates.** Grep for each load-bearing rule's key words across all skills; keep it where it belongs and point there from the rest.
- **Contradictions.** Read neighbouring skills side by side where they meet — a style skill and its counterpart, a skill and the one it layers on.
- **Dead cross-references.** Every section or skill named in prose must still say what the pointer claims.
- **Trigger overlap.** Write a handful of prompts the user typically gives, plus a few casual phrasings, and say which descriptions claim each.
Two claiming one prompt need a sharper boundary; none claiming it needs a wider description.

## Check the instruction files

- **`CLAUDE.md`'s skill list matches `skills/` both ways**, and each entry agrees with that skill's description.
- **`CLAUDE.md` carries no defaults** (see `write-markdown`).
- **The README still describes the repo** — every skill listed, the setup steps still working.

## Check the wiring

- **Every symlink into `~/.claude` resolves.** A dangling one fails silently.
- **`.gitignore` covers what should never be committed**: editor folders, caches, OS files, folders synced in by other tools.
- **No sync-conflict copies** (`name 2.ext` from iCloud and the like) sit in the tree.

## Check memory

- **Delete a memory that restates a skill rule.** Two copies drift, and memory loses because it is per-machine.
- **Promote a correction the user keeps repeating** into the skill it belongs to, then delete the memory.

## Get a cold read

After your own pass, give a fresh agent the files and the standard (`write-skills`, `write-markdown`), never your conclusions, and ask for duplicates, contradictions, dead pointers and description gaps.
An agent handed your findings tends to confirm them; one reading cold finds what your pass was blind to.
Verify each finding against the files before applying it — an agent's mistakes read as confidently as its catches.

## Test the claims

Re-run every code block and library claim as `write-skills` requires, including in skills nobody edited.
A release since the last sweep can remove an API or change a default, making a skill wrong without anything failing.

## Commit and report

- **Commit each skill's fixes separately**, so one can be reverted alone.
- **Put the word count before and after in the commit message**, taken from `wc` at commit time, not from memory; the next sweep's inventory reads it.
- **Report what changed in behaviour**, not every edit, and flag the judgement calls — a rule cut by the default test, a deeper cut than asked — so the user can restore one.
