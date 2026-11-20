# Command line

How a command-line tool reads to the person at the terminal: its help, its names, what it prints while it works and when it fails.
The principles are in `SKILL.md`; `write-entry-points` owns what the tool exposes and how it composes — the commands per stage, the output forms by option, standard output for data only, input routes and exit codes — and this file builds on that shape without restating it.
The Command Line Interface Guidelines (clig.dev) are the wider reference this file picks from.

## Name it

- **Commands are verbs or the plan's nouns, in its Terms** (`fetch`, `compute`, `export metrics`, `status`), the same words the API's routes and the dashboard's screens use, so a person moving between surfaces meets one vocabulary.
- **Options are long, lower-case and hyphenated** (`--days-back`), with a one-letter short form only for the two or three a person types daily (`-f` for `--format`, `-o` for `--output`); a short form for every option exhausts the alphabet and nobody remembers them.
- **One option name means one thing across every command**: `--from` and `--to` everywhere a range is taken, never `--start` on one and `--since` on another.
- **A destructive command asks on a terminal and takes `--yes` in a script**, naming what it will remove and how much (`Delete 41 partitions, 2.3 GB, from 2026-01-01 to 2026-02-10? [y/N]`); with no terminal and no `--yes` it refuses with exit 2.

## Write the help

`--help` is the documentation for anyone at the terminal (`write-entry-points`), so it is designed like a page:

- **The first line says what the command does, as a verb phrase**: `Fetch the last complete period from every active source.`
- **Then usage, arguments, options with their defaults shown, and an Examples block** of two or three real invocations, the everyday one first.
- **The root help lists the commands in the order a newcomer needs them** — set up, the everyday command, inspect, maintain — each with its one-line summary, and ends with where the README is.
- **Bare `myapp` prints the root help and exits 2**, since it was a usage error, not a request for nothing.
- **A typo is answered with the nearest command**: `No such command 'fecth'. Did you mean 'fetch'?`
`typer` 0.29 does both with `no_args_is_help=True` (`write-entry-points`' Python reference); check another framework does before relying on it.

## Show progress

- **On standard error, only on a terminal, for anything over two seconds**: a bar with a count and an estimate where the total is known (`fetch  ████████░░  41/52 items  0:12 left`), a spinner with the current item where it is not.
- **Nothing animated when standard error is not a terminal**: a scheduler's log gets one line per stage at `info` instead (`run-unattended`, Log), since a redrawn bar is hundreds of carriage returns in a file.
- **End with a one-line summary on standard error** — what was done, how long, what to look at next (`Stored 52 items in 0:15; 2 rejected, see myapp status`) — while the rows go to standard output as `write-entry-points` says.

## Write the errors

**An error is one line on standard error, in three parts: what failed, why, and what to do**, with the exit code `run-unattended` sets:

- **Wrong** — `Traceback (most recent call last): ... KeyError: 'MYAPP_TOKEN'`.
- **Right** — `error: no token for the weather source: MYAPP_TOKEN is not set. Add it to .env (README, Configure).`

- **No traceback unless `--log-level debug`**, since a person can act on the sentence and not on the stack; the log keeps the trace.
- **Name the value that was wrong and the values that would be right**: `error: --format "xlsx" is not one of csv, json, parquet, table.`
- **Several failures in one run end with one count line** after their own lines (`3 of 52 items failed; the run stored the rest and exits 1`), so the last thing on screen is the verdict.

## Render the table

`--format table` is the one form drawn for a person:

- **Column headers are the data's own column names**, so what the person reads is what a script will address.
- **Numbers right-aligned with separators and a fixed number of decimals per column** (`SKILL.md`, Numbers and dates), one renderer told each column's precision (`write-entry-points`, Driver shell).
- **Dates and times stay ISO 8601 in UTC**, unlike a screen, since a terminal reader copies them into the next command's `--from`.
- **Colour only for status and change** — the status colours mapped to the terminal's own red, yellow and green, `up` and `down` to blue and red — never as the only signal, and none when standard output is not a terminal or `NO_COLOR` is set to anything non-empty (no-color.org).
- **A table wider than the terminal truncates its widest text column with an ellipsis**, never wraps a row onto two lines.

## Judge it

The evaluator's session (`build-project`'s `references/evaluate.md`, Judge a command or an API) is scored pass or fail, with the transcript as evidence:

1. **Help** — every command's `--help` opens with a verb phrase, shows defaults and has a working example.
2. **Names** — one vocabulary with the plan's Terms and the other surfaces; one meaning per option name.
3. **Errors** — each wrong invocation prints what, why and what to do on one line, no traceback, with the right exit code.
4. **Progress** — a run over two seconds shows progress on a terminal and none in a pipe, and ends with a summary line.
5. **Table** — aligned, formatted, colour off under `NO_COLOR` and in a pipe.
6. **Safety** — a destructive command asks, or refuses without `--yes` off a terminal.
