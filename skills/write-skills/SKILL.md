---
name: write-skills
description: >-
  House conventions for authoring a Claude Code skill in this repo — naming it
  verb-first, writing a description that triggers reliably and states its
  opt-in-ness, opening with the standard existing-project and opt-in caveats,
  structuring the body, and splitting a language-agnostic principle skill from
  its language reference (the SKILL-to-reference contract). Use whenever
  creating or editing a SKILL.md or its references, naming a skill, writing or
  reviewing a skill description, or splitting out a language reference — even if
  the user just says "make a skill", "add a skill", or "fix this skill's
  description". Layers on write-markdown for prose mechanics, and defers the
  draft-eval-iterate loop, file anatomy, progressive disclosure, packaging, and
  description-triggering optimisation to the skill-creator plugin.
---

# Write skills

House conventions for authoring a skill — the decisions that keep this library's skills consistent.
They sit on top of `write-markdown` (how to write the prose) and the `skill-creator` plugin (the draft-eval-iterate loop, the file anatomy, progressive disclosure, packaging, and triggering optimisation).
Cover only what those don't: naming, description style, the standard opening, body structure, and the split between a language-agnostic skill and its language reference.

**In an existing project, ask first.** Where a skill or repo already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Name it

Name a skill **verb-first and compact**, so the name reads as *when Claude reaches for it*, not what topic it's about.
Kebab-case, one or two words, the house prefix carrying the verb:

- **`be-`** — a style to adopt (`be-functional`, `be-oop`).
- **`use-`** — a tool or library (`use-git`, `use-polars`).
- **`write-`** — produce an artefact (`write-python`, `write-tests`).
- **`setup-` / `structure-`** — arrange a project (`setup-python`, `structure-python`).

`write-tests`, not `testing-guide`; `structure-python`, not `python-structure`.

## Write the description

The description *is* the trigger, so optimise it for invocation (the `skill-creator` plugin has a loop for that) — these are the house style rules on top:

- **Cover what's in the skill, precisely.** Every major section is discoverable from the description, and nothing is promised that the body doesn't deliver.
- **Say what, then when.** What the skill does, followed by the phrases and contexts that should invoke it — including the casual ones a user actually types ("even if the user just says 'add a CLI'").
- **State opt-in-ness consistently.** A style skill applied only where it fits says so in the same words each time ("This is an opt-in style skill…"); a how-to that always applies when its task arises makes no opt-in claim.
- **Plain prose, no backticks** (see `write-markdown`), and name the skills it **layers on** and **defers to**.

## Open consistently

Every skill opens the same three-part way:

- **One line** on what the skill is and what it layers on.
- **The language pointer**, only if it has a language reference — a standalone bold line: `**Language-agnostic here.** The Python specifics live in references/python.md.`
- **The caveat**, one of two fixed sentences:
  - *Applied to existing code* → `**In an existing project, ask first.** Where a repo already has …, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.`
  - *An opt-in style skill* → `**This is opt-in.** Reach for <X> where it genuinely fits (below), not by default.` — paired with a `## When to reach for <X>` section of bullets and a closing fallback line.

## Structure the body

- **Sections of principles with punchy headings.** Terse, no wrapper words (`Test data`, not `Where test data lives`); imperative for an action (`Pick a layout`, `Run`), a noun for a catalogue (`Patterns`); sentence case; monospace packages.
- **Order by dependency.** Nothing precedes what it builds on: abstract, depended-upon sections lead, and synthesising or invoking ones (`Pick a layout`, `Run`) trail.
- **No thin stubs, no repetition.** Fold a one-line point into a catalogue section rather than giving it its own; avoid grab-bag headings; state each principle exactly **once**.
- **Explain the why, not just the rule** (see `write-markdown`), and keep examples obeying the language's own skill — annotated and documented per `write-python`.

## Split the principle from the language

A language-agnostic skill keeps the principles and pushes the mechanics to `references/<language>.md`.
Keep the pair consistent:

- **The skill** closes with a `## Language specifics` section: the lead "Read the file for the language you're working in:", a `- **Python** → references/python.md (…)` bullet, and the closer "Add a new references/<language>.md when you work in another language rather than adding its specifics to this file."
- **The reference** opens with the H1 `<skill H1> in Python` and the line "The language-agnostic principles are in `SKILL.md`; this is how they land in Python[ with `<framework>`]."
- **Headings mirror** the skill wherever a topic appears in both; reference-only mechanics (framework wiring, assertions) take their own names. Lead the reference with its structural section and `Run`, again ordered by dependency.
- **The skill states each principle; the reference shows the mechanics** for it — never restating the principle.
