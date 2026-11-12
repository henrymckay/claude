---
name: build-project
effort: medium
description: >-
  How to build a planned project milestone by milestone with minimal input from
  the user — working through its PLAN.md in order, a branch per milestone unless
  the plan decides otherwise, on Sonnet whatever model the session started on by
  handing each milestone to a subagent, failing tests first, the real path
  wired early on a small slice, the plan's terms kept in the code, only what
  the milestone needs built, every call the plan didn't make settled from
  precedent or proposed, and a gate read by what the project ships (the suite,
  a real run, a fresh evaluator scoring the running surface for up to three
  rounds, simplify, a code review, the security checks, a read against the
  plan) passed before each tick, with PLAN.md and the README kept current and
  the build ending with something the user can open; stopping only for a
  change to the plan, a blocking question or a failing check — or, in
  autonomous mode, proceeding on recommended answers recorded as assumptions
  and taking no outward action. Use whenever building, implementing or
  continuing a project that has a PLAN.md, or once a plan from plan-project
  is approved — even if the user just says "build it", "go", "start on M1",
  "carry on" or "build the next step". Layers on plan-project and every skill
  the code falls under, using simplify and code-review for the gate,
  design-interface for the evaluator's criteria, make-decisions for the
  calls, secure-project for the security checks and use-git for branches;
  hands off to review-project after the last milestone.
---

# Build the project

Building a planned project from its `PLAN.md`, one milestone at a time, with a gate before each is ticked.
It layers on `plan-project`, which owns the plan and how it may change, and on every skill the code falls under, any of whose defaults a signed-off `PLAN.md` decision overrides; it uses the built-in `/simplify` and `/code-review`, `design-interface`'s criteria and `secure-project`'s checks in the gate, settles the calls the plan didn't make through `make-decisions`, commits through `use-git`, and hands off to `review-project` after the last milestone.
Three mistakes account for most weak builds: ticking a milestone because the tests pass without running the real thing, building ahead of the milestone's requirements, and names and abstractions drifting from the plan a little each milestone until only the final review sees it, spread across every file.

- **Wrong** — the suite is green, so M2 is ticked; the import command has never been run on a real file.
- **Right** — the suite is green, the command runs on a real input file, and the row count matches the plan's expectation before the tick.

**In an existing project, ask first.** Where a repo already has its own roadmap or build process, check with the user whether to follow it or build from `PLAN.md`, and prefer `PLAN.md` unless they choose to keep theirs.

## Work without waiting

The approved `PLAN.md` is the user's sign-off for building its milestones in order, each on its own branch merged once its gate passes, as `use-git`'s Branches says.
Go from one milestone to the next without asking; stop only when:

- **the work would change a requirement or decision, override a skill, or build something from Not yet** — raise it with the change proposed, as `plan-project` says; a workaround built instead buries the decision where the plan can't record it, and a requirement found to force the design's complexity is asked about, not built around;
- **an open question blocks the next milestone** and `make-decisions` escalates it;
- **a gate check still fails after two fixes aimed at its cause** — report what was tried rather than trying a third.

**In autonomous mode the first two stops become records**, as `plan-project`'s Plan with no user present says; a failing gate still stops the build, and an outward action is left undone and listed in the report, its milestone unticked where the done-when check needs it.

Without a `PLAN.md`, plan first (`plan-project`).

## Hand each milestone to a subagent

**Build on Sonnet at medium effort, whatever the session started on: hand each milestone, from Start a milestone to Close it, to a foreground subagent with `model: sonnet` and `effort: medium`**, briefed as `choose-model`'s Hold a stage on its model says, with the milestone's ID and whether the run is autonomous, and check its report against the repo — the suite, the tick, the commits — before handing over the next.
A session briefed as that subagent works directly.

## Start a milestone

- **Read the milestone's requirements and the sections they point at**, then invoke each skill the code will fall under.
- **Write its checks as failing tests first** — each Verification line the milestone covers, through `write-tests`.
A test written after the code tends to assert what the code does rather than what the plan asked for.
- **Build only what its requirements need.** Structure for a later milestone or anything in Not yet waits; a seam later work will need is noted under Ideas, not built.

## Build it

- **Wire the real path early, on a small slice.** Get real input through to real output, however crude, before refining any stage; a stage polished in isolation can fail to meet the next one.
- **Size every real run to the smallest sample that can show the property** — a few items, a short range — whether it wires the path or checks a claim such as "a re-run writes nothing".
The full-size run happens once a milestone, after the suite passes and the sample comes out right, and again only when the stored result is shown to be wrong: a change made after a half-hour full run costs the half hour twice.
- **Use the Terms.** Every module, function, column and option takes the plan's name for its concept; a new concept the plan lacks is a gap to record under Open, not a name to invent quietly.
- **Record the calls the plan didn't make.** A library picked, a schema shaped, an error policy chosen is settled as `make-decisions` says, goes under Decisions with its source, and is built on; one that would override a skill is a stop above, not a proposal.
A point two skills settle differently is a gap, not an override: pick one, propose it, and file the contradiction.
A better way noticed goes under Ideas with its case, not into the code.

## Gate it

Pass every check before ticking the milestone; a drift caught here is a one-file fix, and caught at the final review it runs through everything built on top.
Read each check by what the project ships, as `plan-project` reads the Design: for a library the real surface is its public API from a fresh interpreter; for a content repo the suite is the docs' lint and link check, the real run is using the content, simplify is a read for duplication, and the code review is a cold read.

1. **The suite passes**, with the linter and type checker clean.
2. **The milestone's done-when check passes on real input** — run it and read the counts (see `write-tests`).
   Where the real input is unreachable, run on a recorded sample, record that under Open, and say so in the report.
   A check that takes minutes at full size passes on a sample here and runs whole after step 7, so a fix from the review does not repeat it.
3. **The evaluator passes the surface**, wherever the milestone changed something a person looks at or uses — a screen, a page, a command's output, an API's docs, a message, the README (below).
4. **`/simplify` on the milestone's diff**, then re-run the suite.
5. **`/code-review` on the diff** at a low level; fix each confirmed bug with a regression test.
6. **The security checks pass** — the dependency audit and the security review, wherever `secure-project`'s Review it calls for them.
7. **The diff reads true to the plan** — names from Terms, nothing beyond the milestone's requirements, no second copy of an existing helper, every decision honoured.
8. **Any performance requirement the milestone covers is met**, measured on input of the size Inputs gives.

### Evaluate the running surface

Tests show the code does what it says; only looking shows whether the surface is any good, and a builder grading its own screens passes what it meant to build.

- **Hand the running surface to a fresh evaluator**, a subagent on `sonnet` (`choose-model`) given the plan's Interface, the launch command and `design-interface`'s criteria and nothing of the builder's account; it starts the surface, screenshots each screen at desktop and phone width in light and dark, or runs a realistic session of the command or API, and returns pass or fail per criterion with its evidence.
The session that handed the milestone over spawns it, so the evaluator is never the builder's own child.
- **Send the failures back to the builder, then evaluate again**, at most three rounds; what still fails after the third goes into the milestone report as open, with the evaluator's evidence, rather than a fourth round.
- **Report each round's cost** — the evaluator's and the fix's tokens priced at `choose-model`'s rates — so the user sees what the polish cost.
- **Never let a criterion loosen another rule**: a fix that would need an outward action, a feature the plan lacks or a weaker security check is reported, not made.

`references/evaluate.md` has the brief, the screenshot script, running a headless browser without touching the system, and judging a command or an API.

## Close it

- **Bring `PLAN.md` up to date** as `plan-project` says, **and the README wherever the milestone changed what a user runs, sets or sees**, committing both on the milestone's branch with the change that made them true; a README left for the final review misleads everyone who reads it in between.
- **File any skill gap the milestone hit** before ticking it, as the session's skill-feedback rule requires; one written into the project's plan is never seen by the sweep that would fix it.
- **Keep the state in the repo, not the conversation.** The ticked milestones, Open and the commits are what a fresh session resumes from after a compaction or a break.
- **Report the milestone** — what now works, one line each for every decision proposed, idea noticed and assumption made, and the decisions settled by precedent as a count (`make-decisions`) — then start the next milestone.
Each gate check in the report names the command that ran it and what it printed — the suite's pass count, the real run's rows; a check not run is reported as not run, never as "should pass", since the next milestone builds on whatever the report claims.

## Finish the build

After the last milestone, run `review-project` against the plan.
**End with something the user can open**: the report's first lines give the command that starts the surface and the address it answers on, the folder of the last round's screenshots, and the deployed address once the user has allowed the deploy; a build that ends with a branch and a test count has left the user to find out what it made.
