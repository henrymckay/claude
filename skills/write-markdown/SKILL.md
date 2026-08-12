---
name: write-markdown
description: >-
  How to write clear, well-structured Markdown for any audience — READMEs, docs,
  guides, changelogs, issues/PRs written for humans, and SKILL.md, CLAUDE.md,
  agent/tool instructions and prompts written for an LLM. Use whenever writing or
  editing Markdown, even if the user just says "write a README", "document this",
  "update the docs", "write a skill", or "tidy up this CLAUDE.md". Covers the
  universal principles that apply to both audiences, then the human-only polish
  and the LLM-only guidance — so decide the reader first, then apply the matching
  rules.
---

# Write Markdown

Markdown has two very different readers: **humans**, who skim and scan, and **Large Language Models (LLMs)**, which parse every token.
Most principles serve both, but some polish helps humans and wastes tokens on a model, and some density suits a model but loses a human.
So **decide the audience first**, apply the universal rules, then add the audience-specific set.

- **Human-facing** — READMEs, documentation, guides, tutorials, changelogs, wikis, issue/PR descriptions.
- **LLM-facing** — `SKILL.md`, `CLAUDE.md`, agent/tool instructions, prompts, anything a model consumes as context.

## Universal principles

- **Be succinct — every word must earn its place.** Cut filler, throat-clearing, and anything the surrounding context already establishes.
  - Filler and lead-ins: "in order to" → "to"; drop "It covers:" before a list that plainly elaborates the sentence above it.
  - Words the context already fixes: in a Claude Code repo, "reinstall any Claude Code plugins" → "reinstall any plugins", and "Anthropic's marketplace" → "the marketplace".
  - Parallel phrasing tightens a list: "When to commit and push, and when to hold off" beats a comma-spliced clause.
- **Structure with sections and headings.** Use a clear hierarchy (one `#` title, then `##`/`###`) with descriptive heading text; don't skip levels.
- **Keep headings punchy and precise.** A heading is a label, not a sentence — use the fewest words that name the section exactly, and cut filler ("Toolchain", not "Toolchain summary"; "Data", not "Package data and assets").
  Prune articles and trailing nouns that add nothing.
- **Headings use sentence case** — capitalise the first word, proper nouns, and code as it's really spelled; not Title Case.
  "Configure the project", "Reach-for libraries", "Naming `.pipe()` helpers" — never "Configure The Project".
  It's the technical-docs standard, and it keeps identifiers in a heading (`polars`, `.pipe()`, `code/`) as the code reads them.
- **Prefer imperative, action-oriented headings** for how-to and task sections — "Add a skill", "Set up on a new machine", not "Adding a skill" or "New machine notes".
  - A verb tells the reader what they'll *do* in that section.
  - This applies to the document's `#` title too when the doc is a how-to — a skill or a guide — so "Write Python", not "Writing Python".
    A doc that *names* a thing keeps a noun title: a README's project name, a reference file's topic.
  - Reference or catalogue sections that don't describe an action (e.g. "Skills", "Requirements") can stay noun phrases.
- **Prefer bullets, one clear statement each.** If a bullet says two things, split it or add a sub-bullet; use sub-bullets to expand or clarify.
- **Order generic lists alphabetically.** When a list has no inherent order, alphabetise it so every item has a predictable place; keep a meaningful order where one exists (steps, priority, chronology).
- **Write action sentences imperatively too, not just headings.** Lead an instruction with a verb — "Install the CLI", not "The CLI can be installed".
  Leave a sentence that states what something *is* declarative — "`CLAUDE.md` holds the project's rules" — the same way reference-section headings stay noun phrases.
- **Fenced code blocks with a language tag** (` ```bash `, ` ```python `), and inline `code` for filenames, commands, flags, identifiers, and tool, package, or library names.
  Monospace them whether or not they are also linked.
  - **Inside backticks, use the real code spelling, not the brand capitalisation.** Backticks mark a token as code, so write the import or command name: `polars` not `Polars`, `numpy` not `NumPy`, `fastapi` not `FastAPI`.
    (An *unmonospaced* brand mention in prose or a title may keep its capitalisation — "Polars is fast".)
- **Emphasise key terms with bold and italic.** Bold the word (or few words) a scanner must not miss — never a whole sentence, since emphasis on everything emphasises nothing.
  Use italics for lighter stress or for a term you are defining.
  Underline isn't native Markdown (it needs raw HTML and reads as a link), so avoid it.
- **Keep runnable code blocks real and copy-pasteable.** Write commands exactly as you would type them: a single space between arguments, no cosmetic column alignment, and no explanatory comments inside the block.
  Put explanation in the surrounding prose instead.
  (Illustrative code examples that teach a pattern may still use teaching comments.)
  - Prefer a space to `=` before a flag's value — `--import-mode importlib`, not `--import-mode=importlib` — since it reads cleaner.
    Keep `=` only where a space would misparse: the value starts with `-`, or the option's argument is optional.
- **Prefer lists over tables.** If a table's later columns just describe the item in the first, it's a list in disguise, so write it as a bullet list with one item per line.
  Reserve tables for genuine comparison or translation, where every column holds a parallel value worth aligning (`pandas` → `polars`, or a feature across several options).
- **One sentence per line** (semantic line breaks) — prose and bullets alike.
  It renders identically to a wrapped paragraph but keeps diffs clean, since rewording one sentence is a one-line change.
  Inside a bullet, break each sentence onto its own line indented to align under the bullet's text; the soft newlines render as spaces, so the item still reads as one flowing bullet.
  A bold label isn't a sentence — keep it on the marker line with the first sentence; it's the *following* sentences that break onto continuation lines.
  Separate paragraphs with a blank line; don't hard-wrap at a fixed column (it reflows the whole paragraph and produces noisy diffs).
- **Be concrete.** A short example beats a paragraph describing one — this helps a human learn and gives a model a pattern to follow.
- **Expand an acronym on first use.** Give the full term with the acronym in parentheses once — "Method-Resolution Order (MRO)", "Easier to Ask Forgiveness than Permission (EAFP)" — then use the short form.
  A reader, human or model, shouldn't have to decode it.
  Skip only acronyms more familiar than their expansion (`HTTP`, `URL`, `CLI`).
- **Use British spelling, consistently** — `-ise`/`-our` (organise, capitalise, colour, behaviour), not the US `-ize`/`-or`.
  Code keeps its own spelling, though: a `serialize` method or a `SerializableMixin` class stays as the code names it.

## For humans

Humans skim, jump to headings, and copy code — optimise for the scan:

- **Front-load.** The first lines say what this is and whether the reader is in the right place.
  A README opens with a one-line description of the project, not its history.
- **Docstrings are human-facing prose too.** Though a docstring is reStructuredText, not Markdown (format it per `write-python`), the same human principles apply — a succinct, imperative summary line, one idea per sentence, the *why* and the non-obvious rather than a restatement of the name.
- **Target each section at its reader.** Put content where the reader who needs it will look.
  Don't strand a maintainer's warning in the setup path a new user reads.
- **Default shape: sections of bullets.** Reserve prose for ideas that genuinely need connected sentences.
- **Lean toward lists over tables.** Humans scan a list faster than they parse a grid.
  Even for a genuine comparison, prefer a list unless several columns' alignment truly aids reading.
  (LLM-facing docs can use tables more freely.)
- **Start sections, and key bullets, with an emoji** as a visual anchor.
  Use it purposefully, not on every line.
- **End every bullet with a full stop** for consistent, finished-looking lists.
- **One idea per sentence.** This is the prose version of one clear statement per bullet.
  Split a compound sentence into short separate ones rather than joining independent clauses with a comma, an "and", an em-dash, a semicolon, or a parenthesis.
  "Personal skills and instructions. Symlinked everywhere." beats one long joined sentence.
  - Write two plain sentences, or in a list start a sub-bullet.
  - No colons or dashes inside a bullet either — don't use them to bolt on an inline list or an aside.
    Break the items into sub-bullets, or rephrase.
    (A lead-in line ending in ":" that introduces a real bulleted list is fine, since that colon isn't inside a bullet.)
  - It's about prose punctuation, not Markdown syntax: link brackets `[text](url)` and hyphenated words are fine.
  - LLMs parse joined clauses fine, so this is a human-only rule.
- **No Oxford comma.** Drop the serial comma before the final "and"/"or" in a list — "uv, ruff, pyright and pytest", not "…pyright, and pytest".
  More broadly avoid a comma before "and"/"or" unless it prevents a genuine ambiguity.
  LLMs parse both, so this is human-only.
- **Tone: second person, active voice, present tense.** "Run `x` to build" beats "The build may be performed by running `x`".
- **Avoid first person** ("I", "we", "my").
  Address the reader as "you" or write impersonally; "Personal coding conventions" beats "My coding conventions".
- **Link references.** The first time you name a tool, library, spec, or standard, hyperlink it to its source so readers can jump there.
  - Code-like names stay monospaced (per the universal rule) and get linked: [`ruff`](https://docs.astral.sh/ruff/), [`polars`](https://pola.rs).
  - True prose names like [Conventional Commits](https://www.conventionalcommits.org) are linked but stay plain.
  - Link the repo's own artifacts too, not just external tools — point a file, skill, or module name at its location in the tree so the reader can open it.
    If you link every dependency but not the thing the doc is about, the most useful link is the one missing.
- **Descriptive link text, kept short.** Anchor the link on the one or two words that name its destination, not a whole phrase or clause.
  - Write "install from a [marketplace](…)", not "[install from a marketplace](…)".
  - Never `[click here](…)` or a bare URL.
- **Use richer render features when they serve the reader** — task lists, collapsible sections, badges, a table of contents for long docs.
- **Reach for GitHub-flavoured alert callouts** to make an aside stand out, where the platform renders them (GitHub and most Markdown viewers):
  - Match the type to intent: `[!NOTE]` for info, `[!TIP]` for advice, `[!IMPORTANT]` for a key point, `[!WARNING]` or `[!CAUTION]` for hazards.
  - Prefer a `[!WARNING]` or `[!CAUTION]` over burying a "don't do this" in prose.
- **Accessibility** — real heading hierarchy (screen readers navigate by it, don't fake headings with bold), image alt text, and don't rely on colour or emoji alone to carry meaning.

## For LLMs

A model parses every token and doesn't skim, so optimise for clarity and context-efficiency, not visual appeal:

- **Explain the *why*, not just the rule.** A model follows an instruction more reliably when it understands the reason — this is the one place to spend extra words, not save them.
- **Progressive disclosure.** Keep the entry file lean and push depth into referenced files that load only when needed (e.g. a skill's `references/`).
- **Lead with triggering/scope.** For a skill, the `description` frontmatter is what decides invocation — make it specific about *what* and *when*.
  Write it as **plain prose**: it's matched as text and rendered nowhere, so backticks, bold, and links in it are literal noise (name `SKILL.md` or `write-python` bare, even though the body monospaces them).
- **Density is fine; cosmetic polish is waste.** Skip emojis, decorative badges, collapsible sections, and full-stop-on-every-bullet consistency — they cost tokens and add no parsing value for a model.
- **Emphasis is a weak lever for a model.** Bold earns its place as a *label* — it marks where a rule or key term starts, which aids parsing (as this skill bolds each rule name) — but as a signal of importance it barely registers.
  Never rely on `**bold**` to force compliance; state importance in words ("mandatory, not advisory").
  Italics add even less, so spend them only where they genuinely clarify.
- **Inline nuance is fine.** A model reads em-dashes, semicolons, and parentheticals without trouble, so don't fragment dense reasoning into sub-bullets just for looks.
- **Skip meta-preamble in a `CLAUDE.md`.** The model already knows the file is the user's instructions, so a role-describing title like "# Global instructions" or a "this file holds cross-project guidance" opener is pure fluff — cut it.
  A short `#` name for the project or scope is optional and harmless; just never follow it with prose describing the file.
  Phrase the instructions as commands to the model, not descriptions of the file.
- **Cut default behaviour from a `CLAUDE.md`.** It earns its always-on context only with what deviates from the model's defaults or is specific to the user.
  "Be concise" and "match the surrounding code" are already how the model behaves, so they are wasted lines.
  Keep the corrections, autonomy grants, and conventions the model would not infer on its own — and if a whole section reduces to defaults, drop the section.

## Avoid

- Burying the point below background or history — front-load instead.
- Deep heading nesting past `###` — usually a sign to split the doc.
- Documenting the obvious while omitting what the reader actually needs.
- Giant unbroken paragraphs and walls of undifferentiated bullets.
- Screenshots of text or code that could be a copy-pasteable code block.
