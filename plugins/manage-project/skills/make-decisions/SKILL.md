---
name: make-decisions
description: >-
  How Claude settles a question no skill or plan decision answers — the
  principles the house picks share, deciding from the general case, the
  nearest precedent cited in one line, and escalating only what is
  irreversible, outward-facing, costly, security-touching or unprecedented.
  Use whenever about to ask the user a question, record an assumption or
  propose a decision — even if the user just says "decide it yourself", "stop
  asking me", "what would we normally do" or "what if this changes later".
---

# Make decisions

How to settle a question the skills and the plan leave open, so the user reads only the calls that need them, and settle it in a shape the next case can extend.
It layers on `plan-project`, whose Decisions, Assumptions and Questions hold the result; `plan-project`, `build-project` and `review-project` use it wherever they would ask, assume or propose, `secure-project` says which security calls wait for the user, and `review-plugin` promotes a decision that recurs into the skill that should own it.
Three mistakes account for most of what goes wrong: asking the user what an earlier answer already settles, so the batch grows past what anyone can read; deciding by taste with no precedent named, so the call can be neither checked nor reopened by number; and carrying a precedent across a difference that matters, where its reason does not hold.

- **Wrong** — "Q4: where should the saved filters live: a JSON file, SQLite or Postgres?"
- **Right** — no question; D9 recorded by precedent, as Record it in one line shows.

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
- **Shape for the general case, build the specific one** — names, keys and seams fit the class of problem, while the code serves only the case asked for (Decide from the general case, below); this is the other half of earning it, not an exception to it.

## Decide from the general case

A brief fixes things the domain does not: one currency, one user, one period, one source, one language.
A design that writes each into its names and keys works until the first one changes, then has to be redone whole, since every table, function and test assumed it.

**Before settling a choice that shapes the design, state it in its general form:**

1. **Name the class of problem** in the domain's terms — "an amount of money", not "the pounds column"; "a measurement over a period", not "yesterday's rainfall".
2. **List the axes of change** — each thing the brief holds fixed that the domain lets vary — and mark the ones the project plausibly grows into, as `plan-project`'s step 3, Place the project, finds them.
3. **Keep each marked axis open where that costs nothing now**: a name without the special case in it, the axis as a column or a key part holding its one value, a parameter where a constant would sit; an axis left unmarked stays as the brief fixed it.
4. **Build only the case asked for.** A second implementation, a lookup of rates nobody supplies, a setting, a screen control or a test for a value no input carries waits in Not yet for the case that earns it, as the first principle says; the abstraction over two cases waits for the second (`write-python`, Avoid).

The test between steps 3 and 4: **keeping the axis open adds no branch, no dependency and no test case beyond the one asked for.**
Where it would, it is building the general case, not shaping for it; a new interface, module or seam between parts is that too, and goes under Ideas as `build-project` says.

- **Wrong** — every amount in a column named `amount_gbp`, and `total_gbp` summing it; the first euro account renames a column, every function and every test.
- **Right** — `amount` in minor units beside a `currency` column, every row `GBP`, totals grouped by that column and nothing converting; the euro account adds rows, and the conversion it needs is the only new code.

**Write the general form into the decision**, so a later project finds it as precedent by its class rather than by its surface: "D4 Amounts carry their currency (an amount of money; axis held open: currency; built: GBP only) over a pounds column — …".
Where the axis crosses components, such as a period shared by a pipeline, an API and a screen, hold it open in the contract between them (`design-pipeline`'s contract, the API's shape in `design-interface`), since a component that fixes it alone forces the others to.

## Find the precedent

Before asking a question, recording an assumption or proposing a decision, look for an answer already given, nearest first:

1. **A signed-off decision in this plan.**
2. **A skill's house pick and the reason it gives.**
3. **A signed-off decision in a neighbouring project's `PLAN.md`** — one this project reads from or feeds, or another of the user's repositories on this machine.
4. **The principles above**, last because a principle fits more cases than any decision and so settles fewer of them for certain.

**Settle by analogy only where the precedent's reason holds here.** Name the property the reason turns on — "small single-writer state whose fields change together" — and check the new case has it; where it does not, the precedent does not apply, and the search goes on.
A proposed decision in another plan is a hint, never a precedent, since nobody has agreed to it.

## Record it in one line

Write the decision under Decisions with its source, marked *(by precedent)* where `plan-project` would mark it *(proposed)*, and build on it:

```markdown
- **D9 Saved filters in SQLite** over a JSON file — `store-data`, Pick the engine (small single-writer state whose fields change together) *(by precedent)*.
```

The mark says the call was derived, not invented, and the user can override it by number.
A call with no precedent that shapes nothing else is decided too, and marked *(proposed)* as `plan-project` says.
Where the precedent is another project's decision rather than a skill's, also file skill feedback naming the decision, by its shape and never the project's data, and the skill that should hold it, so a sweep can make it a default.

## Escalate only these

- **Irreversible** — deleting data, rewriting pushed history, a schema change a reader cannot survive, anything published.
- **Outward-facing** — an outward action as `plan-project`'s Plan with no user present lists them, or anything another person sees or receives, except returning the work as a branch of the project's own repository (`plan-project`, Plan with no user present).
- **Costly** — money, a paid tier, or work that would take longer to undo than the milestone took to build.
- **Security** — a data class looser than private, a credential for an account with money in it beyond read-only, private data sent to an outside service (`secure-project`).
- **A change to the Brief or an override of a skill** — the user's alone, as `plan-project`'s Keep it current says; a requirement a house pick would weaken is one, and is built as stated (`plan-project`, step 4).
- **No precedent, or precedents that disagree**, on a choice that shapes the design.

Each escalation goes into the batch as a question with a recommended answer; in autonomous mode it becomes an assumption on that answer, as `plan-project` says, and leads the final reply, except a security escalation, which takes the more private answer and waits (`secure-project`).

## Report the rest as a count

**The batch lists the escalations, then one line for the rest**: "Decided by precedent: 11 (D12 to D22), each citing its source in the plan."
A milestone report and a review report end the same way.
