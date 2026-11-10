---
name: build-project
description: >-
  How to build a planned project milestone by milestone with minimal input
  from the user — working through its PLAN.md in order, each milestone on its
  own branch unless the plan decides otherwise, writing each check as a
  failing test first, wiring the real path early, keeping the plan's terms in
  the code, recording every call the plan didn't make as a proposed decision
  or an idea, and passing a quality gate read by what the project ships (the
  suite, a real run, simplify, a code review, a read against the plan and any
  performance budget) before ticking each milestone, keeping PLAN.md current
  so a fresh session can resume, filing skill gaps as it goes, and stopping
  only for a change to the plan, a blocking question or a check that won't
  pass. Use whenever building, implementing or continuing a project that has a
  PLAN.md, or once a plan from plan-project is approved — even if the user
  just says "build it", "go", "start on M1", "carry on" or "build the next
  step". Layers on plan-project, the plan it builds from, and on every skill
  the code falls under, using the built-in simplify and code-review for the
  gate and use-git for branches and commits; hands off to review-project when
  the last milestone is done.
---

# Build the project

Building a planned project from its `PLAN.md`, one milestone at a time, with a gate before each is ticked.
It layers on `plan-project`, which owns the plan and how it may change, and on every skill the code falls under — a decision recorded in `PLAN.md` overrides any default in this skill or those, branching included; it uses the built-in `/simplify` and `/code-review` in the gate, commits through `use-git`, and hands off to `review-project` once the last milestone is done.
Three mistakes account for most weak builds: ticking a milestone because the tests pass without running the real thing, building ahead of the milestone's requirements, and names and abstractions drifting from the plan a little each milestone until only the final review sees it, spread across every file.

**In an existing project, ask first.** Where a repo already has its own roadmap or build process, check with the user whether to follow it or build from `PLAN.md`, and prefer `PLAN.md` unless they choose to keep theirs.

## Work without waiting

The approved `PLAN.md` is the user's sign-off for building its milestones in order, each on its own branch merged once its gate passes (see `use-git`) unless its Decisions say otherwise.
Go from one milestone to the next without asking; stop only when:

- **the work would change a requirement or decision** — raise it as `plan-project` says, with the change proposed; a workaround built instead buries the decision where the plan can't record it;
- **an open question blocks the next milestone**;
- **a gate check still fails after two fixes aimed at its cause** — report what was tried rather than trying a third.

Without a `PLAN.md`, see `plan-project`'s When to plan.

## Start a milestone

- **Read the milestone's requirements and the sections they point at**, then invoke each skill the code will fall under.
- **Write its checks as failing tests first** — each Verification line the milestone covers, through `write-tests`.
A test written after the code tends to assert what the code does rather than what the plan asked for.
- **Build only what its requirements need.** Structure for a later milestone or anything in Not yet waits; a seam that later work will need is noted under Open, not built.

## Build it

- **Wire the real path early.** Get real input through to real output, however crude, before refining any stage; a stage polished in isolation can fail to meet the next one.
- **Use the Terms.** Every module, function, column and option takes the plan's name for its concept; a new concept the plan lacks is a gap to record under Open, not a name to invent quietly.
- **Record the calls the plan didn't make.** A library picked, a schema shaped, an error policy chosen goes under Decisions as proposed, with its source; a better way noticed goes under Ideas with its case, not into the code.
The gate keeps the build to the milestone; Open keeps the thought, so it reaches the user instead of dying in the conversation.

## Gate it

Pass every check before ticking the milestone; a drift caught here is a one-file fix, and caught at the final review it runs through everything built on top.
Read each check by what the project ships, as `plan-project` reads the Design: for a library the real surface is its public API from a fresh interpreter; for a content repo the suite is the docs' lint and link check, the real run is using the content, simplify is a read for duplication, and the code review is a cold read.

1. **The suite passes**, with the linter and type checker clean.
2. **The milestone's done-when check passes on real input** — run it and read the counts (see `write-tests`).
Where the real input is unreachable, run on a recorded sample, record that under Open, and say so in the report.
3. **`/simplify` on the milestone's diff**, then re-run the suite.
4. **`/code-review` on the diff** at a low level; fix each confirmed bug with a regression test.
5. **The diff reads true to the plan** — names from Terms, nothing beyond the milestone's requirements, no second copy of an existing helper, every decision honoured.
6. **Any performance requirement the milestone covers is met**, measured on input of the size Inputs gives.

## Close it

- **Bring `PLAN.md` up to date** as `plan-project` says, and commit it with the change that made it true.
- **File any skill gap the milestone hit** before ticking it, as the filing rule in `CLAUDE.md` requires; a gap left to memory is lost by the next milestone.
- **Keep the state in the repo, not the conversation.** The ticked milestones, Open and the commits are what a fresh session resumes from after a compaction or a break; a decision held only in the conversation is lost there.
- **Report the milestone** — what now works, and one line each for every decision proposed, idea noticed and assumption made — then start the next milestone.

## Finish the build

After the last milestone, run `review-project` against the plan; it fixes what it finds and reports what the project now does and what is left.
