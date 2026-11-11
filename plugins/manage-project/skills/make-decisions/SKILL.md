---
name: make-decisions
description: >-
  How Claude settles a question no skill or plan decision answers outright —
  the principles the house picks share (earn it before building it, reuse what
  is already there, measure before optimising, fail loudly, keep one copy of
  each fact, make a re-run safe, give each consumer the least reach, name
  things in the domain's terms), finding the nearest answered precedent (a
  signed-off decision in this plan, a skill's pick and its reason, a signed-off
  decision in a neighbouring project's PLAN.md) and settling the new question
  by analogy with the precedent cited in one line, escalating to the user only
  what is irreversible, outward-facing, costly, touches security or has no
  precedent or conflicting ones, and reporting the rest as a count, in a
  session or in autonomous mode. Use whenever about to ask the user a
  question, record an assumption or propose a decision while planning,
  building or reviewing, or when the list of open questions grows past what
  the user can read — even if the user just says "decide it yourself", "stop
  asking me", "too many questions" or "what would we normally do". Layers on
  plan-project, where each decision is recorded; plan-project, build-project
  and review-project use it at their decision steps, secure-project names
  what always escalates, and review-plugin promotes a decision that recurs
  into the skill that should own it.
---

# Make decisions

How to settle a question the skills and the plan leave open, so the user reads only the calls that need them.
It layers on `plan-project`, whose Decisions, Assumptions and Questions hold the result; `plan-project`, `build-project` and `review-project` use it wherever they would ask, assume or propose, `secure-project` names what always escalates, and `review-plugin` promotes a decision that recurs into the skill that should own it.
Three mistakes account for most of what goes wrong: asking the user what an earlier answer already settles, so the batch grows past what anyone can read; deciding by taste with no precedent named, so the call can be neither checked nor reopened by number; and carrying a precedent across a difference that matters, where its reason does not hold.

- **Wrong** — "Q4: where should the saved filters live: a JSON file, SQLite or Postgres?"
- **Right** — "D9 Saved filters in SQLite over a JSON file — by precedent: `store-data`, Pick the engine (small single-writer state whose fields change together)."

**In an existing project, ask first.** Where a repo already has its own way of recording decisions, such as an architecture decision log, check with the user whether to keep it or apply this skill, and prefer this skill unless they choose to keep theirs.

## The principles

The house picks repeat a handful of reasons; when no single precedent fits, these are the precedents.

- **Earn it before building it** — a layer, a service, a tool or a paid tier waits for the case that needs it, and the cheaper option holds until a measured case earns the dearer (`plan-project`'s Not yet, `setup-python`, `deploy-project`, `send-messages`).
- **Reuse what is already there** — the standard library, the platform's own scheduler, the inbox the reader already reads, before a new dependency or service (`write-python`, `run-unattended`, `send-messages`).
- **Measure before optimising** — compaction, an incremental update or a faster engine is earned by a timed run, not by expectation (`store-data`, `build-project`).
- **Fail loudly** — an error, an exit code or a count beats a quiet wrong answer: a typed literal over a string, a quarantine over a dropped row (`write-sql`, `store-data`, `run-unattended`).
- **Keep one copy of each fact** — one record type, one error model, one place for a query, a pointer instead of a second statement (`write-python`, `write-sql`, `write-skills`).
- **Make a re-run safe** — overwrite rather than append, replace atomically, one code path for the scheduled run and the repair (`store-data`, `run-unattended`).
- **Give each consumer the least reach** — a token per consumer, read-only unless writing is the job (`deploy-project`, `secure-project`).
- **Name things in the domain's terms** — the plan's Terms in the code, the practitioner's word over the user's passing one (`plan-project`, `build-project`).

## Find the precedent

Before asking a question, recording an assumption or proposing a decision, look for an answer already given, nearest first:

1. **A signed-off decision in this plan.**
2. **A skill's house pick and the reason it gives.**
3. **A signed-off decision in a neighbouring project's `PLAN.md`** — one this project reads from or feeds, or another of the user's repositories on this machine.
4. **The principles above.**

**Settle by analogy only where the precedent's reason holds here.** Name the property the reason turns on — "small single-writer state whose fields change together" — and check the new case has it; where it does not, the precedent does not apply, and the search goes on.
A proposed decision in another plan is a hint, never a precedent, since nobody has agreed to it.

## Record it in one line

Write the decision under Decisions with its source, marked *(by precedent)* where `plan-project` would mark it *(proposed)*, and build on it:

```markdown
- **D9 Saved filters in SQLite** over a JSON file — by precedent: `store-data`, Pick the engine (small single-writer state whose fields change together) *(by precedent)*.
```

The user can still override it by number; the mark says the call was derived, not invented.
Where the precedent is another project's decision rather than a skill's, also file skill feedback naming the decision and the skill that should hold it, so a sweep can make it a default.

## Escalate only these

- **Irreversible** — deleting data, rewriting pushed history, a schema change a reader cannot survive, anything published.
- **Outward-facing** — an outward action as `plan-project`'s Plan with no user present lists them, or anything another person sees or receives.
- **Costly** — money, a paid tier, or work that would take longer to undo than the milestone took to build.
- **Security** — a data class looser than private, a credential that can act, a new outside service for private data (`secure-project`).
- **A change to the Brief or an override of a skill** — the user's alone, as `plan-project`'s Keep it current says.
- **No precedent, or precedents that disagree**, on a choice that shapes the design.

Each escalation goes into the batch as a question with a recommended answer; in autonomous mode it becomes an assumption on that answer, as `plan-project` says, and leads the final reply.

## Report the rest as a count

**The batch lists the escalations, then one line for the rest**: "Decided by precedent: 11 (D12 to D22), each citing its source in the plan."
A milestone report and a review report end the same way.
The user who wants to check one reads it in the plan; the user who does not has read every call that needed them.
