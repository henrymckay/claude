# claude

A family of Claude Code plugins that let Claude design, build, review and run a development project end to end from a short prompt, close to autonomously, and that improve themselves as they are used.

Status: re-planned 2026-11-11 around the aim the user restated that day.
The goal, the plugin names and groups, autonomous mode and the ladder rule are the user's; the wording of R1 to R12, D39 to D41, the verification statuses and M15 onward are *(proposed)* until the user answers Open.
Decisions D1 to D38 keep their numbers and standing from the plan this replaces (git history holds it).

## Brief

### Goal

The user wants to give Claude a short prompt, or none beyond "plan this", and get a project that is elegant, efficient, correct and well tested, designed beyond the brief and named in its domain's language, with the planning, management, deployment and upkeep done as well as the code.
The plugins get there by settling in advance the decisions that recur across projects, from a function's name to where a pipeline's data lives, so Claude neither asks them nor re-decides them.
No set of answers written in advance is complete, so the plugins also carry the means for Claude to find and fix their own gaps.
Done looks like: two trial builds of different kinds, each run in autonomous mode from one prompt on a session whose default model is not the ladder's, each passing `review-project` with no defect left, and each plugin shown to work installed alone, the maintenance plugin on a plugin that is not this repo.

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

### Requirements

- **R1 End to end.** With every plugin installed, Claude takes a project from a short prompt to a designed, built, reviewed and deployed result that is elegant, efficient, correct and well tested, thought about beyond the brief and named in its domain's language. (Was R1, R6, R10, R11.)
  - Cost: every other requirement here; and a scope held to Python data, CLI, API and dashboard projects until a project earns more (Not yet).
- **R2 Autonomous.** A project runs with one batch of answers from the user, or with none: in autonomous mode Claude proceeds on its recommended answers, records each as an assumption for later review, and takes no outward action. (New; D35.)
  - Cost: plans that stay unsigned until read, and anything outward (a repository, a deployment, a message) waiting on the user; dropping it leaves every project blocked on a conversation.
- **R3 `manage-project` gives Claude the ability to run a project's lifecycle**: plan it in one `PLAN.md`, build it milestone by milestone behind a gate, review it and fix what the review finds, each stage on the ladder's model whatever the session's default, with the git and Markdown conventions any repository needs. (Was R9 and the trio.)
  - Cost: a subagent hand-off per stage, and a ladder to maintain as models and prices change.
- **R4 `write-code` gives Claude the house style for the code itself**, toolchain-free: functional by default, object-oriented where it fits, Python, SQL, tests, Polars. (Was part of R6.)
  - Cost: house picks the user can't verify alone, re-checked against current releases in each sweep.
- **R5 `structure-app` gives Claude a Python application's set-up and shape**: the `uv` toolchain and house-pick libraries, hexagonal layers, and entry points. (Was part of R6.)
  - Cost: the one plugin tied to a toolchain; a project on another (Bazel) replaces `setup-python` with its own skill.
- **R6 `run-project` gives Claude a project's life after the build**: where its data lives, a job nobody watches, the best free or near-free host per artefact, and messages back to the user. (Was R10, R11 and part of R6.)
  - Cost: free tiers and vendor terms change yearly; the picks are personal, so this plugin is not for work.
- **R7 `maintain-plugin` gives Claude the ability to maintain any plugin**, the user's at home or at work or anyone's whose source it can read: author a skill, review a plugin for drift, and capture skill gaps as they surface. It assumes no particular repository, tracker or toolchain. (Was part of R12.)
  - Cost: a feedback destination per install, and a review that must end in a report where it cannot push.
- **R8 Self-improving.** The plugins improve from real use without relying on anyone's recall: a gap is captured when it surfaces, worked through on a schedule and on demand, each fix verified by running the case, and the user reviews the result; a skill is never edited mid-build. (Was R3, R8.)
  - Cost: a hook, a scheduled task, a trigger suite per plugin, and trial builds to generate the feedback.
- **R9 Alone or together.** Each plugin installs and works on its own, at work included, and they work as a group; a skill that points at an absent plugin degrades to a decision Claude makes and records; a machine that cannot install plugins symlinks them instead. (Was R12.)
  - Cost: a context file per plugin duplicating `CLAUDE.md`'s list, cross-plugin pointers that must read correctly alone, and releases a work install can pin.
- **R10 Not boxed in.** A skill's default is a default: Claude researches the domain and current practice, proposes ideas beyond the brief and the skills, and puts its decisions, alternatives, costs and sources in front of the user to challenge. (Was R7.)
  - Cost: longer plans and one more surface to read; dropping it leaves the user supplying the knowledge.
- **R11 Skills worth loading.** Each skill is clear, concise, consistent with its neighbours, general rather than fitted to one project, and holds nothing Claude does unprompted. (Was R2 and part of R6.)
  - Cost: sweeps, and the `write-skills` rules (state once, keep examples general, run every claim).
- **R12 Public.** The repository is public: generic conventions only, no secrets, no project data, no machine-local state. (Was R4.)
  - Cost: every example in a domain any reader knows, and feedback that describes a shape, never a case.

### Not yet

- **A repository per plugin** — earned when a plugin needs different visibility or another owner; one repo keeps one tracker, one weekly pull request and cross-plugin drift caught in one sweep, and the marketplace can list a plugin that lives elsewhere.
- **Icons, and a listing in the public plugin directory** — earned by wanting other people to find the plugins; the licence is Q3.
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
6. **Sweep** — `review-plugin` works the issues, then checks for drift, and commits each skill's fixes, which loops back to stage 1.

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
| `manage-project` | `plan-project`, `build-project`, `review-project`, `choose-model`, `use-git`, `write-markdown` |
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

- **D30 One repo as a marketplace of five plugins** over one plugin or a repo each — the user installs some at work and not others; one repo keeps one tracker and one sweep (see Not yet). Source: code.claude.com/docs/en/plugins/create-marketplace, checked 2026-11-11.
- **D31 The groups, each named verb-first for the ability it gives** (the user, 2026-11-11): `maintain-plugin` (author skills, review any plugin, capture gaps), `manage-project` (the lifecycle, the model ladder, and `use-git` and `write-markdown`, which any repo needs), `write-code` (style, toolchain-free), `structure-app` (set-up and structure, where `uv` lives) and `run-project` (a project meeting the real world; personal free-tier picks, so not for work). `deploy-project` sits in `run-project` because its body is host picks; `plan-project`'s Runs on is the lifecycle's deployment step. `choose-model` sits in `manage-project` because the ladder is about a project's stages and three of the four skills it governs live there. The name `claude` is reserved by the validator.
- **D1 Symlinks into `~/.claude`** remain a supported wiring for a machine that cannot install plugins; the authoring machine moved to the installed plugins on 2026-11-11 so it runs what others install (D30).
- **D32 Always-on instructions per plugin are a context file printed by a SessionStart hook** over a plugin `CLAUDE.md`, which Claude Code does not load; `CLAUDE.md` keeps the same lines for the symlink wiring, and `review-plugin` checks the two agree.
- **D34 A toolchain's commands live in the skill that owns it** — `uv` in `setup-python`, with `run-project` building on it; `manage-project` and `write-code` name a `uv` command only as that toolchain's example, so they hold under Bazel or anything else.
- **D2 Commit straight to `main`** as `henrymckay <henrymckay@users.noreply.github.com>`, `docs(<skill>): …` over feature branches — a solo docs repo with nothing to merge; overrides `use-git`'s branch default; the scheduled sweep's weekly PR is the one exception.
- **D10 Not yet lives in this plan** over `enhancement` issues — issues are kept for skill feedback.
- **D11 The README points at this plan** with a short note on how the skills fit together, over copying it — the README is for humans, the plan for Claude.
- **D12 Memory holds only what this plan doesn't** — the plan is visible and versioned; memory is per-machine.
- **D9 No performance budget** — nothing here runs.

**How a project runs**

- **D13 A skill's default is a default** (2026-11-10) — a `PLAN.md` decision the user signed off overrides a skill; a reason Claude finds is recorded as a proposed decision and raised before it is built on; a rule stays imperative with its exception in the same sentence, never softened to "prefer", because softened rules were ignored outright.
- **D14 Decisions are surfaced, not buried** — plan-project's one batch lists Claude's decisions with alternatives, costs and sources beside the questions and assumptions; build and review reports list the calls made.
- **D35 Autonomous mode** (the user, 2026-11-11, issue 21) — with no user present, Claude proceeds on its recommended answers, records each as an assumption for the user's later review, keeps decisions marked proposed, and never takes an outward action such as creating a repository, publishing or spending money; `plan-project` defines it and `build-project` and `review-project` each state it. Skill feedback is still recorded as the feedback rule says *(that last clause proposed, from issue 29)*.
- **D5 `review-project` general, `review-plugin` layered on it** over two independent reviews — one set of review mechanics.
- **D6 `build-project`** over `develop-project` — matches "the build" wording across the skills.
- **D26 A fourth sweep outcome, "needs the user"** — an unattended run never changes a decision or settles policy; it leaves the issue open with a recommended answer.

**The feedback loop**

- **D3 Skill feedback as GitHub issues** over memory or a notes file — visible to the user, closable from a commit, and not per-machine.
- **D4 The filing rule in `CLAUDE.md`** over a skill — a skill only loads for a matching task, and feedback arises mid-task in any work.
- **D33 Feedback goes to the owning plugin's repository**, read from its manifest or named in the user's `CLAUDE.md`, over a repository written into the skills; `maintain-plugin`'s `feedback` option (`issues`, `file`, `off`) redirects it on a machine whose work must not reach a public tracker. Issues remain the default.
- **D25 A `Stop` hook prompts for unfiled skill gaps** — the only hook that can reach the model, since `SessionEnd` cannot; hook text in the repo, the `settings.json` entry in the README.
- **D24 The scheduled sweep lands as one weekly PR**; an on-demand sweep run in a session commits to `main` — the PR is the user's review point, and cloud tasks push to a branch by default.
- **D28 The weekly sweep runs on Opus** on Mondays at 02:00 UTC (06:00 Dubai) with no connectors — skill edits are reasoning work, and a connector acting as the user is a risk the sweep doesn't need.
- **D23 A trigger suite per plugin at `plugins/<plugin>/evals/`**, the default folder `claude plugin eval` reads, over one suite at the root — an eval run targets one plugin; the brief-and-answers evaluations stay under `evaluate/`.

**Models**

- **D27 The model ladder** (2026-11-10) — Opus (Fable for the hardest design) at high effort for planning, reviews and skill edits; Sonnet for build milestones, cold reads and research; Haiku for graders, hooks and trigger evals — over one model throughout; applied by the project skills' frontmatter `model` and `effort`, which set the turn's model, and by the Agent tool's per-subagent parameters.
The ladder holds whatever the session's default model is (the user, 2026-11-11, issue 25): the frontmatter changed the model a session was told it was on and not the one serving it, in a headless plan and build and in an interactive sweep (Claude Code 2.1.322, read from each transcript's per-message model), so each stage always hands its work to a subagent with the Agent tool's model and effort set, and the frontmatter is kept for its effort alone.

**House picks the skills carry**

- **D7 `be-functional` the default style, `be-oop` opt-in** over both opt-in.
- **D15 `functools.partial`, closures and `match`** over `toolz` and `plum` as defaults — `toolz` ships no type hints, so pyright loses every curried function; both stay mentioned for the case that earns them.
- **D16 One error model** — raise from the app's `error/` package; an adapter converts a library's failure or classifies an item's outcome at its seam, only a driver decides what the user sees, and nothing in the core catches; `X | None` only for a lookup miss the caller always branches on; no `Result` library.
- **D17 One record type** — `@dataclass(frozen=True, slots=True, kw_only=True)` in the core; `pydantic` only across a trust boundary; `NamedTuple` only for tuple semantics; never `attrs`.
- **D18 `uv_build`** over `hatchling` — zero config for a src layout; `hatchling` only when a build plugin is needed.
- **D19 pyright `strict`** over `standard` on a greenfield project — the only mode that catches an `Unknown` in fresh code.
- **D20 House picks adopted 2026-11-10** — datetime: aware `datetime` + `zoneinfo`, UTC in the core; money: `Decimal` or minor units; storage: hive-partitioned Parquet for pipeline output, DuckDB to query it, MotherDuck when more than one machine or a phone chat must reach it, SQLite for small single-writer state; config: `pydantic-settings` with `.env` locally, a user-editable CSV in the data directory for lists, package YAML for per-source constants; HTTP: sync `httpx`, `tenacity`, `pyrate-limiter`, key in a header; sync core with async only in a driver or adapter whose framework or fan-out needs it; logging: stdlib + `RichHandler` on stderr, JSON lines behind a collector; plotting: `plotly` via `shinywidgets`; frame contracts: `match_to_schema`; test doubles: `monkeypatch` and `time-machine`; releases: `uv version --bump` then tag.
- **D21 Two new skills, `store-data` and `run-unattended`** — the gap probe left 72 decisions open and these two absorb most of them.
- **D22 MotherDuck connects with `duckdb.connect("md:<db>")` and the token in `motherduck_token`**, lower case per its docs (checked 2026-11-10); A1 had it upper case.
- **D29 Message channels for this user** — ntfy for a failure alert (one phone app, no account), the user's own email for a digest with a chart, Claude Code channels (iMessage on the Mac, Telegram elsewhere) for a two-way assistant; Slack only once a workspace exists; iMessage never from the cloud.
- **D36 A `write-sql` skill in `write-code`** (the user, 2026-11-11, issue 30) over a section of `store-data` — decisions only: SQL against Polars, where SQL lives, style, schema changes and testing a documented query, in a dialect-neutral body with a reference per dialect, DuckDB first.
- **D37 `coverage run -m pytest`** over `pytest-cov` *(proposed, issue 31)* — the `-p` plugin `setup-python`'s own `addopts` loads imports the package before `--cov` measures, which read 33% for a true 83% on a two-module package (pytest-cov 7.1, coverage 7.17); cost: two commands where one flag did.
- **D38 A run that finds the lock held writes no manifest row** *(proposed, issue 27)* over a `skipped` row — the run in progress records the night, and a `skipped` row would exit 1 where the lock rule exits 0; `skipped` stays for a source a run ended before reaching.

**Superseded**

- **D8 Evaluation briefs archived to the rough repo** over keeping trade-specific briefs here — they taught one domain. Superseded by D40.

**New in this re-plan**

- **D39 A requirement is verified by behaviour** over by a skill existing *(proposed)* — the ladder's milestone was ticked when `choose-model` was written, and the first trial build then ran on the wrong model; each Verification line below names a run and what it must show, and carries its status.
- **D40 The `evaluate/` folder and its brief-and-answers evaluations are removed** *(proposed)* — trial builds and the per-plugin trigger suites do its job with real feedback; no brief was ever checked in; replaces the old R5 and D8.
- **D41 A release is a tag on `main`** *(proposed)*, `v<major>.<minor>` cut after a sweep is merged and its suites pass, over installing from the tip — a work install pins a tag, so a sweep at home cannot change behaviour at work mid-week; cost: one tag per sweep.

## Delivery

### Verification

Each line names the run that shows it and where that stands on 2026-11-11.

- **R1** — two trial builds of different kinds, each from one prompt, each leaving `review-project` no defect. **Partly met**: `market-data` was planned, built and reviewed (130 tests, 97% coverage; the review fixed four defects and left six decisions for the owner); nothing was deployed, and there is no second build.
- **R2** — a trial build run headless with no user answers ends with an unsigned plan, every answer recorded as an assumption, and no outward action. **Partly met**: `market-data` ran that way under a coordinating session before the skills said how; after the fix a headless plan did it unaided; no whole build has yet.
- **R3** — a plan, a build and a review each started on a default model that is not the stage's show the stage's work on the ladder's model in the transcript's per-message counts. **Met for plan and build** (30 of 30 stage messages on Opus from a Sonnet default; 100 of 100 on Sonnet from an Opus default); the review stage is unmeasured.
- **R4** — a review of a trial build finds no convention the code breaks that `write-code` states, and files as feedback any it had to decide alone. **Met once** (`market-data`: the gaps became issues 28, 30 and 31, all closed).
- **R5** — the same for scaffold, layers and entry points. **Met once** (issues 32 and 33, closed).
- **R6** — the same for storage and unattended running; and one artefact deployed to a house-pick host and one message delivered by a house channel. **Partly met**: storage and scheduling exercised locally (issues 22, 23, 24, 27, closed); no deployment, no message.
- **R7** — `review-plugin` run against a plugin outside this repository produces a report without a push; and `maintain-plugin` installed alone on a second machine records feedback to a file. **Not met**: neither has been run.
- **R8** — the hook files on a seeded gap; a scheduled sweep opens a pull request; a sweep closes real issues with each fix run. **Met**: issue 20; pull request 19; issues 21 to 34 closed on 2026-11-11.
- **R9** — `claude plugin validate` passes everywhere; every trigger case passes; each plugin installed alone completes a task in its area and names what it lacked; a GitHub install on a second machine works; every `skills/` link resolves. **Partly met**: validation, the suites and the links pass; one partial-install run found the missing-plugin gap, fixed since and not re-run; no second machine.
- **R10** — a plan shows its decision list with sources and its ideas; a review can challenge a house pick. **Met once** (`market-data`'s plan: thirteen decisions with probes as sources, five skill overrides argued, four ideas).
- **R11** — a sweep with a fresh cold read ends with no defect open. **Met 2026-11-11**, with leftovers filed as issues 35 to 37.
- **R12** — `review-project`'s secret check, and no project data in any issue. **Met** at each sweep.

### Milestones

Done, in the order they happened (details in git history): M1 sweep the skills, M2 the project trio and feedback rule, M3 record the plan (2026-11-08); M5 unbox the process, M6 settle the code skills, M11 choose the model, M13 send messages (2026-11-10); M7 settle the structure skills, M8 store and run, M9 close the loop, M10 sweep, M12 deploy, M14 split into plugins (2026-11-11).
M11 was ticked on the skill existing and failed in use; D39 is the correction.

- [x] **M4 First trial build** — R1, R8; done when `market-data` is planned, built and reviewed with the trio and its feedback is worked through by a sweep (2026-11-11: sixteen issues filed, fourteen closed by the sweep, the rest filed as 35 to 37).
- [ ] **M15 Re-plan and rename** — R9; done when the plugins carry their verb-first names, this plan is signed off, and the README, the weekly sweep and memory agree with it.
- [ ] **M16 Tidy what the re-plan decided** — R11; done when issues 35 to 37 are settled, the frontmatter `model` lines are kept or dropped by decision, `evaluate/` is removed (D40), a licence is chosen and the first release is tagged (D41).
- [ ] **M17 Prove each plugin alone** — R7, R9; done when the R7 and R9 checks pass: each plugin alone on a task, `review-plugin` on an outside plugin, and a GitHub install on a second machine with feedback to a file.
- [ ] **M18 Second trial build, autonomous** — R1, R2, R3, R6; done when a project of a different kind (Q5) runs from one prompt with no user answers on a non-ladder default, deploys one artefact and sends one message where the user has allowed it, and its feedback is swept.
- [ ] **M19 Grow the scope as earned** — R1; a standing milestone: each Not yet item is built when a trial build or real project earns it.

## Open

### Assumptions

- **A1** The repository and marketplace keep their names (`claude`, `henrymckay`) — only plugins were asked to be renamed.
- **A2** Requirement numbers changed in this re-plan and decision numbers did not — nothing outside this file cites a requirement number; issues and commits cite decisions.
- **A3** The cloud sweep's `gh` is authenticated for REST and blocked for GraphQL, and vendor pages outside its proxy's allowlist are unreachable there, so the free-tier re-check runs in a local sweep (found 2026-11-10).

### Questions

- **Q1** Sign off this re-plan: R1 to R12 as worded, D39 to D41, and M15 to M19? — recommended: yes; blocks M15.
- **Q2** Drop the frontmatter `model` and `effort` lines from the four skills (issue 36)? — they tell a session it is on a model that is not serving it, and the hand-off now does the work; recommended: drop; blocks M16.
- **Q3** Which licence? — recommended: MIT, the usual choice for a public skills repository an employer may need to approve; blocks M16.
- **Q4** Confirm D37 (`coverage` over `pytest-cov`), D38 (no manifest row when the lock is held, and whether to delete the `skipped` outcome nothing produces), and D35's exemption of skill feedback from "no outward action"? — recommended: confirm all three and delete `skipped`; blocks M16.
- **Q5** What is the second trial build? — recommended: a small dashboard over `market-data`'s store, since it exercises what the first did not (a dashboard, a deployment, SQL, a message) on data that already exists; an accounting or tax tool is the alternative and tests a new domain instead; blocks M18.
- **Q6** What happens to `market-data`? — its plan is unsigned with eight questions open, and nothing is pushed; recommended: keep it as the store Q5's dashboard reads, answer its questions when convenient, and decide on a private GitHub repository then; blocks M18 only if Q5 is the dashboard.
- **Q7** At work, is a third-party marketplace allowed, or is it the symlink route? — only the user can find out; blocks M17's second-machine check.

### Ideas

- **I1** A `doctor` check in `maintain-plugin`: one command that validates manifests, runs the hooks, resolves the links and reports which sibling plugins are missing — would turn M17's checks into something a work install runs on day one; costs a script to maintain; not built.
- **I2** Have `build-project` write a short run log (model per stage, wall time, real runs and their size) into the project — the first trial build's model and backfill problems were found only by a coordinator reading transcripts; costs a section in one skill; not built.
- **I3** A budget line in `plan-project`'s Runs on for the build itself (expected stage cost at the ladder's prices) — the user asked about cost twice during the first trial; costs an estimate that will often be wrong; not built.
