---
name: choose-model
description: >-
  How to pick the model, effort and mode for each stage of work, with an eye
  on cost — the ladder (Opus to plan, review and edit skills; Sonnet to build;
  Haiku to grade), holding a stage on its model through a subagent, and
  current prices. Use whenever starting a stage, spawning a subagent, or asked
  which model to use or how to cut token cost — even if the user just says
  "this is expensive" or "use a cheaper model".
---

# Choose the model

Which model, effort and mode each stage of work runs on, chosen for the stage rather than left at whatever the session started with.
`plan-project`, `review-project` and `review-plugin` run on Opus at high effort and `build-project` on Sonnet at medium, each putting itself there; this skill says why and how.
Three mistakes account for most wasted spend: running every stage on the largest model, running a plan or a review on the cheapest, and trusting a skill's frontmatter or the user's `/model` to hold a stage on its rung, when the first is not served and the second is forgotten.

**In an existing project, ask first.** Where a repo already pins a model in its settings, check with the user whether to keep it or apply the ladder, and prefer the ladder unless they choose to keep theirs.

## The ladder

| Stage | Model | Effort | Why |
|---|---|---|---|
| Planning, reviewing, editing skills, ruling on a challenge | `opus` (`fable` for the hardest design) | high | One wrong call here is rebuilt across every milestone; the cost is paid once |
| Build milestones | `sonnet` | medium | The plan has made the decisions; the gate catches what the model misses |
| Cold reads, evaluators, gap probes, stand-alone web research | `sonnet` | medium | Many of them run; each returns conclusions, not files; a plan's own research stays with the planning subagent, since it shapes the draft |
| Graders, hooks, trigger evals | `haiku` | low | A yes/no over a short text, run on every turn or every case |

A model one rung up is earned by a stage that keeps failing its gate on the cheaper one, recorded under Decisions with the gate that failed; a rung down is never earned for planning or review.

## Set the model from inside Claude

- **A skill's frontmatter sets the turn's effort, not reliably its model**: `model` and `effort` are documented to apply from the skill's invocation to the end of that turn, but only the effort is relied on (Hold a stage on its model, Claude Code 2.1.322); a skill that forks (`context: fork`) applies both to a subagent that sees none of the conversation.
- **A subagent takes its own model and effort** from the Agent tool's `model` (`sonnet`, `opus`, `haiku`, `fable`) and `effort` parameters, which outrank the agent's definition, `CLAUDE_CODE_SUBAGENT_MODEL` and the session's model.
- **`opusplan` is the session mode when no project skill is driving**: Opus in plan mode, Sonnet once the plan is approved, switching at the plan-mode boundary.
- **The background model runs the hooks and prompt-type checks**; pin it with `ANTHROPIC_DEFAULT_HAIKU_MODEL` in the `env` block of `settings.json` when a hook must run on a specific model.

## Hold a stage on its model

A session cannot tell which model is serving it: a skill whose frontmatter names a model changes the model the session is *told* it is on, while in measured runs, headless and interactive, every message was still served by the session's default.
So a stage never trusts the reported model, the frontmatter or the user's `/model`; it places itself.

- **Hand the stage to a foreground subagent every time**, with the Agent tool's `model` and `effort` set from the ladder: a build one milestone at a time, a review whole, a plan's gathering, research and draft.
The Agent tool's `model` is the one setting that decides which model serves the work.
- **Hand it over however small the prompt says the work is.** "This should take minutes" or "keep it short" changes the size of the plan, the review or the milestone, never the model it runs on: a short stage on the right model costs cents more, and sessions told a task should take minutes otherwise planned on Sonnet, the rung a plan is never moved down to.
The one exception is the short plan in the conversation for a fix or a small change (`plan-project`, When to plan), which is no planning stage.
- **Keep in the main session only what needs the user or the conversation** — the questions, the sign-off, a stop, the report — so its own model is paid for a handful of messages, not the stage.
- **Brief the subagent as the stage's own**: say it is the subagent the stage was handed to and must do the work itself — which stops it passing the stage on whole, not spawning the cold read or research the stage's skill calls for, and without which it would load the skill and hand the stage on again — and give it the repo, the unit of work, the stage's skill by name and the user's words verbatim, since it sees none of the conversation.
- **Check what comes back against the repo** — the suite, the commits, the plan's headings — before relaying it or handing over the next unit; a subagent reports a failed gate in the same register as a passed one.
- **Read the model from the transcript when it matters**: each assistant message there records the model that served it, the only evidence that a stage ran where the ladder puts it.

## Leave to the user

`/model`, `/effort`, `/fast` and `/compact` are the user's; a skill may ask for one in its report ("start the build session on Sonnet", "compact before the build, now the plan is approved") but never assumes it was done.
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
