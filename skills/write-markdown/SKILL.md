---
name: write-markdown
description: >-
  How to write clear, well-structured Markdown for any audience — READMEs, docs,
  guides, changelogs, issues/PRs written for HUMANS, and SKILL.md, CLAUDE.md,
  agent/tool instructions and prompts written for an LLM. Use whenever writing or
  editing Markdown, even if the user just says "write a README", "document this",
  "update the docs", "write a skill", or "tidy up this CLAUDE.md". Covers the
  universal principles that apply to both audiences, then the human-only polish
  and the LLM-only guidance — so decide the reader first, then apply the matching
  rules.
---

# Writing Markdown

Markdown has two very different readers: **humans**, who skim and scan, and **LLMs**, which parse every token.
Most principles serve both, but some polish helps humans and wastes tokens on a model, and some density suits a model but loses a human.
So **decide the audience first**, apply the universal rules, then add the audience-specific set.

- **Human-facing** — READMEs, documentation, guides, tutorials, changelogs, wikis, issue/PR descriptions.
- **LLM-facing** — `SKILL.md`, `CLAUDE.md`, agent/tool instructions, prompts, anything a model consumes as context.

## Universal principles (both audiences)

- **Be succinct — prefer fewer words over more.** Cut filler ("in order to" → "to") and throat-clearing; every word should earn its place.
- **Structure with sections and headings.** Use a clear hierarchy (one `#` title, then `##`/`###`) with descriptive heading text; don't skip levels.
- **Prefer imperative, action-oriented headings** for how-to and task sections — "Add a skill", "Set up on a new machine", not "Adding a skill" or "New machine notes".
  - A verb tells the reader what they'll *do* in that section.
  - Reference or catalogue sections that don't describe an action (e.g. "Skills", "Requirements") can stay noun phrases.
- **Prefer bullets, one clear statement each.** If a bullet says two things, split it or add a sub-bullet; use sub-bullets to expand or clarify.
- **Order generic lists alphabetically.** When a list has no inherent order, alphabetise it so every item has a predictable place; keep a meaningful order where one exists (steps, priority, chronology).
- **Write imperatively.** Lead with a verb — "Install the CLI", not "The CLI can be installed".
- **Fenced code blocks with a language tag** (` ```bash `, ` ```python `), and inline `code` for filenames, commands, flags, identifiers, and tool, package, or library names. Monospace them whether or not they are also linked.
- **Keep runnable code blocks real and copy-pasteable.** Write commands exactly as you would type them: a single space between arguments, no cosmetic column alignment, and no explanatory comments inside the block. Put explanation in the surrounding prose instead. (Illustrative code examples that teach a pattern may still use teaching comments.)
- **Prefer lists over tables.** If a table's later columns just describe the item in the first, it's a list in disguise, so write it as a bullet list with one item per line. Reserve tables for genuine comparison or translation, where every column holds a parallel value worth aligning (pandas → Polars, or a feature across several options).
- **One sentence per line** (semantic line breaks).
  It renders identically to a wrapped paragraph but keeps diffs clean — rewording one sentence is a one-line change.
  Separate paragraphs with a blank line; don't hard-wrap at a fixed column (it reflows the whole paragraph and produces noisy diffs).
- **Be concrete.** A short example beats a paragraph describing one — this helps a human learn and gives a model a pattern to follow.

## For human readers (add on top)

Humans skim, jump to headings, and copy code — optimise for the scan:

- **Front-load.** The first lines say what this is and whether the reader is in the right place.
  A README opens with a one-line description of the project, not its history.
- **Target each section at its reader.** Put content where the reader who needs it will look. Don't strand a maintainer's warning in the setup path a new user reads.
- **Default shape: sections of bullets.** Reserve prose for ideas that genuinely need connected sentences.
- **Lean toward lists over tables.** Humans scan a list faster than they parse a grid. Even for a genuine comparison, prefer a list unless several columns' alignment truly aids reading. (LLM-facing docs can use tables more freely.)
- **Start sections, and key bullets, with an emoji** as a visual anchor.
  Use it purposefully, not on every line.
- **End every bullet with a full stop** for consistent, finished-looking lists.
- **One idea per sentence.** This is the prose version of one clear statement per bullet. Split a compound sentence into short separate ones rather than joining independent clauses with a comma, an "and", an em-dash, a semicolon, or a parenthesis. "Personal skills and instructions. Symlinked everywhere." beats one long joined sentence.
  - Write two plain sentences, or in a list start a sub-bullet.
  - It's about prose punctuation, not Markdown syntax: link brackets `[text](url)` and hyphenated words are fine.
  - LLMs parse joined clauses fine, so this is a human-only rule.
- **Tone: second person, active voice, present tense.** "Run `x` to build" beats "The build may be performed by running `x`".
- **Avoid first person** ("I", "we", "my"). Address the reader as "you" or write impersonally; "Personal coding conventions" beats "My coding conventions".
- **Link references.** The first time you name a tool, library, spec, or standard, hyperlink it to its source so readers can jump there.
  - Code-like names stay monospaced (per the universal rule) and get linked: [`ruff`](https://docs.astral.sh/ruff/), [`polars`](https://pola.rs).
  - True prose names like [Conventional Commits](https://www.conventionalcommits.org) are linked but stay plain.
- **Descriptive link text, kept short.** Anchor the link on the one or two words that name its destination, not a whole phrase or clause.
  - Write "install from a [marketplace](…)", not "[install from a marketplace](…)".
  - Never `[click here](…)` or a bare URL.
- **Use richer render features when they serve the reader** — task lists, collapsible sections, badges, a table of contents for long docs.
- **Reach for GitHub-flavored alert callouts** to make an aside stand out, where the platform renders them (GitHub and most Markdown viewers):
  - Match the type to intent: `[!NOTE]` for info, `[!TIP]` for advice, `[!IMPORTANT]` for a key point, `[!WARNING]` or `[!CAUTION]` for hazards.
  - Prefer a `[!WARNING]` or `[!CAUTION]` over burying a "don't do this" in prose.
- **Accessibility** — real heading hierarchy (screen readers navigate by it, don't fake headings with bold), image alt text, and don't rely on colour or emoji alone to carry meaning.

## For LLM consumption (apply instead of the human polish)

A model parses every token and doesn't skim, so optimise for clarity and context-efficiency, not visual appeal:

- **Explain the *why*, not just the rule.** A model follows an instruction more reliably when it understands the reason — this is the one place to spend extra words, not save them.
- **Progressive disclosure.** Keep the entry file lean and push depth into referenced files that load only when needed (e.g. a skill's `references/`).
- **Lead with triggering/scope.** For a skill, the `description` frontmatter is what decides invocation — make it specific about *what* and *when*.
- **Density is fine; cosmetic polish is waste.** Skip emojis, decorative badges, collapsible sections, and full-stop-on-every-bullet consistency — they cost tokens and add no parsing value for a model.
- **Inline nuance is fine.** A model reads em-dashes, semicolons, and parentheticals without trouble, so don't fragment dense reasoning into sub-bullets just for looks.

## Human-only vs universal — quick reference

| Convention | Humans | LLMs |
|---|---|---|
| Succinct, structured, imperative, code fences, tables, semantic line breaks | ✅ | ✅ |
| Front-loading, scannable sections-of-bullets | ✅ | ➖ (structure yes, skim-tuning no) |
| Emojis, full stop on every bullet, no inline asides | ✅ | ❌ (token cost, no benefit) |
| Badges, collapsible sections, callouts, TOC | ✅ | ❌ |
| Explain the *why*, progressive disclosure, triggering-first | ➖ | ✅ |

## Things to avoid (either audience)

- Burying the point below background or history — front-load instead.
- Deep heading nesting past `###` — usually a sign to split the doc.
- Giant unbroken paragraphs and walls of undifferentiated bullets.
- Screenshots of text or code that could be a copy-pasteable code block.
- Documenting the obvious while omitting what the reader actually needs.
