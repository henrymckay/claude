---
name: write-skills
description: >-
  House conventions for authoring a Claude Code skill in this repo — naming it
  verb-first, writing a description that triggers reliably, opening with the
  standard placement, failure modes and caveat, structuring the body so each
  rule is stated once with an observable why, and splitting a language-agnostic
  skill from its language reference. Use whenever creating or editing a
  SKILL.md or its references, naming a skill, writing or reviewing a skill
  description, or splitting out a reference — even if the user just says "make
  a skill", "add a skill", or "fix this skill's description". Layers on
  write-markdown for prose mechanics, and defers the draft-eval-iterate loop,
  file anatomy, packaging and description optimisation to the skill-creator
  plugin.
---

# Write skills

House conventions that keep this library's skills consistent.
They layer on `write-markdown` (the prose) and defer to the `skill-creator` plugin for the draft-eval-iterate loop, file anatomy, progressive disclosure, packaging and description optimisation.
Three mistakes account for most weak skills: a description never reconciled with the body that shipped, a rule stated in two places that then drift apart, and a why that names the rule's purpose rather than something a reader could watch happen.

**In an existing project, ask first.** Where a skill or repo already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Name it

Name a skill **verb-first**, one or two kebab-case words, so the name says when Claude reaches for it rather than what topic it covers:

- **`be-`** — a style to adopt (`be-functional`).
- **`setup-` / `structure-`** — arrange a project (`setup-python`, `structure-python`).
- **`use-`** — a tool or library (`use-git`, `use-polars`).
- **`write-`** — produce an artefact (`write-tests`).

`write-tests`, not `testing-guide`.
Each skill is `skills/<name>/SKILL.md` plus any `references/`; keep `skills/` flat, since the name already classifies it.

## Write the description

The description is the trigger: it is all Claude sees when deciding whether to load the skill.

**Draft it twice.** Write it before the body, so the skill is built toward a stated goal; rewrite it after, dropping what the body ended up not covering, adding what it grew to cover, and fixing any phrase that fires on the wrong task.
A description identical to its first draft means the second pass didn't happen.

Write plain prose with no backticks (see `write-markdown`), in this order, mirroring the skill's opening:

1. **What it is** — a phrase naming the skill and its key topics; counterparts use parallel forms ("Functional programming done well — …" / "Object-oriented design done well — …").
2. **When to use it** — "Use when/whenever …", the contexts that should invoke it, ending with the casual phrasings ("even if the user just says '…'").
Cover the whole body and promise nothing it lacks.
3. **What it targets**, only where a version matters — "Targets Polars 2.x."
4. **Opt-in-ness**, for an opt-in style skill only, verbatim: "This is an opt-in style skill: reach for <X> where it genuinely fits, not by default."
5. **The reference pointer**, if any — "Language-agnostic principles here; Python <idioms/build-outs> in references/python.md." or, for a topic split, "Detailed cookbooks live in references/."
6. **Neighbours** — "Layers on <skill>; <skill> is the <…> counterpart", the same skills the opening names.

## Open consistently

Every skill opens with these parts, in order:

1. **Placement** — a line or two saying what the skill is, the skills it **builds on** and the skills it **hands off to** ("for scaffolding, see `setup-python`"), as bare backticked names matching the description.
2. **Failure modes** — the two or three mistakes behind most of what goes wrong.
Take them from what a real run got wrong; a mistake nobody makes spends attention the real ones needed.
3. **Language pointer**, only with a language reference — `**Language-agnostic here.** The Python specifics live in references/python.md.`
4. **Caveat**, one of two fixed forms:
   - Applied to existing code: `**In an existing project, ask first.** Where a repo already has …, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.`
   - Opt-in style: `**This is opt-in.** Reach for <X> where it genuinely fits (below), not by default.` — paired with a `## When to use` section and a closing fallback line.

## Structure the body

- **Use punchy section headings**: imperative for an action (`Pick a layout`), a noun for a catalogue (`Patterns`), sentence case.
- **Order by dependency.** Sections that define vocabulary come before those that spend it, so a reader never meets a term before its definition; synthesising sections (`Pick a layout`, `Run`) trail.
- **State each rule exactly once.** A rule stated twice drifts as soon as one copy is edited, and a reader who meets both wonders whether they differ.
Fold one-line points into a catalogue section rather than giving them a stub heading.
- **Make the why an observable consequence.** "Define `__all__` to make the API explicit" gives a purpose nobody can check; "mark a re-export with a redundant alias, or the linter reads it as an unused import" says what happens, and a reader can watch it happen.
A purpose-only why gets applied by feel and drifts; write the rule so that following and breaking it look different.
Where nothing observable turns on a rule, label it a preference so the reader knows it bends.
- **State a rule as a rule.** Write absolutes imperatively ("Write one method chain"); keep *prefer* for a genuine trade-off and give its exception in the same breath.
If every rule hedges, the absolutes get broken as often as the defaults.
- **Give a load-bearing rule its own line**, not the last sentence of a long paragraph, where it gets read past.
- **Show the anti-pattern for the most-broken rule** as one compact wrong/right pair — a fenced pair in a language-bound skill, a named pair in prose in a language-agnostic one, so it doesn't quietly become a Python skill.
- **Keep examples general.** An example drawn from the project that prompted a rule teaches its domain along with the rule; use the smallest example that shows the rule, from a domain any reader knows.
- **Keep cross-references live.** When you move or reword a rule, grep this skill and its neighbours for the section name and the rule's wording, so no pointer leads to nothing.

## Split the principle from the language

A language-agnostic skill states the principles; `references/<language>.md` shows how they land.

- **The skill** closes with `## Language specifics`: "Read the file for the language you're working in:", a `- **Python** → references/python.md (…)` bullet, and "Add a new references/<language>.md when you work in another language rather than adding its specifics to this file."
- **The reference** opens with the H1 `<skill H1> in Python` and "The language-agnostic principles are in `SKILL.md`; this is how they land in Python[ with `<framework>`]."
- **Headings mirror** the skill wherever a topic appears in both; reference-only mechanics take their own names.
- **A build-out reference leads with its structure** (the package tree) and closes with `Run`; a style reference has neither and orders by dependency alone.
- **The reference never restates a principle** — it shows the mechanics for one the skill states.

A skill tied to one library has no language axis, so it splits by **topic** instead: `references/<topic>.md` cookbooks, each with its own H1 and scope line, and a closing `## Reference cookbooks` section.

**A reference earns its place by holding what the skill cannot**: mechanics too long for the body, a worked trap, a framework build-out.
An API listing does not — the reader already knows a filter takes a predicate, and the real traps get lost among the filler.
Keep only lines that would change what gets written.
