# README and reports

What a README and a report show, and in what order, so a stranger meets the finished work at its best.
The principles are in `SKILL.md`; `write-markdown` owns the prose — headings, sentences, links, callouts — `plan-project` owns the plan the README points at, and `build-project` and `review-project` own what their reports must contain; this file is the surface each makes.

## Lay out the README

A README is the front page of the project for everyone but its builder, read top down and abandoned early, so it is ordered by what a newcomer needs first:

1. **The name and one sentence** saying what it does and for whom, in the plan's Goal's words.
2. **The thing itself** — a screenshot of the main screen in the light scheme, or a terminal capture of the everyday command and its output — with the live address beside it where one is deployed.
3. **Quick start** — the fewest commands from a fresh clone to that screen or output, which run as written (`build-project`'s acceptance run runs them).
4. **Use** — one short section per task a person does, by task (`Fetch a day again`, `Export to CSV`), each with the command and a line of its output.
5. **Configure** — every setting with its default and what it changes, every secret by name and where it is kept, never its value.
6. **How it runs** — what runs where and when (the schedule, the host, where the data lives, what messages it sends and to whom), and how to see whether it is healthy (`status`, the dashboard's age).
7. **Develop** — set-up, the suite, the hooks, the release, and a link to `PLAN.md` for the decisions and why (`write-markdown`, For humans).

- **The first screen of the README answers "what is it and does it work"**: the sentence, the picture and the status, before any install line.
- **A picture is regenerated when its surface changes**, from the evaluator's last round or a scripted capture, never a stale screenshot of a screen that has moved; its alt text says what it shows.
- **Every command is copied from a run**, and every output shown is what that run printed, trimmed but not invented.
- **No badges but the ones a reader acts on** — the release, the last run's status; a row of shields is template chrome (`SKILL.md`, Defaults to avoid).

## Lay out a report

A report is anything the project or the build hands a person to read once — a build's or review's final report, a generated weekly summary, an analysis page — and leads with the verdict, as a dashboard does:

1. **The verdict in one or two sentences**: done or not, healthy or not, the answer to the question asked.
2. **What to open** — the address, the command, the file — so the reader can see it for themselves.
3. **The evidence** — each claim with the command or source behind it and what it printed, as a list or a table with units.
4. **What is left** — open questions with recommended answers, checks not run with why, costs.

- **Numbers, dates and units follow `SKILL.md`'s Numbers and dates**, the same as on a screen.
- **A generated report is a page**: the web reference's tokens, printable on A4 in the light scheme, every chart titled with what and unit; a report a person receives is a digest (`references/messages.md`).
- **Nothing is reported twice**: a finding goes where it matters once, and a summary that repeats the body is cut.

## Judge it

1. **First screen** — the README's opening shows the sentence, a current picture and the live address or status before any install line.
2. **Quick start runs** — a fresh clone and the quick start's commands, run as written, reach the screen or output shown.
3. **Complete** — every setting and secret the code reads is under Configure; every artefact that runs unattended is under How it runs.
4. **Report verdict first** — the opening sentences state the verdict; every claim names its evidence.
