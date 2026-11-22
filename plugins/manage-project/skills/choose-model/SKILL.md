---
name: choose-model
description: >-
  How to pick the model, effort and mode for each stage of work, with an eye
  on cost — the ladder (Opus to plan, review and edit skills; Sonnet to build;
  Haiku to grade), holding a stage on its model through a subagent, spending
  tokens well within one, a ledger of what each cost, and current prices. Use
  whenever starting a stage, spawning a subagent, or asked which model
  to use, what a build cost or how to cut token cost — even if the user just
  says "this is expensive" or "use a cheaper model".
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
| A sweep's independent review (`review-plugin`, Review it from outside) | the best available, `fable` today | the highest it offers | Read-only and run once a sweep; a reviewer on the builder's own model and effort finds what the builder already looked for |
| Build milestones | `sonnet` | medium | The plan has made the decisions; the gate catches what the model misses |
| Cold reads, evaluators, gap probes, stand-alone web research | `sonnet` | medium | Many of them run; each returns conclusions, not files; a plan's own research stays with the planning subagent, since it shapes the draft |
| Graders, hooks, trigger evals | `haiku` | low | A yes/no over a short text, run on every turn or every case |

A model one rung up is earned by a stage that keeps failing its gate on the cheaper one, recorded under Decisions with the gate that failed; a rung down is never earned for planning or review.

## Set the model from inside Claude

- **A skill's frontmatter sets the turn's effort, not reliably its model**: `model` and `effort` are documented to apply from the skill's invocation to the end of that turn, but only the effort is relied on (Hold a stage on its model, Claude Code 2.1.322); a skill that forks (`context: fork`) applies both to a subagent that sees none of the conversation.
- **The frontmatter's effort outranks the Agent tool's for the rest of the turn**, inside a subagent too: a review handed over at `high` that loaded `build-project` to read one section ran 157 of its 184 Opus responses at `medium`, from that load to the turn's end (2.1.325, transcript `effort` per response).
So a skill names an effort in its frontmatter only to raise it, never to lower it, since any stage may load it to read a section; the Agent tool's `effort` sets a lower rung.
- **A subagent takes its own model and effort** from the Agent tool's `model` (`sonnet`, `opus`, `haiku`, `fable`) and `effort` parameters, which outrank the agent's definition, `CLAUDE_CODE_SUBAGENT_MODEL` and the session's model.
- **`opusplan` is the session mode when no project skill is driving**: Opus in plan mode, Sonnet once the plan is approved, switching at the plan-mode boundary.
- **The background model runs the hooks and prompt-type checks**; pin it with `ANTHROPIC_DEFAULT_HAIKU_MODEL` in the `env` block of `settings.json` when a hook must run on a specific model.

## Hold a stage on its model

A session cannot tell which model is serving it: a skill whose frontmatter names a model changes the model the session is *told* it is on, while in measured runs, headless and interactive, every message was still served by the session's default.
So a stage never trusts the reported model, the frontmatter or the user's `/model`; it places itself.

- **Hand the stage to a foreground subagent every time**, with the Agent tool's `model` and `effort` set from the ladder and `run_in_background: false` where the tool offers it, since Claude Code starts a subagent in the background by default: a build one milestone at a time, a review whole, a plan's gathering, research and draft.
The Agent tool's `model` is the one setting that decides which model serves the work.
- **Never end a turn while a stage's subagent is running, above all in a headless run**: where it started in the background anyway, wait for its result before the turn ends, as print mode does when asked (code.claude.com/docs/en/sub-agents).
After the last turn `claude -p` waits for background work only until it has sat idle for `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, ten minutes by default, then stops waiting and drops the partial result, so a milestone left running is cut off mid-work and repeated (code.claude.com/docs/en/headless and env-vars, 2026-11-19).
Whoever starts a long headless run may set that variable to `0`, which waits indefinitely, or `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`, which keeps every subagent in the foreground but removes background commands too; either is a backstop to the rule, not a substitute.
- **Hand it over however small the prompt says the work is.** "This should take minutes" changes the size of the stage, never its model: a short stage on the right model costs cents more, and sessions told a task was quick otherwise planned on Sonnet.
The one exception is the short plan in the conversation for a fix or a small change (`plan-project`, When to plan), which is no planning stage.
- **Keep in the main session only what needs the user or the conversation** — the questions, the sign-off, a stop, the report — so its own model is paid for a handful of messages, not the stage.
- **Brief the subagent as the stage's own**: say it is the subagent the stage was handed to and must do the work itself — which stops it passing the stage on whole, not spawning the cold read or research the stage's skill calls for, and without which it would load the skill and hand the stage on again — and give it the repo, the unit of work, the stage's skill by name and the user's words verbatim, since it sees none of the conversation.
- **Check what comes back against the repo** — the suite, the commits, the plan's headings — before relaying it or handing over the next unit; a subagent reports a failed gate in the same register as a passed one.

## Spend tokens well within a stage

Every request re-sends the whole conversation, so whatever a stage leaves in its context is paid for again on every later turn, at the cache-read price while the cache is warm and full price once it expires.
In one four-milestone build (2026-11-18, Sonnet milestones) cache reads and writes were three quarters or more of each milestone's dollars and output a quarter or less, so a stage's bill follows how much context it carries, more than how much it writes.

- **Delegate what would flood the context, and nothing smaller**: a fresh subagent starts with only its brief and returns a summary, so it pays for itself on reading and research whose output would otherwise stay in the session; a lookup of a few calls is cheaper inline.
- **Brief a fresh subagent rather than fork a long session**: a fork inherits the whole conversation and carries it on each of its turns.
- **Cap output at its source** — a count, a tail, a filter, a file read in part — rather than printing a whole log or page to skim.
- **Mind the cache's lifetime**: a write costs 1.25 times the input price for five minutes or twice for an hour, and Claude Code caches a subscription's main conversation for an hour and subagents for five minutes (code.claude.com/docs/en/prompt-caching, 2026-11-18); the first request after a longer gap pays full price for the whole context, so a large session left idle pays for it again.
- **End a long stage before its context is mostly stale tool output, its state already written down**: `PLAN.md` and the commits for a build, memory for facts that outlast the project, never both, brought up to date at the end of each milestone or task, so a compaction loses nothing the record lacks; this plugin's `PreCompact` hook asks the summary to keep, marked, whatever is still unrecorded.

## Record what a stage cost

**Record each stage's cost as the stage closes, in the project's `costs.csv`**, one row per stage and model, so one build can be set against another and the ladder judged on evidence: the plan, each milestone, each review, and the coordinating session's own row at the end.
**Total it with this skill's `scripts/costs.py`, never by hand**, run in the project's directory, whose newest session it reads, with the path from the skill's base directory: `uv run --script <base>/scripts/costs.py --agent <id> --stage M2 --no-header >> costs.csv` after the stage's subagent returns, its id from the Agent tool's result, nested subagents counted in; `--agent session` totals the coordinating session's own messages, no `--agent` totals every stage at once, and leaving out `--no-header` prints the header line a new ledger starts with.
It reads the session transcript, where each assistant message records the `model` that served it and the `effort` it ran at — the only evidence a stage ran where the ladder puts it — and its `usage`, and each subagent's file under the session's `subagents/` folder, counting nested subagents such as evaluators in the stage that spawned them and a restarted one wherever its file lies, so an interrupted build still totals.
A response is written as one record per content block, each repeating its usage, so a hand sum over records counts it several times; the script counts each response once, as `scripts/test_costs.py` pins on a made-up session.
The columns, alphabetical as `store-data` keeps a stored table: `agents`, `cache_read`, `cache_write`, `dollars` (list price, from Know the prices), `effort`, `input`, `model`, `output`, `session`, `stage`, `started`, `wall_minutes`.
A row whose responses ran at more than one effort shows each with its count (`medium:157/high:27`); report such a row as a stage off its rung and find the skill load that moved it.
The format is internal and changes between releases, so where a total looks wrong, check the fields the script reads before trusting it; on four real sessions its dollars came within 6% of Claude Code's own running total, which also counts the background model's calls (2.1.325).
The script is plain Python, so any Python from 3.12 runs it where `uv` is absent.

**Report it in the terms the user pays in**: on a subscription, its share of the plan's allowance (`/usage`), list-price dollars only a proxy; on the API, dollars.

## Leave to the user

`/model`, `/effort`, `/fast` and `/compact` are the user's; a skill may ask for one in its report ("start the build session on Sonnet", "compact before the build, now the plan is approved") but never assumes it was done.
`/fast` keeps the model and its quality, runs up to 2.5 times faster and bills at twice the rate, on Opus and Fable only; it earns its place while the user is waiting on an interactive session, never for background work.
`effortLevel` in user settings is ignored by Opus 5.5 and later, so effort for a session is `/effort` or the skill's frontmatter.

## Know the prices

Per million tokens on the API, read from platform.claude.com/docs/en/about-claude/pricing on 2026-11-18:

| Model | Input | Output | Cache read |
|---|---|---|---|
| Fable 5.2 (`fable`) | $8 | $40 | $0.20 |
| Opus 5.5 (`opus`) | $4 | $20 | $0.20 |
| Sonnet 5.5 (`sonnet`) | $2 | $10 | $0.10 |
| Haiku 5.5 (`haiku`), prompts to 100k | $0.10 | $0.50 | $0.01 |

The `fable` alias resolves to the current Fable, so a session pinned to an older full model ID pays more for less; a subscription shares its allowance across models, so the ladder stretches it rather than the bill.
Check the prices against the current pricing page before quoting them; a release moves them, and `scripts/costs.py` holds the same table, changed with this one.
