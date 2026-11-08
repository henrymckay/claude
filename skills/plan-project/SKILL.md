---
name: plan-project
description: >-
  How to plan a project before building it — one PLAN.md at the repo root with
  a standard set of sections (goal, numbered requirements, inputs, outputs,
  data flow, interface, errors, decisions, not yet, verification, milestones,
  open questions), drafted with the user through plan mode, then kept current
  as each milestone is built. Use whenever starting a new project or repo, or a
  build that adds a new input, output or interface; when the user wants to
  think a project through, write a spec or design, or decide what to build
  first; and whenever a repo already has a PLAN.md — even if the user just says
  "let's plan this", "new project", "what should this look like", or "build
  the next step". Layers on write-markdown; hands off to setup-python,
  structure-python, write-entry-points and write-tests for the build.
---

# Plan the project

A project's plan lives in one `PLAN.md` at the repo root: what it must do, in the user's words, and the design that answers it.
It is written with the user before the build and kept current as the build proceeds.
It layers on `write-markdown`, and hands the build to `setup-python`, `structure-python`, `write-entry-points` and `write-tests`, whose rules it points at rather than restates.
Three mistakes account for most weak plans: design slipped into the requirements before anyone asked for it, structure planned before a requirement needs it, and a costly requirement accepted without asking what it is for.

**In an existing project, ask first.** Where a repo already has a plan, spec or design document, check with the user whether to convert it to `PLAN.md` or keep it, and prefer `PLAN.md` unless they choose to keep theirs.

## When to plan

Plan a new project, and any build that adds a new input, output or interface.
A fix or small change needs only a short plan in the conversation; a full `PLAN.md` for it costs more than the change.

## Sections

Use these headings, in this order, in every plan.
Write "None" rather than dropping a section, so a reader can tell a settled blank from a forgotten one.

- **Goal** — the problem it solves and for whom, and what done looks like as something observable.
- **Requirements** — what it must do, numbered (R1, R2, …) and in the user's words, including constraints: where it runs, offline, reproducible, private, fast.
A requirement that forces complexity carries its cost, so the user can drop it before anything is built around it.
- **Inputs** — each source: what it is, where it comes from, format, size and frequency, credentials, and how far it can be trusted.
- **Outputs** — each artefact: where it goes, format, schema (columns, types, key, order), write rule (overwrite or append-only), and who reads it.
- **Data flow** — the stages from input to output: what one row is at each, its key, and the transform to the next; mark where IO happens.
- **Interface** — every command, option or screen, with a real invocation and sample output; what goes to standard output and what to standard error; exit codes.
- **Errors** — what can go wrong at each input and output, and what happens: fail, skip or empty, and the message.
- **Decisions** — each choice, the alternatives rejected and why: libraries, storage, any shape the user argued for.
- **Not yet** — what is deliberately left out, and what would earn it.
- **Verification** — how each requirement is checked, by ID: a test, or a real run with an expected count.
- **Milestones** — ordered steps as a checklist, each runnable and checkable on its own.
- **Open questions** — what is undecided, each naming the milestone it blocks.

## Draft it with the user

1. **Start in plan mode.** It blocks edits until the user approves, which is the sign-off the plan needs.
2. **Draft Goal and Requirements by asking**, a few questions per round, and write them in the user's words.
Requirements say *what*, never *how*; a design choice written as a requirement escapes the scrutiny the design gets.
3. **Price each costly requirement** — what it forces in the design and what dropping it saves — and ask what it is for before designing around it.
4. **Design the remaining sections from the requirements**, following the skill that owns each: the interface from `write-entry-points`, the layers and boundary from `structure-python`, the data flow from `be-functional` and, for frames, `use-polars`.
5. **Present the whole draft as the plan-mode plan.** On approval, write `PLAN.md` and commit it.

## Write it for Claude

- **Number the requirements and cite them.** A milestone, test or plan-mode step that names R4 shows what it serves, and a requirement nothing cites is visibly unbuilt.
- **Show, don't describe.** A real command line and three sample rows fix an interface and a schema; a paragraph about them leaves the details to be guessed.
- **Record what was rejected.** A decision without its rejected alternatives gets reopened, or quietly reversed by a build that thinks it is improving things.
- **Point at a skill instead of restating it.** The plan says what this project does; the skills say how every project does it, and a copy in the plan drifts from the skill.
- **Keep only what changes the build.** A line no milestone or test would read differently without is background, and belongs in the README.

## Build from it

- **Take one milestone per piece of work.** Its plan-mode plan cites the requirement IDs it covers and the sections it follows.
- **Change `PLAN.md` only with the user's sign-off.** When the work would overturn a decision or add a requirement, say so in the plan-mode plan, so the approval covers the change.
- **Update it with the code.** Tick the milestone, move anything built out of Not yet, close answered questions, and commit `PLAN.md` with the change that made it true.
A plan left behind becomes a second, wrong README.
