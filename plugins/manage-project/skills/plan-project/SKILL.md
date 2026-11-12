---
name: plan-project
effort: high
description: >-
  How to plan a project before building it — turning a loose conversation
  into one PLAN.md: gather what can be found, research the domain and
  current practice, citing sources, frame the project wider than the brief
  and aim each surface at the best in class, draft every section, settle gaps from precedent and record assumptions in
  place of questions, treat every house pick as a default to deviate from
  openly, then put the questions, assumptions and decisions to the user in
  one batch with recommended answers, through plan mode — or, in autonomous
  mode, proceed on those answers with every decision left proposed and no
  outward action taken. One layout for any project, a program, a library or
  a content repo: brief, design, delivery and open items, changed only with
  the user's sign-off; a small change gets a short plan in the conversation
  instead. It plans on Opus whatever the session's model, through a
  subagent. Use whenever starting a new project or repo, or a build that
  adds a new input, output or interface; when the user wants to think a
  project through, write a spec or design, or decide what to build first;
  and whenever a PLAN.md needs changing or rewriting — even if the user just
  says "let's plan this", "new project" or "what should this look like".
  Layers on write-markdown; settles open questions through make-decisions,
  classes every input and output through secure-project, sets each
  surface's bar through design-interface, points the design
  at the skills that own each part, hands the build to build-project, and
  the finished build to review-project.
---

# Plan the project

A project's plan lives in one `PLAN.md` at the repo root: what it must do, in the user's words, and the design that answers it.
It layers on `write-markdown`, settles what the skills leave open through `make-decisions`, classes every input and output through `secure-project`, sets each surface's ambition from `design-interface`, points its design at `setup-python`, `structure-python`, `write-entry-points`, `be-functional`, `use-polars`, `write-sql`, `write-tests`, `store-data`, `deploy-project`, `run-unattended` and `send-messages` rather than restating them, hands the build to `build-project`, and the finished build to `review-project`.
Three mistakes account for most weak plans: interviewing the user section by section instead of drafting and asking only what the draft can't settle, design slipped into the requirements, and structure planned before a requirement needs it.

**In an existing project, ask first.** Where a repo already has a plan, spec or design document, check with the user whether to convert it to `PLAN.md` or keep it, and prefer `PLAN.md` unless they choose to keep theirs.

## When to plan

Plan a new project, and any build that adds a new input, output or interface.
A fix or small change needs only a short plan in the conversation; a full `PLAN.md` for it costs more than the change.
To extend a project that already has a `PLAN.md`, run the steps below on the new part alone, adding its requirements, design and milestones to the existing plan.
**Where a brainstorming or design skill has already run, or another plugin's method is driving the work, take its output as this plan's input rather than replacing it**: its framing and choices become the draft's starting point, cited as their source, and only the gaps go through the steps below.
**To re-plan around a restated aim, rewrite the plan whole** through the same steps, since the git history keeps the old one:

- **Renumber the requirements freely**, with no "was R4" trail in the file.
- **Keep every decision's number**, since commits and issues cite them; mark a dropped one superseded, naming what replaced it, and never reuse its number.
- **Collapse finished milestones to one line** naming their range and the date they closed.
- **State once, at the top, which carried-over items are signed off and which are proposed**, rather than marking each line.

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

- **<source>** — <what it is, where from, format, size and frequency, credentials, how far it can be trusted; its class (`secure-project`)>.

### Data flow

1. **<stage>** — one row is <…>, keyed by <…>; <the transform to the next stage>. (IO)

### Outputs

**<artefact>** — <where it goes, format, write rule (overwrite or append-only), who reads it; its class>.

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

- **<screen>** — <the question it answers, what it shows from which output, how it refreshes, and its design (`design-interface`, Plan the design before the code)>.

### Runs on

- **<artefact>** — <host and tier, its limit that matters, how it is deployed from the repo, where its secret lives and when it next rotates; the date the tier was checked>.

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

The schema table is for a tabular output only, its rows in the order the columns are stored (`store-data`, Shape a stored table); the endpoint table for an HTTP API; the screen list for a dashboard or GUI; Runs on names a host for every artefact that runs when the user is not at the shell — a launchd or systemd unit on the user's own machine included — from `deploy-project`'s and `run-unattended`'s picks.
Where work arrives continuously, as issues or feedback, the milestones cover only the planned work, and Verification names where the rest is tracked.

## Go from conversation to plan

Draft the whole plan first and ask afterwards.
Questions asked before a draft exists are guesses at what matters; a draft shows which gaps actually change the design, and lets the user answer by reacting rather than inventing.

- **Wrong** — "What storage do you want? Which scheduler? How should errors be reported?", one message per section, each answered from nothing.
- **Right** — a full draft with the house picks filled in, then one message: "A3 assumes Parquet; D2 picks launchd over cron because …; Q1 needs you — recommended: yes."

**Plan on Opus at high effort, whatever the session started on and however small or urgent the prompt calls the project: hand steps 2 to 8 — the gathering, the research, the draft and its self-check — to a foreground subagent through the Agent tool with `model: opus` and `effort: high`**, briefed as the planning subagent that does the work itself, with the user's words verbatim, the repo and this skill by name, and have it return the draft and the batch; plan mode, the batch and the sign-off stay in the main session, where the user is.
A session briefed as that subagent works directly; any other hands over (`choose-model`, Hold a stage on its model).

1. **Start in plan mode**; its approval is the plan's sign-off.
   With nobody to approve it, see Plan with no user present.
2. **Gather before asking.** Read the conversation, the repo, any neighbouring repo it reads from or feeds, and samples of the real input data.
   Where the input needs a credential, ask for it now and record a sample response; it becomes the first test fixture (see `write-tests`).
   Never ask what a file, a command or a quick check can answer.
3. **Frame it wider than the brief.** A brief names what the user thought of today, in the words they happened to use; the design has to fit the domain and outlast the next request.
   Search the web and read the current docs of the libraries and the comparable tools, not memory alone, and record each source beside the assumption or decision it informed, so the user can check the claim rather than trust it.
   A claim that could not be checked — no search available, a page that will not load — is an assumption marked unverified, never a decision's source.
   - **Learn the domain's language.** Look up how practitioners name the things involved, the standard data shapes and units, and the formats and libraries to reuse rather than build.
     Take the Terms from it; where the user's word differs, use the domain's and record the choice as an assumption.
   - **Place the project.** Who reads its outputs, which projects feed it or read from it, and what it plausibly grows into.
     Let that shape the names and the seams between stages, and put the growth itself under Not yet; building for it now is the structure-ahead-of-need mistake.
   - **Compare rival designs.** Sketch two or three for each structural choice, judged against how comparable tools do it and where they fall short, and record the losers under Decisions.
   - **Aim at the best in class.** For each surface the project ships — a dashboard, a command, an API, a message, a page, the README — write in the Interface what a best-in-class version of it would be, from `design-interface`'s Set the bar and the strongest comparable tools found above, and scope the milestones to reach it; it is a default the user can lower in the batch.
     The ambition is in finish, presentation and completeness of what was asked, never in features the brief lacks or in risk: it loosens neither `secure-project`, nor the rule against outward action, nor building only what a requirement needs.
   - **Keep what the brief didn't ask for.** A capability the research turned up, or a better shape for something the user fixed, goes under Ideas with its case, so the user sees it without it entering the design.
4. **Extract the requirements.** Pull every statement of intent out of the conversation, merge duplicates, and number what remains in the user's words.
   Where two statements conflict, the later one wins, recorded as a question if the conflict matters.
   Keep requirements to *what*; a *how* the user insisted on stays as a requirement, and one they only floated becomes a decision.
5. **Draft every section**, following the skill that owns it: the interface from `write-entry-points` and its look and bar from `design-interface`, the layers and boundary from `structure-python`, the data flow from `be-functional` and, for frames, `use-polars`, the store from `store-data`, a query other projects read it by from `write-sql`, Runs on from `deploy-project` and `run-unattended`, any message to the user from `send-messages`, and each input's and output's class, with where it may go, from `secure-project`.
   For a Python project M1 is the scaffold from `setup-python`, logging, and the first real path from input to output, however thin; each Verification line is a check `write-tests` would accept.
   For a job that runs unattended, M2 makes it run and fail visibly with nobody watching — the schedule, the lock, the exit codes and `status` — before any screen: a screen is earned by data worth showing, and a pipeline that stops silently leaves none.
   A notification is part of M2 only when a requirement asks for one; `run-unattended`'s Report the outcome says what signals a failure until then.
   Size the work from the inputs' size and frequency: where speed or memory matters, state the budget as a requirement with a timed check in Verification; where it plainly doesn't, write that under Decisions, so nobody optimises it.
6. **Fill each gap from precedent, not with a question.** Settle it as `make-decisions` says — the nearest answered decision, cited in one line — and record what was assumed in place of an answer under Assumptions with what changes if it is wrong.
   A requirement Claude inferred rather than heard is an assumption too, so the Brief stays the user's.
   A house pick is a default: where research shows it fits this project badly, choose otherwise and record it under Decisions as proposed, with the source and the skill and section it overrides; the batch puts it to the user, and approval of the plan is its sign-off.
7. **Raise as a question only what `make-decisions` escalates**, and a costly requirement whose purpose is unclear.
   Give each a recommended answer, so the user can reply "yes" or by number.
8. **Check the draft against itself** before asking: every requirement cited by a milestone and a Verification line, every term used in one sense, every decision consistent with the Outputs, Interface and Runs on it touches, and every requirement checkable — a vague word such as fast, secure or robust gets a measure or a question.
   A gap found here is a one-line edit; found by the build, it is a milestone built on one reading of two.
9. **Ask once, in one batch**: the questions with their recommendations, as multiple choice where the options are few; the proposed decisions, assumptions and ideas listed by ID, each decision with its alternatives, cost and source, for the user to override or adopt; the decisions settled by precedent as one counted line (`make-decisions`); and a line on what Claude would push back on in the brief.
   The user reviews a list of calls, not a document, so each line stands alone.
   A second round only where an answer opened a question the first round couldn't have asked.
10. **Fold the answers in.** Each confirmed assumption or answered question moves into Requirements or Decisions; each overridden one changes the sections it touched.
11. **Call the plan complete when every question is answered** — an assumption the user's reply leaves alone counts as confirmed, and a question only the build can settle stays under Open — then present it as the plan-mode plan, and on approval write `PLAN.md` and commit it.

## Plan with no user present

**Autonomous mode** is a session with nobody to answer it: a headless or scheduled run, or one the user told to ask nothing and carry on without them.
Every step above holds except the ones that wait for the user:

- **Write `PLAN.md` directly**, skipping plan mode, and open it with a line saying the plan is unsigned, the date and who asked for the run.
- **Proceed on each question's recommended answer**, recorded under Assumptions with the question it replaced, for the user's later review.
- **Leave every decision *(proposed)* or *(by precedent)***, those that override a skill included, and build on them; only the user's review signs one off, and the Brief stays as they wrote it.
- **Take no outward action** — creating a repository, publishing, deploying, messaging anyone, spending or moving money, acting on an account; do the local part, list the step under Questions for the user to take, and leave unticked a milestone whose check needs it.
Skill feedback is not such an action: it is recorded as the session's feedback rule says.
- **Put the batch of step 9 in the final reply**, so the first thing the user reads is the list of calls to confirm or change.

## Write it for Claude

- **Cite by ID.** A milestone, check or plan-mode step that names R4 shows what it serves, and a requirement nothing cites is visibly unbuilt.
- **Show, don't describe.** A real command line and a schema table fix an interface and an output; a paragraph about them leaves the details to be guessed.
- **Use the Terms everywhere.** One name per concept, in the plan and in the code; a second name for the same thing reads as a second thing.
- **Write what is decided as fact** — "Each day is written to its own file" — mark what Claude decided alone *(proposed)*, or *(by precedent)* where `make-decisions` settled it, and put what only the user can settle under Open; a "could" in the Design gets built as either.
- **Write each decision as one entry: the decision, the alternative it beat, its cost, and its source where one matters.** A decision without its rejected alternative gets reopened, or quietly reversed by a build that thinks it is improving things; one without its source can only be trusted, never checked.
Who said what and when belongs in the commit that recorded it, not in the entry.
- **Point at a skill instead of restating it.** The plan says what this project does; the skills say how every project does it, and a copy in the plan drifts from the skill.
- **Keep only what changes the build.** A line no milestone or check would read differently without is background, and belongs in the README.

## Keep it current

- **Change a requirement or decision only with the user's sign-off.** When work would overturn a decision, add a requirement, build something from Not yet or override a skill, say so in a plan-mode plan, so the approval covers the change.
- **Trim at sign-off.** Drop the *(proposed)* marks the sign-off covers, and the history that no longer changes what anyone does — dated quotes, "was:" trails, how a decision got there — since git keeps it; keep every ID and every decision's substance.
- **Update it with the code.** Tick the milestone, move out of Not yet what the user signed off building, record the build's assumptions under Open, its calls under Decisions as proposed, and its ideas under Ideas, and commit `PLAN.md` with the change that made it true.
A proposed decision that fills a gap the skills leave is built on and raised in the milestone report; one that overrides a skill waits for the sign-off above.
A plan left behind becomes a second, wrong README.
