---
name: review-plugin
description: >-
  How to review your own Claude Code plugin, or a repo serving as one, for
  drift — the checks a skills repo needs on top of review-project: each
  description against its body, bloat and overfitted examples, rules
  duplicated or contradicted across skills, trigger overlap, CLAUDE.md and the
  README against the skills, the symlinks wiring it into ~/.claude, and
  auto-memory. Use after a run of skill edits, or whenever the user asks to
  review, audit, tidy or sweep their skills, plugin or Claude repo, even if
  they just say "check the skills for drift" or "tidy up my skills". Not for a
  third-party plugin. Layers on review-project, which runs the cold read, the
  fixes and the report, and on write-skills and write-markdown, the standard it
  checks against.
---

# Review the plugin

A review of your own Claude Code plugin, or a repo serving as one — skills, instruction files, wiring and memory — after edits made one at a time during other work.
It runs `review-project` with the skills as the code under review and adds the checks below, judging against `write-skills` and `write-markdown` rather than restating them.
Three mistakes account for most drift: a description no longer matching the body it introduces, a rule stated in two skills that then contradict, and a rule or example overfitted to the project that prompted it.

**In an existing project, ask first.** Where a repo already has its own conventions for its skills, check with the user whether to review against them or against `write-skills`, and prefer `write-skills` unless they choose to match.

## Take an inventory

Count the words in every `SKILL.md` and reference, skipping folders synced in by other tools.
Compare each against its neighbours and against the counts the last review recorded in its commit messages; a file that grew while its neighbours held steady is where to look first.

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
- **The README lists every skill**, each described as its skill describes itself.

## Check the wiring

- **Every symlink into `~/.claude` resolves**, or is dangling on purpose.
- **`.gitignore` covers what should never be committed**: editor folders, caches, OS files, folders synced in by other tools.
- **No sync-conflict copies** (`name 2.ext` from iCloud and the like) sit in the tree.

## Check memory

- **Delete a memory that restates a skill rule.** Two copies drift, and memory loses because it is per-machine.
- **Promote a correction the user keeps repeating** into the skill it belongs to, then delete the memory.

## Adapt review-project

- **Correctness is the claims.** Re-run every code block and library claim as `write-skills` requires, including in skills nobody edited; a release since the last review can remove an API or change a default, making a skill wrong without anything failing.
- **Brief the cold read** with `write-skills` and `write-markdown` as the standard, asking for duplicates, contradictions, dead pointers and description gaps.
- **Commit each skill's fixes separately, with its word count before and after**, taken from `wc` at commit time, not from memory; the next inventory reads it.
- **Flag in the report every rule cut by the default test**, so the user can restore one.
