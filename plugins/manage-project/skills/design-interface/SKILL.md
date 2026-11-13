---
name: design-interface
description: >-
  How every surface a project ships should look and read — one house design
  system (colour, type, spacing, charts, states), a design plan before code,
  and the bar a dashboard, page, CLI, API, message or README must clear. Load
  it before the first line of any screen, chart, page or styled output, even a
  prototype. Use whenever designing, styling or judging a surface — even if
  the user just says "make it look good", "add dark mode" or "this looks
  primitive".
---

# Design the interface

How a project's surfaces look and read: one house design system, the bar each kind of surface must clear, and the criteria a running surface is scored against.
It layers on the built-in `dataviz` skill for choosing a chart's form and marks, whose reference palette the chart colours below adopt; `plan-project` sets each surface's ambition from the bar here, `write-entry-points` builds the surface, and `build-project`'s gate runs the evaluator against the criteria here.
Three mistakes account for most surfaces that look primitive: a framework's default theme shipped because no instruction asked for anything else, a look decided afresh in each project so no two match and every one re-argues its colours, and a surface judged by reading its code rather than by looking at it running.

- **Wrong** — the dashboard's tests pass and the build is ticked; nobody opened it, and it ships in the framework's default blue on white with a grey chart that stays white in dark mode.
- **Right** — the tokens are written first, every screen is screenshotted at desktop and phone width in light and dark, and a fresh reader scores those screenshots against the criteria before the tick.

**Technology-neutral here.** The web specifics live in `references/web.md`, the Python frameworks' in `references/python.md`.

**In an existing project, ask first.** Where a repo already has a design system or a brand, check with the user whether to keep it or apply the house system, and prefer the house system unless they choose to keep theirs.

## Set the bar

Every surface a project ships aims at a best-in-class version of its kind, and the plan says so (`plan-project`).
**Ambition is finish, presentation and completeness of what was asked, never extra features or extra risk**: nothing here loosens `secure-project`, the rule against outward action in autonomous mode, or building only what the plan needs, and a fix that would is reported, not made.
The bar per kind of surface, each line a criterion the evaluator can check:

- **Dashboard** — the house system below in full, answer first, every state designed, light and dark, usable at phone width; each control answers within 200 ms on the real data where the browser holds it, within a second where it waits on a server.
- **Web page or static site** — the same tokens; one characteristic thing first, not a generic hero; body text under 80 characters a line; a title, a description and a favicon; loads fast from a cold cache.
- **Command-line tool** — `--help` that is the documentation (`write-entry-points`); an error that names what failed and how to fix it in one line, with the exit code; progress on standard error for anything over two seconds; `--format table` aligned, numbers right-aligned, colour only on a terminal and never when `NO_COLOR` is set (`write-entry-points` owns the data forms).
- **API** — a docs page with a title, a description and every endpoint summarised with an example request and response, errors included; one name and one unit per field across endpoints.
- **Message or digest** — the subject carries the verdict and the first line the answer; one chart, rendered with the tokens, where a trend matters; a link to the dashboard; counts only for private data (`send-messages`, `secure-project`).
- **README** — one sentence saying what it is, a screenshot or a terminal capture near the top for anything a person looks at, then a quick start that runs as written.

## The house design system

One look for every project, whichever technology serves it: neutral warm greys, one blue accent, dense and data-first, light and dark.
**Write the tokens into one file before any component**, under the role names below, and read every colour, size and radius from it; a hex value typed into a component is what stays white when the page turns dark.
A project with its own brand swaps the values under a plan decision and keeps the roles, so every rule below still applies.

### Colour roles

| Role | Light | Dark | For |
|---|---|---|---|
| `background` | `#f6f6f3` | `#0d0d0d` | the page |
| `surface` | `#fcfcfb` | `#1a1a19` | cards, chart and table surfaces |
| `raised` | `#fcfcfb` | `#222221` | popovers, menus, tooltips |
| `sunken` | `#efeeea` | `#262625` | table headers, secondary buttons, hover |
| `text` | `#0b0b0b` | `#f0efec` | body and values |
| `text-2` | `#52514e` | `#c3c2b7` | secondary text, legend |
| `muted` | `#66655f` | `#a9a8a0` | labels, captions, axis text |
| `border` | `#e4e3dc` | `#ffffff17` | card and table rules |
| `input` | `#d5d4cb` | `#ffffff29` | control outlines |
| `grid` | `#e1e0d9` | `#2c2c2a` | chart gridlines |
| `axis` | `#c3c2b7` | `#383835` | chart axis lines |
| `accent` | `#2a78d6` | `#3987e5` | primary action, focus ring, selection, series 1 |
| `on-accent` | `#ffffff` | `#ffffff` | text on the accent |
| `up` | `#2a78d6` | `#3987e5` | a rise, a gain |
| `down` | `#e34948` | `#e66767` | a fall, a loss |

- **Status colours are fixed in both schemes**: `good` `#0ca30c`, `warning` `#fab219`, `serious` `#ec835a`, `critical` `#d03b3b`, and `neutral` `#b4b3aa` light, `#5a5954` dark.
- **Status as text takes a darker step in light and a lighter one in dark**, for contrast: `good` `#006300` / `#3fcf3f`, `warning` `#7a5300` / `#fab219`, `critical` `#b02a2a` / `#f08a8a`.
- **A status colour never carries meaning alone** — always with a label or an icon.
- **Up and down are blue and red, not green and red**, which about one man in twelve cannot tell apart; green for up only where the user asks for it.
- **The chart series are `dataviz`'s reference palette**, in its order, light then dark: blue `#2a78d6` / `#3987e5`, orange `#eb6834` / `#d95926`, aqua `#1baf7a` / `#199e70`, yellow `#eda100` / `#c98500`, magenta `#e87ba4` / `#d55181`, green `#008300`, violet `#6250d6` / `#9085e9`, red `#e34948` / `#e66767`.
  The order is what keeps neighbours apart for colour-blind readers; a scatter or small multiples take three series at most and fold the rest into "Other".
  A sequential scale is one blue ramp, a diverging one blue to red through `sunken`.

### Type

- **Inter**, the variable font, bundled with the app rather than fetched from a font service, so it renders offline and on the first paint; the system UI stack behind it.
- **Tabular numerals on every number** — tiles, tables, axes, tooltips — so digits line up down a column and a ticking value does not jitter.
- **A scale of six sizes**: 12 px captions and axis text, 13 tables and secondary text, 14 body, 16 card titles, 20 page title, 28 tile values; weights 400, 500 and 600 only.
- **Sentence case everywhere**, labels included: an all-caps label above every tile is the commonest tell of a generated page.

### Space, shape and depth

- **A 4 px grid**: 4, 8, 12, 16, 24, 32; card padding 16 (12 at phone width), the gap between cards 16 (12).
- **Radii** 6 px for controls, 8 for inner elements, 12 for cards.
- **Cards are flat** — a 1 px `border`, no shadow; a shadow only on what floats (popovers, tooltips: `0 4px 16px` black at 16%).
- **Content at most 1280 px wide**, centred, under a header 56 px tall holding the name, the navigation, the data's age and the scheme toggle.

### Layout and density

- **Answer, explanation, detail, in that order down the page**: a row of three to five tiles (a muted label, the value, a muted line of context: unit, comparison or age), then the charts in cards, then the tables.
- **A chart's card is titled with what it shows and its unit**, with a one-line subtitle for its span or source; a legend only for two or more series, and direct labels where they fit.
- **A table** right-aligns numbers and left-aligns text, rows 36 px tall, a `sunken` sticky header, newest first, scrolling inside its card, paginated or virtualised past about a hundred rows.
- **Dense, not decorated**: more data per screen than a marketing page carries, and no banner, gradient wash, illustration or emoji on a dashboard.
- **At phone width** (390 px): one column, controls wrap, tables scroll inside their own container, and the page itself never scrolls sideways.

### Numbers and dates

- **One formatting module**, `en-GB`, with thousands separators; never a number shown as its language's default string, which is where `0.30000000000000004` and an unrounded float come from.
- **Compact in a tile** (`1.9M`) with the exact figure in its context line or tooltip; a fixed number of decimals per column, chosen by the quantity (a measurement to the precision it is recorded at, a percentage to two places with its sign).
- **Dates as `12 Nov 2026`**, times on the 24-hour clock with the zone named once per screen, and an age as `7 h ago` with the absolute time in its tooltip; ISO 8601 only in URLs, APIs and files.
- **A unit in the column header or axis title**, never repeated in every cell.

### States

Design four states besides the happy one:

- **Loading** — a skeleton in the content's own shape, and fixed heights so nothing jumps when data arrives.
- **Empty** — what would fill it and what to do ("No runs yet — the first nightly writes here").
- **Stale** — the data's age always visible, `warning` once it is stale (`run-unattended`'s definition: two missed runs unless the plan sets another) and `critical` when the last run failed, with text and an icon.
- **Error** — what failed and what to do about it, in the interface's voice, with the rest of the page still working.

### Light and dark

Follow the system's colour scheme by default, with a toggle that remembers the viewer's choice and applies before the first paint, so the page never flashes the other scheme.
Every chart and table redraws from the tokens when the scheme changes; a chart library themed once at start-up is the white chart on the dark page.

### Defaults to avoid

Each is a framework's or a model's default, and makes a surface look generated:

- **A framework's own theme left showing** — Bootstrap's blue, Mantine's violet, Plotly's grey plot area, a chart library's rainbow palette.
- **Template chrome** — all-caps eyebrow labels, identical shadowed cards, gradient washes, an emoji in the interface, a `→` on every link.
- **Chart defaults** — animation on a data update, a pie of more than three slices, 3D, two y axes, a legend where a direct label fits, a spinner where a skeleton fits.
- **Copy defaults** — title case, placeholder text, "Submit", an apology in an error, a vague "Something went wrong".

## Plan the design before the code

Before any component, write the design into the plan's Interface, one entry per screen (`plan-project`): the question it answers, its tiles, each chart with its form (`dataviz`'s reference on choosing a form), its tables and its four states, and an ASCII wireframe of the main screen at desktop and phone width.
Read that against Defaults to avoid and change what is generic; then build the tokens, then the shared pieces (tile, card, chart wrapper, table, status chip, error note, formatting), then the screens from them.

## Look at it running

**Judge a surface only from the running thing.** A dashboard is screenshotted at 1440 by 900 and 390 by 844, light and dark, each screen after its data has drawn; a command or an API is judged from a realistic session's transcript.
Look at every screenshot yourself as you build and fix what reads wrong; `build-project`'s gate then has a fresh evaluator score them, pass or fail with evidence:

1. **Answer first** — the first screen shows the numbers the plan's screen list names within the top 900 px at desktop width.
2. **House look** — colours, type, radii and spacing come from the tokens in both schemes; nothing in Defaults to avoid shows.
3. **Charts** — each titled with what and unit, axes legible and unclipped, series from the palette, redrawn in dark.
4. **Numbers** — tabular, aligned and formatted as above; no raw float, no ISO timestamp on screen.
5. **Phone** — no sideways page scroll at 390 px, nothing clipped or overlapping, every control reachable.
6. **States** — the data's age visible; the empty and error states designed, forced where the evaluator can force them.
7. **Speed** — each interaction within the bar's time on the real data, measured.
8. **Copy** — sentence case, plain words, units named, no placeholder.
9. **Access** — text contrast at least 4.5 to 1, a visible focus ring, status never by colour alone, each chart labelled for a screen reader.
10. **Finish** — a title and a favicon, no page or console error, consistent spacing, nothing half-aligned.

For a command, an API, a message or a README, the criteria are its lines in Set the bar.

## Technology specifics

Read the file for the technology you're building in:

- **Web** → `references/web.md` (the tokens as CSS variables, Tailwind and shadcn/ui, the scheme toggle, ECharts and Lightweight Charts themed from the tokens, the formatting module).
- **Python** → `references/python.md` (one tokens module, the Plotly templates, Dash with Mantine and AG Grid, Shiny's theme and dark mode, a digest's chart image).

Add a new `references/<technology>.md` when you build in another rather than adding its specifics to this file.
