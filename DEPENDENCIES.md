# Dependencies

The plan is [`PLAN.md`](PLAN.md); what each sweep cost is in [`costs.csv`](costs.csv) and what it proved in [`verification.csv`](verification.csv).
Reconstructed 2026-11-21 by sweep 13; entries before then were not recorded as they happened.

## Accounts and services

- **GitHub repository and issue tracker** — public, free; holds the source, the releases the install line pins and the `skill-feedback` issues; first commit 2026-06-27; removed by archiving the repository, which keeps the issues.
- **Claude Code cloud scheduled task** — the weekly sweep, Mondays 02:00 UTC on Opus, no connectors; its identifier is kept off this public repository; billed against the owner's Claude plan; removed in the scheduled-tasks list.
- **The owner's Claude plan** — pays for every sweep, trial build and outside review; running cost per sweep in `costs.csv`, at list prices.

## Credentials

- **The GitHub CLI's login** — repository and issue access for a local sweep; kept in the CLI's own store on the owner's machine; never read or printed by a sweep.
- **The scheduled task's GitHub access** — granted to the cloud environment when the task was made; revoked in the task's settings.

No credential is held in the repository.

## Tools

- **Claude Code 2.1.330** — the version the hooks, the guard, the launcher's profile and preflight were last proved on (2026-11-22, sweep 14's launcher runs); the launcher writes the version it ran under into each run's `status.json`.
- **`claude plugin validate --strict` and `claude plugin eval`** — the manifest check and the trigger suites, both from Claude Code.
- **`python3`, 3.9 or later** — runs the guard hook and `grant.py` under the machine's own interpreter; macOS ships 3.9 at `/usr/bin/python3`.
- **`sh`** — runs every plugin's `session-start.sh` and `guard.sh`; checked under `sh` and `dash`.
- **`uv`** — runs the launcher, `costs.py` and every test suite as PEP 723 scripts; Python 3.12 or later for those.
- **`git` and `gh`** — branches, pull requests and issues.
- **`pip` 26.3 and `pre-commit` 4.7.0** — inside a run, `pip` takes `PIP_USE_DEPRECATED=legacy-certs` from the launcher, since its default trust store fails in the macOS sandbox; `pre-commit` keeps its store in the run's scratch folder (measured 2026-11-22).
- **`pytest` and `ruff`** — pulled by `uv` for the suites and the formatting check.

## Connectors, plugins and skills

- **The six house plugins** — this repository; `v0.5` is the newest release tag, behind `main` by sweeps 8 to 13.
- **`skill-creator`, `plugin-dev`, `commit-commands`, `claude-security`** — Anthropic's official marketplace; optional companions named in the README; none required.

No connector is used by a sweep.

## Packages

None outside the PEP 723 headers of the scripts, which name `pytest` only.
