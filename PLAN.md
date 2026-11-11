# claude

A family of Claude Code plugins that let Claude design, build and run a development project end to end from a short prompt, and that improve themselves as they are used.

Status: re-planned 2026-11-11.
The requirement wording, D39 to D41 and M15 onward are *(proposed)* until the user answers Q1; R13, M20, D45 to D51 and the changes to D2 and D24 are *(proposed)* until the user answers Q8.

## Brief

### Goal

Claude gets a short prompt and delivers a project that is elegant, efficient, correct and well tested, designed beyond the brief and named in its domain's language, with the planning, deployment and upkeep done as well as the code.
The plugins settle in advance the decisions that recur across projects, easy to hard, so Claude neither asks nor re-decides them; since no such set is ever complete, they also let Claude find and fix their own gaps.
Done looks like: two trial builds of different kinds, each run in autonomous mode from one prompt and leaving `review-project` no defect, and each plugin shown to work installed alone.

### Terms

- **skill** — a `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter, plus any `references/`, per the Agent Skills standard.
- **plugin** — a folder under `plugins/` with a manifest, skills, a session-start hook and a trigger suite, named verb-first for the ability it gives and installable on its own; the repo is a **marketplace** listing five.
- **context file** — a plugin's `hooks/context.md`, its always-on skill list, printed at session start.
- **description** — a skill's frontmatter trigger text, all Claude sees when deciding to load it.
- **reference** — a file under a skill's `references/`, loaded only when the skill points there.
- **instruction file** — `CLAUDE.md`, loaded every session.
- **house pick** — a library or tool a skill chooses over its rivals.
- **drift** — a skill's description, rules or examples falling out of line with its body, its neighbours or current tools.
- **skill feedback** — a GitHub issue labelled `skill-feedback` on the owning plugin's repository, filed when a skill steered Claude wrong in real work; a machine that must not reach a public tracker records it to a file instead.
- **autonomous mode** — a run with no user present: Claude proceeds on its recommended answers, records each as an assumption, and takes no outward action (D35).
- **outward action** — creating a repository, publishing, deploying, messaging or spending money.
- **the ladder** — which model and effort runs each stage (D27).
- **trial build** — a real project planned, built and reviewed with the plugins to test them, its skill feedback worked through by a sweep.
- **build stream** / **skills stream** — building real projects with the skills as they stand / improving the skills from skill feedback and evaluations.
- **sweep** — one `review-plugin` run over the repo: the open skill feedback first, then the drift checks, landed as one pull request.
- **trigger suite** — a plugin's `evals/` cases, one casual prompt per skill, run with `claude plugin eval` to show each description still fires.
- **data class** — public, licensed, private or personal, recorded for each input and output of a project (`secure-project`).

### Requirements

- **R1 End to end.** With every plugin installed, Claude does consistent, high-quality development projects from a minimal prompt: designed, built, reviewed and deployed.
  - Cost: every other requirement; scope held to Python data, CLI, API and dashboard projects until a project earns more.
- **R2 Autonomous.** A project runs with one batch of answers from the user, or with none (autonomous mode, D35).
  - Cost: plans stay unsigned until read, and every outward action waits on the user.
- **R3 `manage-project`** lets Claude plan, build and review a project, each stage on the ladder's model whatever the session's default, with the git and Markdown conventions any repository needs.
  - Cost: a subagent hand-off per stage.
- **R4 `write-code`** gives Claude the house style for the code itself, toolchain-free: functional, object-oriented, Python, SQL, tests, Polars.
  - Cost: house picks the user can't verify alone, re-checked each sweep.
- **R5 `structure-app`** gives Claude a Python application's set-up and shape: the `uv` toolchain, house-pick libraries, layers, entry points.
  - Cost: the one plugin tied to a toolchain.
- **R6 `run-project`** gives Claude a project's life after the build: its data, a job nobody watches, a free or near-free host per artefact, messages to the user.
  - Cost: free tiers change yearly; the picks are one person's, so an install with its own infrastructure leaves it out.
- **R7 `maintain-plugin`** lets Claude maintain any plugin whose source it can read, on any machine: author a skill, review for drift, capture gaps.
It assumes no particular repository, tracker or toolchain.
  - Cost: a feedback destination per install; a report where it cannot push.
- **R8 Self-improving.** A skill gap is captured when it surfaces, worked through on a schedule and on demand, and each fix verified by running the case; the user reviews the result, and no skill is edited mid-build.
  - Cost: a hook, a scheduled task, a trigger suite per plugin, trial builds.
- **R9 Alone or together.** Each plugin installs and works on its own, on any machine, and they work as a group; a machine that cannot install plugins symlinks them.
  - Cost: a context file per plugin, pointers that must read correctly alone, releases an install can pin.
- **R10 Not boxed in.** A skill's default is a default: Claude researches, proposes ideas beyond the brief and the skills, and shows its decisions, alternatives, costs and sources for the user to challenge.
  - Cost: longer plans.
- **R11 Skills worth loading.** Each is clear, concise, consistent with its neighbours, general, and holds nothing Claude does unprompted.
  - Cost: sweeps and the `write-skills` rules.
- **R12 Public.** Generic conventions only: no secrets, no project data, no machine-local state.
- **R13 Safe with private data** *(proposed)*. A project whose data is private, or which holds a credential for an account with money in it, exposes neither, without the user having to notice: the data is private until the plan says otherwise, and nothing moves money without a person confirming it.
  - Cost: a class per input and output in every plan, hosts picked from it, the owner's machine in place of the free public hosts for private data, and a security step in every gate.

### Not yet

- **A repository per plugin** — earned when a plugin needs different visibility or another owner; one repo keeps one tracker, one weekly pull request and cross-plugin drift caught in one sweep, and the marketplace can list a plugin that lives elsewhere.
- **Icons, and a listing in the public plugin directory** — earned by wanting other people to find the plugins.
- **Toolchain skills other than `uv`** (Bazel and the like) — they belong in the repo that uses the toolchain, as project skills or a private plugin.
- **A debugging skill** — earned when skill feedback shows debugging going wrong.
- **References for a language other than Python** — earned by the first non-Python project; the scope is Python data, CLI, API and dashboards (2026-11-10).
- **CI for projects** — declined again 2026-11-10 as marginal for one-machine unattended tools; earned by a project with a second contributor or a deploy.
- **An evaluation per fixed issue** — declined as too big; the trigger suites check only that descriptions fire, and a sweep verifies a fix by running the issue's case.
- **Snapshot tests, mutation testing, a task runner, Docker, dev containers, docs generation** — each earned by the first project that needs it; the skills say "none" until then.
- **`agents/`, `commands/` and `rules/`** — the `~/.claude` symlinks for the first two already exist and dangle on purpose.
- **Slack as a message channel** — earned once the user has a workspace they read; the skill names it as an alternative until then.
- **An `advisor` second-model step mid-task** — Claude Code documents one; earned when a build stage keeps failing its gate on Sonnet.
- **More SQL dialects for `write-sql`** — earned by the first project on one; DuckDB is the only reference.
- **A plugin per domain** (accounting, tax, trading) — a domain skill starts in its project's own `.claude/skills/`, and is promoted to a plugin, in its own repository if private, once a second repository needs it.

## Design

### Inputs

- **The user's conversations and corrections** — the requirements and most rules; corrections about skills arrive as skill feedback.
- **Skill feedback issues** — `gh issue list -R henrymckay/claude --label skill-feedback`.
- **Current tool docs and releases** — Claude Code, uv, ruff, Polars and the rest; every skill claim is checked against the current release.
- **Trial builds** — `market-data` on 2026-11-11, which filed sixteen issues; each later one feeds the same loop.

### Data flow

1. **Skill source** — `plugins/<plugin>/skills/<name>/SKILL.md` in this repo, edited only in the skills stream. (IO)
2. **Wiring** — either the plugins are installed from the marketplace, or `~/.claude/skills` is a symlink to the repo's `skills/` folder of links into the plugins and `~/.claude/CLAUDE.md` a symlink to the repo's; never both on one machine, which would load every skill twice. (IO)
3. **Loading** — every session loads each description and the always-on list (`CLAUDE.md` when symlinked, each installed plugin's context file otherwise); a skill's body loads when its description or the list triggers it, a reference when the body points there.
4. **Applying** — Claude follows the loaded skills in real work in other repos.
5. **Feedback** — a skill that steers wrong becomes skill feedback on the owning plugin's repository. (IO)
6. **Sweep** — `review-plugin` works the issues, then checks for drift, commits each skill's fixes on one branch and opens one pull request, whose merge loops back to stage 1.

### Outputs

- **`plugins/<plugin>/skills/<name>/SKILL.md`** — frontmatter `name` and `description`, then a body laid out by `write-skills`; read by Claude.
- **`plugins/<plugin>/`** — `.claude-plugin/plugin.json`, `hooks/` (the context file and the script that prints it; `maintain-plugin` adds the feedback rule and the Stop hook) and `evals/` (one trigger case per skill).
- **`.claude-plugin/marketplace.json`** — lists the five plugins by relative path.
- **`skills/<name>`** — a relative symlink to the skill in its plugin, for the symlink wiring.
- **`plugins/<plugin>/skills/<name>/references/*.md`** — language or topic depth, per `write-skills`.
- **`CLAUDE.md`** — Work, Answers and the mandatory Skills list; read by Claude every session.
- **`README.md`** — for humans: what each skill does, setup, configuration, feedback, evaluation.
- **`PLAN.md`** — this file.

### Interface

Installed, any subset:

```bash
claude plugin marketplace add henrymckay/claude
claude plugin install manage-project@henrymckay
```

Symlinked, where the skills are authored or plugins cannot be installed:

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Skills trigger from their descriptions or by name (`/plan-project`, or `/manage-project:plan-project` when installed); "review the skills" runs `review-plugin`.

| Plugin | Skills |
|---|---|
| `maintain-plugin` | `review-plugin`, `write-skills`, the feedback rule and Stop hook |
| `manage-project` | `plan-project`, `build-project`, `review-project`, `choose-model`, `make-decisions`, `secure-project`, `use-git`, `write-markdown` |
| `write-code` | `be-functional`, `be-oop`, `write-python`, `write-sql`, `write-tests`, `use-polars` |
| `structure-app` | `setup-python`, `structure-python`, `write-entry-points` |
| `run-project` | `store-data`, `run-unattended`, `deploy-project`, `send-messages` |

### Runs on

- **The skills and `CLAUDE.md`** — the user's machine: the five plugins installed from the repo as a local marketplace, which loads them in place so edits stay live, and `~/.claude/CLAUDE.md` symlinked; another machine installs from GitHub, or symlinks `skills/`; nothing is deployed.
- **The weekly sweep** — a Claude Code cloud scheduled task (`trig_01NmQMC42vGPjqQEDE8XrgzQ`), Mondays 02:00 UTC on Opus, cloning the public repo and opening one PR; no connectors; checked 2026-11-10.
- **The Stop hook** — carried by the installed `maintain-plugin` (`plugins/maintain-plugin/hooks/hooks.json`); with the symlink wiring its `Stop` entry is merged into `~/.claude/settings.json`.
- **The trigger suite** — `claude plugin eval` on the user's machine, or in the sweep where the CLI is available.

### Errors

- **A description fails to trigger, or fires on the wrong task** — found by review-plugin's trigger-overlap check or by skill feedback; fixed in the description.
- **A rule is duplicated or contradicted** — found by review-plugin; kept where it belongs, pointed at from elsewhere.
- **A library claim goes stale** — found by re-running every claim against the current release in each sweep.
- **A symlink dangles** — found by review-plugin's wiring check; `agents` and `commands` dangle on purpose.
- **Feedback carries project data** — the `CLAUDE.md` rule requires describing the shape of the case; delete or edit such an issue on sight.

### Decisions

Numbers are stable; the groups are for reading.

**The repository and its wiring**

- **D30 One repo as a marketplace of five plugins** over one plugin or a repo each — an install takes some and not others; one repo keeps one tracker and one sweep (see Not yet). Source: code.claude.com/docs/en/plugins/create-marketplace, checked 2026-11-11.
- **D31 The groups, each named verb-first for the ability it gives** (the user, 2026-11-11): `maintain-plugin` (author skills, review any plugin, capture gaps), `manage-project` (the lifecycle, the model ladder, and `use-git` and `write-markdown`, which any repo needs), `write-code` (style, toolchain-free), `structure-app` (set-up and structure, where `uv` lives) and `run-project` (a project meeting the real world; one person's free-tier picks, so the plugin an install is likeliest to leave out). `deploy-project` sits in `run-project` because its body is host picks; `plan-project`'s Runs on is the lifecycle's deployment step. `choose-model` sits in `manage-project` because the ladder is about a project's stages and three of the four skills it governs live there. The name `claude` is reserved by the validator.
- **D1 Symlinks into `~/.claude`** remain a supported wiring for a machine that cannot install plugins; the authoring machine moved to the installed plugins on 2026-11-11 so it runs what others install (D30).
- **D32 Always-on instructions per plugin are a context file printed by a SessionStart hook** over a plugin `CLAUDE.md`, which Claude Code does not load; `CLAUDE.md` keeps the same lines for the symlink wiring, and `review-plugin` checks the two agree.
- **D34 A toolchain's commands live in the skill that owns it** — `uv` in `setup-python`, with `run-project` building on it; `manage-project` and `write-code` name a `uv` command only as that toolchain's example, so they hold under Bazel or anything else.
- **D2 Commit as `henrymckay <henrymckay@users.noreply.github.com>`, `docs(<skill>): …`; a sweep lands by pull request, and only an edit the user makes or asks for in a session outside a sweep goes straight to `main`** *(proposed change, issue 42)* — was: everything straight to `main` except the scheduled sweep; every skill change is now reviewed in one place before it reaches an install; overrides `use-git`'s branch default for the direct edits only.
- **D10 Not yet lives in this plan** over `enhancement` issues — issues are kept for skill feedback.
- **D11 The README points at this plan** with a short note on how the skills fit together, over copying it — the README is for humans, the plan for Claude.
- **D12 Memory holds only what this plan doesn't** — the plan is visible and versioned; memory is per-machine.
- **D9 No performance budget** — nothing here runs.
- **D41 A release is a tag on `main`** *(proposed)*, `v<major>.<minor>` cut after a sweep is merged and its suites pass, over installing from the tip — an install pins a tag, so a sweep cannot change behaviour on another machine mid-week; cost: one tag per sweep; overrides `use-git`, Release (a `vX.Y.Z` tag at a milestone, not per merge).
- **D43 The MIT licence** (the user, 2026-11-11) over Apache 2.0 or none — without one nobody else may use the plugins, and MIT is the one an organisation approves most readily.
- **D44 Nothing in the repo distinguishes home from work** (the user, 2026-11-11) — the plugins are for anyone on any machine; a constraint is named for what it is (a tracker that must stay private, a toolchain other than `uv`, a marketplace that is not allowed).

**How a project runs**

- **D13 A skill's default is a default** — a signed-off `PLAN.md` decision overrides a skill; a reason Claude finds is a proposed decision, raised before it is built on (in autonomous mode, recorded and built on); a rule stays imperative with its exception in the same sentence, because softened rules were ignored outright.
- **D14 Decisions are surfaced, not buried** — plan-project's one batch lists Claude's decisions with alternatives, costs and sources beside the questions and assumptions; build and review reports list the calls made.
- **D35 Autonomous mode** (the user, 2026-11-11, issue 21) — with no user present, Claude proceeds on its recommended answers, records each as an assumption for the user's later review, keeps decisions marked proposed, and never takes an outward action such as creating a repository, publishing or spending money; `plan-project` defines it and `build-project` and `review-project` each state it. Skill feedback is still recorded as the feedback rule says (issue 29; the user, 2026-11-11).
- **D5 `review-project` general, `review-plugin` layered on it** over two independent reviews — one set of review mechanics.
- **D6 `build-project`** over `develop-project` — matches "the build" wording across the skills.
- **D26 A fourth sweep outcome, "needs the user"** — an unattended run never changes a decision or settles policy; it leaves the issue open with a recommended answer.
- **D46 Settle an open question from precedent** (the user, 2026-11-11, issue 40: "yes to make-decisions"): a skill in `manage-project` finds the nearest answered decision and cites it, escalating only the irreversible, outward-facing, costly, security-touching or unprecedented; the mark *(by precedent)* beside *(proposed)* and reporting those as a count are *(proposed)* — over every gap becoming a question or a proposed decision, which left a first autonomous build with more calls than the user could read.
- **D47 `secure-project` in `manage-project`, and private by default** *(proposed, issue 46)* — over a section of `deploy-project` or a sixth plugin: every project needs it whatever its hosts, `run-project` is the plugin an install is likeliest to leave out (D31), and plan, build and review call it; an input or output with no class is private, a looser class is the user's call, and nothing that moves money happens without a signed-off decision and a person confirming each action, never in autonomous mode.

**The feedback loop**

- **D3 Skill feedback as GitHub issues** over memory or a notes file — visible to the user, closable from a commit, and not per-machine.
- **D4 The filing rule in `CLAUDE.md`** over a skill — a skill only loads for a matching task, and feedback arises mid-task in any work.
- **D33 Feedback goes to the owning plugin's repository**, read from its manifest or named in the user's `CLAUDE.md`, over a repository written into the skills; `maintain-plugin`'s `feedback` option (`issues`, `file`, `off`) redirects it on a machine whose work must not reach a public tracker. Issues remain the default.
- **D25 A `Stop` hook prompts for unfiled skill gaps** — the only hook that can reach the model, since `SessionEnd` cannot; hook text in the repo, the `settings.json` entry in the README.
- **D24 Every sweep lands as one pull request**, scheduled or run in a session *(proposed change, issue 42; the user: "even a session sweep should probably be a PR")* — the pull request is the user's review point; was: a session sweep committed to `main`.
- **D45 The sweep merges its own pull request only when every trigger suite passes and no rule was cut, generalised or left for the user; otherwise the user merges** *(proposed, issue 42)* — over the user merging every sweep, which keeps a routine sweep waiting on a read nobody needs; cost: a rule change the user never reads when the sweep judged it routine.
- **D28 The weekly sweep runs on Opus** on Mondays at 02:00 UTC with no connectors — skill edits are reasoning work, and a connector acting as the user is a risk the sweep doesn't need.
- **D23 A trigger suite per plugin at `plugins/<plugin>/evals/`**, the default folder `claude plugin eval` reads, over one suite at the root — an eval run targets one plugin; the brief-and-answers evaluations stay under `evaluate/`.
- **D39 A requirement is verified by behaviour** over by a skill existing *(proposed)* — the ladder's milestone was ticked when `choose-model` was written, and the first trial build then ran on the wrong model; each Verification line below names a run and what it must show, and carries its status.
- **D40 The `evaluate/` folder and its brief-and-answers evaluations are removed** *(proposed)* — trial builds and the per-plugin trigger suites do its job with real feedback; no brief was ever checked in; replaces the old R5 and D8.

**Models**

- **D27 The model ladder** — Opus (Fable for the hardest design) at high effort for planning, reviews and skill edits; Sonnet for build milestones, cold reads and research; Haiku for graders, hooks and trigger evals — over one model throughout. It holds whatever the session's default is (the user, issue 25): frontmatter changes the model a session is told it is on, not the one serving it (Claude Code 2.1.322, from per-message transcript models), so each stage hands its work to a subagent with the Agent tool's model and effort set.
- **D42 No skill names a model in its frontmatter** (the user, 2026-11-11, issue 36) over keeping the lines as documentation — a `model` line changes the model a session is told it is on, not the one serving it, so it only misleads; the hand-off in D27 places each stage, and the `effort` lines stay.

**House picks**

The skill named holds the pick, its alternative and its reason; the plan keeps the number.

- **D7 `be-functional` the default style, `be-oop` opt-in.**
- **D15 `functools.partial`, closures and `match`** over `toolz` and `plum`, which stay mentioned — `be-functional`.
- **D16 One error model**: raise from `error/`, convert at an adapter's seam, decide in a driver, catch nothing in the core — `write-python`.
- **D17 One record type**, the frozen, slotted, keyword-only dataclass — `write-python`.
- **D18 `uv_build`** over `hatchling` — `setup-python`.
- **D19 pyright `strict`** — `setup-python`.
- **D20 House picks for datetime, money, storage, config, HTTP, logging, plotting and test doubles** (2026-11-10) — each named, with its alternative, in the skill that owns it: `write-python`, `store-data`, `structure-python`, `setup-python`, `write-tests`.
- **D21 `store-data` and `run-unattended` exist** because a gap probe left 72 decisions open and they absorb most.
- **D22 MotherDuck's token variable is lower case**, `motherduck_token` — `store-data`.
- **D29 Message channels**: ntfy for an alert, email for a digest, Claude Code channels for a chat; Slack once a workspace exists — `send-messages`.
- **D36 A `write-sql` skill in `write-code`** (the user, 2026-11-11, issue 30) over a section of `store-data` — decisions only: SQL against Polars, where SQL lives, style, schema changes and testing a documented query, in a dialect-neutral body with a reference per dialect, DuckDB first.
- **D37 `coverage run -m pytest`** over `pytest-cov` (issue 31; the user, 2026-11-11) — the `-p` plugin `setup-python`'s own `addopts` loads imports the package before `--cov` measures, which read 33% for a true 83% on a two-module package (pytest-cov 7.1, coverage 7.17); cost: two commands where one flag did.
- **D38 A run that finds the lock held writes no manifest row** (issue 27; the user, 2026-11-11) over a `skipped` row — the run in progress records the night, and a `skipped` row would exit 1 where the lock rule exits 0; the `skipped` outcome is deleted, since nothing produces it.
- **D48 A stored table's columns in alphabetical order, its timestamps UTC with their zone** (the user, 2026-11-11, issue 41) — `store-data`, Shape a stored table; the exceptions — partition keys in the path, the manifest and a plan's schema table following the rule — are *(proposed)*.
- **D49 A bounded catch-up window**, default three days set per source, over no automatic catch-up (the user's direction, 2026-11-11, issue 45; the default *(proposed)*) — `run-unattended`; a wider gap is reported and left for an explicit backfill.
- **D50 `sqlfluff` for SQL from a project's first `.sql` file** *(proposed, issue 43)* over `sqruff` (17 times faster on 200 files but pre-1.0) and `sqlfmt` (packs columns onto one line) — `write-sql` names it, `setup-python` wires the hook.
- **D51 Hive-partitioned Parquet kept over a table format** *(proposed, issue 44)* — Delta Lake is the named alternative once a write spans partitions or corrects rows; DuckLake needs a catalog to back up and has no Polars reader; checked 2026-11-11 against deltalake 1.6, DuckDB 2.0 and Polars 2.1 — `store-data`.

**Superseded**

- **D8 Evaluation briefs archived to the rough repo** over keeping trade-specific briefs here — they taught one domain. Superseded by D40 once it is signed off.

## Delivery

### Verification

Each line names the run that shows it, then its status on 2026-11-11.

- **R1** — two trial builds of different kinds, each from one prompt, each leaving `review-project` no defect. **Partly**: `market-data` planned, built and reviewed (130 tests; four defects fixed, six decisions left to the owner); nothing deployed; no second build.
- **R2** — a trial build with no user answers ends with an unsigned plan, every answer an assumption, no outward action. **Partly**: a headless plan did it unaided; no whole build yet.
- **R3** — a stage started on a default that is not its model shows its work on the ladder's model in the transcript's per-message counts. **Met for plan and build** (30 of 30 on Opus from Sonnet; 100 of 100 on Sonnet from Opus); review unmeasured.
- **R4, R5** — a trial build's review finds no stated convention broken, and files as feedback what the build decided alone. **Met once** (issues 28, 30 to 33, closed).
- **R6** — the same for storage and scheduling; one artefact deployed to a house-pick host; one message delivered. **Partly**: local only (issues 22 to 24 and 27, closed).
- **R7** — `review-plugin` on a plugin outside this repository ends in a report with no push; `maintain-plugin` alone on a second machine records feedback to a file. **Not met**.
- **R8** — the hook files a seeded gap; a scheduled sweep opens a pull request; a sweep closes real issues, each fix run. **Met** (issue 20; pull request 19; issues 21 to 34).
- **R9** — `claude plugin validate` and every trigger case pass; every `skills/` link resolves; each plugin alone completes a task and names what it lacked; a GitHub install works on a second machine. **Partly**: the first three pass; the rest not run.
- **R10** — a plan shows its decisions with sources and its ideas; a review can challenge a house pick. **Met once** (`market-data`'s plan).
- **R11** — a sweep with a fresh cold read leaves no defect open. **Partly**: the 2026-11-11 sweep settled issues 35 to 46 and listed its cold read's leftovers in its pull request.
- **R12** — `review-project`'s secret check; no project data in any issue. **Met** each sweep.
- **R13** — a trial build over private data, run autonomously, plans every input and output private, keeps them off public hosts and GitHub, holds a read-only credential and prepares no order. **Partly**: a headless plan did all four (2026-11-11); no build yet.

### Milestones

M1 to M14 are done (2026-11-08 to 11; git history has them), M4 being the first trial build.
M11 was ticked on a skill existing and failed in use, hence D39.

- [ ] **M15 Re-plan and rename** — R9; done when the plugins carry their verb-first names (done) and the user signs this plan off (Q1).
- [ ] **M16 Tidy** — R11; done when issues 35 to 37 are settled, `evaluate/` is removed (D40) and the first release is tagged (D41).
- [ ] **M17 Prove each plugin alone** — R7, R9; done when their checks pass.
- [ ] **M18 Second trial build, autonomous** — R1, R2, R3, R6; done when a dashboard over `market-data`'s store (the user's choice, 2026-11-11: it exercises a dashboard, a deployment, SQL and a message, which the first build did not) runs from one prompt with no user answers on a non-ladder default, deploys one artefact and sends one message where the user allows, and its feedback is swept.
- [ ] **M20 Third trial build, over private data** *(proposed)* — R13, R2; done when a project over the user's own account data runs from one prompt in autonomous mode, holds only a read-only credential, and its review finds nothing `secure-project` forbids.
- [ ] **M19 Grow the scope as earned** — R1; standing: a Not yet item is built when a trial build or a project earns it.

## Open

### Assumptions

- **A1** The repository and marketplace keep their names (`claude`, `henrymckay`) — only plugins were asked to be renamed.
- **A2** The cloud sweep's `gh` is authenticated for REST and blocked for GraphQL, and vendor pages outside its proxy's allowlist are unreachable there, so the free-tier re-check runs in a local sweep (found 2026-11-10).

### Questions

- **Q1** Sign off this re-plan: R1 to R12 as worded, D39 to D41, and M15 to M19? — recommended: yes; blocks M15.
- **Q6** May the second trial build deploy its dashboard, and to which account? — `market-data` is kept only as that build's data source and deleted after it (the user, 2026-11-11), with no GitHub repository of its own; the build stops before any outward action and lists the deployment for the user; recommended: decide when the build reports; blocks only the deployed half of M18.
- **Q7** Does every machine these will be installed on allow a third-party marketplace, or do some need the symlink route? — only the user can find out; blocks M17's second-machine check.
- **Q8** Sign off the 2026-11-11 sweep's proposals: R13, M20, D45, D47, the proposed parts of D46 and D48 to D51, and the changes to D2 and D24? — recommended: yes, by merging its pull request; the policy calls inside `secure-project` and `make-decisions` are listed there one by one.

### Ideas

- **I1** A `doctor` check in `maintain-plugin`: one command that validates manifests, runs the hooks, resolves the links and reports which sibling plugins are missing — would turn M17's checks into something a new install runs on day one; costs a script to maintain; not built.
- **I2** Have `build-project` write a short run log (model per stage, wall time, real runs and their size) into the project — the first trial build's model and backfill problems were found only by a coordinator reading transcripts; costs a section in one skill; not built.
- **I3** A budget line in `plan-project`'s Runs on for the build itself (expected stage cost at the ladder's prices) — the user asked about cost twice during the first trial; costs an estimate that will often be wrong; not built.
