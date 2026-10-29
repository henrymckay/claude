---
name: write-markdown
description: >-
  How to write clear, well-structured Markdown for any audience — READMEs, docs,
  guides, changelogs and issues/PRs written for humans, and SKILL.md, CLAUDE.md,
  agent instructions and prompts written for an LLM. Use whenever writing or
  editing Markdown, even if the user just says "write a README", "document
  this", "update the docs", "write a skill", or "tidy up this CLAUDE.md". Covers
  the universal principles first, then the human-only polish and the LLM-only
  guidance, so decide the reader first and apply the matching set. write-skills
  layers on this for authoring a skill.
---

# Write Markdown

Markdown has two readers: **humans**, who skim, and **LLMs**, which read every token.
Most rules serve both, but polish that helps a human wastes a model's context, and density that suits a model loses a human.
So **decide the audience first**, apply the universal rules, then the audience's own set.

- **Human-facing** — READMEs, docs, guides, changelogs, issue and PR descriptions.
- **LLM-facing** — `SKILL.md`, `CLAUDE.md`, agent instructions, prompts, anything a model consumes as context.

`write-skills` layers on this for authoring a skill.
Three mistakes account for most weak Markdown: filler that restates what the context already fixes, prose where a heading or list would carry the structure, and polish aimed at the wrong reader.

**In an existing project, ask first.** Where a repo already has an established house style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Universal principles

### Words

- **Every word earns its place.** Cut filler, lead-ins and anything the context already establishes.
  - "in order to" → "to"; drop "It covers:" before a list that plainly elaborates the line above it.
  - In a Claude Code repo, "reinstall any Claude Code plugins" → "reinstall any plugins".
- **Match the density of the neighbours.** You can pass "every word earns its place" sentence by sentence and still write a section three times the length of those around it.
Read the comparable sections first and write to their scale; push depth to where it can be long (a linked page, a reference file) and leave a pointer.
Re-read the result in place, where excess length is obvious at a glance.
- **Write instructions imperatively.** "Install the CLI", not "The CLI can be installed".
Once a passage gives instructions, every sentence in it is one — a step that slips into narration breaks the parallelism that makes a sequence scannable.
A sentence stating what something *is* stays declarative: "`CLAUDE.md` holds the project's rules".
- **Be concrete.** A short example beats a paragraph describing one; it teaches a human and gives a model a pattern to copy.
- **Expand an acronym on first use** — "MRO (Method Resolution Order)" — unless it is more familiar than its expansion (`API`, `CLI`, `HTTP`, `URL`).
- **Use British spelling** (organise, colour, behaviour); code keeps its own (`serialize`).

### Structure

- **One `#` title, then `##` and `###`, never skipping a level.** Nesting past `###` usually means the doc should split.
- **Headings are short labels in sentence case.** Name the section in the fewest exact words — "Toolchain", not "Toolchain summary" — and capitalise only the first word, proper nouns and code as spelled: "Name `.pipe()` steps", never "Name The Steps".
- **Use imperative headings for task sections** — "Set up on a new machine", not "Setup notes" — including the `#` title of a how-to doc ("Write Python").
Catalogue sections and docs that *name* a thing keep nouns ("Requirements", a README's project name).
- **One statement per bullet.** If a bullet says two things, split it or add a sub-bullet.
- **Alphabetise a list with no inherent order**, so every item has a predictable place; keep a meaningful order (steps, priority, dependency) where one exists.
- **Prefer lists to tables.** A table whose later columns only describe the first is a list in disguise.
Keep tables for genuine comparison, where every column holds a parallel value worth aligning (`pandas` → `polars`, a feature across options).

### Formatting

- **One sentence per line** (semantic line breaks).
It renders identically to a wrapped paragraph, but a reworded sentence becomes a one-line diff; hard-wrapping at a column reflows the whole paragraph instead.
  - A top-level bullet's continuation sentences sit flush left; a nested or numbered item's stay indented, or they would leave the item.
  - A bold label stays on the line with the first sentence.
- **Bold the few words a scanner must not miss**, never a whole sentence; italics for a term being defined or light stress.
Avoid underline — it needs raw HTML and reads as a link.
- **Monospace code**: filenames, commands, flags, identifiers, and package or tool names, whether or not they are linked.
  - Inside backticks use the code spelling, not the brand: `polars`, `numpy`, `fastapi`.
  - A name in prose that refers to the package is code too — "`fastapi` validates the body".
  - Leave unmonospaced only proper nouns that aren't the package: a company (Posit), a service (Redis), a formal product name (Shiny for Python).

### Code blocks

- **Tag every fenced block with its language** (` ```bash `, ` ```python `).
- **Make runnable blocks copy-pasteable.** Write commands exactly as typed — single spaces, no column alignment, no explanatory comments — and put the explanation in prose.
Teaching examples may keep teaching comments.
  - Separate a flag from its value with a space (`--import-mode importlib`); use `=` only where a space would misparse.
- **Hold an example to its language's conventions** — in Python, `write-python`, down to what `ruff` accepts.
A reader copies examples, so one that fails the project's linter teaches exactly the habit the project rejects.

## For humans

Humans skim, jump to headings and copy code, so optimise for the scan.
Some rules below have an observable effect (a buried point goes unread); others are **house preference**, worth following for consistency but not worth arguing from — the emoji anchors, full stops and dropped Oxford comma.

- **Front-load.** The first lines say what this is and whether the reader is in the right place — a README opens with a one-line description, not history.
- **Put content where its reader looks.** Don't strand a maintainer's warning in the setup path a new user reads.
- **Default to sections of bullets**; keep prose for ideas that need connected sentences.
- **One idea per sentence.** Split compound sentences instead of joining clauses with commas, "and", dashes, semicolons or parentheses.
Inside a bullet, don't bolt on an aside or inline list with a colon or dash — use sub-bullets.
A lead-in line ending in ":" before a real list is fine.
- **Second person, active voice, present tense, no first person.** "Run `x` to build", not "The build may be performed"; "Personal conventions", not "My conventions".
- **Link the first mention** of a tool, library, standard — and the repo's own files and skills, which are the links most often missing.
Anchor the link on the one or two words naming its destination: "install from a [marketplace](…)", never "[click here](…)" or a bare URL.
- **Use GitHub alert callouts** for asides: `[!NOTE]` info, `[!TIP]` advice, `[!IMPORTANT]` key point, `[!WARNING]` or `[!CAUTION]` for a hazard rather than a "don't" buried in prose.
- **Use richer features where they help** — task lists, collapsible sections, a table of contents for a long doc.
- **Keep it accessible.** Real headings rather than bold lines (screen readers navigate by them), alt text on images, and never colour or emoji alone carrying meaning.
- **House style:**
  - Start sections and key bullets with an emoji anchor, sparingly.
  - End every bullet with a full stop.
  - No Oxford comma — "uv, ruff and pytest" — unless it prevents a real ambiguity.
- **Docstrings follow the human rules too**, though they are reStructuredText formatted per `write-python`: an imperative summary line and the *why* rather than a restatement of the name.

## For LLMs

A model reads every token and doesn't skim, so optimise for clarity per token, not visual appeal.

- **Explain the why.** A model follows a rule more reliably when it knows the reason — the one place to spend words rather than save them.
- **Disclose progressively.** Keep the entry file lean and push depth into files that load only when needed, such as a skill's `references/`.
- **Lead with triggering and scope.** A skill's `description` decides whether it is invoked, so make it specific about what and when.
Write it as plain prose: it is matched as text and rendered nowhere, so backticks, bold and links in it are literal noise.
- **Density is fine; polish is waste.** Skip emojis, badges, collapsible sections and full stops for consistency's sake.
Em-dashes, semicolons and parentheticals parse fine, so don't fragment dense reasoning into sub-bullets for looks.
- **Use bold as a label, not a lever.** Bolding where a rule starts aids parsing; bolding to force compliance barely registers.
State importance in words ("mandatory, not advisory").
- **Cut meta-preamble from a `CLAUDE.md`.** The model knows the file holds the user's instructions, so a "this file contains…" opener is noise; phrase every line as a command.
- **Cut default behaviour from a `CLAUDE.md`.** It is loaded every session, so it earns its place only with what deviates from the model's defaults or is specific to the user — "be concise" and "match the surrounding code" are wasted lines.

## Avoid

- Burying the point below background or history.
- Documenting the obvious while omitting what the reader needs.
- Giant paragraphs and walls of undifferentiated bullets.
- Screenshots of text or code that could be a copy-pasteable block.
