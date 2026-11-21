# claude

A marketplace of Claude Code plugins that let Claude do impressive projects entirely autonomously and securely, from a short prompt to a retired project, with each plugin detachable from the rest.

Records: [`DEPENDENCIES.md`](DEPENDENCIES.md), [`costs.csv`](costs.csv), [`verification.csv`](verification.csv).

Signed off by the owner: R1 to R8 (2026-11-21, issue 157), D1 to D53 (2026-11-12), D61 bar its `author.name` sentence (2026-11-13), D62 to D70 (under the owner's delegation, 2026-11-19) and D71 to D81 (2026-11-20).
Everything else is proposed: R9, D54 to D60, D82 onwards, the amendments dated 2026-11-21, the coverage map, the Design's text and the Not yet list.
The unsigned backlog is counted under Open.
Test logs and long rationale live in the pull request or skill each decision points at; this file keeps one line per decision.

## Brief

### Goal

The owner's aim, in their words: "I want these plugins to let claude do impressive projects entirely autonomously and in a secure way. and for different plugins to be detachable."
Claude gets one prompt and delivers a project that is elegant, correct and well tested, designed beyond the brief, planned, deployed, run and retired as well as coded; the plugins settle recurring decisions in advance and find and fix their own gaps.
Done looks like: every row of the coverage map graded *repeated* or deliberately left out, two trial builds of different kinds run through the launcher from one prompt with nobody present and leaving `review-project` no defect, each plugin shown to work installed alone, and a change shown to improve a build against a fixed control (issue 150).

### Terms

- **skill** — a `SKILL.md` with any `references/` and `scripts/`.
- **plugin** — a folder under `plugins/`, installable alone; the repo is a **marketplace** of six.
- **always-on file** — a plugin's `hooks/context.md` or `hooks/shared.md`, or an instruction file: paid for in every session and subagent.
- **sweep** — one `review-plugin` run: the open skill feedback, every drift check, the outside review, landed as one pull request.
- **trial build** — a real project built with the plugins to test them.
- **launcher** — `build-project`'s `scripts/launch.py`: it starts an unattended run under the **run profile** (settings that give it less than the owner has), proves the profile with a **preflight** and accepts a finish only through its **gate**.
- **standing grant** — a project's `grant.json`, approved in advance by the owner.
- **guard hook** — `manage-project`'s `PreToolUse` hook: it asks before, or unattended refuses, what cannot be undone.
- **autonomous mode** — no user present: answers assumed, decisions proposed, no outward action the grant does not allow.
- **outward action** — creating a repository, publishing, deploying, messaging, spending or moving money, or acting on an account.

### Requirements

The owner named R1 to R8 as the qualities every plugin, skill and project is judged by; R9 is proposed.
Each states the result that would show it failing, and what it costs.

- **R1 Autonomous** — one prompt, nobody present, start to finish; a stopped run resumes, an overspending one stops, and the owner learns which.
  - Fails when a launcher run waits on a question, ends `finished` without the launcher's gate, or takes an outward action its grant does not make possible.
  - Cost: unsigned plans, outward steps that wait, a launcher and profile for every run.
- **R2 Impressive** — best-in-class design and ideas beyond the brief, not boxed in by this plugin set.
  - Fails when a trial plan lacks a best-in-class line per surface or an idea beyond the brief, or its evaluator still fails a surface after three rounds.
  - Cost: longer plans and gates, a research step, outside plugins vetted.
- **R3 Secure** — safe with data, credentials and money, enforced, not only advised; no secret or project data in the public repo.
  - Fails when the preflight lets a probe through, an attack passes a profile deny or the approved grant, a secret or project data reaches the repo or a tracker, or a money-moving connector call runs unconfirmed.
  - Cost: a class per input and output, a security step per gate, the guard before every tool call, a profile narrower than the owner.
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
  - Cost: a hand-off per stage, a ledger per project, the launcher's limit, the budget table.
- **R8 Adaptive** — the plugins find and fix their own gaps, keep up with tools and prices, and show a change improved things.
  - Fails when a feedback issue survives two sweeps unsettled and unmapped, or a change is called an improvement without a run against the control (issue 150).
  - Cost: hooks, a weekly sweep, trigger suites, claims re-checked, a control build.
- **R9 Legible** *(proposed, D125)* — what the owner must read and decide after a run or sweep fits on one screen; sign-off is by exception; the unsigned backlog is tracked.
  - Fails when a report's part for the owner runs past one screen (about 40 lines), the plan calls something signed that the owner did not sign, or the backlog line under Open is stale.
  - Cost: detail deferred to the pull request; decisions stand as proposed until read.


### Not yet

- **A repository per plugin** — earned by different visibility or another owner (D30).
- **A listing in the plugin directory, icons; `agents/`, `commands/`, `rules/`; Slack; an `advisor` step** — none earned yet.
- **Toolchain skills other than `uv`, references for languages beyond Python and TypeScript, more SQL dialects** — each earned by the first project that needs it, which looks first for an outside plugin (D97, D105).
- **A debugging skill** — issue 148.
- **A skill for architecture across components** — earned by a seam decided badly that `make-decisions` missed (D104).
- **CI, snapshot or mutation tests, a task runner, Docker, docs generation** — each earned by the first project that needs it; a container around a run is I5.
- **A plugin per domain** — a domain skill starts in its project and is promoted once a second repository needs it; issue 71 holds trading.
- **Asking the owner one question from afar mid-run** — designed (D112), issue 155.
- **A browser inside an unattended run on macOS** — earned once one starts inside the sandbox (D117).

## Design

### Inputs

- **The owner's conversations and corrections** — the requirements and most rules.
- **Skill-feedback issues** — labelled `skill-feedback` on the repository each `plugin.json` names; public, so they carry a case's shape, never a project's data.
- **Current tool docs and releases** — every skill claim is checked against them each sweep.
- **Trial builds and their records** — each files feedback and grades the coverage map from its own `verification.csv`.

### Data flow

1. **Skill source** — edited in a sweep or by the owner. (IO)
2. **Wiring** — installed plugins with `installed.md`, or the symlink route with `symlinked.md`, never both. (IO)
3. **Loading** — descriptions and always-on files in every session and subagent; the guard before every tool call.
4. **Applying** — real work elsewhere; unattended runs through the launcher.
5. **Feedback** — a skill that steers wrong becomes an issue. (IO)
6. **Sweep** — issues, checks and the outside review in one pull request, whose merge loops to stage 1.

### Outputs

- **Skills and their scripts** — `costs.py`, `launch.py`, `guard.sh`, `guard.py`, `grant.py`, each with tests.
- **Each plugin's wiring** — manifest, `hooks/` and `evals/`.
- **`.claude-plugin/marketplace.json`**, **`skills/`** symlinks, **`instructions/`**, **`README.md`**, this plan and its three records.

### Interface

```bash
claude plugin marketplace add "henrymckay/claude#$(git ls-remote --tags --refs --sort=-version:refname https://github.com/henrymckay/claude.git 'v*' | head -n 1 | cut -d/ -f3)"
claude plugin install manage-project@henrymckay
```

An unattended build, from the project's folder:

```bash
uv run --script <manage-project>/skills/build-project/scripts/launch.py prompt.md --budget-usd 20 --gate-command "uv run pytest -q" --commit-as "Name <noreply address>"
```

It prints one line, `finished`, `blocked`, `limit` or `failed`, and exits 0, 3, 4 or 5; `--preflight-only` proves the profile and starts nothing.

| Plugin | Skills | Ability, and its cost |
|---|---|---|
| `manage-project` | `plan-project`, `build-project`, `review-project`, `retire-project`, `choose-model`, `make-decisions`, `secure-project`, `use-git`, `write-markdown` | A project's plan, build, review and retirement, the launcher and the guard; a subagent hand-off per stage |
| `design-project` | `design-interface`, `design-pipeline` | What a project shows and holds, before it is built; a sixth plugin to install |
| `write-code` | `be-functional`, `be-oop`, `write-python`, `write-typescript`, `write-sql`, `write-tests`, `use-polars` | The code's house style, toolchain-free; picks re-checked each sweep |
| `structure-app` | `setup-python`, `structure-python`, `write-entry-points` | A Python application's set-up and shape; the one plugin tied to `uv` |
| `run-project` | `store-data`, `run-unattended`, `deploy-project`, `send-messages` | Life after the build; free tiers that change yearly |
| `maintain-plugin` | `review-plugin`, `write-skills` | Author and sweep any plugin; a feedback destination per install |

### Runs on

- **The skills** — the owner's machine, the six plugins installed from the repo as a local marketplace; another machine installs a release or symlinks.
- **The weekly sweep** — a Claude Code cloud scheduled task on Opus, cloning the public repo and opening one pull request, with no connectors; its identifier stays out of this public file.
- **The hooks** — `maintain-plugin`'s `Stop` hook and `manage-project`'s guard, about 0.1 to 0.4 seconds a call; merged by hand under the symlink wiring.
- **An unattended run** — the owner's machine, started by the launcher, its folder under `~/.cache/claude-runs/`; the sandbox needs macOS, Linux or WSL2.
- **Threat model** — a hook runs as a shell command and a skill as instructions, so every change lands by reviewed pull request (D2, D24) and an install pins a release (D41); the repo holds no credential; an unattended run's boundary is the run profile plus the approved grant, proved by the preflight, and the guard's patterns are defence in depth, its bypass cases kept in its tests.
- **Unattended runs** — trial builds start through the launcher; this repo grants nothing, so a run here takes no outward action.

### Errors

- **A description misfires, a rule drifts or a file outgrows its budget** — found by the sweep and fixed where the rule belongs; feedback holding project data is edited on sight.
- **The guard asks about an ordinary command** — approve it and file the case; set `guard` to `off` meanwhile if it keeps asking.
- **The guard misses a dangerous call** — file its shape; the run profile, not the guard, is the boundary.
- **The preflight refuses a run** — read `status.json`; a Claude Code update that opened the profile is fixed in the launcher before any run.
- **An unattended run needs more than its profile gives** — it ends `blocked` naming what it needs.

### Decisions

Numbers are stable; each line is the choice, what it beat, and where the evidence lives.

**Budgets** (D54, amended by D81, D91, D95, D106, D115, D125, D128; figures in words unless marked):

| Item | Budget | Now |
|---|---|---|
| `instructions/installed.md` | 180 | 176 |
| `instructions/symlinked.md` | 1,055 | 1,050 |
| `hooks/shared.md`, each copy | 380 | 377 |
| `manage-project`'s context file | 170 | 167 |
| `write-code`'s context file | 80 | 75 |
| Every other context file | 70 | 59 at most |
| `hooks/compact.md` (D72) | 65 | 65 |
| `README.md` | 980 | 977 |
| `PLAN.md` (D125: about 5,000) | 5,500 | 5,499 |
| A skill description | 500 characters | all under |
| A sweep, build and checks | $40 | `costs.csv` |
| A sweep's outside review | $25 | `costs.csv` |
| The launcher's preflight | $0.05 a run | about $0.01 |

**The repository and its wiring**

- **D1** Symlinks into `~/.claude` stay a supported wiring beside installed plugins.
- **D2** Commit as the owner's no-reply identity; a sweep lands by pull request; overrides `use-git`, Branches.
- **D9** No performance budget. *Amended 2026-11-21 (proposed): hooks and the launcher now run; their time and cost are in the budget table.*
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
- **D95, D106, D115** Budgets after the instruction-file split and later additions; figures in the table.
- **D129** *(proposed)* The root `CLAUDE.md` link is removed: the owner's link points at `installed.md`, and the link loaded the skill list twice here; completes D94.

**How a project runs**

- **D5** `review-project` general, `review-plugin` layered on it.
- **D6** `build-project`, over `develop-project`.
- **D13** A skill's default is a default; a signed decision overrides it, a reason Claude finds is a proposed decision.
- **D14** Decisions surfaced with alternatives, costs and sources.
- **D26** A sweep outcome "needs the user" for policy.
- **D35** Autonomous mode: answers assumed, decisions proposed, no outward action; amended by D111, D123.
- **D46** Settle an open question from precedent, escalating only what `make-decisions` lists.
- **D47** `secure-project` in `manage-project`, private by default; nothing moves money without a signed decision and a person confirming.
- **D52** A named method plugin leads; the convention skills still apply.
- **D57** Every shipped surface aims at the best in class.
- **D58** An evaluator pass in the gate, up to three rounds.
- **D59** The ladder holds when a prompt calls the work small.
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
- **D125** *(proposed)* A plan holds to about 5,000 words with a `Next` list, one line per decision and one budget table, cut without waiting for sign-off, over the 17,000 words this one reached; adds R9; `plan-project`; issue 165.

**Running unattended**

- **D108** A guard hook in `manage-project`, on by default, asking a person present and refusing when nobody is, over permission rules alone; Python 3.9 and named tuples for that script, overriding `write-python`; `secure-project`, PR 161.
- **D109** An unattended run starts under the run profile, over the owner's settings, `--bare` or a container; `build-project`, PR 161.
- **D110** The launcher starts, resumes and bounds a run by spend and turns read from records the run cannot write; PR 161.
- **D111** A standing grant is `grant.json`, used only as the owner approved its SHA-256 for that project; amends D35; amended by D123.
- **D112** Asking the owner one question from afar is designed and not built (issue 155).
- **D116** *(proposed)* Local binding opt-in per run (`--allow-local-binding`), over always on: on macOS it opens every localhost service and nothing narrower exists (code.claude.com/docs/en/sandboxing, 2026-11-21); a Haiku shakedown served, fetched, reached PyPI and stored with it.
- **D117** *(proposed)* No browser in an unattended run, over opening `~/Library` to writes: on macOS Chrome fails inside the sandbox, so the evaluator's screenshots wait for an attended session; two Haiku runs.
- **D118** *(proposed)* A preflight before every run — Haiku tries forbidden things on decoys, the launcher puts to the guard what a model declines — refusing to start on anything through, untried, unfinished or a connector loaded; about $0.01; the sandbox's own keychain refusal untested; `build-project`.
- **D119** *(proposed)* The run folder sits inside the home folder, since the sandbox lets commands write to temp folders; the preflight found it.
- **D120** *(proposed)* `finished` is the launcher's gate, not the model's line: records read as data, and `git status` and the gate commands run in a sandboxed Haiku session, so after a run the launcher executes nothing from the project; a real false `finished` was refused and ended `blocked`.
- **D121** *(proposed)* The usage window is waited out by Claude Code's retry watchdog up to `--usage-wait-hours`, over fixed retries (code.claude.com/docs/en/errors, 2026-11-21); not met live.
- **D122** *(proposed)* `status.json` records the Claude Code version, the release, the preflight and the probe cost.
- **D123** *(proposed)* Grant approval shows a plain summary and needs `y` or `--yes`; a field no script enforces is refused, so account `actions` and limits leave the format and a secret's scope is the real limit; amends D111.
- **D124** *(proposed)* The guard asks before, or unattended refuses, a connector call that trades, moves money, sends or shares, from its name and its arguments read as data; issue 164.

**Models**

- **D27** The model ladder, each stage handed to a subagent with its model set — `choose-model`.
- **D42** No skill names a model in its frontmatter; amended by D82.
- **D70** A build milestone with a visible surface stays on Sonnet: $5.45 against $10.75 on Opus for one plan, both passing.
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
- **D81** Budgets raised for the tenth skill; in the table.
- **D86** Stale is one period plus a margin when an alert watches — `run-unattended`.
- **D87** A punctual run triggered by a Cloudflare Worker's Cron Trigger — `deploy-project`; not run live.
- **D89** `design-interface` covers every surface a person meets.
- **D90** `design-pipeline` settles each table's grain, key, layer, load and freshness before the store.
- **D91** Budgets for the sixth plugin; in the table.
- **D96** The missing-plugins rule ends with a check against the map.
- **D97** `write-typescript` in `write-code`.
- **D98** TypeScript 7, oxlint, Prettier — `write-typescript`.
- **D99** Every `tsconfig` strict with named extra checks — `write-typescript`.
- **D100** Outside values `unknown` until Zod checks them — `write-typescript`.
- **D101** TanStack Query, React Compiler on — `write-typescript`.
- **D102** Named exports, kebab-case files, no barrels — `write-typescript`.
- **D103** A Worker's `Env` from `wrangler types`, tested with `@cloudflare/vitest-plugin` — `deploy-project`.

**Superseded**

- **D8** Evaluation briefs archived outside this repo — by D40.

## Delivery

### Verification

Each line's dated results are in [`verification.csv`](verification.csv); the map below grades each stage from them and from the trial projects' own records.

- **R1** — a trial build through the launcher from one prompt ends `finished` through the gate, or `blocked` on one step.
- **R2** — a trial plan's best-in-class lines and ideas, and its evaluator passing every surface.
- **R3** — the preflight on the current Claude Code, the guard's suite, an outside attack, a private-data trial, the secret scan.
- **R4** — `validate --strict`, every trigger case, each plugin alone, a build on a subset.
- **R5** — each graded cell against its last recorded result; the three records present.
- **R6** — each map row above *designed*, or an issue or reason.
- **R7** — each run within its limit, each sweep within budget (`costs.csv`), each file and description within its figure.
- **R8** — each open issue in a cell; an improvement measured against the control (issue 150).
- **R9** — the report's owner part on one screen; the backlog line current.

**Coverage map.** Rows are a project's stages, so R6 is read from the rows; each cell names what delivers it and its grade.
**S** seen once, **R** repeated on a second kind of project, **F** failing at its last recorded result, **D** designed only, **G** a gap and its issue, **—** not wanted yet (note below).
Runs: **T1** nightly pipeline (M4, 2026-11-10); **T2** dashboard over its store (M18, 2026-11-12); **T3** three evaluated dashboard builds (2026-11-12); **T4** public scheduled pipeline with alerts, acceptance run 2026-11-19 (R2 and coverage failed, four lines not run); **T5** each plugin alone (2026-11-11, 2026-11-21); **T6**, **T7** sweeps 12 and 13's launcher and guard runs (2026-11-21).
T1 and T2 predate the records, so their grades rest on the dated milestone notes until their next run (`review-plugin`, Check the coverage map).

| Stage | R1 | R2 | R3 | R4 | R5 | R7 | R8 | R9 |
|---|---|---|---|---|---|---|---|---|
| Frame | S autonomous plan T2 | R frame wider T1 T2; D outside plugins | R classes T1 T4 | S alone T5 | R sources T1 T2 | S Opus plan T2 | R docs read T1 T2 | D |
| Plan | S unsigned T2 | S best in class T3; G top model for plans 168 | S classes T4; D threat model | S alone T5 | R Verification lines T1 T2 | D budget line | S kept current T4 | D size rule |
| Design | D | S design system T3; G medium's conventions 159 | D loopback guard | S alone T5 | D grain, key | D run cost | S pick changed (D69) | — (1) |
| Build | S gate refuses a false finish T7; D full launcher build | S evaluator T3 | S profile, guard T6 T7 | S alone T5; G subset 152 | F coverage T4; G figures 153 | S Sonnet, `costs.py` T2 | R feedback mid-build T1 T4 | D |
| Verify | S review T2 | S cold read T3 | R secret check T4, sweeps | S alone T5 | F four lines not run T4; G debugging 148 | S `costs.py` T4 | D pick challenged | D |
| Deploy | D grant remotes T6; G from afar 155 | D static dashboard | S host from class T4 | S alone T5 | S schedule fired T4 | S free tier T4; D bill read | S tiers re-checked | — (1) |
| Operate | F without the owner's machine T4; G after failure 151 | S stale alert T4 | D rotation; G 151 | S alone T5 | S stale threshold T4 | D usage read | G update cadence 151 | — (1) |
| Undo | G 156 | — (2) | D guard refuses deletes T6 T7; G 156 | G 156 | G 156 | — (2) | — (2) | — (2) |
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
| Public scheduled pipeline with alerts | deployed; acceptance failed R2 and coverage | T4 |
| Static dashboard on GitHub Pages; private data over Tailscale; a real account read-only | not yet | M21, M22, M20 |
| TypeScript front end or Worker; intraday pipeline; an uncovered language | designed | D97, D87, D90, D105 |

### Milestones

M1 to M18 are done (2026-11-08 to 12; git history has them); M16 tagged `v0.1`.
Sweeps are not milestones; their order is the `Next` list.

- [ ] **M21 Third trial build, public and deployed** — R1, R6, R7; done when a public-data project runs from one prompt with a scheduled pipeline, a store and a hosted dashboard, its acceptance run passing every line.
- [ ] **M22 Fourth trial build, private path** — R3, R6; private data on the owner's machine, reached over Tailscale, nothing public; after M21.
- [ ] **M20 Fifth trial build, over a real account** — R3, R1; a read-only credential, autonomous, nothing `secure-project` forbids; after M22.
- [ ] **M19 Grow the scope as earned** — R6, R2; standing.

**Next**, in order:

1. This sweep (13): the launcher's preflight and gate, the connector guard, this plan, the outside review step, the records.
2. The third trial's acceptance re-run through the launcher, with no deploy rights in its grant.
3. The control build (issue 150), with issue 152's subset arm.
4. The intraday trial (D90).
5. Issues 153, 159 and 160.
6. Then 148, 151, 155, 156 and the rest, in the order the map's gaps rank them.

## Open

### Assumptions

- **A1** The repository and marketplace keep their names (D62).
- **A2** The cloud sweep cannot use GraphQL or reach most vendor pages, so the free-tier re-check runs locally.
- **A3** Every machine these go on allows a third-party marketplace; unchecked machine by machine.
- **A4** `claude -p` keeps marking a session unattended for hooks (undocumented); if not, the launcher's `CLAUDE_GUARD=deny` still holds.

### Questions

- **Q9** Once MotherDuck takes the current DuckDB client, replace a project's two stores with one DuckLake? — recommended: yes, trialled in the next such project.
- **Q11** Which technology makes slick, fast dashboards? — recommended: D56; blocks M21's dashboard.
- **Q13** Accept R9 Legible and the sign-off by exception it implies? — recommended: yes; the alternative keeps every decision waiting for a full read.

**Unsigned backlog** (R9): 56 proposed decisions (D54 to D60, D82 to D130), D61's `author.name` sentence, R9, the dated amendments to D9, D12 and D40, and the map; the oldest, D54, dates from 2026-11-12.

### Ideas

- **I1** A `doctor` command that validates, runs the hooks and names missing siblings; partly met by the built-ins.
- **I2** A run log per build; mostly met by `costs.csv` and the run folder.
- **I3** An expected cost per stage in a plan's Runs on.
- **I4** More rules in hooks, each earned by a slip one could catch (issue 53).
- **I5** A container or virtual machine around a whole unattended run.
