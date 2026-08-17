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

The description *is* the trigger, so optimise it for invocation (the `skill-creator` plugin has a loop for that).
Write it in **plain prose, no backticks** (see `write-markdown`), in a fixed order so every description reads the same way and **mirrors the skill's own opening**:

- **What it is** — a short phrase naming the skill and its key topics; counterpart skills use a **parallel** form ("Functional programming done well — …" / "Object-oriented design done well — …").
- **When to use it** — "Use when/whenever …", then the contexts and phrases that should invoke it, ending with the casual ones ("even if the user just says '…'"). Cover the whole body and promise nothing it doesn't deliver.
- **Opt-in-ness, in fixed words** — an opt-in style skill states, verbatim and matching its body line, "This is an opt-in style skill: reach for <X> where it genuinely fits, not by default." A how-to that always applies when its task arises makes no opt-in claim.
- **The reference pointer, in fixed words** — a language-agnostic skill with a language reference states "Language-agnostic principles here; Python <idioms/build-outs/…> in references/python.md.", matching its `Language specifics` section.
- **What it builds on and to** — "Layers on <skill> …; <skill> is the <…> counterpart" — the same skills the opening names.

## Open consistently

Every skill opens the same three-part way:

- **A line or two placing the skill in the web** — what it is, then the skills it **builds on** and the skills it **builds to**.
  - *Builds on* — the ones it layers on or assumes as a base: `write-entry-points` "layers on `structure-python` and `be-functional`"; `write-tests` "follows the same conventions as the code it covers — in Python that's `write-python`".
  - *Builds to* — where it hands an adjacent concern off: "for scaffolding, see `setup-python`"; "the concrete wiring lives in `write-entry-points`".
  - Bare backticked names, and name the same build-on and build-to skills the description does, so a reader can follow the thread in either direction.
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
