---
name: choose-model
description: >-
  How to pick the model, effort and mode for each stage of a project or of
  this plugin's own upkeep, with an eye on cost — the ladder (Opus or Fable
  for planning, reviews and skill edits; Sonnet for build milestones, cold
  reads and research; Haiku for graders, hooks and trigger evals), the
  mechanics Claude controls itself (a skill's frontmatter sets the turn's
  effort and names its model, the Agent tool sets each subagent's, opusplan splits plan
  from execution), holding a stage on its model whatever the session started
  on by always handing it to a subagent, and the mechanics only the user sets
  (/model, /effort, /fast),
  the background model, current prices per million tokens, and keeping context
  lean. Use whenever starting a stage of work, spawning a subagent, writing or
  editing a skill that should run on a particular model, or when the user asks
  which model to use, how to cut token cost, or whether to turn on fast mode —
  even if they just say "this is expensive", "use a cheaper model" or "which
  model for this". Layers on plan-project, build-project, review-project and
  review-plugin, which each put their own stage on the ladder.
---

# Choose the model

Which model, effort and mode each stage of work runs on, chosen for the stage rather than left at whatever the session started with.
`plan-project`, `review-project` and `review-plugin` run on Opus at high effort and `build-project` on Sonnet at medium, each putting itself there; this skill says why, how, and how to go further.
Three mistakes account for most wasted spend: running every stage on the largest model, running a plan or a review on the cheapest, and trusting a skill's frontmatter or the user's `/model` to hold a stage on its rung, when the first is not served and the second is forgotten.

**In an existing project, ask first.** Where a repo already pins a model in its settings, check with the user whether to keep it or apply the ladder, and prefer the ladder unless they choose to keep theirs.

## The ladder

| Stage | Model | Effort | Why |
|---|---|---|---|
| Planning, reviewing, editing skills, ruling on a challenge | `opus` (`fable` for the hardest design) | high | One wrong call here is rebuilt across every milestone; the cost is paid once |
| Build milestones | `sonnet` | medium | The plan has made the decisions; the gate catches what the model misses |
| Cold reads, gap probes, web research | `sonnet` | medium | Many of them run; each returns conclusions, not files |
| Graders, hooks, trigger evals | `haiku` | low | A yes/no over a short text, run on every turn or every case |

A model one rung up is earned by a stage that keeps failing its gate on the cheaper one, recorded under Decisions with the gate that failed; a rung down is never earned for planning or review.

## Set the model from inside Claude

- **A skill's frontmatter sets the turn's effort, and its model at most**: `model: opus` and `effort: high` are documented to apply from the moment the skill is invoked to the end of that turn, the session's own resuming at the next prompt.
The effort does and the model is not relied on (Hold a stage on its model, Claude Code 2.1.322); a skill that forks (`context: fork`) applies both to a subagent that sees none of the conversation.
- **A subagent takes its own model and effort** from the Agent tool's `model` (`sonnet`, `opus`, `haiku`, `fable`) and `effort` parameters, which outrank the agent's definition, `CLAUDE_CODE_SUBAGENT_MODEL` and the session's model, so a cold read, a gap probe or a research run goes out on Sonnet whatever the session is on, and a grader on Haiku.
- **`opusplan` is the session mode when no project skill is driving**: Opus in plan mode, Sonnet once the plan is approved, switching at the plan-mode boundary.
- **The background model runs the hooks and prompt-type checks**; pin it with `ANTHROPIC_DEFAULT_HAIKU_MODEL` in the `env` block of `settings.json` when a hook must run on a specific model.

## Hold a stage on its model

The ladder holds whatever model the session started on, and a session cannot tell which model is serving it: loading a skill whose frontmatter names a model changes the model the session is *told* it is on, while in the runs measured, headless and interactive, every message went on being served by the session's default.
So a stage never trusts the reported model, the frontmatter or the user's `/model`; it places itself.

- **Hand the stage to a foreground subagent every time**, with the Agent tool's `model` and `effort` set from the ladder: a build one milestone at a time, a review whole, a plan's gathering, research and draft.
The Agent tool's `model` is the one setting that decides which model serves the work.
- **Keep in the main session only what needs the user or the conversation** — the questions, the sign-off, a stop, the report — so its own model is paid for a handful of messages, not the stage.
- **Brief the subagent as the stage's own**: say it is the subagent the stage was handed to and must do the work itself, and give it the repo, the unit of work, the stage's skill by name and the user's words verbatim, since it sees none of the conversation.
A session briefed that way works directly; without that line it would load the skill and hand the stage on again.
- **Check what comes back against the repo** — the suite, the commits, the plan's headings — before relaying it or handing over the next unit; a subagent reports a failed gate in the same register as a passed one.
- **Read the model from the transcript when it matters**: each assistant message there records the model that served it, the only evidence that a stage ran where the ladder puts it.

## Leave to the user

`/model`, `/effort` and `/fast` are the user's; a skill may ask for one in its report ("start the build session on Sonnet") but never assumes it was done.
`/fast` keeps the model and its quality, runs up to 2.5 times faster and bills at twice the rate, on Opus and Fable only; it earns its place while the user is waiting on an interactive session, never for background work.
`effortLevel` in user settings is ignored by Opus 5.5 and later, so effort for a session is `/effort` or the skill's frontmatter.

## Know the prices

Per million tokens, input and output, on the API in November 2026; cache reads cost a twentieth of input:

| Model | Input | Output |
|---|---|---|
| Fable 5.2 (`fable`) | $8 | $40 |
| Opus 5.5 (`opus`) | $4 | $20 |
| Sonnet 5.5 (`sonnet`) | $2 | $10 |
| Haiku 5.5 (`haiku`), prompts under 100k | $0.10 | $0.50 |

The `fable` alias resolves to the current Fable, so a session pinned to an older full model ID pays more for less; a subscription shares its allowance across models, so the ladder stretches it rather than the bill.
Check the prices against the current pricing page before quoting them; a release moves them.

## Keep the context lean

- **Delegate the reading, keep the conclusion.** A subagent that reads twenty files returns a page; the same twenty files read in the main session stay in its context for the rest of the day.
- **Compact before a long build**, after the plan is approved, so the build starts from the plan and the code, not from the conversation that produced them.
- **Keep a description to what decides the trigger and the body's scope**, as `write-skills` says; every description is loaded on every turn of every session, so a rule restated there is paid thousands of times.
