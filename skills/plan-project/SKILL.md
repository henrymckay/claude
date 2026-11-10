---
name: plan-project
model: opus
effort: high
description: >-
  How to plan a project before building it — turning a loose conversation into
  one PLAN.md with minimal input from the user: gather what can be found,
  research the domain and current practice with sources recorded, frame the
  project wider than the brief (the domain's vocabulary, its wider context,
  rival designs), draft every section, record assumptions in place of
  questions, treat every house pick as a default to deviate from openly, then
  put the questions, assumptions and decisions in front of the user in one
  batch with recommended answers, through plan mode. The plan has a fixed
  layout for any kind of project — a program, a library, or a content repo
  such as docs or skills: a brief (goal, terms, numbered requirements with
  their cost, not yet), a design (inputs, data flow, outputs, interface as a
  command, endpoint table or screen list, errors, decisions with sources),
  delivery (verification, milestones) and open items (assumptions, questions,
  ideas the brief didn't ask for), whose requirements and decisions change
  only with the user's sign-off; a fix or small change gets a short plan in
  the conversation instead. It is written for Claude to follow: cited by ID,
  shown not described, in the plan's own terms, pointing at skills rather than
  restating them. Use whenever starting a new project or repo, or a build that
  adds a new input, output or interface; when the user wants to think a
  project through, write a spec or design, or decide what to build first; and
  whenever a PLAN.md needs changing — even if the user just says "let's plan
  this", "new project" or "what should this look like". Layers on
  write-markdown; points the design at setup-python, structure-python,
  write-entry-points, be-functional, use-polars and write-tests, hands the
  build to build-project, and the finished build to review-project.
---

# Plan the project

A project's plan lives in one `PLAN.md` at the repo root: what it must do, in the user's words, and the design that answers it.
It is written with the user before the build and kept current as the build proceeds.
It layers on `write-markdown`, points its design at `setup-python`, `structure-python`, `write-entry-points`, `be-functional`, `use-polars` and `write-tests` rather than restating them, hands the build to `build-project`, and the finished build to `review-project`.
Three mistakes account for most weak plans: interviewing the user section by section instead of drafting and asking only what the draft can't settle, design slipped into the requirements, and structure planned before a requirement needs it.

**In an existing project, ask first.** Where a repo already has a plan, spec or design document, check with the user whether to convert it to `PLAN.md` or keep it, and prefer `PLAN.md` unless they choose to keep theirs.

## When to plan

Plan a new project, and any build that adds a new input, output or interface.
A fix or small change needs only a short plan in the conversation; a full `PLAN.md` for it costs more than the change.
To extend a project that already has a `PLAN.md`, run the steps below on the new part alone, adding its requirements, design and milestones to the existing plan.

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
  - Cost: <…>.

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

| method | path | returns |
|---|---|---|
| <GET> | <path, with its query bounds> | <shape; link the Outputs table> |

- **<screen>** — <what it shows, from which output, and how it refreshes>.

### Errors

- **<what goes wrong>** — <fail, skip or empty, and the message>.

### Decisions

- **D1 <choice>** over <alternatives> — <why>; <cost>; <source: the doc, tool or measurement that settled it>; <overrides `<skill>`, <section>, where it does>; (proposed) until the user signs it off.

## Delivery

### Verification

- **R1** — <a test, or a real run with an expected count>.
- **R2** — <a timed run on full-size input, within its budget>.
- **R3** — <for an endpoint, a request and its expected body; for a screen, the output it renders and a check that it renders it>.

### Milestones

- [ ] **M1 <name>** — R1, R2; done when <check>.

## Open

### Assumptions

- **A1** <what was assumed in place of an answer> — <why it is the likely answer, and its source>; <what changes if it is wrong>.

### Questions

- **Q1** <question> — recommended: <answer>; blocks M2.

### Ideas

- **I1** <a better way noticed but not asked for> — <the case for it, and what it would cost>; not built.
````

The groups mark who owns what: the user owns the **Brief**, Claude answers it with the **Design**, **Delivery** orders and checks the work, and **Open** holds what is still the user's to settle.

**Read the Design headings by what the project ships.** The skeleton is written for a program that turns inputs into outputs; keep every heading for any other kind of project, so the layout stays the one every plan shares, and read each by what it ships:

- **A library** — Interface is its public API, and Data flow traces its main call paths.
- **A content or configuration repo** (docs, skills, dotfiles) — Inputs are what it is written from, Data flow is how a change travels from source to where it takes effect, Outputs are the files it ships and their format, and Interface is how a person or tool invokes them.

The schema table is for a tabular output only; the endpoint table for an HTTP API; the screen list for a dashboard or GUI.
Where work arrives continuously, as issues or feedback, the milestones cover only the planned work, and Verification names where the rest is tracked.

## Go from conversation to plan

Draft the whole plan first and ask afterwards.
Questions asked before a draft exists are guesses at what matters; a draft shows which gaps actually change the design, and lets the user answer by reacting rather than inventing.

- **Wrong** — "What storage do you want? Which scheduler? How should errors be reported?", one message per section, each answered from nothing.
- **Right** — a full draft with the house picks filled in, then one message: "A3 assumes Parquet; D2 picks launchd over cron because …; Q1 needs you — recommended: yes."

1. **Start in plan mode**; its approval is the plan's sign-off.
2. **Gather before asking.** Read the conversation, the repo, any neighbouring repo it reads from or feeds, and samples of the real input data.
   Where the input needs a credential, ask for it now and record a sample response; it becomes the first test fixture (see `write-tests`).
   Never ask what a file, a command or a quick check can answer.
3. **Frame it wider than the brief.** A brief names what the user thought of today, in the words they happened to use; the design has to fit the domain and outlast the next request.
   Search the web and read the current docs of the libraries and the comparable tools, not memory alone, and record each source beside the assumption or decision it informed, so the user can check the claim rather than trust it.
   - **Learn the domain's language.** Look up how practitioners name the things involved, the standard data shapes and units, and the formats and libraries to reuse rather than build.
     Take the Terms from it; where the user's word differs, use the domain's and record the choice as an assumption.
   - **Place the project.** Who reads its outputs, which projects feed it or read from it, and what it plausibly grows into.
     Let that shape the names and the seams between stages, and put the growth itself under Not yet; building for it now is the structure-ahead-of-need mistake.
   - **Compare rival designs.** Sketch two or three for each structural choice, judged against how comparable tools do it and where they fall short, and record the losers under Decisions.
   - **Keep what the brief didn't ask for.** A capability the research turned up, or a better shape for something the user fixed, goes under Ideas with its case, so the user sees it without it entering the design.
4. **Extract the requirements.** Pull every statement of intent out of the conversation, merge duplicates, and number what remains in the user's words.
   Where two statements conflict, the later one wins, recorded as a question if the conflict matters.
   Keep requirements to *what*; a *how* the user insisted on stays as a requirement, and one they only floated becomes a decision.
5. **Draft every section**, following the skill that owns it: the interface from `write-entry-points`, the layers and boundary from `structure-python`, the data flow from `be-functional` and, for frames, `use-polars`.
   For a Python project M1 is the scaffold from `setup-python`, logging, and the first real path from input to output, however thin; each Verification line is a check `write-tests` would accept.
   Size the work from the inputs' size and frequency: where speed or memory matters, state the budget as a requirement with a timed check in Verification; where it plainly doesn't, write that under Decisions, so nobody optimises it.
6. **Fill each gap with an assumption, not a question.** Take the house pick from the skills, or the answer the rest of the conversation implies, and record it under Assumptions with what changes if it is wrong.
   A requirement Claude inferred rather than heard is an assumption too, so the Brief stays the user's.
   A house pick is a default: where research shows it fits this project badly, choose otherwise and record it under Decisions as proposed, with the source and the skill and section it overrides; the batch puts it to the user, and approval of the plan is its sign-off.
7. **Raise as a question only what an assumption can't carry**: a choice that splits the design, a costly requirement whose purpose is unclear, a concern that could sink the project.
   Give each a recommended answer, so the user can reply "yes" or by number.
8. **Ask once, in one batch**: the questions with their recommendations, as multiple choice where the options are few; the assumptions, decisions and ideas listed by ID, each decision with its alternatives, cost and source, for the user to override or adopt; and a line on what Claude would push back on in the brief.
   The user reviews a list of calls, not a document, so each line stands alone.
   A second round only where an answer opened a question the first round couldn't have asked.
9. **Fold the answers in.** Each confirmed assumption or answered question moves into Requirements or Decisions; each overridden one changes the sections it touched.
10. **Call the plan complete when every question is answered** — an assumption the user's reply leaves alone counts as confirmed, and a question only the build can settle stays under Open — then present it as the plan-mode plan, and on approval write `PLAN.md` and commit it.

## Write it for Claude

- **Cite by ID.** A milestone, check or plan-mode step that names R4 shows what it serves, and a requirement nothing cites is visibly unbuilt.
- **Show, don't describe.** A real command line and a schema table fix an interface and an output; a paragraph about them leaves the details to be guessed.
- **Use the Terms everywhere.** One name per concept, in the plan and in the code; a second name for the same thing reads as a second thing.
- **Write what is decided as fact** — "Each day is written to its own file" — mark what Claude decided alone *(proposed)*, and put what only the user can settle under Open; a "could" in the Design gets built as either.
- **Record what was rejected, and the source.** A decision without its rejected alternatives gets reopened, or quietly reversed by a build that thinks it is improving things; one without its source can only be trusted, never checked.
- **Point at a skill instead of restating it.** The plan says what this project does; the skills say how every project does it, and a copy in the plan drifts from the skill.
- **Keep only what changes the build.** A line no milestone or check would read differently without is background, and belongs in the README.

## Keep it current

- **Change a requirement or decision only with the user's sign-off.** When work would overturn a decision, add a requirement, build something from Not yet or override a skill, say so in a plan-mode plan, so the approval covers the change.
- **Update it with the code.** Tick the milestone, move out of Not yet what the user signed off building, record the build's assumptions under Open, its calls under Decisions as proposed, and its ideas under Ideas, and commit `PLAN.md` with the change that made it true.
A proposed decision that fills a gap the skills leave is built on and raised in the milestone report; one that overrides a skill waits for the sign-off above.
A plan left behind becomes a second, wrong README.
