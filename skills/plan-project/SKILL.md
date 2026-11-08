---
name: plan-project
description: >-
  How to plan a project before building it — turning a loose conversation into
  one PLAN.md with minimal input from the user: gather what can be found,
  draft every section, record assumptions in place of questions, then ask one
  batch with recommended answers, through plan mode. The plan has a fixed
  layout: a brief (goal, terms, numbered requirements, not yet), a design
  (inputs, data flow, outputs, interface, errors, decisions), delivery
  (verification, milestones) and open items (assumptions, questions), and is
  kept current as each milestone is built. Use whenever starting a new project
  or repo, or a build that adds a new input, output or interface; when the
  user wants to think a project through, write a spec or design, or decide
  what to build first; and whenever a repo already has a PLAN.md — even if the
  user just says "let's plan this", "new project", "what should this look
  like", or "build the next step". Layers on write-markdown; hands off to
  setup-python, structure-python, write-entry-points and write-tests for the
  build.
---

# Plan the project

A project's plan lives in one `PLAN.md` at the repo root: what it must do, in the user's words, and the design that answers it.
It is written with the user before the build and kept current as the build proceeds.
It layers on `write-markdown`, and hands the build to `setup-python`, `structure-python`, `write-entry-points` and `write-tests`, whose rules it points at rather than restates.
Three mistakes account for most weak plans: interviewing the user section by section instead of drafting and asking only what the draft can't settle, design slipped into the requirements, and structure planned before a requirement needs it.

**In an existing project, ask first.** Where a repo already has a plan, spec or design document, check with the user whether to convert it to `PLAN.md` or keep it, and prefer `PLAN.md` unless they choose to keep theirs.

## When to plan

Plan a new project, and any build that adds a new input, output or interface.
A fix or small change needs only a short plan in the conversation; a full `PLAN.md` for it costs more than the change.

## Lay it out

Use this skeleton for every plan, every heading present and in this order.
Write "None" under a heading with nothing to say, so a settled blank reads differently from a forgotten one.

````markdown
# <project>

<One sentence: what it does and for whom.>

## Brief

### Goal

<The problem, who has it, and what done looks like as something observable.>

### Terms

- **<term>** — <its meaning; code uses this name for it>.

### Requirements

- **R1** <What it must do, in the user's words.>
  - Cost: <what it forces in the design, and what dropping it saves>.
- **R2** <A constraint: where it runs, offline, reproducible, private, fast.>

### Not yet

- **<left out deliberately>** — <what would earn it>.

## Design

### Inputs

- **<source>** — <what it is, where from, format, size and frequency, credentials, how far it can be trusted>.

### Data flow

1. **<stage>** — one row is <…>, keyed by <…>; <the transform to the next stage>. (IO)

### Outputs

**<artefact>** — <where it goes, format, write rule (overwrite or append-only), who reads it>.

| column | type | meaning |
|---|---|---|
| <name> | <type> | <meaning; mark the key> |

### Interface

```bash
<a real invocation>
```

<Sample output, what goes to standard output and what to standard error, exit codes, and the schedule if it runs unattended.>

### Errors

- **<what goes wrong>** — <fail, skip or empty, and the message>.

### Decisions

- **<choice>** over <alternatives> — <why>.

## Delivery

### Verification

- **R1** — <a test, or a real run with an expected count>.

### Milestones

- [ ] **M1 <name>** — R1, R2; done when <check>.

## Open

### Assumptions

- **A1** <what was assumed in place of an answer> — <why it is the likely answer>; <what changes if it is wrong>.

### Questions

- **Q1** <question> — recommended: <answer>; blocks M2.
````

The groups mark who owns what: the user owns the **Brief**, Claude answers it with the **Design**, **Delivery** orders and checks the work, and **Open** holds what is still the user's to settle.

## Go from conversation to plan

Draft the whole plan first and ask afterwards.
Questions asked before a draft exists are guesses at what matters; a draft shows which gaps actually change the design, and lets the user answer by reacting rather than inventing.

1. **Start in plan mode.** It blocks edits until the user approves, which is the sign-off the plan needs.
2. **Gather before asking.** Read the conversation, the repo, any neighbouring repo it reads from or feeds, and samples of the real input data.
Never ask what a file, a command or a quick check can answer.
3. **Extract the requirements.** Pull every statement of intent out of the conversation, merge duplicates, and number what remains in the user's words.
Where two statements conflict, the later one wins, recorded as a question if the conflict matters.
Keep requirements to *what*; a *how* the user insisted on stays as a requirement, and one they only floated becomes a decision.
4. **Draft every section**, following the skill that owns it: the interface from `write-entry-points`, the layers and boundary from `structure-python`, the data flow from `be-functional` and, for frames, `use-polars`.
5. **Fill each gap with an assumption, not a question.** Take the house pick from the skills, or the answer the rest of the conversation implies, and record it under Assumptions with what changes if it is wrong.
A requirement Claude inferred rather than heard is an assumption too, so the Brief stays the user's.
6. **Raise as a question only what an assumption can't carry**: a choice that splits the design, a costly requirement whose purpose is unclear, a concern that could sink the project.
Give each a recommended answer, so the user can reply "yes" or by number.
7. **Ask once, in one batch**: the questions with their recommendations, as multiple choice where the options are few, and the assumptions listed for the user to override by ID.
A second round only where an answer opened a question the first round couldn't have asked.
8. **Fold the answers in.** Each confirmed assumption or answered question moves into Requirements or Decisions; each overridden one changes the sections it touched.
9. **Call the plan complete when nothing blocks M1** — every assumption confirmed or overridden, every question blocking M1 answered — then present it as the plan-mode plan, and on approval write `PLAN.md` and commit it.

## Write it for Claude

- **Cite by ID.** A milestone, check or plan-mode step that names R4 shows what it serves, and a requirement nothing cites is visibly unbuilt.
- **Show, don't describe.** A real command line and a schema table fix an interface and an output; a paragraph about them leaves the details to be guessed.
- **Use the Terms everywhere.** One name per concept, in the plan and in the code; a second name for the same thing reads as a second thing.
- **Write what is decided as fact** — "Each day is written to its own file" — and put what is not under Open; a "could" in the Design gets built as either.
- **Record what was rejected.** A decision without its rejected alternatives gets reopened, or quietly reversed by a build that thinks it is improving things.
- **Point at a skill instead of restating it.** The plan says what this project does; the skills say how every project does it, and a copy in the plan drifts from the skill.
- **Keep only what changes the build.** A line no milestone or check would read differently without is background, and belongs in the README.

## Build from it

- **Take one milestone per piece of work.** Its plan-mode plan cites the requirement IDs it covers and the sections it follows.
- **Change `PLAN.md` only with the user's sign-off.** When the work would overturn a decision or add a requirement, say so in the plan-mode plan, so the approval covers the change.
- **Update it with the code.** Tick the milestone, move anything built out of Not yet, record what the build assumed or left unanswered under Open, and commit `PLAN.md` with the change that made it true.
A plan left behind becomes a second, wrong README.
