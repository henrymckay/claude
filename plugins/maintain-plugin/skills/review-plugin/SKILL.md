---
name: review-plugin
effort: high
description: >-
  How to review a Claude Code plugin, marketplace or skills repo for drift —
  skill feedback, every check (counts, descriptions, duplicates, claims,
  instruction files, hooks, trigger suites, records), the coverage map, trial
  builds, how a sweep runs, an outside review, one pull request. Load it
  before the first check of a review, audit or sweep of a plugin or skills
  repo — even if the user just says "check the skills for drift" or "work
  through the skill feedback".
---

# Review the plugin

A review of a Claude Code plugin, a marketplace of several, or a repo serving as one — skills, instruction files, wiring and memory — after edits made one at a time during other work.
It takes whatever plugin source it is pointed at: the checkout it runs in, a path, or a repository to clone.
Where the user can push, it fixes and commits; where they cannot, it stops at the report and offers it as an issue or a pull request from a fork, since another owner's conventions may be deliberate.
It runs `review-project` with the skills as the code under review and adds the checks below, judging against `write-skills` and `write-markdown` rather than restating them.
Anthropic's `plugin-dev` plugin, if installed, checks hooks, manifests, agents and commands more deeply than Check the wiring; without it, `claude plugin validate --strict` and running each hook are the floor.
Three mistakes account for most drift: a description no longer matching the body it introduces, a rule stated in two skills that then contradict, and a rule or example overfitted to the project that prompted it.
**Run every check in the Check sections below in every sweep, whatever the brief names**; a trial build is a separate, paid event the owner starts. A sweep briefed as "settle these issues" that settles them and stops leaves the drift no issue reported, such as a README still describing a folder the plan has removed.

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
Several reports against one skill mean its structure is wrong; rework the skill rather than patching each report.
**Promote a decision that recurs.** Where feedback, or a plan the sweep can read, shows one decision made again by precedent from another project, or proposed alike in two, make it the owning skill's default with its reason (`make-decisions`), so the next project finds it in the skill instead of re-deciding it.

## Run a trial build

A trial build tests the plugins on a real project, so its planning is under test as much as its code.

- **The session under test plans and builds it; the coordinating session does neither**, even when "new project" fires `plan-project`: it writes a brief in the user's words that names no technology the skills should choose, starts a fresh session with only the plugins, and relays the user's own answers, never its own.
Run with nobody watching, it is a cloud session on the trial's repository alone, as `build-project`'s `references/unattended.md` sets up, so it holds none of the owner's credentials or other projects, and none of their connectors once each is removed from the task and the template's deny is in place; a local headless run sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, the backstop `choose-model`'s Hold a stage on its model names, and says in its report what it ran with.
- **Total its cost with `choose-model`'s script** from its transcripts, whether or not the build kept `costs.csv`, so every trial build is priced the same way.
- **Sweep what it leaves**, and a real build's wherever its run log can be read: its skill feedback, and from its transcript or run log a table of the skills the main session invoked against the skills the work called for (a language's skill for each language written, `write-tests` for each test, `build-project` for the build) and of any stage served by the wrong model; cite each miss's file and line and file it as feedback, since a session that skipped a skill never reports the gap itself, and every one-line trigger case passed while two builds missed skills mid-task.
- **Fill in the coverage map's evidence** where the marketplace's plan keeps one (Check the coverage map): each cell the build exercised gets the build as its evidence, and each it found wanting the issue it filed.

## Check the coverage map

Where the plan of the marketplace under review keeps a coverage map — a project's stages against the qualities its requirements name, each cell naming what delivers it and what proved it — re-read it whole in every sweep, since gaps otherwise surface only when someone asks again what is missing:

- **Each cell still true**: the skill or hook it names exists and still does what the cell says, and an issue it cites is still open, or the cell moves to what closed it.
- **Three grades, each citing a dated run**: *seen once* — one real run exercised it and passed; *repeated* — runs on two kinds of project passed; *failing* — its last recorded result failed.
A cell keeps a passing grade only while the last recorded result for it, in the cited project's own `verification.csv` or this repo's, is a pass — for a project built before the records, the dated milestone note, until its next run replaces it — so check the map against those records, never against the plan's own text; a cell whose evidence is only a skill's text, a unit test or a probe is *designed*, not graded, and the map's table of project kinds calls a kind built only once a build has completed it.
- **A default resting on one kind of project is provisional**: a skill default or decision drawn from a single project says so until a second kind of project confirms it, so the next project tests it rather than inherits it.
- **Every open skill-feedback issue sits in a cell**, and every empty cell has an issue or a reason it is not wanted yet; a sweep that closes an issue moves its cell to the fix and the run that showed it.

## Run the sweep

How a sweep is carried out, so another session or another user of the plugin runs it the same way and the report shows each step happened:

- **One builder, isolated**: a single agent on `choose-model`'s rung for skill edits, in its own git worktree on a branch from `main`, never in the main checkout, in the background so the coordinating session stays free to relay; it works the feedback and runs every check in this skill.
- **One checker, who re-runs rather than reads**: before the merge, the coordinating session re-runs itself every test suite, `claude plugin validate --strict`, the trigger cases the sweep changed and each artefact the report cites (a branch, a CI run, a transcript), and takes from the builder's report only what it read (a docs page, a count); the report marks each claim as re-run or reported, and the merge note names what the checker re-ran.
- **Findings from an automated review** (a commit security review on push, say) go back to the builder one by one, each fixed with a test that fails first or rebutted with a test showing the case already refused, weighed by layer: a way past a boundary a skill relies on (the vendor's isolation as a skill sets it up, a credential's scope) blocks the merge, and a weakness in a second layer is fixed in the sweep where that is cheap and filed where it is not.
**Before adding to security machinery the plugins carry, ask whether the vendor's own control covers it**, and prefer configuring that: three sweeps of a home-made launcher and guard drew a finding per fix round, and asked about 531 of 2,841 ordinary calls to raise 26 worth asking (issue 173), until both were removed for Claude Code's cloud sessions and permission controls.
- **The outside review** (below) runs once the builder has finished and before the merge.
- **The cost is recorded**: the sweep's rows in the repo's `costs.csv`, per model, totalled with `choose-model`'s script from the transcripts and held against the plan's per-sweep budget; a sweep over budget says why.
- **The owner is asked only for what is theirs, on one screen at the top of the report**: the steps the merge leaves them (Land it as one pull request), each decision left proposed with its recommended answer, and the release tag, with the plan's count of what is still unsigned brought up to date; the detail follows below it, for whoever wants it.

## Review it from outside

**End every sweep with one targeted review by a fresh agent on the best available model at its highest effort (`choose-model`), read-only, given the diff and the plan but none of the builder's reasoning or report**, since a builder checked by its own model and effort finds what it already looked for: twelve sweeps passed their own checks while an outside review found unproven claims graded proven, a boundary tested less than its second layer and a plan too long to act on.
Brief it with the questions below, asking for no tidy-ups, rather than having it load this skill, whose frontmatter effort would hold it at `high` for the rest of its turn (`choose-model`, Set the model from inside Claude).
It has two parts:

1. **The plan and the trajectory, always**, by the same questions every sweep, so one sweep's answers can be compared with the last:
   1. Do the requirements still follow from the aim, and can each still fail observably?
   2. Is every cell the coverage map grades as passing still backed by its last recorded result? Check the map against the records of the projects it cites, not against the plan's own text.
   3. Is the `Next` list the best next step, or is more valuable evidence being deferred?
   4. Which decisions now contradict, repeat or no longer hold; which defaults rest on one project?
   5. Can a fresh session act on the plan at its current size?
   6. What is the weakest part of the whole approach to a sceptical outsider, and what would they do instead?
   7. What did the last review propose, and was it done, declined with a reason, or dropped silently?
   8. Given the recent builds' tables of skills invoked against skills called for (Run a trial build) and every description and start-up line, which triggers are likeliest to miss or misfire, and what prompt would show each?
2. **The sweep's riskiest change, chosen per sweep**: code that runs, a boundary, or the skill a build depends on most, reviewed from the diff.

**The reviewer judges the wording; runs on the building model judge whether a skill fires**, since a skill that fires for the best model can stay silent for the model that builds.
So each prompt question 8 proposes becomes a trigger case (Check the wiring), with a scaffold where the miss is mid-task, run on the building model against the old wording and the new, and a predicted miss counts only once a run shows it.
Question 8 also runs alone, before the merge, in any sweep that changes a description or a start-up line.

- **The report ranks findings by how much each should change what is done next**, marks each verified (re-run) or inferred (read), and ends with proposals the owner accepts or declines.
- **A finding that blocks the merge is fixed in the sweep; the rest are filed** as issues, so the next sweep starts from them.
- **It runs with no spend cap and records its cost against the plan's budget for it afterwards**, a review over budget reported with the reason rather than cut short, and is skipped only with the reason in the report; a full review of every skill stays a separate, rarer event.

## Land it as one pull request

Work on one branch and open one pull request carrying the report as its body, whether the sweep runs as a scheduled task or in a session, so the user reviews every skill change in one place before it reaches an install.
Who merges is the plan's decision; without one, the user does.

**Name in the report and the pull request every step the merge leaves the user**, since each changes their configuration and is theirs to run: a plugin the sweep adds, or one a skill moves into, owes `claude plugin install <plugin>@<marketplace>`, because a marketplace entry is not an installation and the moved skill otherwise vanishes from every session while the skill list still calls it mandatory; a changed hook or instruction file owes a restart, and a renamed instruction file a new link.
After the merge, compare the plugins in `marketplace.json` with `claude plugin list` and name any not installed.

## Take an inventory

Count the words in every `SKILL.md` and reference, skipping folders synced in by other tools, and in the README, each instruction file, `PLAN.md` and each context file.
Measure each description in characters against `write-skills`' limit, and each plugin's always-on cost with `claude plugin details <plugin>@<marketplace>`; the total across the marketplace is what competes for the listing's budget, so a sweep that lets it grow says why.
Compare each against its neighbours and against the counts the last sweep recorded in its commit messages and report.
A skill that grew while its neighbours held steady is where to look first; a top-level file that grew is a finding in itself, since each fix adds a sentence and nobody restructures the whole.

## Check each skill

- **Description against body, both ways**, and within its character limit (`write-skills`, Write the description).
- **Overfitting**: names, data and edge cases from one project, restated in a domain any reader knows or cut (`write-skills`, Keep examples general).
- **The default test**: each rule Claude would follow unprompted is cut (`write-skills`, Cut what Claude does unprompted); word counts miss this bloat.

## Check across skills

- **Duplicates.** Grep for each load-bearing rule's key words across all skills; keep it where it belongs and point there from the rest.
- **Contradictions.** Read neighbouring skills side by side where they meet — a style skill and its counterpart, a skill and the one it layers on.
- **Plugin boundaries.** A skill that points at one in another plugin must still read correctly with that plugin absent, and a toolchain's commands stay in the skill that owns the toolchain, named elsewhere only as that skill's example.
- **Dead cross-references.** Every section or skill named in prose must still say what the pointer claims.
- **Trigger overlap.** Write a handful of prompts the user typically gives, plus a few casual phrasings, and say which descriptions claim each.
Two claiming one prompt need a sharper boundary; none claiming it needs a wider description.

## Check the instruction files

- **The always-on skill list matches the skills both ways**, and each entry agrees with that skill's description: the list is each plugin's `hooks/context.md`, printed into every session and subagent, and the owner's instruction file where the skills are symlinked instead of installed; where both exist they carry the same line for a skill.
Where every plugin of a marketplace carries the same rules, such as a map of each plugin to its skills so a plugin installed alone can name what it lacks, they sit in one file copied byte for byte into each plugin and printed once however many are installed: `cmp` the copies, and check the map against the plugin folders and the symlink wiring's instruction file.
- **Each instruction file holds what its wiring needs and no more**: one for a machine with the plugins installed carries only the owner's own rules, since anything the plugins print it would add a second copy of; one for the symlink wiring carries the owner's rules and everything the plugins print, and the two agree on the owner's rules.
- **Judge the README, each instruction file, `PLAN.md` and each context file whole against `write-markdown`**, for length and organisation as well as truth, never only the lines a fix touched.
A file patched sweep after sweep reads as drip-fed even when every line is true; rewrite it whole from what the repo is today rather than adding to it.
- **Hold each always-on file to a word budget**, the plan's or one the sweep sets and records there, kept as `write-markdown` says; a file over budget is a finding.
The instruction files and the context files carry no defaults (see `write-markdown`).
- **The README is true**: it lists every skill as its skill describes itself, and its setup, configuration and feedback sections hold against the repo and the plan; a section describing something a `PLAN.md` decision, proposed or signed off, removes is a finding even while the thing still exists.
- **A routine's prompt the repo holds is true** against the repo, the plan and this skill, read as the README is, since a scheduled sweep's prompt kept only in the task went stale unseen.
- **`PLAN.md`'s Decisions agree with the skills both ways**; a decision a skill contradicts, or a skill default the plan overrides without saying so, is a finding.

## Check the wiring

- **Every manifest validates**: `claude plugin validate --strict` on the marketplace and on each plugin, which fails on warnings the runtime tolerates (a missing author, an unknown field), with every plugin folder listed in `marketplace.json` and every skill in exactly one plugin.
- **The built-in audits, read as leads**: `/doctor prompt-audit <plugin folder>`, in a session, for outdated or conflicting instructions across skills and instruction files, and, on a machine that has used the plugins, `/skill-doctor` (`claude -p "/skill-doctor"` prints it), whose never-invoked skills are a description that does not fire or a skill nobody needs.
Verify each finding against the files before acting, as for the cold read.
- **Each hook runs**: pipe the session-start script a `SessionStart` and a `SubagentStart` input (`{"session_id":"x","hook_event_name":"SubagentStart","agent_id":"a"}`) and read what it prints, the second as valid JSON whose `additionalContext` stays under the 10,000 characters past which Claude Code hands over a file path instead; a prompt hook is checked by the case that should trip it.
- **The rules reach a subagent**, since a subagent loads `CLAUDE.md` but no session-start output, and every stage runs in one: in an empty folder, run `claude -p` with only the plugins (`--setting-sources project,local` and a `--plugin-dir` each, so neither the user's `CLAUDE.md` nor an installed copy masks the result), have it spawn a general-purpose subagent in the foreground that lists the headings it can see, and confirm each count in both transcripts' hook records: every plugin's list and the shared rules once in the session and once in the subagent, with one plugin and with all.
- **Every symlink resolves**, into `~/.claude` and from a top-level `skills/` folder into the plugins, or is dangling on purpose.
- **`.gitignore` covers what should never be committed**: editor folders, caches, OS files, folders synced in by other tools.
- **No sync-conflict copies** (`name 2.ext` from iCloud and the like) sit in the tree.
- **Each trigger suite passes**, run from every plugin folder the sweep touched: `claude plugin eval . --ablation none --no-publish --trust-plugin`, adding `--scaffold` where a case names a `scaffold_script`, which otherwise runs in an empty folder, and `--allow-tools Write` where a case writes a file.
Each skill has a case that should fire it; a skill with a near neighbour that could claim its prompts also gets one that should not, a `tool_used` grader on `Skill` with `min: 0` and `max: 0`, added only where the two are likeliest to be confused, since every case is a paid session.
A case whose skill hands its work to a subagent lists `Agent` under `disallowed_tools` in its `prompt.md`, since `allowed_tools` does not withhold it and the subagent runs the whole stage after the `Skill` call has already passed, at many times the cost and up to the cap; one whose skill works at length inline raises `timeout_seconds` above the 300-second default instead.
The no-plugin arm (`--ablation with-without`) shows nothing for a trigger case, which cannot fire a skill that is not installed; it earns its cost only for a case that grades behaviour.
`--trust-plugin` stands in for the trust prompt no unattended run can answer, so pass it only for a plugin whose source the sweep has read; a case scoring 0 at no cost with an API or timeout note never reached the model, so rerun it rather than reword its description.
- **The feedback wiring works**: the `skill-feedback` label exists on the plugin's repository and `gh issue list` runs authenticated (`gh api` where GraphQL is blocked).

## Check memory

- **Delete a memory that restates a skill rule.** Two copies drift, and memory loses because it is per-machine.
- **Promote a correction the user keeps repeating** into the skill it belongs to, then delete the memory.

## Adapt review-project

- **Correctness is the claims.** Re-run every code block and library claim as `write-skills` requires, including in skills nobody edited; a release since the last review can remove an API or change a default, making a skill wrong without anything failing.
Read every free-tier limit and price a skill quotes against the vendor's plan page too, and update the date beside it, since tiers move without a release.
- **Hold the sweep on Opus** as `choose-model`'s Hold a stage on its model says, by handing it to a subagent briefed as the sweep's own.
- **Brief the cold read** with `write-skills` and `write-markdown` as the standard, asking for duplicates, contradictions, dead pointers and description gaps, spawned by the coordinating session where the sweep was handed to a subagent (`review-project`, Set the standard); it runs on `sonnet`, as does a gap probe, and only a trigger grader or a hook on `haiku` (see `choose-model`).
- **Commit each skill's fixes separately, with its word count before and after**, taken from `wc` at commit time, not from memory, on every commit that touches a skill; the next inventory reads it, and one skill's fixes are read together, which is why this overrides review-project's commit per fix.
- **Flag in the report every rule cut by the default test, generalised, or left for the user**, so the user can restore or settle one.
- **State the net words across skills and references, and each top-level file's count before and after**; justify any growth, since a sweep that only adds leaves the next reader more to read.
- **The records apply to a plugin repo too** (`review-project`, The records are true), each created where missing: `DEPENDENCIES.md` lists the Claude Code version the hooks were last proved on, the validators and eval tool, each hook's interpreter and the oldest version it supports, any scheduled sweep (by name, never its id in a public repo) and the tracker; `costs.csv` holds a row per sweep, trial build and outside review, per model, with its source and a blank where a figure is unknown, never an estimate; `verification.csv` holds a row per Verification line with its dated result, which the coverage map cites.
- **List every check in the report as done, with what it found, or skipped, with why** — each check `review-project` names, the records among them, and each of this skill's, by name, one line each for the README, each instruction file and each context file — so a check either skill names shows as a gap rather than passing unseen.
