# claude

A marketplace of Claude Code plugins that let Claude do impressive projects entirely autonomously and securely, from a short prompt to a retired project, with each plugin detachable from the rest.

Records: [`DEPENDENCIES.md`](DEPENDENCIES.md), [`costs.csv`](costs.csv), [`verification.csv`](verification.csv).

Signed off by the owner: R1 to R8 (2026-11-21, issue 157), D1 to D53 (2026-11-12), D61 bar its `author.name` sentence (2026-11-13), D62 to D70 (under the owner's delegation, 2026-11-19) and D71 to D81 (2026-11-20).
Everything else is proposed: R9, the Fails-when lines under R1 to R8, D54 to D60, D82 onwards bar D133 and D138 (decided under delegation), the amendments dated 2026-11-21, the coverage map, the Design's text and the Not yet list.
The unsigned backlog is counted under Open.
One line per decision; each signed decision's full text is at commit `7aa0625`, and test logs and rationale live in the pull request or skill each line cites.

## Brief

### Goal

The owner's aim, in their words: "I want these plugins to let claude do impressive projects entirely autonomously and in a secure way. and for different plugins to be detachable."
Claude gets one prompt and delivers a project that is elegant, correct and well tested, designed beyond the brief, planned, deployed, run and retired as well as coded; the plugins settle recurring decisions in advance and find and fix their own gaps.
Done looks like: every map row graded *repeated* or deliberately left out, two trials of different kinds run unattended from one prompt leaving `review-project` no defect, each plugin shown to work alone, and a change shown to beat a fixed control (issue 150).

### Terms

- **skill** — a `SKILL.md` with any `references/` and `scripts/`.
- **plugin** — a folder under `plugins/`, installable alone; the repo is a **marketplace** of six.
- **always-on file** — a plugin's `hooks/context.md` or `hooks/shared.md`, or an instruction file: paid for in every session and subagent.
- **sweep** — one `review-plugin` run: the open skill feedback, every drift check, the outside review, landed as one pull request.
- **trial build** — a real project built with the plugins to test them.
- **cloud session** — a Claude Code session in a virtual machine Anthropic hosts, given one repository; how an unattended run is made (D138).
- **autonomous mode** — no user present: answers assumed, decisions proposed, no outward action but returning the work as a branch.
- **outward action** — creating a repository, publishing, deploying, messaging, spending or moving money, or acting on an account.

### Requirements

The owner named R1 to R8 as the qualities every plugin, skill and project is judged by; R9 is proposed.
Each states the result that would show it failing, and what it costs.

- **R1 Autonomous** — one prompt, nobody present, start to finish, with one batch of answers from the owner or none; a stopped run resumes, an overspending one stops, and the owner learns which.
  - Fails when an unattended run waits on a question, is called finished before CI passes on its branch and the owner has read the diff, or takes an outward action beyond pushing its branch.
  - Cost: unsigned plans, outward steps that wait, a cloud environment and start-up hook per project.
- **R2 Impressive** — best-in-class design and ideas beyond the brief, not boxed in by this plugin set.
  - Fails when a trial plan lacks a best-in-class line per surface or an idea beyond the brief, or its evaluator still fails a surface after three rounds.
  - Cost: longer plans and gates, a research step, outside plugins vetted.
- **R3 Secure** — safe with data, credentials and money, enforced, not only advised; no secret or project data in the public repo.
  - Fails when an unattended run is given what `build-project` withholds, reaches a host or repository its environment does not allow, or pushes to a protected default branch; a secret or project data reaches the repo or a tracker; or a money-moving connector call runs unconfirmed.
  - Cost: a class per input and output, a security step per gate, private-data and real-account work attended for now.
- **R4 Modular** — any plugin works alone or with the others, on any machine.
  - Fails when `validate --strict` or a trigger case fails, or a plugin alone makes a call a missing skill owns without naming it.
  - Cost: a context file per plugin, six copies of the shared rules, pinnable releases.
- **R5 Proven** — results right and shown right, with plan, cost and test results recorded.
  - Fails when a cell graded as passing has a last recorded result that is not a pass, or a build or this repo lacks a record.
  - Cost: a run per requirement, three records per project, the map kept true.
- **R6 Complete** — plan, build, verify, deploy, operate, undo and retire.
  - Fails when a row of the map has nothing above *designed*: today undo and retire, each with its issue or reason.
  - Cost: every other requirement; scope held to Python data, command-line, API and dashboard projects, with a TypeScript front end or Worker beside them.
- **R7 Frugal** — build and running cost bounded and known; each skill worth its load.
  - Fails when a run passes its limit by more than one poll, a sweep passes its budget unexplained, or a file or description passes its budget.
  - Cost: a hand-off per stage, a ledger per project, the budget table; a cloud session has no spend cap, so its cost is read afterwards.
- **R8 Adaptive** — the plugins find and fix their own gaps, keep up with tools and prices, and show a change improved things.
  - Fails when a feedback issue survives two sweeps unsettled and unmapped, or a change is called an improvement without a run against the control (issue 150).
  - Cost: hooks, a weekly sweep, trigger suites, claims re-checked, a control build.
- **R9 Legible** *(proposed, D125)* — what the owner must read and decide after a run or sweep fits on one screen; sign-off is by exception; the unsigned backlog is tracked.
  - Fails when a report's part for the owner runs past one screen (about 40 lines), the plan calls something signed that the owner did not sign, or the backlog line under Open is stale.
  - Cost: detail deferred to the pull request; decisions stand as proposed until read.


### Not yet

- **A repository per plugin** — earned by different visibility or another owner (D30).
- **A listing in the plugin directory, icons; `agents/`, `commands/`, `rules/`; Slack; an `advisor` step** — none earned yet.
- **Toolchain skills beyond `uv`, languages beyond Python and TypeScript, more SQL dialects, architecture across components** — each earned by the first project that needs it, which looks first for an outside plugin (D97, D104, D105).
- **A debugging skill** — issue 148.
- **CI, snapshot or mutation tests, a task runner, Docker, docs generation** — each earned by the first project that needs it.
- **An unattended run holding private data or a real account** — attended until a vendor control can hold it (D138).
- **A plugin per domain** — a domain skill starts in its project and is promoted once a second repository needs it; issue 71 holds trading.

## Design

### Inputs

- **The owner's conversations and corrections** — the requirements and most rules.
- **Skill-feedback issues** — labelled `skill-feedback` on the repository each `plugin.json` names; public, so they carry a case's shape, never a project's data.
- **Current tool docs and releases** — every skill claim is checked against them each sweep.
- **Trial builds and their records** — each files feedback and grades the map from its own `verification.csv`.

### Data flow

Skill source, wiring, loading, applying, feedback, sweep, looping back to source; the README's Feedback and sweeps has the loop.

### Outputs

- **Skills, their scripts and templates** — `costs.py` with its tests; `build-project`'s start-up hook and `secure-project`'s permission rules, in each skill's `assets/`.
- **Each plugin's wiring** — manifest, `hooks/` and `evals/`.
- **`.claude-plugin/marketplace.json`**, **`skills/`** symlinks, **`instructions/`**, **`README.md`**, this plan and its three records.

### Interface

```bash
claude plugin marketplace add "henrymckay/claude#$(git ls-remote --tags --refs --sort=-version:refname https://github.com/henrymckay/claude.git 'v*' | head -n 1 | cut -d/ -f3)"
claude plugin install manage-project@henrymckay
```

An unattended build is a cloud session on the project's repository alone, the plugins loaded by `build-project`'s hook pinned to a reviewed commit; its work comes back as a branch (`build-project`'s `references/unattended.md`).

| Plugin | Skills |
|---|---|
| `manage-project` | `plan-project`, `build-project`, `review-project`, `retire-project`, `choose-model`, `make-decisions`, `secure-project`, `use-git`, `write-markdown` |
| `design-project` | `design-interface`, `design-pipeline` |
| `write-code` | `be-functional`, `be-oop`, `write-python`, `write-typescript`, `write-sql`, `write-tests`, `use-polars` |
| `structure-app` | `setup-python`, `structure-python`, `write-entry-points` |
| `run-project` | `store-data`, `run-unattended`, `deploy-project`, `send-messages` |
| `maintain-plugin` | `review-plugin`, `write-skills` |

### Runs on

- **The skills** — the owner's machine, installed from the repo as a local marketplace; elsewhere a release, or symlinks.
- **The weekly sweep** — a Claude Code cloud scheduled task on Opus with no connectors, opening one pull request; its identifier stays off this public file.
- **The hooks** — each plugin's start-up hooks and `maintain-plugin`'s `Stop` hook, merged by hand under the symlink wiring.
- **An unattended run** — a Claude Code cloud session on one repository, at the Limited network level, holding no private data, money credential or connector (D138).
- **Threat model** — a hook runs as a shell command and a skill as instructions, so changes land by reviewed pull request (D2, D24), installs pin a release (D41) and a cloud session's hook pins a commit; the repo holds no credential; the plugins enforce nothing themselves, so an unattended run's boundary is the vendor's virtual machine and network policy, the default branch's protection and what the session is not given.
- **Unattended runs** — trial builds run as cloud sessions; this repo's sweeps take no outward action beyond their pull request.

### Errors

- **A description misfires, a rule drifts or a file outgrows its budget** — found by the sweep and fixed where the rule belongs; feedback holding project data is edited on sight.
- **The start-up hook does not load the plugins** — its line tells the session to stop, and the prompt's opening check catches a hook that never ran; fix it and start a new session.
- **An unattended run needs more than it was given** — it lists the step for the owner in its report and on its branch.

### Decisions

Numbers are stable; each line is the choice, what it beat, and where the evidence lives.

**Budgets** (D54, amended by D81, D91, D95, D106, D115, D125, D128; figures in words unless marked):

| Item | Budget | Now |
|---|---|---|
| `instructions/installed.md` | 180 | 176 |
| `instructions/symlinked.md` | 1,055 | 1,055 |
| `hooks/shared.md`, each copy | 380 | 377 |
| `manage-project`'s context file | 170 | 164 |
| `write-code`'s context file | 80 | 78 |
| Every other context file | 70 | 56 at most |
| `hooks/compact.md` (D72) | 65 | 65 |
| `README.md` | 980 | 948 |
| `PLAN.md` (D125: about 5,000) | 5,500 | 5,495 |
| A skill description | 500 characters | all under |
| A sweep, build and checks | $40 | `costs.csv` |
| A sweep's outside review | $25 | `costs.csv` |

**The repository and its wiring**

- **D1** Symlinks into `~/.claude` stay a supported wiring beside installed plugins.
- **D2** Commit as the owner's no-reply identity; a sweep lands by pull request, and only an edit the owner makes or asks for outside a sweep goes straight to `main`; overrides `use-git`, Branches.
- **D9** No performance budget. *Amended 2026-11-21 (proposed): hook time and cost are budgeted.*
- **D10** Not yet lives in this plan, over `enhancement` issues.
- **D11** The README is for humans and points here.
- **D12** Memory holds only what this plan doesn't. *Amended 2026-11-21 (proposed): next steps live in `Next`, never in memory.*
- **D30** One repo as a marketplace, over one plugin or a repo each. *Amended by D88: six plugins.*
- **D31** Plugins named verb-first for their ability; `use-git` and `write-markdown` in `manage-project`. *Amended by D88: six plugins.*
- **D32** Always-on lists printed by hooks, over a plugin `CLAUDE.md`; amended by D92 to D94.
- **D34** A toolchain's commands live in the skill that owns it.
- **D41** A release is a tag `v<major>.<minor>` on `main` after a merged sweep, cut by the owner; overrides `use-git`, Release.
- **D43** The MIT licence.
- **D44** Nothing in the repo tells the owner's machines apart.
- **D54** Word budgets for the always-on files and the README, in the table above; an addition says what it removed.
- **D60** The install line looks up the newest release tag, over naming it.
- **D61** The owning account is named only where an install needs it. *(proposed: `author.name` reads `claude contributors`.)*
- **D62** Keep the marketplace name until the repository moves.
- **D63** A description under 500 characters, never past 1,000 — `write-skills`.
- **D64** A should-not-trigger case only beside a near neighbour.
- **D65** Beside another authoring plugin, `write-skills` sets what a skill says.
- **D66** `use-git`'s no-footer rule calls itself the owner's instruction.
- **D88** A sixth plugin, `design-project`, for `design-interface` and `design-pipeline`; amends D30, D31, D55.
- **D92** Each plugin prints its rules into every subagent from a `SubagentStart` hook; PR 146.
- **D93** The shared rules print once per start through an atomic marker; PR 146.
- **D94** Two instruction files, `installed.md` and `symlinked.md`; completed by D129.
- **D81, D91, D95, D106, D115** Budgets raised as skills, plugins and files grew; figures in the table.
- **D129** *(proposed)* The root `CLAUDE.md` link is removed: the owner's link points at `installed.md`, and the link loaded the skill list twice here; completes D94.

**How a project runs**

- **D5** `review-project` general, `review-plugin` layered on it.
- **D6** `build-project`, over `develop-project`.
- **D13** A skill's default is a default; a signed decision overrides it, a reason Claude finds is a proposed decision.
- **D14** Decisions surfaced with alternatives, costs and sources.
- **D26** A sweep outcome "needs the user" for policy.
- **D35** Autonomous mode: answers assumed, decisions proposed, no outward action; amended by D111, D123, then D138: none but returning the work as a branch.
- **D46** Settle an open question from precedent, escalating only what `make-decisions` lists.
- **D47** `secure-project` in `manage-project`, private by default; nothing moves money without a signed decision and a person confirming; the policy stays open to refinement as real projects reach it.
- **D52** A named method plugin leads; the convention skills still apply.
- **D57** Every shipped surface aims at the best in class.
- **D58** An evaluator pass in the gate, up to three rounds.
- **D59** The ladder holds when a prompt calls the work small. *Amended by D143 (proposed): the plan's counts, never the prompt, can choose `build-project`'s small path.*
- **D74** A build ends with the review, then an acceptance run.
- **D75** Three records beside `PLAN.md` (`build-project`, Keep the records).
- **D76** Stage costs totalled into `costs.csv` by `costs.py`.
- **D77** Coverage at two levels, every core branch and a rising floor; overrides `write-tests`' old "no percentage".
- **D78** A commit identity before the first commit; a schedule is deployed once it has fired.
- **D79** Each check's result appended to `verification.csv`, never edited.
- **D80** Teardown is `retire-project`, each irreversible step confirmed.
- **D83** Running cost on each account's line in `DEPENDENCIES.md`.
- **D84** A project older than the records gets them at its first review.
- **D85** Both coverage levels run as one `pre-push` hook.
- **D104** Reasoning from the general case is a section of `make-decisions`, over a design skill; PR 158.
- **D105** Outside plugins are looked for, vetted and proposed; installing is the owner's step; PR 158.
- **D113** Untrusted content is a section of `secure-project`.
- **D114** Threat model and Unattended runs lines in a plan's Runs on.
- **D142** *(proposed)* A skill fires at a moment the session sees before acting, named alike in its description and context line, never a topic or a state its work creates late, and hands on by invoking the next skill; over topic triggers, which left four skills unloaded in two unattended builds; `write-skills`; issue 181.
- **D143** *(proposed; amends D27 and D70, signed, and D59)* `build-project` has a small path, read from the plan (at most three milestones, one language, nothing deployed or scheduled, no credential or private data), built in the main session with the review by a fresh agent and the acceptance run always, over one size a session waived; issue 181.
- **D144** *(proposed; amends D27, signed)* `plan-project` plans in place when the session's start-up model is Opus, and a run with nobody present skips plan mode; issue 186.
- **D145** *(proposed)* The owner's unattended set-up moves to `build-project`'s `references/unattended.md`, off the builder's path.
- **D125** *(proposed)* A plan holds to about 5,000 words, 5,500 at most, with a `Next` list, one line per decision and one budget table, cut without waiting for sign-off, over the 17,000 words this one reached; adds R9; `plan-project`; issue 165.

**Running unattended**

- **D108 to D111, D116 to D124, D131 to D133** *(superseded by D138; D133 decided under delegation, 2026-11-22)* The guard hook and its asks and refusals, the launcher with its run profile, spend and turn bounds, preflight, gate, folders and status file, and the standing grant; PR 161, issue 164; each line's text is at commit `7d7f9fd`.
- **D112** Asking the owner one question from afar is designed and not built (issue 155).
- **D138** *(decided by the coordinator under the owner's delegation, 2026-11-22; not the owner's sign-off)* **The plugins carry no security machinery of their own: the launcher with its profile, preflight and gate, the guard hook and the standing grant are removed**, over a fourth sweep hardening them; isolation comes from the vendor and the skills say how to use it.
An unattended run is a Claude Code cloud session on the project's repository alone, plugins loaded by a start-up hook pinned to a reviewed SHA, the default branch protected, work returned as a branch, "finished" decided by CI on that branch and the owner reading the diff; it is given no private data, money credential, connector or second repository, so such runs stay attended; a local unattended run is the lesser option for low-risk public work, under Claude Code's own `dontAsk` mode, permission rules and sandbox.
Evidence: issue 173's replay (531 asks of 2,841 calls, 26 worth asking), issue 163, PR 176 closed unmerged, T10; `build-project`, `secure-project`.
- **D139** *(proposed)* A cloud session loads the plugins from a `SessionStart` hook that installs only when the marketplace's checkout is at the pinned SHA, over `enabledPlugins` (documented not to load in a cloud session) and an environment setup script (untried); T10 throwaway and the hook's local tests.
- **D140** *(proposed)* `secure-project` ships a starting set of denies and asks, Claude Code rules only, for the owner's user settings; it stops the file tools and named commands, not a script or a shell write, which only the sandbox stops; `build-project`'s `local-run.json` adds the sandbox keys for a local run.
- **D141** *(proposed)* Skill feedback a run cannot file goes in its report and never stops it; issue 178.

**Models**

- **D27** The model ladder, each stage handed to a subagent with its model set — `choose-model`.
- **D42** No skill names a model in its frontmatter; amended by D82.
- **D70** A build milestone with a visible surface stays on Sonnet: $5.45 against $10.75 on Opus for one plan, both passing; provisional, one project.
- **D73** A stage's subagent runs in the foreground, with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` as backstop.
- **D82** A skill names an effort only to raise it, so `build-project` dropped its `effort: medium`; overrides D42 for that line.
- **D126** *(proposed)* Every sweep ends with a read-only outside review on the best model at its highest effort, seven fixed questions then the riskiest change, over the builder checking itself; `review-plugin`; issue 162.

**The feedback loop**

- **D3** Skill feedback as GitHub issues.
- **D4** The filing rule is always on.
- **D23** A trigger suite per plugin at `plugins/<plugin>/evals/`.
- **D24** Every sweep lands as one pull request.
- **D25** A `Stop` hook prompts for unfiled skill gaps.
- **D28** The weekly sweep runs on Opus with no connectors.
- **D33** Feedback goes to the owning plugin's repository, or a file where it must not be public.
- **D39** A requirement is verified by behaviour, not by a skill existing.
- **D40** No brief-and-answers evaluations; trial builds and trigger suites instead. *(proposed 2026-11-21: superseded by issue 150's control build if the owner accepts it.)*
- **D45** The coordinating session reviews and merges a sweep's pull request.
- **D107** The owner's qualities as requirements, with a coverage map; PR 161.
- **D127** *(proposed)* `review-plugin` says how a sweep is run and checked, over a coordinator's memory; issue 166.
- **D128** *(proposed)* This repo keeps the three records, costs back-filled only from pull requests with unknowns blank; issue 167.
- **D130** *(proposed)* The coverage map grades cells seen once, repeated or failing from dated runs, held only while the last result passes, over proven against designed; issue 165.

**House picks** — each named, with its alternative and reason, in the skill shown.

- **D7** `be-functional` the default style, `be-oop` opt-in.
- **D15** `functools.partial`, closures and `match` — `be-functional`.
- **D16** One error model — `write-python`.
- **D17** One record type, the frozen keyword-only dataclass — `write-python`.
- **D18** `uv_build` — `setup-python`.
- **D19** pyright `strict` — `setup-python`.
- **D20** Picks for datetime, money, storage, config, HTTP, logging, plotting and test doubles — their owning skills.
- **D21** `store-data` and `run-unattended` exist to absorb the gaps a probe left open.
- **D22** MotherDuck's token variable is `motherduck_token` — `store-data`.
- **D29** ntfy for alerts, email for digests, Claude Code channels for chat — `send-messages`.
- **D36** `write-sql` in `write-code`, a DuckDB reference first.
- **D37** `coverage run -m pytest` over `pytest-cov`.
- **D38** A run that finds the lock held writes no manifest row — `run-unattended`.
- **D48** Stored columns alphabetical, timestamps UTC with their zone — `store-data`.
- **D49** A three-day catch-up window by default — `run-unattended`.
- **D50** `sqlfluff` from a project's first `.sql` file.
- **D51** Hive-partitioned Parquet by default; DuckLake or Delta Lake where a table format is needed — `store-data`.
- **D53** A MotherDuck project pins the client MotherDuck accepts, on Python 3.14; overrides `setup-python`'s floor.
- **D55** One house design system — `design-interface`; in `design-project` since D88.
- **D56** A dashboard is a built web front end behind one data module — `write-entry-points`.
- **D67** A `PreCompact` hook says what a compaction keeps.
- **D68** An API is earned; a small read-only one on Cloudflare Workers Free — `deploy-project`.
- **D69** Candles are ECharts' candlestick series — `design-interface`.
- **D71** An event job rations its pushes — `send-messages`.
- **D72** The `PreCompact` text holds to 65 words.
- **D86** Stale is one period plus a margin when an alert watches — `run-unattended`; provisional, one project.
- **D87** A punctual run triggered by a Cloudflare Worker's Cron Trigger — `deploy-project`; not run live; provisional, one project.
- **D89** `design-interface` covers every surface a person meets.
- **D90** `design-pipeline` settles each table's grain, key, layer, load and freshness before the store.
- **D96** The missing-plugins rule ends with a check against the map.
- **D97** `write-typescript` in `write-code`.
- **D98** TypeScript 7, oxlint, Prettier — `write-typescript`.
- **D99** Every `tsconfig` strict with named extra checks — `write-typescript`.
- **D100** Outside values `unknown` until Zod checks them — `write-typescript`.
- **D101** TanStack Query, React Compiler on — `write-typescript`.
- **D102** Named exports, kebab-case files, no barrels — `write-typescript`.
- **D103** A Worker's `Env` from `wrangler types`, tested with `@cloudflare/vitest-plugin` — `deploy-project`.

## Delivery

### Verification

Each line's dated results are in [`verification.csv`](verification.csv); the map below grades each stage from them and from the trial projects' own records.

- **R1** — a trial build from one prompt, run as a cloud session, returns a branch whose CI passes and whose diff the owner accepts, or names the one step it needs.
- **R2** — a trial plan's best-in-class lines and ideas, and its evaluator passing every surface.
- **R3** — a cloud session refusing an off-list host and another repository, the default branch's protection holding, the permission template's denies, an outside attack, an attended private-data trial, the secret scan.
- **R4** — `validate --strict`, every trigger case, each plugin alone, a build on a subset.
- **R5** — each graded cell against its last recorded result; the three records present.
- **R6** — each map row above *designed*, or an issue or reason.
- **R7** — each run within its limit, each sweep within budget (`costs.csv`), each file and description within its figure.
- **R8** — each open issue in a cell; an improvement measured against the control (issue 150).
- **R9** — the report's owner part on one screen; the backlog line current.

**Coverage map.** Rows are a project's stages, so R6 is read from the rows; each cell names what delivers it and its grade.
**S** seen once, **R** repeated on a second kind of project, **F** failing at its last recorded result, **D** designed only, **G** a gap and its issue, **—** not wanted yet (note below).
Runs: **T1** nightly pipeline (M4, 2026-11-10); **T2** dashboard over its store (M18, 2026-11-12); **T3** three evaluated dashboard builds (2026-11-12); **T4** public scheduled pipeline with alerts, acceptance run 2026-11-19 at `ab59d13` (its own R1, R2, R4 and Acceptance failed; R8, R10, R12, R15 and R18 not run; coverage passed); **T5** each plugin alone (2026-11-11, 2026-11-21); **T6** to **T9** launcher and guard runs, uncited since D138; **T10**, **T11** throwaway cloud sessions in the owner's public sandbox repository, T11 with the shipped hook.
T4's grades are read by script from the last row per line of its `verification.csv`; T1 and T2 predate the records, so theirs rest on the dated milestone notes until their next run (`review-plugin`, Check the coverage map).

| Stage | R1 | R2 | R3 | R4 | R5 | R7 | R8 | R9 |
|---|---|---|---|---|---|---|---|---|
| Frame | S autonomous plan T2 | R frame wider T1 T2; D outside plugins | R classes T1 T4 | S alone T5 | R sources T1 T2 | S Opus plan T2 | R docs read T1 T2 | D |
| Plan | S unsigned T2 | S best in class T3; G top model for plans 168 | S classes T4; D threat model | S alone T5 | R Verification lines T1 T2 | D budget line | S kept current T4 | D size rule |
| Design | D | S design system T3; G medium's conventions 159 | D loopback guard | S alone T5 | D grain, key | D run cost | S pick changed (D69) | — (1) |
| Build | D pinned plugins loaded, branch back T11, a probe; D finish by the owner's diff | S evaluator T3 | D cloud VM refused an off-list host T10, another repository's API refused, git push untested; D binding branch rule; D permission rules | S alone T5; G subset 152 | S coverage T4; G figures 153 | S Sonnet, `costs.py` T2 | R feedback mid-build T1 T4 | D |
| Verify | S review T2; G 181 | S cold read T3 | S secret check, sweeps (T4's R8 not run) | S alone T5 | F Acceptance and R1, R2, R4 failed, five not run T4; G debugging 148 | S `costs.py` T4 | D pick challenged | D |
| Deploy | D deploy after the owner's merge; G from afar 155 | F dashboard slick and fast T4 (R4) | S deployed at no cost T4 (R6) | S alone T5 | F scheduled slot did not fire T4 (R2) | S free tier T4 (R6); D bill read | S tiers re-checked | — (1) |
| Operate | F nightly fetch with no machine on T4 (R1, R2); G after failure 151 | D stale alert (T4's R12 not run) | D rotation; G 151 | S alone T5 | D stale threshold (D86) | D usage read | G update cadence 151 | — (1) |
| Undo | G 156 | — (2) | D a person confirms each delete; G 156 | G 156 | G 156 | — (2) | — (2) | — (2) |
| Retire | — (3) | — (3) | D revoke first | D alone | D removal confirmed | D billing stopped first | — (3) | — (3) |
| Improve the plugins | S weekly sweep | D outside skills | R no connectors, no project data, sweeps | S shared rules T5; G versions 152 | S records (sweep 13); G control 150 | S budgets per sweep | S issues closed by run; G improvement 150 | D; G output styles 160 |

1. No decision for the owner arises here beyond the plan's.
2. Earned once a project can be rolled back or restored (issue 156).
3. Every teardown step is outward and confirmed one by one (D80).

Issue 71, trading, waits for its first project (Not yet).



**Kinds of project built so far.**

| Kind | Status | Evidence |
|---|---|---|
| Nightly Python pipeline over licensed data, local store | built and reviewed, local | T1 |
| Dashboard over that store, FastAPI and React | built and reviewed, local | T2, T3 |
| Public scheduled pipeline with alerts | deployed; acceptance failed R1, R2, R4 and Acceptance | T4 |
| Static dashboard; private data over Tailscale; a read-only real account | not yet | M21, M22, M20 |
| TypeScript front end or Worker; intraday; an uncovered language | designed | D97, D87, D90, D105 |

### Milestones

M1 to M18 are done (2026-11-08 to 12; git history has them); M16 tagged `v0.1`.
Sweeps are not milestones; their order is the `Next` list.

- [ ] **M21 Third trial build, public and deployed** — R1, R6, R7; done when a public-data project runs from one prompt with a scheduled pipeline, a store and a hosted dashboard, its acceptance run passing every line.
- [ ] **M22 Fourth trial build, private path** — R3, R6; private data on the owner's machine, reached over Tailscale, nothing public; after M21.
- [ ] **M20 Fifth trial build, over a real account** — R3, R1; a read-only credential, autonomous, nothing `secure-project` forbids; after M22.
- [ ] **M19 Grow the scope as earned** — R6, R2; standing.

**Next**, in order:

1. The owner's blind ranking of the control build's three arms, run 2026-11-22 (issue 150).
2. The control brief rerun on sweep 17's pin, read for `build-project` loaded and a fresh review before the report (D142, D143).
3. A full sweep ending in an outside review on the top model at maximum effort, which the owner asked for before the intraday trial.
4. The intraday trial (D90), on the owner's go.
5. Issues 153, 159 and 160.
6. Then 148, 151, 155, 156 and the rest, in the order the map's gaps rank them.

Private-data and real-account trials (M22, M20) are attended for now (D138).

## Open

### Assumptions

- **A2** The cloud sweep cannot use GraphQL or reach most vendor pages, so the free-tier re-check runs locally.
- **A3** Every machine these go on allows a third-party marketplace; unchecked machine by machine.
- **A4** Dropped with the guard (D138).

### Questions

- **Q9** Once MotherDuck takes the current DuckDB client, replace a project's two stores with one DuckLake? — recommended: yes, trialled in the next such project.
- **Q11** Which technology makes slick, fast dashboards? — recommended: D56; blocks M21's dashboard.
- **Q13** Accept R9 Legible and the sign-off by exception it implies? — recommended: yes; the alternative keeps every decision waiting for a full read.
- **Q14** R3 says "enforced, not only advised", while D138 says the plugins enforce nothing: reword R3 to "enforced by the vendor's controls the skills configure", or reverse D138? — recommended: reword.

**Unsigned backlog** (R9): 50 proposed decisions (D54 to D60, D82 to D132 bar the 15 D138 superseded, D139 to D145) and D138, decided under delegation, D61's `author.name` sentence, R9, the dated amendments to D9, D12 and D40, and the map; the oldest, D54, dates from 2026-11-12.

### Ideas

I1, I2, I4 cut 2026-11-22.

- **I3** An expected cost per stage in a plan's Runs on.
- **I5** A container or virtual machine around a whole unattended run; now the cloud session of D138.
