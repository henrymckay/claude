---
name: build-project
effort: medium
description: >-
  How to build a planned project milestone by milestone — each on the
  ladder's model through a subagent, failing tests first, a gate (the suite,
  a real run, an evaluator, a review, security checks) before each tick,
  records of dependencies, cost and checks, and a final review and acceptance
  run; in autonomous mode, no outward action. Use whenever building,
  implementing or continuing a project that has a PLAN.md — even if the user
  just says "build it", "go", "start on M1" or "carry on".
---

# Build the project

Building a planned project from its `PLAN.md`, one milestone at a time, with a gate before each is ticked.
It layers on `plan-project`, which owns the plan and how it may change, and on every skill the code falls under, any of whose defaults a signed-off `PLAN.md` decision overrides; it uses the built-in `/simplify` and `/code-review`, `design-interface`'s criteria and `secure-project`'s checks in the gate, settles the calls the plan didn't make through `make-decisions`, commits through `use-git`, hands off to `review-project` after the last milestone, and keeps the records `retire-project` reads when the project is retired.
Three mistakes account for most weak builds: ticking a milestone because the tests pass without running the real thing, building ahead of the milestone's requirements, and names and abstractions drifting from the plan a little each milestone until only the final review sees it, spread across every file.

- **Wrong** — the suite is green, so M2 is ticked; the import command has never been run on a real file.
- **Right** — the suite is green, the command runs on a real input file, and the row count matches the plan's expectation before the tick.

**In an existing project, ask first.** Where a repo already has its own roadmap or build process, check with the user whether to follow it or build from `PLAN.md`, and prefer `PLAN.md` unless they choose to keep theirs.

## Work without waiting

The approved `PLAN.md` is the user's sign-off for building its milestones in order, each on its own branch merged once its gate passes, as `use-git`'s Branches says.
Go from one milestone to the next without asking; stop only when:

- **the work would change a requirement or decision, override a skill, or build something from Not yet** — raise it with the change proposed, as `plan-project`'s Keep it current says, since a workaround buries the decision where the plan can't record it; a requirement found to force the design's complexity is asked about, not built around;
- **an open question blocks the next milestone** and `make-decisions` escalates it;
- **a gate check still fails after two fixes aimed at its cause** — report what was tried rather than trying a third.

**In autonomous mode the first two stops become records**, as `plan-project`'s Plan with no user present says; a failing gate still stops the build, and an outward action is left undone and listed in the report, its milestone unticked where the done-when check needs it.

Without a `PLAN.md`, plan first (`plan-project`).

## Hand each milestone to a subagent

**Build on Sonnet at medium effort, whatever the session started on: hand each milestone, from Start a milestone to Close it, to a foreground subagent with `model: sonnet` and `effort: medium`**, briefed as `choose-model`'s Hold a stage on its model says, with the milestone's ID and whether the run is autonomous, and check its report against the repo — the suite, the tick, the commits — before handing over the next.
**Never end a turn while a milestone's subagent is running** (`choose-model`, Hold a stage on its model).
A session briefed as that subagent works directly.

**Name in each brief the skills the milestone's files call for, to be invoked before the first file**, read from the plan sections it builds and from each file's language and surface — the language's skill and `be-functional` for any code, `write-tests` for its tests, `secure-project`, `write-entry-points` and `deploy-project` for a served API, `design-interface` for a screen, `write-markdown` for the README.
Briefed without a list, later subagents in a trial build loaded only this skill, even for a token-holding API in a new language; a list is checkable against the transcript.

## Start a milestone

- **Read the milestone's requirements and the sections they point at**, then invoke each skill its brief names and any other the code falls under.
- **Write its checks as failing tests first** — each Verification line the milestone covers, through `write-tests`.
A test written after the code tends to assert what the code does rather than what the plan asked for.
- **Build only what its requirements need.** Structure for a later milestone or anything in Not yet waits; a seam later work will need is noted under Ideas, not built.

## Build it

- **Wire the real path early, on a small slice.** Get real input through to real output, however crude, before refining any stage; a stage polished in isolation can fail to meet the next one.
- **Size every real run to the smallest sample that can show the property** — a few items, a short range — whether it wires the path or checks a claim such as "a re-run writes nothing".
Run full size once a milestone, after the suite passes and the sample comes out right, and again only when the stored result is shown to be wrong: a change made after a half-hour full run costs the half hour twice.
- **Use the Terms.** Every module, function, column and option takes the plan's name for its concept; a new concept the plan lacks is a gap to record under Open, not a name to invent quietly.
- **Record the calls the plan didn't make.** A library picked, a schema shaped, an error policy chosen is settled as `make-decisions` says, goes under Decisions with its source, and is built on; one that would override a skill is a stop above, not a proposal.
A point two skills settle differently is a gap, not an override: pick one, propose it, and file the contradiction.
A better way noticed goes under Ideas with its case, not into the code.

## Gate it

Pass every check before ticking the milestone; a drift caught here is a one-file fix, and caught at the final review it runs through everything built on top.
Read each check by what the project ships, as `plan-project` reads the Design: for a library the real surface is its public API from a fresh interpreter; for a content repo the suite is the docs' lint and link check, the real run is using the content, simplify is a read for duplication, and the code review is a cold read.

1. **The suite passes**, with the linter and type checker clean and branch coverage at both of `write-tests`' levels (Coverage and speed).
2. **The milestone's done-when check passes on real input** — run it and read the counts (see `write-tests`).
   Where the real input is unreachable — a service down, a credential the user supplied refused — run on a recorded sample or a local stand-in, record that under Open, say so in the report, and leave unticked a milestone whose done-when needs the real thing; a blocker outside the code is not a failing gate, so the build goes on.
   A check that takes minutes at full size passes on a sample here and runs whole after step 7, so a fix from the review does not repeat it.
   A check that runs only on the deployed surface, such as a site that deploys from the default branch alone, runs after the merge, with every other check passed on the branch first, and the milestone is ticked on `main` once it passes.
3. **The evaluator passes the surface**, wherever the milestone changed something a person looks at or uses — a screen, a page, a command's output, an API's docs, a message, the README (below).
4. **`/simplify` on the milestone's diff**, then re-run the suite.
5. **`/code-review` on the diff** at a low level; fix each confirmed bug with a regression test.
   An empty result does not show the review ran: count it only with an explicit no-findings line, and otherwise hand the diff to a fresh reviewer subagent.
6. **The security checks pass** — the dependency audit and the security review, wherever `secure-project`'s Review it calls for them.
7. **The diff reads true to the plan** — names from Terms, nothing beyond the milestone's requirements, no second copy of an existing helper, every decision honoured.
8. **Any performance requirement the milestone covers is met**, measured on input of the size Inputs gives.

### Evaluate the running surface

Tests show the code does what it says; only looking shows whether the surface is any good, and a builder grading its own screens passes what it meant to build.

- **Hand the running surface to a fresh evaluator**, briefed as `references/evaluate.md` says, which scores it against `design-interface`'s criteria.
Whichever session runs the gate spawns it — the milestone's subagent, or the main session when the subagent cannot spawn one — and the builder never scores its own screens.
- **Fix the failures, then evaluate again with a fresh evaluator**, at most three rounds; what still fails after the third goes under the plan's Questions with the evaluator's evidence and proposed change, and the milestone is ticked, since an unmet criterion is open polish, not a failed gate, unless it breaks a requirement.
- **Report each round's cost**, totalled by `choose-model`'s script for the evaluator's subagent (Record what a stage cost), so the user sees what the polish cost.
- **A fix that would loosen another rule is reported, not made** (`design-interface`, Set the bar).

`references/evaluate.md` has the brief, the screenshot script, running a headless browser without touching the system, and judging a command or an API.

## Close it

- **Bring `PLAN.md` up to date** as `plan-project` says, **and the README wherever the milestone changed what a user runs, sets or sees**, committing both on the milestone's branch with the change that made them true; a README left for the final review misleads everyone who reads it in between.
- **Bring the records up to date** (Keep the records): `DEPENDENCIES.md` with every account, service, credential, tool, connector or plugin the milestone used or created, and `verification.csv` with each Verification line its gate ran, in the milestone's commits; its row of `costs.csv` is written and committed by the session that spawned the milestone's subagent, once it has returned.
- **File any skill gap the milestone hit** before ticking it, as the session's skill-feedback rule says, never in the project's plan.
- **Keep the state in the repo, not the conversation.** The ticked milestones, Open and the commits are what a fresh session resumes from after a compaction or a break.
- **Report the milestone** — what now works, one line each for every decision proposed, idea noticed and assumption made, and the decisions settled by precedent as a count (`make-decisions`) — then start the next milestone.
Each gate check names the command that ran it and what it printed — the suite's pass count and coverage, the real run's rows; a check not run is reported as not run, never as "should pass", since the next milestone builds on what the report claims.

## Keep the records

**A project keeps three records at its root beside `PLAN.md`, each written as the work happens, never reconstructed at the end**, when an account opened three milestones back and a check run in the first are already forgotten.
`PLAN.md` names them under its title (`plan-project`), the dependency record points back at the plan, and the final report points at all three, so each is found from the others:

- **`DEPENDENCIES.md`** — everything outside the code the project depends on, as a lock file records its packages, so the owner can see what it costs, what to rotate and what to remove when it is retired (`retire-project`).
- **`costs.csv`** — what each stage cost, a row per stage and model (`choose-model`, Record what a stage cost).
- **`verification.csv`** — what each check showed and when, appended at every gate that runs a Verification line and at the acceptance run, so a later reader sees what was proven without the session that proved it.

**Start the dependency record from the plan's Inputs and Runs on at the first milestone, and add each entry in the commit that first uses or creates the thing**, with how it is removed, since that is when the command is known:

```markdown
# Dependencies

The plan is [`PLAN.md`](PLAN.md).

## Accounts and services

- **<provider> <service>** — <the tier relied on and the limit that matters>; used by <artefact>; opened <date>; holds <every repository, database, bucket, topic, schedule or token created there>; removed by <command or console step>.

## Credentials

- **`<NAME>`** — grants <scope> on <account>; kept in <store>; read by <consumer>; created <date>, rotate by <date>; revoked at <where>.

## Tools

- **<tool> <version>** — needed by <the build, the run or a hook>; installed with <command>.

## Connectors and plugins

- **<name>** — what <the build or the run> used it for.

## Packages

The lock file lists them.
```

- **Name, never value**: a credential by its variable name and where it is kept, an account by provider and purpose, so the record is safe in a public repository; the code host's own account counts, since the project dies with it.
- **Runs on says what the design chose; this file says what exists.** Where they disagree, one of them is wrong, and `review-project` checks one against the other.

**Append a row to `verification.csv` for each Verification line a gate or the acceptance run checks**, pass or not, with the columns `command`, `commit` (the short hash it ran on), `date`, `line` (the line's ID, `Acceptance`, or `coverage`), `printed` (the counts it printed, on one line), `result` (`pass`, `fail` or `not run`) and `stage` (the milestone, `review` or `acceptance`); never edit a row, so the last row for a line is what the project now shows and the rows before it say when that changed.

## Finish the build

After the last milestone, before the final report and in this order, autonomous and headless runs included:

1. **Run `review-project` against the plan.** The build is not finished until it has run; a report written without it says why at the top and calls the build unreviewed.
2. **Run the acceptance run**: every line of the plan's Verification on the final commit, the Acceptance line's commands included, after the review's fixes so it proves what ships; a full-size line that already passed on that commit is recorded from that run rather than repeated.
Each line goes into `verification.csv` with the stage `acceptance`, and the report lists each with the command that ran it and what it printed, a line not run as not run with the reason, and both coverage levels with any uncovered branch named; without the list the build is not reported complete.

**End with something the user can open**: the report's first lines give the command that starts the surface and its address, the folder of the last round's screenshots, and the deployed address once the user has allowed the deploy, not just a branch and a test count.
**Report what the build cost** from `costs.csv`, per stage and per model, the coordinating session's own row added last, as `choose-model`'s Record what a stage cost says, so each build is evidence for or against the ladder; and point at each of the three records, naming anything `DEPENDENCIES.md` gained since the plan.
