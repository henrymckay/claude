# claude

A marketplace of Claude Code plugins that let Claude design, build and run a project end to end from a short prompt, and that improve themselves as they are used.

Signed off by the user on 2026-11-12 (Q1), except the lines marked *(proposed)*.
The security policy (R13, D47, `secure-project`) stays open to refinement as real projects reach it.

## Brief

### Goal

Claude gets a short prompt and delivers a project that is elegant, efficient, correct and well tested, designed beyond the brief and named in its domain's language, with the planning, deployment and upkeep done as well as the code.
The plugins settle in advance the decisions that recur across projects, so Claude neither asks nor re-decides them; since no such set is ever complete, they also let Claude find and fix their own gaps.
Done looks like: two trial builds of different kinds, each run in autonomous mode from one prompt and leaving `review-project` no defect, and each plugin shown to work installed alone.

### Terms

- **skill** — a `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter, plus any `references/`, per the Agent Skills standard.
- **plugin** — a folder under `plugins/` with a manifest, skills, a session-start hook and a trigger suite, named verb-first and installable alone; the repo is a **marketplace** of five.
- **context file** — a plugin's `hooks/context.md`, its always-on skill list, printed at session start.
- **description** — a skill's frontmatter trigger text, all Claude sees when deciding to load it.
- **reference** — a file under a skill's `references/`, loaded only when the skill points there.
- **always-on file** — `CLAUDE.md` or a context file: read, and paid for, in every session.
- **house pick** — a library or tool a skill chooses over its rivals.
- **drift** — a skill's description, rules or examples falling out of line with its body, its neighbours or current tools.
- **skill feedback** — a GitHub issue labelled `skill-feedback` on the owning plugin's repository, filed when a skill steered Claude wrong in real work; a machine that must not reach a public tracker records it to a file instead.
- **autonomous mode** — a run with no user present: Claude proceeds on its recommended answers, records each as an assumption, and takes no outward action (D35).
- **outward action** — creating a repository, publishing, deploying, messaging, spending or moving money, or acting on an account.
- **the ladder** — which model and effort runs each stage (D27).
- **trial build** — a real project planned, built and reviewed with the plugins to test them, its skill feedback worked through by a sweep.
- **sweep** — one `review-plugin` run over the repo: the open skill feedback first, then every drift check, landed as one pull request.
- **trigger suite** — a plugin's `evals/` cases, one casual prompt per skill, run with `claude plugin eval` to show each description still fires.
- **data class** — public, licensed, private or personal, recorded for each input and output of a project (`secure-project`).

### Requirements

- **R1 End to end.** With every plugin installed, Claude does consistent, high-quality development projects from a minimal prompt: designed, built, reviewed and deployed.
  - Cost: every other requirement; scope held to Python data, CLI, API and dashboard projects until a project earns more.
- **R2 Autonomous.** A project runs with one batch of answers from the user, or with none (D35).
  - Cost: plans stay unsigned until read, and every outward action waits on the user.
- **R3 `manage-project`** lets Claude plan, build and review a project, each stage on the ladder's model whatever the session's default, with the git and Markdown conventions any repository needs.
  - Cost: a subagent hand-off per stage.
- **R4 `write-code`** gives Claude the house style for the code itself, toolchain-free: functional, object-oriented, Python, SQL, tests, Polars.
  - Cost: house picks the user can't verify alone, re-checked each sweep.
- **R5 `structure-app`** gives Claude a Python application's set-up and shape: the `uv` toolchain, house-pick libraries, layers, entry points.
  - Cost: the one plugin tied to a toolchain.
- **R6 `run-project`** gives Claude a project's life after the build: its data, a job nobody watches, a free or near-free host per artefact, messages to the user.
  - Cost: free tiers change yearly; the picks are one person's, so an install with its own infrastructure leaves it out.
- **R7 `maintain-plugin`** lets Claude maintain any plugin whose source it can read, on any machine: author a skill, review for drift, capture gaps; it assumes no particular repository, tracker or toolchain.
  - Cost: a feedback destination per install; a report where it cannot push.
- **R8 Self-improving.** A skill gap is captured when it surfaces, worked through on a schedule and on demand, and each fix verified by running the case; the user reviews the result, and no skill is edited mid-build.
  - Cost: a hook, a scheduled task, a trigger suite per plugin, trial builds.
- **R9 Alone or together.** Each plugin installs and works on its own, on any machine, and they work as a group; a machine that cannot install plugins symlinks them.
  - Cost: a context file per plugin, pointers that read correctly alone, releases an install can pin.
- **R10 Not boxed in.** A skill's default is a default: Claude researches, proposes ideas beyond the brief and the skills, and shows its decisions, alternatives, costs and sources for the user to challenge.
  - Cost: longer plans.
- **R11 Skills worth loading.** Each is clear, concise, consistent with its neighbours, general, and holds nothing Claude does unprompted; the always-on files stay as short as their job allows.
  - Cost: sweeps and the `write-skills` rules.
- **R12 Public.** Generic conventions only: no secrets, no project data, no machine-local state.
- **R13 Safe with private data.** A project whose data is private, or which holds a credential for an account with money in it, exposes neither without the user having to notice: the data is private until the plan says otherwise, and nothing moves money without a person confirming it.
  - Cost: a class per input and output in every plan, hosts picked from it, the owner's machine in place of the free public hosts for private data, and a security step in every gate.

### Not yet

- **A repository per plugin** — earned when a plugin needs different visibility or another owner (D30).
- **Icons, and a listing in the public plugin directory** — earned by wanting other people to find the plugins.
- **Toolchain skills other than `uv`** — they belong in the repo that uses the toolchain, as project skills or a private plugin.
- **A debugging skill** — earned when skill feedback shows debugging going wrong.
- **References for a language other than Python** — earned by the first non-Python project.
- **CI for projects** — marginal for one-machine unattended tools; earned by a second contributor or a deploy.
- **An evaluation per fixed issue** — too big; the trigger suites check that descriptions fire, and a sweep runs each issue's case.
- **Snapshot tests, mutation testing, a task runner, Docker, dev containers, docs generation** — each earned by the first project that needs it; the skills say "none" until then.
- **`agents/`, `commands/` and `rules/`** — none yet.
- **Slack as a message channel** — earned once the user has a workspace they read.
- **An `advisor` second-model step mid-task** — earned when a build stage keeps failing its gate on Sonnet.
- **More SQL dialects for `write-sql`** — earned by the first project on one; DuckDB is the only reference.
- **A plugin per domain** (accounting, tax, trading) — a domain skill starts in its project's `.claude/skills/` and is promoted to a plugin, private if need be, once a second repository needs it.

## Design

### Inputs

- **The user's conversations and corrections** — the requirements and most rules; corrections about skills arrive as skill feedback.
- **Skill feedback issues** — `gh issue list -R henrymckay/claude --label skill-feedback`.
- **Current tool docs and releases** — every skill claim is checked against the current release.
- **Trial builds** — each files skill feedback for the next sweep.

### Data flow

1. **Skill source** — `plugins/<plugin>/skills/<name>/SKILL.md`, edited only in a sweep or by the user. (IO)
2. **Wiring** — the plugins installed from the marketplace, or `~/.claude/skills` and `~/.claude/CLAUDE.md` symlinked to the repo's `skills/` and `CLAUDE.md`; never both on one machine, which loads every skill twice. (IO)
3. **Loading** — every session loads each description and the always-on files; a skill's body loads when its description or the list triggers it, a reference when the body points there.
4. **Applying** — Claude follows the loaded skills in real work in other repos.
5. **Feedback** — a skill that steers wrong becomes skill feedback on the owning plugin's repository. (IO)
6. **Sweep** — `review-plugin` works the issues, then the drift checks, and opens one pull request, whose merge loops back to stage 1.

### Outputs

- **`plugins/<plugin>/skills/<name>/SKILL.md`** and its `references/` — laid out by `write-skills`; read by Claude.
- **`plugins/<plugin>/`** — `.claude-plugin/plugin.json`, `hooks/` (the context file and its script; `maintain-plugin` adds the feedback rule and the `Stop` hook) and `evals/` (one trigger case per skill).
- **`.claude-plugin/marketplace.json`** — the five plugins by relative path.
- **`skills/<name>`** — a relative symlink to each skill, for the symlink wiring.
- **`CLAUDE.md`** — the owner's working rules, skill list and feedback rule; read by Claude every session.
- **`README.md`** — for humans: the plugins, install, configuration, feedback and trial builds.
- **`PLAN.md`** — this file.

### Interface

```bash
claude plugin marketplace add henrymckay/claude#v0.1
claude plugin install manage-project@henrymckay
```

Symlinked instead, where plugins cannot be installed or the skills are authored:

```bash
git clone https://github.com/henrymckay/claude.git
ln -s "$PWD/claude/skills" ~/.claude/skills
ln -s "$PWD/claude/CLAUDE.md" ~/.claude/CLAUDE.md
```

Skills trigger from their descriptions or by name (`/plan-project`, or `/manage-project:plan-project` when installed); "review the skills" runs `review-plugin`.

| Plugin | Skills |
|---|---|
| `maintain-plugin` | `review-plugin`, `write-skills`, the feedback rule and `Stop` hook |
| `manage-project` | `plan-project`, `build-project`, `review-project`, `choose-model`, `make-decisions`, `secure-project`, `use-git`, `write-markdown` |
| `write-code` | `be-functional`, `be-oop`, `write-python`, `write-sql`, `write-tests`, `use-polars` |
| `structure-app` | `setup-python`, `structure-python`, `write-entry-points` |
| `run-project` | `store-data`, `run-unattended`, `deploy-project`, `send-messages` |

### Runs on

- **The skills and `CLAUDE.md`** — the user's machine, with the five plugins installed from the repo as a local marketplace, which loads them in place so edits stay live, and `~/.claude/CLAUDE.md` symlinked; another machine installs a release from GitHub, or symlinks; nothing is deployed.
- **The weekly sweep** — a Claude Code cloud scheduled task (`trig_01NmQMC42vGPjqQEDE8XrgzQ`), Mondays 02:00 UTC on Opus, cloning the public repo and opening one pull request; no connectors.
- **The `Stop` hook** — carried by `maintain-plugin` (`plugins/maintain-plugin/hooks/hooks.json`); with the symlink wiring its entry is merged into `~/.claude/settings.json`.
- **The trigger suites** — `claude plugin eval` on the user's machine, or in a sweep where the CLI is available.

### Errors

- **A description fails to trigger, or fires on the wrong task** — found by `review-plugin`'s trigger-overlap check or by skill feedback; fixed in the description.
- **A rule is duplicated or contradicted** — found by `review-plugin`; kept where it belongs, pointed at from elsewhere.
- **A library claim goes stale** — found by re-running every claim against the current release each sweep.
- **A symlink dangles** — found by `review-plugin`'s wiring check.
- **An always-on file or the README grows past its budget** — found by `review-plugin`'s inventory; the file is rewritten whole (D54).
- **Feedback carries project data** — the feedback rule requires the shape of the case only; delete or edit such an issue on sight.

### Decisions

Numbers are stable; the groups are for reading.

**The repository and its wiring**

- **D30 One repo as a marketplace of five plugins** over one plugin or a repo each — an install takes some and not others, and one repo keeps one tracker, one sweep and cross-plugin drift in view; cost: a plugin needing other visibility must move out (Not yet). Source: code.claude.com/docs/en/plugins/create-marketplace.
- **D31 Five plugins, each named verb-first for the ability it gives** (the user's) — `use-git` and `write-markdown` sit in `manage-project` because any repo needs them; `uv` lives only in `structure-app`; `run-project` holds one person's free-tier picks, so an install can leave it out, and `deploy-project` sits there because its body is host picks; `choose-model` sits in `manage-project`, where three of the four skills it governs live. The validator reserves the name `claude`.
- **D1 Symlinks into `~/.claude` stay a supported wiring** for a machine that cannot install plugins; the authoring machine runs the installed plugins, so it runs what others install.
- **D32 Always-on instructions per plugin are a context file printed by a `SessionStart` hook** over a plugin `CLAUDE.md`, which Claude Code does not load; `CLAUDE.md` carries the same lines for the symlink wiring, and `review-plugin` checks they agree.
- **D34 A toolchain's commands live in the skill that owns it** — `uv` in `setup-python`, with `run-project` building on it; `manage-project` and `write-code` name a `uv` command only as that toolchain's example, so they hold under any toolchain.
- **D2 Commit as `henrymckay <henrymckay@users.noreply.github.com>`; a sweep lands by pull request, and only an edit the user makes or asks for outside a sweep goes straight to `main`** over everything straight to `main` — every skill change is reviewed in one place before it reaches an install; overrides `use-git`'s branch default for those direct edits.
- **D10 Not yet lives in this plan** over `enhancement` issues — issues are kept for skill feedback.
- **D11 The README is for humans and points at this plan** over copying it.
- **D12 Memory holds only what this plan doesn't** — the plan is visible and versioned; memory is per-machine.
- **D9 No performance budget** — nothing here runs.
- **D41 A release is a tag `v<major>.<minor>` on `main`, cut after a sweep is merged and its suites pass,** over installing from the tip — an install pins a tag, so a sweep cannot change behaviour on another machine mid-week; cost: one tag per sweep, cut by the user; overrides `use-git`, Release (a tag per milestone).
- **D43 The MIT licence** over Apache 2.0 or none — without one nobody else may use the plugins, and MIT is the one an organisation approves most readily.
- **D44 Nothing in the repo distinguishes one of the user's machines or settings from another** — the plugins are for anyone; a constraint is named for what it is (a tracker that must stay private, a toolchain other than `uv`, a marketplace that is not allowed).
- **D54 Word budgets for the top-level files** *(proposed)* — `CLAUDE.md` 900 words, each context file 325 (`manage-project`'s 410), the README 800; `PLAN.md` has none, but its decisions keep the shape decision, alternative, cost, source — over no budget, under which `CLAUDE.md` grew ninefold one sentence at a time (issue 69); cost: an addition must say what it removed, and a file near its budget is rewritten whole rather than patched (`review-plugin`).

**How a project runs**

- **D13 A skill's default is a default** — a signed-off `PLAN.md` decision overrides a skill; a reason Claude finds is a proposed decision, raised before it is built on (in autonomous mode, recorded and built on); a rule stays imperative with its exception in the same sentence, because softened rules were ignored outright.
- **D14 Decisions are surfaced, not buried** — `plan-project`'s one batch lists Claude's decisions with alternatives, costs and sources beside the questions and assumptions; build and review reports list the calls made.
- **D35 Autonomous mode** — with no user present, Claude proceeds on its recommended answers, records each as an assumption, keeps decisions proposed and takes no outward action; `plan-project` defines it, `build-project` and `review-project` state it; skill feedback is still recorded as the feedback rule says.
- **D5 `review-project` general, `review-plugin` layered on it** over two independent reviews — one set of review mechanics.
- **D6 `build-project`** over `develop-project` — matches "the build" across the skills.
- **D26 A fourth sweep outcome, "needs the user"** — an unattended run never changes a decision or settles policy; it leaves the issue open with a recommended answer.
- **D46 Settle an open question from precedent** (`make-decisions`, in `manage-project`) over every gap becoming a question or a proposed decision, which left the first autonomous build with more calls than the user could read — cite the nearest answered decision, mark the call *(by precedent)*, report those as a count, and escalate only the irreversible, outward-facing, costly, security-touching or unprecedented.
- **D47 `secure-project` in `manage-project`, private by default,** over a section of `deploy-project` or a sixth plugin — every project needs it whatever its hosts, and `run-project` is the plugin an install is likeliest to leave out; an input or output with no class is private, licensed data under personal-use terms is private, a looser class is the user's call, a loopback server checks `Host` and `Origin`, and nothing that moves money happens without a signed-off decision and a person confirming each action, never in autonomous mode; cost: the security step in every gate (R13); open to refinement.
- **D52 Another method plugin driving takes the lead** over this family winning silently — where the user or the project names another plugin's method (one that plans, builds or reviews, such as `superpowers`), `plan-project`, `build-project` and `review-project` stand down unless named, the convention skills still apply, and `plan-project` takes a brainstorming or design skill's output as its input rather than replacing it; cost: a line in `manage-project`'s context file and `CLAUDE.md`, and one in `plan-project`. Source: issue 54's trials beside `superpowers` 7.0.2, where the prompt's wording, not a rule, decided which plugin led.

**The feedback loop**

- **D3 Skill feedback as GitHub issues** over memory or a notes file — visible to the user, closable from a commit, not per-machine.
- **D4 The filing rule is always on** (`CLAUDE.md`, or `maintain-plugin`'s hook) over a skill — a skill loads only for a matching task, and feedback arises mid-task in any work.
- **D33 Feedback goes to the owning plugin's repository**, read from its manifest or named in the user's `CLAUDE.md`, over a repository written into the skills; `maintain-plugin`'s `feedback` option (`issues`, `file`, `off`) redirects it on a machine whose work must not reach a public tracker.
- **D25 A `Stop` hook prompts for unfiled skill gaps** — the only hook that can reach the model, since `SessionEnd` cannot.
- **D24 Every sweep lands as one pull request**, scheduled or run in a session, over a session sweep committing to `main` — the pull request is where a sweep is reviewed.
- **D45 The coordinating session reviews and merges a sweep's pull request** over the user merging every sweep or the sweep merging its own — the sweep opens it and stops, and the coordinator checks the report against the branch and merges; cost: a rule change the user never reads unless the report flags it, which is why every rule cut, generalised or left is listed there.
- **D28 The weekly sweep runs on Opus with no connectors** — skill edits are reasoning work, and a connector acting as the user is a risk the sweep doesn't need.
- **D23 A trigger suite per plugin at `plugins/<plugin>/evals/`**, the folder `claude plugin eval` reads, over one suite at the root — an eval run targets one plugin.
- **D39 A requirement is verified by behaviour** over by a skill existing — the ladder's milestone was once ticked when `choose-model` was written, and the first trial build then ran on the wrong model; each Verification line names a run and what it must show.
- **D40 No brief-and-answers evaluations** over the `evaluate/` folder — trial builds and the trigger suites do its job with real feedback; replaces D8.

**Models**

- **D27 The model ladder** over one model throughout — Opus (Fable for the hardest design) at high effort for planning, reviews and skill edits; Sonnet for build milestones, cold reads and research; Haiku for graders, hooks and trigger evals. It holds whatever the session's default is: frontmatter changes the model a session is told it is on, not the one serving it (Claude Code 2.1.322, per-message transcript models), so each stage hands its work to a subagent with the model and effort set.
- **D42 No skill names a model in its frontmatter** over keeping the lines as documentation — such a line only misleads (D27); the `effort` lines stay.

**House picks**

The skill named holds the pick, its alternative and its reason.

- **D7 `be-functional` the default style, `be-oop` opt-in.**
- **D15 `functools.partial`, closures and `match`** over `toolz` and `plum`, which stay mentioned — `be-functional`.
- **D16 One error model**: raise from `error/`, convert at an adapter's seam, decide in a driver, catch nothing in the core — `write-python`.
- **D17 One record type**, the frozen, slotted, keyword-only dataclass — `write-python`.
- **D18 `uv_build`** over `hatchling` — `setup-python`.
- **D19 pyright `strict`** — `setup-python`.
- **D20 House picks for datetime, money, storage, config, HTTP, logging, plotting and test doubles**, each named with its alternative in the skill that owns it: `write-python`, `store-data`, `structure-python`, `setup-python`, `write-tests`. The dashboard pick (Shiny with Plotly, `write-entry-points` and `deploy-project`) is under review (Q11).
- **D21 `store-data` and `run-unattended` exist** because a gap probe left 72 decisions open and they absorb most.
- **D22 MotherDuck's token variable is lower case**, `motherduck_token` — `store-data`.
- **D53 A project that needs MotherDuck pins the DuckDB client MotherDuck accepts and runs on Python 3.14** over the house floor of 3.15 — MotherDuck accepts DuckDB 1.4.1 to 1.5.6, a 2.0 client's extension refuses to load, and 1.5.6 has no 3.15 wheel; cost: one project off the floor until MotherDuck supports DuckDB 2.0; overrides `setup-python`'s floor for that project — `store-data`.
- **D29 Message channels**: ntfy for an alert, email for a digest, Claude Code channels for a chat; Slack once a workspace exists — `send-messages`.
- **D36 A `write-sql` skill in `write-code`** over a section of `store-data` — decisions only (SQL against Polars, where SQL lives, style, schema changes, testing a documented query) in a dialect-neutral body with a reference per dialect, DuckDB first.
- **D37 `coverage run -m pytest`** over `pytest-cov` — the `-p` plugin in `setup-python`'s `addopts` imports the package before `--cov` measures, which read 33% for a true 83% (pytest-cov 7.1, coverage 7.17); cost: two commands where one flag did.
- **D38 A run that finds the lock held writes no manifest row** over a `skipped` row — the run in progress records the night, and a `skipped` row would exit 1 where the lock rule exits 0.
- **D48 A stored table's columns in alphabetical order, its timestamps UTC with their zone** — `store-data`, Shape a stored table; partition keys stay in the path, and the manifest and a plan's schema table follow the rule.
- **D49 A bounded catch-up window**, three days by default and set per source, over no automatic catch-up — `run-unattended`; a wider gap is reported and left for an explicit backfill.
- **D50 `sqlfluff` for SQL from a project's first `.sql` file** over `sqruff` (17 times faster on 200 files but pre-1.0) and `sqlfmt` (packs columns onto one line) — `write-sql` names it, `setup-python` wires the hook.
- **D51 Hive-partitioned Parquet stays the default; DuckLake is the table format where every reader goes through DuckDB, Delta Lake where Polars or another engine must write** — one writer's nightly output needs nothing a table format adds, and every format leaves files that read wrong without it until cleanup (DuckDB 2.0.0, DuckLake 1.1, deltalake 1.6.6, Polars 2.1.0); no format is ruled out for lacking a Polars reader, since DuckDB hands a frame over with `.pl()`; DuckLake with a MotherDuck catalog waits on D53 (Q9) — `store-data`, Pick a table format.

**Superseded**

- **D8 Evaluation briefs archived outside this repo** — superseded by D40.

## Delivery

### Verification

Each line names the run that shows it, then its status.

- **R1** — two trial builds of different kinds, each from one prompt, each leaving `review-project` no defect. **Partly**: a pipeline (130 tests; four defects fixed, six decisions left to the owner) and a dashboard over its store (M18), each planned, built and reviewed from one prompt; nothing deployed, so neither is end to end (M21).
- **R2** — a build with no user answers ends with an unsigned plan, every answer an assumption, no outward action. **Met once** (M18).
- **R3** — a stage started on a default that is not its model shows its work on the ladder's model in the transcript's per-message counts. **Met** for plan and build from either default, and in M18 for plan, review, build and cold reads.
- **R4, R5** — a trial build's review finds no stated convention broken, and files as feedback what the build decided alone. **Met once** (issues 28, 30 to 33).
- **R6** — the same for storage and scheduling; one artefact deployed to a house-pick host; one message delivered. **Partly**: local only (M21 deploys).
- **R7** — `review-plugin` on a plugin outside this repository ends in a report with no push; `maintain-plugin` alone on a second machine records feedback to a file. **Met on this machine** (M17): alone and headless, it reviewed another owner's plugin from a read-only clone into a report, and with `feedback` set to `file` appended a dated entry; the second machine waits on Q7.
- **R8** — the hook files a seeded gap; a scheduled sweep opens a pull request; a sweep closes real issues, each fix run. **Met** (issue 20; pull requests 19, 55, 63, 67).
- **R9** — `claude plugin validate` and every trigger case pass; every `skills/` link resolves; each plugin alone completes a task and names what it lacked; a GitHub install works on a second machine. **Met on this machine**: each plugin alone, headless (`--setting-sources project,local`, one `--plugin-dir`), named each missing skill with its plugin and recorded its calls as proposed, five of five in each run of the current wording; with all five loaded, none reported a plugin missing, though most runs add a line saying none was. The second machine waits on Q7.
- **R10** — a plan shows its decisions with sources and its ideas; a review can challenge a house pick. **Met once** (the first trial build's plan).
- **R11** — a sweep with a fresh cold read leaves no defect open, and each always-on file and the README are within budget (D54). **Partly**: sweeps 1 to 3 (pull requests 55, 63, 67) settled issues 35 to 65.
- **R12** — `review-project`'s secret check; no project data in any issue. **Met** each sweep.
- **R13** — a trial build over private data, run autonomously, plans every input and output private, keeps them off public hosts and GitHub, holds a read-only credential and prepares no order. **Partly**: a headless plan did all four; no build yet (M22, M20).

### Milestones

M1 to M18 are done (2026-11-08 to 12; git history has them): M4 and M18 were the first two trial builds, a pipeline and a dashboard over its store, neither deployed, since the pipeline's data is licensed for personal use (D47); M16 tagged `v0.1`; M17 proved each plugin alone, bar the second machine (Q7).
The first trial build's project folder is kept, unpushed, until every trial build is done.
Sweeps are not milestones.

- [ ] **M21 Third trial build, public and deployed** — R1, R2, R6; done when a project over public market data runs from one prompt with a scheduled pipeline, a store and a hosted dashboard, each deployed publicly; each outward step waits on the user's go-ahead; the dashboard technology follows Q11.
- [ ] **M22 Fourth trial build, private path** — R13, R6; done when a project over private data runs on the owner's machine and is reached over Tailscale, with nothing on a public host; after M21.
- [ ] **M20 Fifth trial build, over a real account** — R13, R2; done when a project over the user's own account data runs from one prompt in autonomous mode, holds only a read-only credential, and its review finds nothing `secure-project` forbids; after M22.
- [ ] **M19 Grow the scope as earned** — R1; standing: a Not yet item is built when a trial build or a project earns it.

## Open

### Assumptions

- **A1** The repository and marketplace keep their names (`claude`, `henrymckay`) — only the plugins were renamed.
- **A2** The cloud sweep's `gh` is authenticated for REST and blocked for GraphQL, and vendor pages outside its proxy's allowlist are unreachable there, so the free-tier re-check runs in a local sweep.

### Questions

- **Q7** Does every machine these will be installed on allow a third-party marketplace, or do some need the symlink route? — not known yet; blocks R7's and R9's second-machine checks.
- **Q9** Once MotherDuck accepts the current DuckDB client, should a project on MotherDuck replace its two stores (the Parquet tree and the MotherDuck tables beside it) with one DuckLake whose catalog MotherDuck holds and whose files sit in the project's own bucket? — recommended: yes, as a trial in the next project that needs MotherDuck, the tree staying the default elsewhere; costs a bucket and its credential on every writer, and the files read true only through the catalog (D51, D53).
- **Q11** Which technology makes slick, fast dashboards in 2026, Python or not? — the user asked Claude to choose afresh; research is running; until it reports, Shiny stays the pick in `write-entry-points` and `deploy-project`; blocks M21's dashboard.

### Ideas

- **I1** A `doctor` check in `maintain-plugin`: one command that validates manifests, runs the hooks, resolves the links and reports which sibling plugins are missing — would let a new install check itself on day one; costs a script to maintain; not built.
- **I2** `build-project` writes a short run log (model per stage, wall time, real runs and their size) into the project — the first trial build's model and backfill problems were found only by reading transcripts; costs a section in one skill; not built.
- **I3** A budget line in `plan-project`'s Runs on for the build itself (expected stage cost at the ladder's prices) — the user asked about cost twice during the first trial; costs an estimate that will often be wrong; not built.
- **I4** More rules enforced by hooks (issue 53) — today only the feedback `Stop` hook enforces; a hook earns its place when a trial build breaks a rule a hook could have caught; not built.
