# claude

Personal Claude Code skills and global instructions that let Claude build a high-quality project from a few prompts.

## Brief

### Goal

The user wants to set Claude off with minimal guidance and get a project that is elegant, efficient, correct and well tested, designed beyond the initial brief and named in its domain's language.
Done looks like: a real project planned, built and reviewed with these skills, needing one batch of answers from the user, and passing `review-project` with no defects left.

### Terms

- **skill** — a `skills/<name>/SKILL.md` with frontmatter, plus any `references/`, per the Agent Skills standard.
- **description** — a skill's frontmatter trigger text, all Claude sees when deciding to load it.
- **reference** — a file under a skill's `references/`, loaded only when the skill points there.
- **instruction file** — `CLAUDE.md`, loaded every session.
- **house pick** — a library or tool a skill chooses over its rivals.
- **drift** — a skill's description, rules or examples falling out of line with its body, its neighbours or current tools.
- **skill feedback** — a GitHub issue labelled `skill-feedback`, filed when a skill steered Claude wrong in real work.
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
- **R5** Keep the evaluation scaffolding, with no briefs checked in for now.

### Not yet

- **Packaging as an installable plugin** (`.claude-plugin/plugin.json`, marketplace) — earned when the skills need installing on another machine or by someone else; plugin skills are namespaced, so every cross-reference would change.
- **A debugging skill** — earned when skill feedback shows debugging going wrong.
- **A data-storage skill** — earned the same way.
- **A hook that prompts for skill feedback** — earned if issues are rarer than the user's corrections after a few builds.
- **References for a language other than Python** — earned by the first non-Python project.
- **CI** — declined for setup-python; nothing in this repo runs.
- **An evaluation per fixed issue** — declined as too big.
- **Checked-in evaluation briefs** — earned by a brief general enough to suit any user; the trade briefs are archived in the rough repo.
- **`agents/`, `commands/` and `rules/`** — the `~/.claude` symlinks for the first two already exist and dangle on purpose.

## Design

### Inputs

- **The user's conversations and corrections** — the requirements and most rules; corrections about skills arrive as skill feedback.
- **Skill feedback issues** — `gh issue list -R henrymckay/claude --label skill-feedback`.
- **Current tool docs and releases** — Claude Code, uv, ruff, Polars and the rest; every skill claim is checked against the current release.
- **Evaluation runs** — none checked in at present.

### Data flow

1. **Skill source** — `skills/<name>/SKILL.md` in this repo, edited only in the skills stream. (IO)
2. **Wiring** — `~/.claude/skills` and `~/.claude/CLAUDE.md` are symlinks into the repo, so a commit takes effect in the next session. (IO)
3. **Loading** — every session loads `CLAUDE.md` and each description; a skill's body loads when its description or `CLAUDE.md`'s list triggers it, a reference when the body points there.
4. **Applying** — Claude follows the loaded skills in real work in other repos.
5. **Feedback** — a skill that steers wrong becomes a skill-feedback issue here. (IO)
6. **Sweep** — `review-plugin` works the issues, then checks for drift, and commits each skill's fixes. Back to 1.

### Outputs

**`skills/<name>/SKILL.md`** — frontmatter `name` and `description`, then a body laid out by `write-skills`; read by Claude.
**`skills/<name>/references/*.md`** — language or topic depth, per `write-skills`.
**`CLAUDE.md`** — Work, Answers and the mandatory Skills list; read by Claude every session.
**`README.md`** — for humans: what each skill does, setup, configuration, feedback, evaluation.
**`PLAN.md`** — this file.
**`evaluate/prompt.md`** — the evaluation driver.

### Interface

```bash
git clone https://github.com/henrymckay/claude.git
ln -s /path/to/claude/skills ~/.claude/skills
ln -s /path/to/claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Skills trigger from their descriptions or by name (`/plan-project`); "review the skills" runs `review-plugin`.

### Errors

- **A description fails to trigger, or fires on the wrong task** — found by review-plugin's trigger-overlap check or by skill feedback; fixed in the description.
- **A rule is duplicated or contradicted** — found by review-plugin; kept where it belongs, pointed at from elsewhere.
- **A library claim goes stale** — found by re-running every claim against the current release in each sweep.
- **A symlink dangles** — found by review-plugin's wiring check; `agents` and `commands` dangle on purpose.
- **Feedback carries project data** — the `CLAUDE.md` rule requires describing the shape of the case; delete or edit such an issue on sight.

### Decisions

- **Symlinks into `~/.claude`** over an installable plugin or symlinking all of `~/.claude` — no namespacing of names, and machine-local state stays out of git.
- **Commit straight to `main`** as `henrymckay <henrymckay@users.noreply.github.com>`, `docs(<skill>): …` over feature branches — a solo docs repo with nothing to merge; overrides `use-git`'s branch default.
- **Skill feedback as GitHub issues** over memory or a notes file — visible to the user, closable from a commit, and not per-machine.
- **The filing rule in `CLAUDE.md`** over a skill — a skill only loads for a matching task, and feedback arises mid-task in any work.
- **`review-project` general, `review-plugin` layered on it** over two independent reviews — one set of review mechanics.
- **`build-project`** over `develop-project` — matches "the build" wording across the skills.
- **`be-functional` the default style, `be-oop` opt-in** over both opt-in.
- **Evaluation briefs archived to the rough repo** over keeping trade-specific briefs here — they taught one domain.
- **No performance budget** — nothing here runs.
- **Not yet lives in this plan** over `enhancement` issues — issues are kept for skill feedback.
- **The README points at this plan** with a short note on how the skills fit together, over copying it — the README is for humans, the plan for Claude.
- **Memory holds only what this plan doesn't** — the plan is visible and versioned; memory is per-machine.

## Delivery

### Verification

- **R1** — M4: a real project built with plan-project → build-project → review-project, the user answering one batch, and review-project leaving no defects.
- **R2** — a `review-plugin` sweep that ends with no defects open, every code block through ruff and every library claim run.
- **R3** — the `skill-feedback` label exists, `CLAUDE.md` carries the rule, and review-plugin's first section works the issues; ongoing work is tracked in the issues, not here.
- **R4** — review-project's secret check, and no project data in any open issue.
- **R5** — `evaluate/prompt.md` present, no briefs under `evaluate/`.

### Milestones

- [x] **M1 Sweep the skills** — R2; done when review-plugin left no defects (2026-11-08).
- [x] **M2 Project trio and feedback loop** — R1, R3; done when plan-, build- and review-project and the skill-feedback rule were committed (2026-11-08).
- [ ] **M3 Record the plan** — R3, R4; done when `PLAN.md` is committed, the README points at it, and memory holds only what this plan doesn't.
- [ ] **M4 First real build** — R1; done when `market-data` is planned, built and reviewed with the trio in its own session, and its skill feedback is worked through by review-plugin.

## Open

### Assumptions

None.

### Questions

None.
