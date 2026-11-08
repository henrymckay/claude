---
name: review-project
description: >-
  How to review a whole project and then fix what the review finds — checking
  it against its PLAN.md where there is one, then correctness (the tests, the
  real surface, a bug hunt), the test suite, conformance to the skills,
  modernity (current releases, no deprecated APIs, the latest language),
  documentation and safety, with an unanchored cold read; then fixing the
  findings by impact, each with its own commit and, for a bug, a regression
  test. Use whenever the user asks to review, audit, critique or tidy a repo or
  project, check it against its plan or the conventions, find what is out of
  date, or fix what a review found — even if they just say "review this repo",
  "what's wrong with this project", or "is this up to date". Works without a
  PLAN.md. Layers on plan-project and every skill the project's code falls
  under, using the built-in code-review for the bug hunt; review-plugin extends
  it for a Claude Code plugin.
---

# Review the project

A review of a whole project against its plan, the skills and the current state of its tools, followed by fixing what it finds.
It layers on `plan-project` (the plan it checks against) and on every skill the code falls under, and uses the built-in `/code-review` for the bug hunt rather than reimplementing one; `review-plugin` extends it for a Claude Code plugin.
Three mistakes account for most weak reviews: reading code instead of running it, reporting a preference as a defect when no plan or skill backs it, and fixing everything in one sweep, with no regression test and a recorded decision quietly overturned.

**In an existing project, ask first.** Where a repo already has its own conventions, check with the user whether to review against them or against the skills, and prefer the skills unless they choose to match.

## Set the standard

Judge the project against what it set out to do and what the skills require, never against taste.

- **The plan** — `PLAN.md` where there is one: its requirements, decisions and Not yet.
Without one, take the goal from the README and the conversation, run every other check, and say in the report that the plan checks were skipped.
- **The skills** — invoke each one the code falls under, and the project's own `CLAUDE.md`.
- **Record each finding** with an ID, its evidence (a file and line, or a command and its output) and the requirement or rule it breaks.
A finding that cites neither is a preference: label it one, or drop it.

## Check against the plan

Skip this section without a `PLAN.md`.

- **Every requirement is built and cited by a check** in Verification; a requirement nothing cites is unbuilt until shown otherwise.
- **Every ticked milestone is true** — run its check.
- **Nothing in Not yet has been built**, and every decision is honoured; structure ahead of its requirement is a finding, however diligent it looks.
- **Open holds nothing stale** — an assumption the code already settled, a question already answered.

## Check correctness

- **Run the whole suite** and read every failure and warning.
- **Run the real surface** — every command, endpoint or screen against real input — and read the counts, not the exit code (see `write-tests`).
- **Hunt for bugs with `/code-review`** on the codebase rather than a diff, at the level the user asked for; never `max` or `ultra` unless they asked.

## Check the tests

Measure coverage, then read *which* branches are uncovered, and hold the suite to `write-tests` — above all that each fixture can exhibit the failure its test looks for, and that every overridden library default is pinned by its effect.
A high percentage over tests that assert nothing is a finding, not a pass.

## Check against the skills

Read the code against each skill invoked above: the layout against `setup-python`, the layers against `structure-python`, the drivers against `write-entry-points`, and the code against `write-python`, `be-functional` and, for frames, `use-polars`.
Quote the rule a finding breaks.
A rule the project breaks on purpose — a recorded decision, its own `CLAUDE.md` — is not a finding.

## Check modernity

- **Dependencies at their current releases** — for Python, `uv tree --outdated --depth 1`.
Read the changelog before recommending a major upgrade.
- **No deprecated APIs** — run the suite with deprecations as errors (`uv run pytest -W error::DeprecationWarning`).
- **The latest stable language** — `requires-python` and the syntax it allows.
- **No superseded tool or library** — compare with the house picks in `setup-python`, and with the pre-commit revisions.

## Check documentation and safety

- **The README matches the code** — run its commands as written.
- **No secret in the tree or its history.**
- **No known vulnerability in the locked dependencies** — for Python, `uv export --format requirements-txt --no-emit-project > requirements.txt`, then `uvx pip-audit -r requirements.txt --disable-pip`.

## Get a cold read

After your own pass, give a fresh agent the files and the standard, never your conclusions, and ask what breaks the plan or the skills.
An agent handed your findings tends to confirm them; one reading cold finds what your pass was blind to.
Verify each finding against the files before keeping it — an agent's mistakes read as confidently as its catches.

## Report

Rank the findings by what they would change — a wrong answer before a missing test, a missing test before a style breach — and give each its evidence and the rule it breaks.
Separate defects from judgement calls, and list the checks skipped and why.

## Fix

Fix the defects without waiting, in ranked order; ask first only about a judgement call or a change to a requirement or decision in `PLAN.md`, which needs the user's sign-off (see `plan-project`).

- **Fix the cause, not the symptom.** A bug gets a regression test that fails before the fix and passes after.
- **Commit each fix on its own** (see `use-git`), so one can be reverted alone.
- **Re-run every check at the end**, since one fix can break what another check passed.
- **Bring `PLAN.md` and the README up to date** with what changed, then report what changed in behaviour and what was left, and why.
