# claude

Personal Claude Code skills and global instructions that let Claude build a high-quality project from a few prompts.

## Brief

### Goal

The user wants to set Claude off with minimal guidance and get a project that is elegant, efficient, correct and well tested, designed beyond the initial brief and named in its domain's language.
Done looks like: a real project planned, built and reviewed with these skills, needing one batch of answers from the user, and passing `review-project` with no defects left.

### Terms

- **skill** — a `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter, plus any `references/`, per the Agent Skills standard.
- **plugin** — a folder under `plugins/` with a manifest, skills, a session-start hook and a trigger suite, installable on its own; the repo is a **marketplace** listing five.
- **context file** — a plugin's `hooks/context.md`, its always-on skill list, printed at session start.
- **description** — a skill's frontmatter trigger text, all Claude sees when deciding to load it.
- **reference** — a file under a skill's `references/`, loaded only when the skill points there.
- **instruction file** — `CLAUDE.md`, loaded every session.
- **house pick** — a library or tool a skill chooses over its rivals.
- **drift** — a skill's description, rules or examples falling out of line with its body, its neighbours or current tools.
- **skill feedback** — a GitHub issue labelled `skill-feedback` on the owning plugin's repository, filed when a skill steered Claude wrong in real work; a machine that must not reach a public tracker records it to a file instead.
- **evaluation** — a build from a `brief.md`, graded against its `answers.md`, driven by `evaluate/prompt.md`.
- **build stream** / **skills stream** — building real projects with the skills as they stand / improving the skills from skill feedback and evaluations.

### Requirements

- **R1** With the skills loaded, Claude produces a stylistic, elegant, efficient, correct and well-tested project from minimal guidance, thought about beyond the initial brief and named in its domain's language.
  - Cost: the plan → build → review trio and every quality gate in it; dropping it leaves code-level skills only.
- **R2** Skills are clear, concise, non-contradictory and not overfitted to one project.
  - Cost: `review-plugin` sweeps and the write-skills rules (state once, keep examples general, run every claim).
- **R3** Skills improve from real feedback, not speculation, without editing them mid-build.
  - Cost: the skill-feedback issue rule in `CLAUDE.md` and review-plugin's Work the feedback.
- **R4** The repo is public: generic conventions only, no secrets, no project data, no machine-local state.
  - Cost: every example in a domain any reader knows, and feedback issues that describe a shape, never a case.
- **R5** Keep the evaluation scaffolding, with no briefs checked in for now.
  - Cost: `evaluate/prompt.md` maintained with nothing exercising it until a brief general enough to publish exists.
- **R6** The skills carry the pre-made decisions a Python data, CLI, API or dashboard project needs — process, design, packages, naming, organisation — so none has to be asked during planning, and nothing Claude does by default.
  - Cost: house picks the user can't verify alone and periodic re-checks against current releases; dropping it leaves every build to re-decide.
- **R7** The skills don't box Claude in: it researches the domain and current practice, treats a skill's default as a default, proposes ideas beyond the brief and the skills, and puts its decisions, alternatives, costs and sources in front of the user so they can challenge them.
  - Cost: longer plans and one more surface to read; dropping it leaves the user supplying the knowledge.
- **R8** The plugin maintains and improves itself as it is used: skill gaps are captured without relying on recall, worked through on a schedule, and fixes are checked by running, with the user reviewing the result.
  - Cost: a hook, a scheduled task, a trigger eval suite; dropping it leaves improvement to the user remembering to ask.
- **R9** Each stage of a project, and of this plugin's upkeep, runs on the most appropriate model, effort and mode with an eye on cost, chosen by Claude where Claude can choose.
  - Cost: a ladder to maintain as models and prices change; dropping it leaves every stage on whatever the session started with.
- **R10** A project's deployment is decided in the plan and built by the skills — dashboards, pipelines, data and APIs on the best free or very-low-cost hosts — so none of it is a decision during the build.
  - Cost: free tiers change yearly, so the picks need re-checking in each sweep.
- **R11** A deployed project can message the user — alerts, digests, a two-way assistant — through channels the user reads, and a Claude Code session can reach them too.
- **R12** The skills install selectively and work beyond this repo and machine: grouped into plugins that stand alone and work together, usable by symlink where plugins cannot be installed, with the review and the feedback loop applying to any plugin whose source can be read (2026-11-11).
  - Cost: five manifests, a context file per plugin duplicating `CLAUDE.md`'s list, a trigger suite per plugin, and cross-plugin pointers that must read correctly with the neighbour absent.
  - Cost: a secret per channel on each host; dropping it leaves outages unnoticed.

### Not yet

- **A repository per plugin** — earned when a plugin needs different visibility or another owner; one repo keeps one tracker, one weekly pull request and cross-plugin drift caught in one sweep, and the marketplace can list a plugin that lives elsewhere.
- **A licence and icons** — earned by submitting to the public plugin directory; the licence is the user's choice.
- **Toolchain skills other than `uv`** (Bazel and the like) — they belong in the repo that uses the toolchain, as project skills or a private plugin.
- **A debugging skill** — earned when skill feedback shows debugging going wrong.
- **References for a language other than Python** — earned by the first non-Python project; the scope is Python data, CLI, API and dashboards (2026-11-10).
- **CI for projects** — declined again 2026-11-10 as marginal for one-machine unattended tools; earned by a project with a second contributor or a deploy.
- **An evaluation per fixed issue** — declined as too big; the trigger suite (R8) checks only that descriptions fire.
- **Snapshot tests, mutation testing, a task runner, Docker, dev containers, docs generation** — each earned by the first project that needs it; the skills say "none" until then.
- **Checked-in evaluation briefs** — earned by a brief general enough to suit any user; the trade briefs are archived in the rough repo.
- **`agents/`, `commands/` and `rules/`** — the `~/.claude` symlinks for the first two already exist and dangle on purpose.
- **Slack as a message channel** — earned once the user has a workspace they read; the skill names it as an alternative until then.
- **An `advisor` second-model step mid-task** — Claude Code documents one; earned when a build stage keeps failing its gate on Sonnet.

## Design

### Inputs

- **The user's conversations and corrections** — the requirements and most rules; corrections about skills arrive as skill feedback.
- **Skill feedback issues** — `gh issue list -R henrymckay/claude --label skill-feedback`.
- **Current tool docs and releases** — Claude Code, uv, ruff, Polars and the rest; every skill claim is checked against the current release.
- **Evaluation runs** — none checked in at present.

### Data flow

1. **Skill source** — `plugins/<plugin>/skills/<name>/SKILL.md` in this repo, edited only in the skills stream. (IO)
2. **Wiring** — either the plugins are installed from the marketplace, or `~/.claude/skills` is a symlink to the repo's `skills/` folder of links into the plugins and `~/.claude/CLAUDE.md` a symlink to the repo's; never both on one machine, which would load every skill twice. (IO)
3. **Loading** — every session loads each description and the always-on list (`CLAUDE.md` when symlinked, each installed plugin's context file otherwise); a skill's body loads when its description or the list triggers it, a reference when the body points there.
4. **Applying** — Claude follows the loaded skills in real work in other repos.
5. **Feedback** — a skill that steers wrong becomes skill feedback on the owning plugin's repository. (IO)
6. **Sweep** — `review-plugin` works the issues, then checks for drift, and commits each skill's fixes, which loops back to stage 1.

### Outputs

- **`plugins/<plugin>/skills/<name>/SKILL.md`** — frontmatter `name` and `description`, then a body laid out by `write-skills`; read by Claude.
- **`plugins/<plugin>/`** — `.claude-plugin/plugin.json`, `hooks/` (the context file and the script that prints it; `meta` adds the feedback rule and the Stop hook) and `evals/` (one trigger case per skill).
- **`.claude-plugin/marketplace.json`** — lists the five plugins by relative path.
- **`skills/<name>`** — a relative symlink to the skill in its plugin, for the symlink wiring.
- **`plugins/<plugin>/skills/<name>/references/*.md`** — language or topic depth, per `write-skills`.
- **`CLAUDE.md`** — Work, Answers and the mandatory Skills list; read by Claude every session.
- **`README.md`** — for humans: what each skill does, setup, configuration, feedback, evaluation.
- **`PLAN.md`** — this file.
- **`evaluate/prompt.md`** — the evaluation driver.

### Interface

Installed, any subset:

```bash
claude plugin marketplace add henrymckay/claude
claude plugin install project@henrymckay
```

Symlinked, where the skills are authored or plugins cannot be installed:

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Skills trigger from their descriptions or by name (`/plan-project`, or `/project:plan-project` when installed); "review the skills" runs `review-plugin`.

| Plugin | Skills |
|---|---|
| `meta` | `choose-model`, `review-plugin`, `write-skills`, the feedback rule and Stop hook |
| `project` | `plan-project`, `build-project`, `review-project`, `use-git`, `write-markdown` |
| `code` | `be-functional`, `be-oop`, `write-python`, `write-sql`, `write-tests`, `use-polars` |
| `scaffold` | `setup-python`, `structure-python`, `write-entry-points` |
| `operate` | `store-data`, `run-unattended`, `deploy-project`, `send-messages` |

### Runs on

- **The skills and `CLAUDE.md`** — the user's machine: the five plugins installed from the repo as a local marketplace, which loads them in place so edits stay live, and `~/.claude/CLAUDE.md` symlinked; another machine installs from GitHub, or symlinks `skills/`; nothing is deployed.
- **The weekly sweep** — a Claude Code cloud scheduled task (`trig_01NmQMC42vGPjqQEDE8XrgzQ`), Mondays 02:00 UTC on Opus, cloning the public repo and opening one PR; no connectors; checked 2026-11-10.
- **The Stop hook** — carried by the installed `meta` plugin (`plugins/meta/hooks/hooks.json`); with the symlink wiring its `Stop` entry is merged into `~/.claude/settings.json`.
- **The trigger suite** — `claude plugin eval` on the user's machine, or in the sweep where the CLI is available.

### Errors

- **A description fails to trigger, or fires on the wrong task** — found by review-plugin's trigger-overlap check or by skill feedback; fixed in the description.
- **A rule is duplicated or contradicted** — found by review-plugin; kept where it belongs, pointed at from elsewhere.
- **A library claim goes stale** — found by re-running every claim against the current release in each sweep.
- **A symlink dangles** — found by review-plugin's wiring check; `agents` and `commands` dangle on purpose.
- **Feedback carries project data** — the `CLAUDE.md` rule requires describing the shape of the case; delete or edit such an issue on sight.

### Decisions

- **D1 Symlinks into `~/.claude`** remain a supported wiring for a machine that cannot install plugins; the authoring machine moved to the installed plugins on 2026-11-11 so it runs what others install (D30).
- **D2 Commit straight to `main`** as `henrymckay <henrymckay@users.noreply.github.com>`, `docs(<skill>): …` over feature branches — a solo docs repo with nothing to merge; overrides `use-git`'s branch default; the scheduled sweep's weekly PR is the one exception.
- **D3 Skill feedback as GitHub issues** over memory or a notes file — visible to the user, closable from a commit, and not per-machine.
- **D4 The filing rule in `CLAUDE.md`** over a skill — a skill only loads for a matching task, and feedback arises mid-task in any work.
- **D5 `review-project` general, `review-plugin` layered on it** over two independent reviews — one set of review mechanics.
- **D6 `build-project`** over `develop-project` — matches "the build" wording across the skills.
- **D7 `be-functional` the default style, `be-oop` opt-in** over both opt-in.
- **D8 Evaluation briefs archived to the rough repo** over keeping trade-specific briefs here — they taught one domain.
- **D9 No performance budget** — nothing here runs.
- **D10 Not yet lives in this plan** over `enhancement` issues — issues are kept for skill feedback.
- **D11 The README points at this plan** with a short note on how the skills fit together, over copying it — the README is for humans, the plan for Claude.
- **D12 Memory holds only what this plan doesn't** — the plan is visible and versioned; memory is per-machine.
- **D13 A skill's default is a default** (2026-11-10) — a `PLAN.md` decision the user signed off overrides a skill; a reason Claude finds is recorded as a proposed decision and raised before it is built on; a rule stays imperative with its exception in the same sentence, never softened to "prefer", because softened rules were ignored outright.
- **D14 Decisions are surfaced, not buried** — plan-project's one batch lists Claude's decisions with alternatives, costs and sources beside the questions and assumptions; build and review reports list the calls made.
- **D15 `functools.partial`, closures and `match`** over `toolz` and `plum` as defaults — `toolz` ships no type hints, so pyright loses every curried function; both stay mentioned for the case that earns them.
- **D16 One error model** — raise from the app's `error/` package; an adapter converts a library's failure or classifies an item's outcome at its seam, only a driver decides what the user sees, and nothing in the core catches; `X | None` only for a lookup miss the caller always branches on; no `Result` library.
- **D17 One record type** — `@dataclass(frozen=True, slots=True, kw_only=True)` in the core; `pydantic` only across a trust boundary; `NamedTuple` only for tuple semantics; never `attrs`.
- **D18 `uv_build`** over `hatchling` — zero config for a src layout; `hatchling` only when a build plugin is needed.
- **D19 pyright `strict`** over `standard` on a greenfield project — the only mode that catches an `Unknown` in fresh code.
- **D20 House picks adopted 2026-11-10** — datetime: aware `datetime` + `zoneinfo`, UTC in the core; money: `Decimal` or minor units; storage: hive-partitioned Parquet for pipeline output, DuckDB to query it, MotherDuck when more than one machine or a phone chat must reach it, SQLite for small single-writer state; config: `pydantic-settings` with `.env` locally, a user-editable CSV in the data directory for lists, package YAML for per-source constants; HTTP: sync `httpx`, `tenacity`, `pyrate-limiter`, key in a header; sync core with async only in a driver or adapter whose framework or fan-out needs it; logging: stdlib + `RichHandler` on stderr, JSON lines behind a collector; plotting: `plotly` via `shinywidgets`; frame contracts: `match_to_schema`; test doubles: `monkeypatch` and `time-machine`; releases: `uv version --bump` then tag.
- **D21 Two new skills, `store-data` and `run-unattended`** — the gap probe left 72 decisions open and these two absorb most of them.
- **D22 MotherDuck connects with `duckdb.connect("md:<db>")` and the token in `motherduck_token`**, lower case per its docs (checked 2026-11-10); A1 had it upper case.
- **D23 A trigger suite per plugin at `plugins/<plugin>/evals/`**, the default folder `claude plugin eval` reads, over one suite at the root — an eval run targets one plugin; the brief-and-answers evaluations stay under `evaluate/`.
- **D24 The scheduled sweep lands as one weekly PR**; an on-demand sweep run in a session commits to `main` — the PR is the user's review point, and cloud tasks push to a branch by default.
- **D25 A `Stop` hook prompts for unfiled skill gaps** — the only hook that can reach the model, since `SessionEnd` cannot; hook text in the repo, the `settings.json` entry in the README.
- **D26 A fourth sweep outcome, "needs the user"** — an unattended run never changes a decision or settles policy; it leaves the issue open with a recommended answer.
- **D27 The model ladder** (2026-11-10) — Opus (Fable for the hardest design) at high effort for planning, reviews and skill edits; Sonnet for build milestones, cold reads and research; Haiku for graders, hooks and trigger evals — over one model throughout; applied by the project skills' frontmatter `model` and `effort`, which set the turn's model, and by the Agent tool's per-subagent parameters.
The ladder holds whatever the session's default model is (the user, 2026-11-11, issue 25): the frontmatter changed the model a session was told it was on and not the one serving it, in a headless plan and build and in an interactive sweep (Claude Code 2.1.322, read from each transcript's per-message model), so each stage always hands its work to a subagent with the Agent tool's model and effort set, and the frontmatter is kept for its effort alone.
- **D28 The weekly sweep runs on Opus** on Mondays at 02:00 UTC (06:00 Dubai) with no connectors — skill edits are reasoning work, and a connector acting as the user is a risk the sweep doesn't need.
- **D29 Message channels for this user** — ntfy for a failure alert (one phone app, no account), the user's own email for a digest with a chart, Claude Code channels (iMessage on the Mac, Telegram elsewhere) for a two-way assistant; Slack only once a workspace exists; iMessage never from the cloud.
- **D30 One repo as a marketplace of five plugins** over one plugin or a repo each — the user installs some at work and not others; one repo keeps one tracker and one sweep (see Not yet). Source: code.claude.com/docs/en/plugins/create-marketplace, checked 2026-11-11.
- **D31 The groups**: `meta` (working with Claude Code itself), `project` (the lifecycle plus `use-git` and `write-markdown`, which any repo needs), `code` (style, toolchain-free), `scaffold` (set-up and structure, where `uv` lives) and `operate` (a project meeting the real world; personal free-tier picks, so not for work). `deploy-project` sits in `operate` because its body is host picks; `plan-project`'s Runs on is the lifecycle's deployment step. The name `claude` is reserved by the validator, hence `meta`.
- **D32 Always-on instructions per plugin are a context file printed by a SessionStart hook** over a plugin `CLAUDE.md`, which Claude Code does not load; `CLAUDE.md` keeps the same lines for the symlink wiring, and `review-plugin` checks the two agree.
- **D33 Feedback goes to the owning plugin's repository**, read from its manifest or named in the user's `CLAUDE.md`, over a repository written into the skills; `meta`'s `feedback` option (`issues`, `file`, `off`) redirects it on a machine whose work must not reach a public tracker. Issues remain the default.
- **D34 A toolchain's commands live in the skill that owns it** — `uv` in `setup-python`, with `operate` building on it; `project` and `code` name a `uv` command only as that toolchain's example, so they hold under Bazel or anything else.

- **D35 Autonomous mode** (the user, 2026-11-11, issue 21) — with no user present, Claude proceeds on its recommended answers, records each as an assumption for the user's later review, keeps decisions marked proposed, and never takes an outward action such as creating a repository, publishing or spending money; `plan-project` defines it and `build-project` and `review-project` each state it. Skill feedback is still recorded as the feedback rule says *(that last clause proposed, from issue 29)*.
- **D36 A `write-sql` skill in `code`** (the user, 2026-11-11, issue 30) over a section of `store-data` — decisions only: SQL against Polars, where SQL lives, style, schema changes and testing a documented query, in a dialect-neutral body with a reference per dialect, DuckDB first.
- **D37 `coverage run -m pytest`** over `pytest-cov` *(proposed, issue 31)* — the `-p` plugin `setup-python`'s own `addopts` loads imports the package before `--cov` measures, which read 33% for a true 83% on a two-module package (pytest-cov 7.1, coverage 7.17); cost: two commands where one flag did.
- **D38 A run that finds the lock held writes no manifest row** *(proposed, issue 27)* over a `skipped` row — the run in progress records the night, and a `skipped` row would exit 1 where the lock rule exits 0; `skipped` stays for a source a run ended before reaching.

## Delivery

### Verification

- **R1** — M4: a real project built with plan-project → build-project → review-project, the user answering one batch, and review-project leaving no defects.
- **R2** — a `review-plugin` sweep that ends with no defects open, every code block through ruff and every library claim run.
- **R3** — the `skill-feedback` label exists, `CLAUDE.md` carries the rule, and review-plugin's first section works the issues; ongoing work is tracked in the issues, not here.
- **R4** — review-project's secret check, and no project data in any open issue.
- **R5** — `evaluate/prompt.md` present, no briefs under `evaluate/`.
- **R6** — the gap probe re-run (a fresh agent plans the generic nightly fetch → store → metrics → CLI → API → dashboard tool from the skills alone) leaves no decision open that a skill should settle, and names no rule it would have followed anyway.
- **R7** — a plan written with plan-project shows the decision list with sources; the trio's files each state when and how to deviate from a skill; a review can flag a house pick as wrong for the project.
- **R8** — the hook fires and files on a seeded gap; the scheduled task runs and opens a PR; `claude plugin eval . --ablation none`, run in each plugin folder, passes every case under its `evals/`.
- **R9** — `choose-model` exists; plan-, build-, review-project and review-plugin carry the ladder in their frontmatter; a subagent spawned by a review goes out on the ladder's model.
- **R10** — `deploy-project` exists with a verified free-tier pick per artefact, `plan-project`'s skeleton has a Runs on section, and the gap probe (R6) leaves no deployment decision open.
- **R11** — `send-messages` exists with a working send for each house channel, and `run-unattended` points at it for the alert it deferred.
- **R12** — `claude plugin validate` passes on the marketplace and each plugin; a session loaded with `--plugin-dir` receives the context file and sees the skills; every link under `skills/` resolves; each plugin's trigger suite passes; no skill or hook names this repository.

### Milestones

- [x] **M1 Sweep the skills** — R2; done when review-plugin left no defects (2026-11-08).
- [x] **M2 Project trio and feedback loop** — R1, R3; done when plan-, build- and review-project and the skill-feedback rule were committed (2026-11-08).
- [x] **M3 Record the plan** — R3, R4; done when `PLAN.md` is committed, the README points at it, and memory holds only what this plan doesn't (2026-11-08).
- [x] **M5 Unbox the process** — R7; done when CLAUDE.md and plan-, build-, review-project and review-plugin state the default-is-a-default rule, research with sources, the decision list in the batch, the fourth sweep outcome, and the gap probe's process contradictions are ruled on (2026-11-10).
- [x] **M6 Settle the code skills** — R6; done when write-python, be-functional, be-oop, write-tests and their references carry the error model, record type, datetime, money, typing depth and async decisions, the wrong claims are fixed, the default-test cuts are made, and every code block and library claim runs (2026-11-10).
- [x] **M7 Settle the structure skills** — R6; done when setup-python, structure-python, write-entry-points, use-polars and use-git carry the house picks above, the ten gap-probe contradictions are ruled on, and every claim runs (2026-11-11).
- [x] **M8 Store and run** — R6; done when `store-data` and `run-unattended` exist, are listed in CLAUDE.md and the README, and the gap probe re-run (R6) passes (2026-11-11).
- [x] **M9 Close the loop** — R8; done when the Stop hook, the weekly scheduled task and the trigger eval suite each pass their R8 check (2026-11-11: the hook, from the installed `meta` plugin, filed seeded issue #20; the sweep opened pull request 19; 20 of 20 trigger cases pass).
- [x] **M10 Sweep** — R2; done when review-plugin, with a fresh cold read, leaves no defects (2026-11-11).
- [x] **M11 Choose the model** — R9; done when `choose-model` is committed and the four project skills carry `model` and `effort` (2026-11-10).
- [x] **M12 Deploy** — R10; done when `deploy-project` is committed with sources for every free-tier claim, `plan-project` has Runs on, and the gap probe leaves no deployment decision open (2026-11-11).
- [x] **M13 Send messages** — R11; done when `send-messages` is committed with its sends run, and `run-unattended` and `CLAUDE.md` point at it (2026-11-10).
- [x] **M14 Split into plugins** — R12; done when its verification passes and the README, the weekly sweep and memory describe the new layout (2026-11-11).
- [ ] **M4 First real build** — R1; done when `market-data` is planned, built and reviewed with the trio in its own session, and its skill feedback is worked through by review-plugin; it runs after M10.

## Open

### Assumptions

- **A2** Resolved 2026-11-10 by the first run: the cloud task's `gh` is authenticated for REST but GraphQL is blocked, so the sweep lists issues with `gh api` and can open a pull request; vendor pages outside the proxy's allowlist are unreachable there, so the free-tier re-check runs in a local sweep.

### Questions

None.

### Ideas

None.
