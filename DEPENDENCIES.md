# Dependencies

The plan is [`PLAN.md`](PLAN.md); what each sweep cost is in [`costs.csv`](costs.csv) and what it proved in [`verification.csv`](verification.csv).
Reconstructed 2026-11-21 by sweep 13; entries before then were not recorded as they happened.

## Accounts and services

- **GitHub repository and issue tracker** — public, free; holds the source, the releases the install line pins and the `skill-feedback` issues; first commit 2026-06-27; removed by archiving the repository, which keeps the issues.
- **Claude Code cloud scheduled task** — the weekly sweep, Mondays 02:00 UTC on Opus, no connectors; its stored prompt is one line telling the session to read and follow `routines/weekly-sweep.md`, set by the owner by hand and undone by editing the task; its identifier is kept off this public repository; billed against the owner's Claude plan; removed in the scheduled-tasks list.
- **The owner's Claude plan** — pays for every sweep, trial build and outside review, cloud sessions included at no separate charge; running cost per sweep in `costs.csv`, at list prices.
- **Sweep 15's throwaways in the owner's public sandbox repository** — recorded on the closed `sweep-15` branch, not re-checked by sweep 16, which touched no other repository: two `sweep15-*.yml` workflows on its default branch, a `sweep15-proof` branch, any `claude-run/*` branches and each run's artifact (14 days); removed by deleting the workflows and branches and letting the artifacts expire.
- **The cloud proof of 2026-11-22 in the owner's public sandbox repository** — one-off scheduled tasks in the owner's scheduled-tasks list, the `claude/…` branches they pushed, a second cloned repository's session, and the trial `SessionStart` hook and settings on the sandbox's default branch; made by the coordinating session for D138; removed by deleting the tasks in the list, the branches, and the hook and settings commit from the sandbox's default branch.

## Credentials

- **The GitHub CLI's login** — repository and issue access for a local sweep; kept in the CLI's own store on the owner's machine; never read or printed by a sweep.
- **The scheduled task's GitHub access** — granted to the cloud environment when the task was made; revoked in the task's settings.
- **`CLAUDE_CODE_OAUTH_TOKEN` in the owner's public sandbox repository** — recorded on the closed `sweep-15` branch for the hosted runner, which sweep 16 removed; removed: the repository's secret list was empty when the coordinator checked it on 2026-11-22. A token made with `claude setup-token` for it, if one was, stays valid until revoked at claude.ai under Settings, Claude Code.

No credential is held in the repository.

## Tools

- **Claude Code 2.1.330** — the version the hooks, `build-project`'s start-up hook template and `secure-project`'s permission template were last proved on (2026-11-22, sweep 16).
- **`claude plugin validate --strict` and `claude plugin eval`** — the manifest check and the trigger suites, both from Claude Code.
- **`python3`** — reads the marketplace list in `build-project`'s start-up hook inside a cloud session, Ubuntu 24.04's own.
- **`sh`** — runs every plugin's `session-start.sh` and the start-up hook template; checked under `sh` and `dash`.
- **`uv`** — runs `costs.py` and its tests as PEP 723 scripts; Python 3.12 or later for those.
- **`git` and `gh`** — branches, pull requests and issues.
- **`pytest` and `ruff`** — pulled by `uv` for the suites and the formatting check.
- **The launcher, guard hook and standing grant** — removed 2026-11-22 (sweep 16, D138), with `python3` 3.9's use for the guard, `pip`'s certificate setting and the `pre-commit` store inside a run; no release tag ever held them, so only a machine loading the plugins from `main` between sweeps 12 and 16 runs the guard, until it loads them again.

## Connectors, plugins and skills

- **The six house plugins** — this repository; `v0.5` is the newest release tag, behind `main` by sweeps 8 to 16.
- **`skill-creator`, `plugin-dev`, `commit-commands`, `claude-security`** — Anthropic's official marketplace; optional companions named in the README; none required.
- **`secure-project`'s permission rules and `build-project`'s `local-run.json`** — proposed for the owner to merge, the first into their user settings, the second into a file passed with `--settings` for a local run; not merged by any sweep; removed by deleting the rules, or the file.

No connector is used by a sweep.

## Packages

None outside the PEP 723 headers of the scripts, which name `pytest` only.
