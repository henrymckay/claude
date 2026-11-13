---
name: review-project
effort: high
description: >-
  How to review a whole project and fix what it finds — against its PLAN.md,
  then correctness, tests, the skills' conventions, current releases, docs and
  safety, with a cold read, each finding's evidence re-run and each fix its
  own commit. Use whenever the user asks to review, audit or tidy a repo,
  check it against its plan or fix what a review found — even if they just say
  "review this repo" or "is this up to date". Not for a plugin or skills repo,
  which is review-plugin's.
---

# Review the project

A review of a whole project against its plan, the skills and the current state of its tools, followed by fixing what it finds.
It layers on `plan-project` (the plan it checks against) and on every skill the code falls under, uses the built-in `/code-review` for the bug hunt, `secure-project` for the safety checks and `make-decisions` for the judgement calls; `review-plugin` extends it for a Claude Code plugin.
Three mistakes account for most weak reviews: reading code instead of running it, reporting a preference as a defect when no plan or skill backs it, and fixing everything in one sweep, with no regression test and a recorded decision quietly overturned.

- **Wrong** — "Defect: the adapter should use a dataclass here" with no rule cited, fixed in the same sweep as a real bug.
- **Right** — "Judgement call: a dataclass would read better (no rule); Defect: `fetch` returns one page when given no limit (`write-python`, Decide every default)", the defect fixed with a regression test, the call left for the reply.

**In an existing project, ask first.** Where a repo already has its own conventions, check with the user whether to review against them or against the skills, and prefer the skills unless they choose to match.

## Set the standard

**Review on Opus at high effort, whatever the session started on: hand the review and its fixes to a foreground subagent with `model: opus` and `effort: high`**, briefed as `choose-model`'s Hold a stage on its model says, with whether the run is autonomous, and relay its report.
A session briefed as that subagent works directly.

Judge the project against what it set out to do and what the skills require, never against taste.

- **The plan** — `PLAN.md` where there is one: its requirements, decisions and Not yet.
Without one, take the goal from the README and the conversation, run every other check, and say in the report that the plan checks were skipped.
- **The skills** — invoke each one the code falls under, and read the project's own `CLAUDE.md`.
- **Record each finding** with an ID, its evidence (a file and line, or a command and its output) and the requirement or rule it breaks.
A finding that cites neither is a preference: label it one, or drop it.
- **A challenge is neither.** A house pick or recorded decision that evidence — a measurement, the current docs, a comparable tool — shows fits this project badly is reported as a challenge, with the evidence and a proposed change, and never fixed without sign-off.
Without this class a review can only ever confirm the skills.

## Check against the plan

Skip this section without a `PLAN.md`.

- **Every requirement is built and cited by a check** in Verification; a requirement nothing cites is unbuilt until shown otherwise.
- **Every ticked milestone is true** — run its check, and untick one that fails.
- **Nothing in Not yet has been built**, and every decision is honoured; structure ahead of its requirement is a finding, however diligent it looks.
- **Open holds nothing stale** — an assumption the code already settled, a question already answered.

## Check correctness

- **Run the whole suite** and read every failure and warning.
- **Run the real surface** — every command, endpoint or screen against real input — and read the counts, not the exit code (see `write-tests`).
- **Measure what the plan budgets** — time and memory on input of the size Inputs gives, against each performance requirement.
Without a budget, time the real surface anyway and flag only what is slow at its real input size, profiling before naming a cause.
- **Hunt for bugs with `/code-review`** on the codebase rather than a diff, at a medium level unless the user named one.

## Check the tests

Measure branch coverage with the toolchain's own command (`setup-python`, Libraries), check the report shows the package's import lines as run before trusting its number, then read *which* branches are uncovered, and hold the suite to `write-tests` — above all that each fixture can exhibit the failure its test looks for, and that every overridden library default is pinned by its effect.
A high percentage over tests that assert nothing is a finding, not a pass.

## Check against the skills

Read the code against each skill invoked above: the layout against `setup-python`, the layers against `structure-python`, the drivers against `write-entry-points`, and the code against `write-python`, `be-functional`, for frames `use-polars` and for queries `write-sql`.
Quote the rule a finding breaks.
A rule the project breaks under a `PLAN.md` decision naming the skill is not a defect; it can still be challenged.

## Check modernity

- **Dependencies at their current releases** — under `setup-python`'s toolchain, `uv tree --outdated --depth 1`.
Read the changelog before recommending a major upgrade.
- **No deprecated APIs** — run the suite with deprecations as errors (for `pytest`, `uv run pytest -W error::DeprecationWarning`).
- **The latest stable language** — `requires-python` and the syntax it allows.
- **No superseded tool or library** — compare with the house picks in `setup-python`, and with the pre-commit revisions.
- **Each house pick still stands** — a release since the skill was written can change the picture; check the pick's current standing and challenge it with evidence where it no longer fits.

## Check documentation and safety

- **The README matches the code and the plan** — run its commands as written, check each claim about an outside tool against that tool's current docs, and read it against Decisions: a section describing something a decision, proposed or signed off, removes is a finding even while the thing still exists.
- **The project's `CLAUDE.md` is current** — no stale path or command, no default Claude follows anyway, nothing a skill contradicts; it and the README are judged whole against `write-markdown` for length and organisation, not only for truth.
- **The project keeps `secure-project`** — every input and output classed and nowhere its class forbids, no secret in the tree or its history, and the dependency audit and the security review clean, run as its Review it says.

## Get a cold read

After your own pass, give a fresh agent on `sonnet` (see `choose-model`) the files and the standard, never your conclusions, and ask what breaks the plan or the skills; an agent handed your findings tends to confirm them.
Spawn it even when this review was handed to you with "do the work yourself": that line forbids passing the review on whole, not a second reader.
Where the skills live outside the directories the agent may read, put the rules themselves in the brief, and report a cold read that never saw the standard as partial.
Verify each finding, the cold read's and your own, by re-running its evidence — open the line, run the command — before it enters the report; an agent's mistakes read as confidently as its catches, and `/code-review` and `claude-security` already have independent agents confirm theirs.

## Report

Rank the findings by what they would change — a wrong answer before a missing test, a missing test before a style breach — and give each its evidence and the rule it breaks.
Separate defects from judgement calls and challenges, and list the checks skipped and why.
Every claim that a check passed or a fix works names the command that showed it and what it printed; one with no run behind it is reported as not run.

## Fix

Fix the defects without waiting, in ranked order; a judgement call a precedent settles is fixed too, citing it (`make-decisions`), while one with no precedent, a challenge or a change to a requirement or decision in `PLAN.md` waits for the user's reply to the report (see `plan-project`).

- **In autonomous mode the report is the batch**, as `plan-project`'s Plan with no user present says: review against the skills where the opening would have asked, fix the defects, leave each judgement call, challenge and decision change in the report with a recommended answer and every decision *(proposed)*, record what was assumed under the plan's Assumptions, and take no outward action.
- **A bug gets a regression test** that fails before the fix and passes after.
- **Commit each fix on its own** (see `use-git`), so one can be reverted alone.
- **Re-run every check at the end**, since one fix can break what another check passed.
- **Bring `PLAN.md` and the README up to date** with what changed, then report what changed in behaviour, the calls made while fixing, and what was left, and why.
