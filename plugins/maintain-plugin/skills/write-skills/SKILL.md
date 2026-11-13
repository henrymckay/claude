---
name: write-skills
description: >-
  House conventions for authoring a Claude Code skill — its name, a
  description that triggers within the listing's budget, the opening, rules
  stated once with an observable why and their exceptions, house picks,
  general examples, a control run for a doubtful rule, and references. Use
  whenever creating or editing a SKILL.md or its references, or writing a
  skill description — even if the user just says "make a skill" or "fix this
  skill's description".
---

# Write skills

House conventions that keep a library's skills consistent.
They layer on `write-markdown` (the prose); `review-plugin` sweeps a whole repo against them.
Anthropic's `skill-creator` plugin, if installed, runs the draft, test and iterate loop and tunes a description against queries that should and should not trigger it; without it, run the control in Cut what Claude does unprompted by hand and check triggering with the plugin's trigger suite (`review-plugin`).
Three mistakes account for most weak skills: a description never reconciled with the body that shipped, a rule stated in two places that then drift apart, and a why that names the rule's purpose rather than something a reader could watch happen.

**In an existing project, ask first.** Where a skill or repo already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

**Beside another authoring plugin, this skill sets what a skill says and theirs set how it is made.** With `skill-creator`, `plugin-dev` or `superpowers` loaded too, use their loops, scaffolds and validators; where their advice on content differs — a description in the third person, of trigger phrases only, or about 100 insistent words; rules as prohibition tables or capitalised laws; no rule without a failing test first — follow this skill, as convention skills hold beside another planning plugin, unless the user names the other plugin's conventions.
Skills written half to one set and half to the other read as drift at the next sweep, and each pass rewrites the other's half.

## Name it

Name a skill **verb-first** in a few kebab-case words, so the name says when Claude reaches for it rather than what topic it covers:

- **`be-`** — a style to adopt (`be-functional`).
- **`build-`** — carry a plan out (`build-project`).
- **`design-`** — settle how something looks and reads before it is built (`design-interface`).
- **`plan-`** — settle a design before building (`plan-project`).
- **`review-`** — check against a standard and fix (`review-project`, `review-plugin`).
- **`setup-` / `structure-`** — arrange a project (`setup-python`, `structure-python`).
- **`use-`** — a tool or library (`use-git`, `use-polars`).
- **`write-`** — produce an artefact (`write-tests`).

`write-tests`, not `testing-guide`.
Each skill is `skills/<name>/SKILL.md` plus any `references/`; keep `skills/` flat, since the name already classifies it.

## Write the description

The description is the trigger: it is all Claude sees when deciding whether to load the skill.

**Draft it twice.** Write it before the body, so the skill is built toward a stated goal; rewrite it after, dropping what the body ended up not covering, adding what it grew to cover, checking that the body says when to deviate, and fixing any phrase that fires on the wrong task.
A description identical to its first draft means the second pass didn't happen.

**Keep it under 500 characters, and never past 1,000.**
Claude Code cuts each description at 1,536 characters, and once the session's descriptions together pass 1% of the context window it drops the least-used skills' descriptions, leaving only their names; every installed plugin shares that budget, so a long description costs some other skill its trigger (Claude Code docs, 2026-11).
`claude plugin details <plugin>@<marketplace>` prints each skill's always-on cost.

Write plain prose with no backticks (see `write-markdown`), in this order:

1. **What it is** — a phrase naming the skill's subject and its main topics, not its rules; counterparts use parallel forms ("Functional programming done well — …" / "Object-oriented design done well — …").
2. **When to use it** — "Use when/whenever …", the contexts that should invoke it, ending with the casual phrasings ("even if the user just says '…'").
   Cover the whole body and promise nothing it lacks.
   For a skill that governs work a model can answer inline — a snippet, a function, a README — open this part with "Load it before the first line of …, even …", since the model otherwise answers without loading anything.
3. **What it targets**, only where a version matters — "Targets Polars 2.x."
4. **Opt-in-ness**, for an opt-in style skill only, verbatim: "Opt-in: reach for <X> where it genuinely fits, not by default."
5. **A boundary**, only where a near neighbour would claim the same prompt — "Not for <…>, which is <skill>'s."

Neighbours, references and house picks belong in the opening, which is read when the skill is followed; in the description they spend the shared budget on nothing that decides whether the skill loads.

## Open consistently

Every skill opens with these parts, in order:

1. **Placement** — a line or two saying what the skill is, the skills it **builds on** and the skills it **hands off to** ("for scaffolding, see `setup-python`"), as bare backticked names.
2. **Failure modes** — the two or three mistakes behind most of what goes wrong.
   Take them from what a real run got wrong; a mistake nobody makes spends attention the real ones needed.
3. **Language pointer**, only with a language reference — `**Language-agnostic here.** The Python specifics live in references/python.md.`
4. **Caveat**, one of two fixed shapes, omitted only for a skill that applies to nothing but the user's own material:
   - Applied to existing material: `**In an existing project, ask first.** Where a repo already has <X>, check with the user whether to keep it or apply <Y>, and prefer <Y> unless they choose to keep theirs.` — <Y> is this skill, or what it produces (`PLAN.md`).
   - Opt-in style: `**This is opt-in.** Reach for <X> where it genuinely fits (below), not by default.` — paired with a `## When to use` section and a closing fallback line.

## Structure the body

- **Use punchy section headings**: imperative for an action (`Pick a layout`), a noun for a catalogue (`Patterns`), sentence case.
- **Order by dependency.** Sections that define vocabulary come before those that spend it, so a reader never meets a term before its definition; synthesising sections (`Pick a layout`, `Run`) trail.
- **Cut what Claude does unprompted.** For each rule ask whether Claude would follow it with no skill loaded — pure functions, no bare `except`, atomic commits — and cut it if so; it spends the reader's attention that the corrections, house picks and non-obvious traps needed, and it reads as reasonable advice, so word counts never catch it.
Where the answer is in doubt, no real run has shown the failure and a control is cheap, settle it with one: give a fresh subagent the case with the rule left out, three times, since a failure that comes one run in three passes a single run, and add the rule only if a control gets it wrong; a failure seen in real work outranks a clean control, which runs without the load that caused it.
- **State each rule exactly once.** A rule stated twice drifts as soon as one copy is edited, and a reader who meets both wonders whether they differ.
Fold one-line points into a catalogue section rather than giving them a stub heading.
- **Make the why an observable consequence.** "Define `__all__` to make the API explicit" gives a purpose nobody can check; "mark a re-export with a redundant alias, or the linter reads it as an unused import" says what happens, and a reader can watch it happen.
A purpose-only why gets applied by feel and drifts; write the rule so that following and breaking it look different.
Where nothing observable turns on a rule, label it a preference so the reader knows it bends.
- **State a rule as a rule, with its exception in the same sentence.** Write absolutes imperatively ("Order parameters alphabetically, except in a pipeline module, where they follow the data"); keep *prefer* for a genuine trade-off.
A rule softened to *prefer* is ignored outright; a rule with a named exception is applied, and the exception with it.
- **Name the pick, the alternative and the case that earns it.** "Use `functools.partial`; `toolz.curry` composes more freely but ships no type hints, so pyright loses the function's type — reach for it only where that cost is paid knowingly."
A non-default stays mentioned without becoming the default, and the reader knows what reaching for it costs.
- **Say when to deviate.** A skill is a set of defaults: a `PLAN.md` decision the user signed off overrides one, and a measurement or the current docs do once recorded there as a proposed decision and raised, so Claude deviates openly rather than silently or never.
- **Fit the rule's form to the failure it answers.** A missing fact gets the fact and its version; a misread rule, a wrong/right pair; a rule known but dropped under pressure — a harness reminder, a long task — its own line naming that pressure and saying the rule wins, since a rule silent about its rival loses to whichever spoke last.
- **Give a load-bearing rule its own line**, not the last sentence of a long paragraph, where it gets read past.
- **Ship a script when runs keep writing the same one.** Put it in the skill's `scripts/` and point at it, since each rewrite is a fresh chance to get it wrong.
- **Show the anti-pattern for the most-broken rule** as one compact wrong/right pair — a fenced pair in a language-bound skill, a named pair in prose in a language-agnostic one, so it doesn't quietly become a Python skill.
- **Keep examples general.** An example drawn from the project that prompted a rule teaches its domain along with the rule; use the smallest example that shows the rule, from a domain any reader knows.
- **Generalise a rule added mid-project.** A rule written to fix one incident arrives in that project's terms; restate it so a reader from any domain would apply it, and grep the neighbouring skills first — if one already says it, extend that, or the two copies drift apart.
- **Run what the skill claims.** Pass every code block through the language's formatter and linter (for Python, `uvx ruff@latest format --diff` and `uvx ruff@latest check`), and run every library claim in a throwaway script against the current release (for Python, a PEP 723 script under `uv run`), naming the version in the commit message.
Reading passes examples the linter fails and claims the library contradicts.
- **Keep cross-references live.** When you move or reword a rule, grep this skill and its neighbours for the section name and the rule's wording, so no pointer leads to nothing.

## Split the principle from the language

A language-agnostic skill states the principles; `references/<language>.md` shows how they land.

- **The skill** closes with `## Language specifics`: "Read the file for the language you're working in:", a `- **Python** → references/python.md (…)` bullet, and "Add a new references/<language>.md when you work in another language rather than adding its specifics to this file."
- **The reference** opens with the H1 `<skill H1> in Python` and "The language-agnostic principles are in `SKILL.md`; this is how they land in Python[ with `<framework>`]."
- **Headings mirror** the skill wherever a topic appears in both; reference-only mechanics take their own names.
- **A build-out reference leads with its structure** (the package tree) and closes with `Run`; a style reference has neither and orders by dependency alone.
- **The reference never restates a principle** — it shows the mechanics for one the skill states.

A skill whose specifics vary along another axis splits the same way under that axis's name — `write-sql` by engine, with `**Dialect-neutral here.**`, `references/duckdb.md` and a closing `## Dialect specifics`.

A skill tied to one library has no language axis, so it splits by **topic** instead: `references/<topic>.md` cookbooks, each with its own H1 and scope line, and a closing `## Reference cookbooks` section.

**A reference earns its place by holding what the skill cannot**: mechanics too long for the body, a worked trap, a framework build-out.
An API listing does not — the reader already knows a filter takes a predicate, and the real traps get lost among the filler.
Keep only lines that would change what gets written.
