---
name: build-project
description: >-
  How to build a planned project milestone by milestone — each on the
  ladder's model through a subagent, failing tests first, a gate (the suite,
  a real run, an evaluator, a review, security checks) before each tick,
  records of dependencies, cost and checks, a final review and acceptance run,
  and a cloud session for a run nobody watches. Use whenever building, implementing
  or continuing a project that has a PLAN.md — even if the user just says
  "build it", "go", "start on M1" or "carry on".
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

**In autonomous mode the first two stops become records**, as `plan-project`'s Plan with no user present says; a failing gate still stops the build, and an outward action is left undone and listed in the report, its milestone unticked where the done-when check needs it (`plan-project`, Plan with no user present).

**No proposed decision skips the method, however small the project**: a subagent per milestone, the gate's fresh evaluator and review, the final review and the acceptance run hold whatever the prompt or the session makes of the project's size (`choose-model`, Hold a stage on its model), since with nobody present they are what make "finished" worth reading.
An unattended build that recorded "small, so build in the main session" as a proposed decision ran no review and shipped two high defects one would have caught.
Only the user's words or a signed decision drop one of these, and the report's first lines name every one that did not run.

Without a `PLAN.md`, plan first (`plan-project`).

## Run it with nobody present

**The plugins enforce nothing themselves: the only enforced boundaries for a run nobody watches are a cloud session's virtual machine and network policy, and, on the owner's machine, Claude Code's permission mode and built-in sandbox; a local session with neither has none**, whatever a skill tells it, so it holds only what the owner would hand a stranger.
Everything else below is text the session follows or a step the owner takes, and says which; `secure-project`'s Use Claude Code's own controls has the controls themselves.

**Run a build nobody watches — a trial build, or one started from a phone or a schedule — as a Claude Code cloud session on the project's repository alone**, started from claude.ai/code, `claude --cloud` or a scheduled task: it runs in a fresh Linux virtual machine Anthropic hosts, with nothing of the owner's machine in reach and the GitHub credential kept outside it, swapped in by a proxy (code.claude.com/docs/en/claude-code-on-the-web and cloud-environments, read 2026-11-22).
It is included in a Claude subscription, counted against its usage limits with no charge for the machine, and no per-session spend cap is documented, so the plan's budget is checked from the transcript afterwards (`choose-model`); scheduled tasks are a research preview, and a scheduled task's run starts in auto mode, whose classifier "does not guarantee safety" (permission-modes).

- **Load the plugins with the start-up hook in `assets/`**: copy `load-plugins.sh` into the project's `.claude/hooks/` and merge `settings.json` into its `.claude/settings.json`, on the default branch.
A cloud session installs none of the plugins a repository's `enabledPlugins` names (documented, and seen: the setting alone loaded nothing), so the hook adds the marketplace and installs each plugin at project scope, which loads them into that same session: the shipped hook, pinned, installed all six in a one-repository cloud session, whose skills and start-up text arrived, no `mcp__` tool was offered and `.claude/settings.json` stayed unchanged (Claude Code 2.1.330 in the VM, 2026-11-22, a throwaway probe).
The template's static `enabledPlugins` load nothing alone; they are there because the install writes the same entries back, so the file stays unchanged.
The hook runs only where `CLAUDE_CODE_REMOTE` is `true`, prints nothing when it works and logs nowhere; on a failed step it first uninstalls the plugins it installed, removes the marketplace and puts the settings file back as it found it, then prints "Plugins not loaded: <why>. Do no work; report this line and stop." on standard output and exits 0, since a `SessionStart` hook's standard error reaches the user alone (code.claude.com/docs/en/hooks; tried locally, where a session given that line stopped and reported it; the failure path is not yet run in a cloud session).
- **Check that the plugins loaded, since some failures print nothing**: a session given two repositories, or a thread in a claude.ai project, runs no hook from the repository's settings at all (documented), and an install that succeeds may still not load in that session.
So every unattended prompt opens with "stop and say so unless `build-project` is among your skills", and the owner checks the transcript's skill list before reading the branch; both are text, not a control.
- **Pin the marketplace to a reviewed commit, by its full SHA and nothing else**: the hook adds `<owner>/<repo>#<full commit SHA>`, refuses a pin that is not 40 lowercase hexadecimal characters, and installs nothing unless the marketplace's checkout is at exactly that commit and each plugin's source in it is a relative path inside the checkout, so a moved tag or branch, or a plugin fetched from elsewhere, cannot change what runs; the pinned commit must stay on a branch or tag of the repository, or the add fails and nothing loads (a marketplace's `ref` takes a full SHA from Claude Code 2.1.324, code.claude.com/docs/en/plugins/marketplace-reference, read 2026-11-22; the `#` form with a SHA matched in the cloud run above; a missing SHA, a moved checkout, an outside plugin source and a failed third install, each refused and undone, tried locally on 2.1.330).
Move the pin only after reading the diff between the two commits, since the plugins' hooks run as commands in every session.
- **Protect the default branch in the form that binds the session**, since GitHub applies a rule to the access the owner connected and a classic rule exempts administrators by default: a ruleset with an empty bypass list, or a classic rule with "Do not allow bypassing the above settings" (code.claude.com/docs/en/routines; docs.github.com, About protected branches and About rulesets, read 2026-11-22).
Either needs a public repository or a paid GitHub plan for a private one; it stops a direct push, not a pull request the session opens and merges through the API, which only auto mode's default block on merging an unapproved pull request and the rule above stand against.
The session's git proxy refuses tags and branch deletions but does not limit which branches a push can update (cloud-environments, GitHub proxy), and a push to the default branch was reported allowed with no rule in place (tried 2026-11-22), so before the first run the owner shows one push from a cloud session refused and records it in `DEPENDENCIES.md`.
- **Keep the environment's network at Limited**, its default, and add a host the project's data needs to that environment's list rather than opening it to Full; Limited is not an exit control, since its default list includes cloud storage and `gist.github.com`, so it does not keep a private repository's code in.
- **Give a key the run needs as a network secret** of the environment, which the proxy attaches to requests for the hosts listed without the session seeing it, never as an environment variable, which anyone using the environment can read (cloud-environments).
- **The work comes back as a branch** (`claude/…` when tried), and the session takes no other outward action (`plan-project`, Plan with no user present), which is text and auto mode's classifier, not a control.

**Give it nothing it could spend, leak or damage**, since an instruction slipped into something it reads acts with whatever it holds; a run that needs any of these stays attended:

- **Private or personal data** (`secure-project`, Classify the data).
- **A credential for an account with money in it**, as an environment variable or anywhere else.
- **A second repository**, or `/web-setup`'s token, which reaches every repository the owner's `gh` login can.
- **A connector**: a scheduled task includes every connector on the account by default, writes included, and connector traffic skips the network list (routines, cloud-environments), so remove each from the task; the template's `mcp__*` deny refuses any that remains in a session with one repository (documented; tried locally, not yet in a cloud session).

**The owner's reading of the diff is the one independent check; CI on the branch reruns only what the branch says to run**, since the session writes the tests, their thresholds, the linters' configuration and, for a new project, the workflow itself.
The review, the acceptance run and the records are done on the branch as Finish the build and Keep the records say, and nothing the run says about itself makes it finished.

- **Read first, against the default branch**: `.github/workflows/`; tests removed, skipped or loosened; coverage and other thresholds; tool configuration; `.claude/`, `CLAUDE.md`, `.pre-commit-config.yaml` and the build files, which run on the owner's machine, or in CI with its secrets, once the branch is checked out or pushed, outside any sandbox; for a first build, the whole workflow.
- **Put the workflow on the default branch before the first unattended build** (`setup-python`, Toolchain), so CI runs what the owner wrote, not only what the session did.
- **Keep secrets out of reach of the branch's CI**: GitHub withholds secrets only from workflows triggered from a fork, so a workflow the session edits runs on its own branch with the repository's secrets; a deploy's secrets go in a GitHub environment whose deployment branches allow the default branch alone, which on GitHub Free exists for public repositories only (docs.github.com, Using secrets, Deployments and environments, Managing environments for deployment, read 2026-11-22).

**A local run nobody watches is the lesser option, for low-risk public work only**, configured with Claude Code's own controls and no code of ours (code.claude.com/docs/en/permissions, permission-modes, sandboxing and cli-reference, read 2026-11-22):

- **One settings file, passed with `--settings`**: `assets/local-run.json` with `secure-project`'s permission rules merged into it and its placeholders filled; sandbox keys given that way, or by managed settings, are ones the project's own settings cannot loosen.
It turns the sandbox on with no unsandboxed retry and no run without it, denies sandboxed commands the home folder but the project, denies writes to other sessions' folders under `/private/tmp/claude-<uid>/` (on macOS; Linux takes no wildcard there, so name each), leaves the network list empty and refuses every connector.
- **The command**: `claude -p` from the project's folder with `--settings` that file, `--setting-sources project,local` so the owner's own allow rules and hooks are not inherited, `--strict-mcp-config`, `--permission-mode dontAsk`, an `--allowedTools` list of the tools the build uses, and `--max-budget-usd` and `--max-turns`, an estimate spend can pass.
- **What it leaves open**: `dontAsk` refuses only what would otherwise prompt, so reads in the working folder and read-only commands run unasked, as do the project's own allow rules and a hook's approval; Claude's file tools, MCP servers and hooks run outside the sandbox; every host added to the network list is a way out, and the empty list stops installs until the hosts are named; a toolchain or cache in the home folder needs an `allowRead` entry or a cache inside the project.
In a session with that file (2026-11-22, Claude Code 2.1.330): another folder's `.env` was refused to the Read tool and to a script, a project file read, an append to another session's script refused, a write to the run's own temporary folder made, `pypi.org` refused at the proxy, and every push, history rewrite and environment dump the rules name refused.

**Record each set-up step the owner takes in `DEPENDENCIES.md` when it is taken**, with who made it, when and how it is removed (Keep the records): the cloud environment with its network level, hosts and network secrets, the Claude GitHub App's access to the repository, the start-up hook and the commit it pins, the branch rule and the refused push that proved it, the CI workflow put on the default branch, a scheduled task by name, and the branches the runs leave.

## Hand each milestone to a subagent

**Build on Sonnet at medium effort, whatever the session started on: hand each milestone, from Start a milestone to Close it bar the gate's agents and the tick (below), to a foreground subagent with `model: sonnet` and `effort: medium`**, briefed as `choose-model`'s Hold a stage on its model says, with the milestone's ID and whether the run is autonomous, and check its report against the repo — the suite, the tick, the commits — before handing over the next.
**Never end a turn while a milestone's subagent is running** (`choose-model`, Hold a stage on its model).
A session briefed as that subagent works directly.

**The gate's agents are the handing session's, since a subagent may be unable to spawn one** (`choose-model`, Hold a stage on its model): the milestone's subagent runs every other gate check, commits and returns unticked; the handing session then spawns the evaluator (step 3), `/code-review` (step 5) and a `claude-security` review (step 6) on the milestone's branch, hands their findings to a subagent to fix with the suite re-run, and ticks the milestone only once each passes.
Briefed to "follow Start a milestone through Close it", builders in an unattended build judged their own screens and code instead, and one review at the end found nine problems.

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
The session that handed the milestone over spawns it after the hand-back (Hand each milestone to a subagent), and the builder never scores its own screens.
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

**A project keeps three records at its root beside `PLAN.md`, each written as the work happens, never reconstructed at the end**, when an account opened three milestones back and a check run in the first are already forgotten; the one exception is a project built before them (below).
`PLAN.md` names them under its title (`plan-project`), the dependency record points back at the plan, and the final report points at all three, so each is found from the others:

- **`DEPENDENCIES.md`** — everything outside the code the project depends on, as a lock file records its packages, so the owner can see what it costs, what to rotate and what to remove when it is retired (`retire-project`).
- **`costs.csv`** — what each stage of the build cost, a row per stage and model (`choose-model`, Record what a stage cost); what the deployed project costs to run goes on each account's line in `DEPENDENCIES.md`, since it is a bill per service, not per stage.
- **`verification.csv`** — what each check showed and when, appended at every gate that runs a Verification line and at the acceptance run, so a later reader sees what was proven without the session that proved it.

**Start the dependency record from the plan's Inputs and Runs on at the first milestone, and add each entry in the commit that first uses or creates the thing**, with how it is removed, since that is when the command is known:

```markdown
# Dependencies

The plan is [`PLAN.md`](PLAN.md).

## Accounts and services

- **<provider> <service>** — <the tier relied on and the limit that matters>; used by <artefact>; opened <date>; holds <every repository, database, bucket, topic, schedule or token created there>; running cost <the month's bill, $0 inside the tier> at <the usage read against that limit> on <date read>, cap <the spend limit, or none>; removed by <command or console step>.

## Credentials

- **`<NAME>`** — grants <scope> on <account>; kept in <store>; read by <consumer>; created <date>, rotate by <date>; revoked at <where>.

## Tools

- **<tool> <version>** — needed by <the build, the run or a hook>; installed with <command>.

## Connectors, plugins and skills

- **<name>@<marketplace> <version or commit>** — <a plugin, skill, language server or connector>; from <its source repository>; runs <its hooks and servers, or nothing>; relied on by <the plan, the build or the run> for <what>; installed by the user at <scope> on <date>, or proposed and not installed.

## Packages

The lock file lists them.
```

- **A step the owner takes by hand for the project — a token, a secret, an install, an account or repository setting — is an entry too**, named where the skill asks for the step, with who took it and how it is undone, since `retire-project` reads the teardown from this file and a step nobody recorded outlives the project.
- **Name, never value**: a credential by its variable name and where it is kept, an account by provider and purpose, so the record is safe in a public repository; the code host's own account counts, since the project dies with it.
- **Every plugin or skill outside the house family that the work relied on gets a line**, with the version `claude plugin list` shows, since the next session on another machine has only this file to tell it what the build had loaded; the house plugins themselves go on one line with their release tag.
- **Runs on says what the design chose; this file says what exists.** Where they disagree, one of them is wrong, and `review-project` checks one against the other.
- **Read each account's running cost from the provider once the artefact has run for a day**, from its usage or billing page or command, never estimated from the plan, and again at every review, so a service drifting toward the edge of its tier shows before it bills or stops.

**A project built before these records existed gets them at its first review**, in three different ways, since only one can be rebuilt honestly:

- **Reconstruct `DEPENDENCIES.md`** from the workflows, the host's secret listings, the plan's Runs on and each provider's console, and say so in its opening line (`Reconstructed <date> by review; entries before then were not recorded as they happened`).
- **Start `verification.csv` at the review and the acceptance run**, never back-filled from milestone notes, whose checks no longer exist to re-run; the plan's notes stay where they are as the earlier evidence.
- **Start `costs.csv` with its header and the review's own row**, and name in the report the stages whose transcripts are gone or were never totalled, rather than a row of guesses.

**Append a row to `verification.csv` for each Verification line a gate or the acceptance run checks**, pass or not, with the columns `command`, `commit` (the short hash it ran on), `date`, `line` (the line's ID, `Acceptance`, or `coverage`), `printed` (the counts it printed, on one line), `result` (`pass`, `fail` or `not run`) and `stage` (the milestone, `review` or `acceptance`); never edit a row, so the last row for a line is what the project now shows and the rows before it say when that changed.

## Finish the build

After the last milestone, before the final report and in this order, autonomous and headless runs included:

1. **Run `review-project` against the plan.** The build is not finished until it has run; a report written without it says why at the top and calls the build unreviewed.
2. **Run the acceptance run**: every line of the plan's Verification on the final commit, the Acceptance line's commands included, after the review's fixes so it proves what ships; a full-size line that already passed on that commit is recorded from that run rather than repeated.
Each line goes into `verification.csv` with the stage `acceptance`, and the report lists each with the command that ran it and what it printed, a line not run as not run with the reason, and both coverage levels with any uncovered branch named; without the list the build is not reported complete.

**End with something the user can open**: the report's first lines give the command that starts the surface and its address, the folder of the last round's screenshots, and the deployed address once the user has allowed the deploy, not just a branch and a test count.
**Report what the build cost** from `costs.csv`, per stage and per model, the coordinating session's own row added last, as `choose-model`'s Record what a stage cost says, so each build is evidence for or against the ladder; and point at each of the three records, naming anything `DEPENDENCIES.md` gained since the plan.
