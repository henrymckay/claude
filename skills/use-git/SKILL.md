---
name: use-git
description: >-
  Conventions for using git well — branch strategy, commit granularity, commit
  messages, rebase or merge, pushing/PRs, and what to exclude from commits. Use
  whenever committing, branching, writing commit messages, opening pull
  requests, or managing git history in any repository and any language, even if
  the user just says "commit this", "make a branch", or "clean up the history".
  Language-agnostic. The commit-commands plugin runs the commit, push and PR
  flows; this skill defines the conventions those flows follow.
---

# Use git

Conventions for keeping history clean and reviewable, in any repository and any language.
The `commit-commands` plugin runs the commit, push and PR flows; these are the conventions those flows follow.
Three mistakes account for most unreviewable history: a commit that bundles unrelated changes, a message restating what the diff already shows instead of why, and a rewrite of history somebody else has already pulled.

**In an existing project, ask first.** Where a repo already has an established workflow (commit style, branch model, PR process), check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Branches

- Work on **short-lived feature branches** off the main/trunk branch; keep them small and merge often.
Long-running branches drift and cause painful merges.
- Name branches `type/short-description`, kebab-cased: `feat/user-search`, `fix/null-login`, `chore/bump-deps`, `docs/readme`.
- Keep a branch focused on one piece of work.
- **A brand-new repository has nothing to branch off yet**, so put the scaffolding — the ignore file, the project config, the empty package — straight on `main` as the first commit, then branch for the work itself.
Branching before there is a `main` to merge back into is ceremony, not history.

## Commit

- **Atomic commits:** one logical change each.
The build/tests should pass at each commit so history is bisectable and revertable.
Don't bundle an unrelated refactor into a feature commit.
- Commit locally often; tidy up before sharing.
Noticing that a commit landed out of order — tests committed ahead of the fix they need, so that commit does not pass on its own — is exactly what the tidy-up is for: `git reset --soft` back to before them and re-commit in the right order.
That touches no file and no shared history, so it needs no sign-off, unlike the `--hard` and force-push cases below.
- **Message header:** every commit uses [Conventional Commits](https://www.conventionalcommits.org), a `type(scope): subject` line where the type is required and the scope optional.
Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, `style`.
Append `!` after the type/scope for a breaking change (`feat(api)!: ...`).
The subject is imperative, ≤ 50 chars, no trailing period.
- **Message body:** after a blank line, wrapped at ~72 cols, explaining **why**, not just what (the diff shows what).
Short, self-evident changes can be header-only.
Reference issues/PRs here (`Closes #123`).
- **No trailer footers.** Do not append `Co-authored-by:`, `Generated with ...`, or similar attribution/tool footers to commit messages.
A footer is permanent and unfilterable — it rides along in every `git log`, `git blame` and release note for the life of the repo, and the tool that put it there is stale within a year.
Nothing reads it: authorship is already in the commit metadata, and what a change was for belongs in the body.

```text
feat(search): rank users by recent activity

Sort results by last-active so the people you interact with most surface
first. Falls back to alphabetical when activity data is missing.
```

## Push

Push freely — it backs work up and shows progress, with little downside.
**Push after each atomic commit**, since each already leaves the branch in a coherent, working state; only batch when a commit is a deliberate mid-sequence step that would push the branch through a briefly-broken state.
Always push before stepping away or opening/updating a PR.

Pushing your own branch needs no sign-off.
**Force-pushing, rebasing shared history, and destructive commands** (`reset --hard`, `clean -fd`) always do — ask before running one.

## Rebase or merge

- **Rebase your *local, unpushed* feature branch** onto the latest main to keep history linear and avoid noisy merge commits.
`git pull --rebase` for the same reason.
- **Never rebase or force-push branches others may have pulled** — it rewrites shared history.
If you must force-push your *own* branch, use `--force-with-lease`, never bare `--force`.
- Integrate finished work via PR; squash-merge or merge-commit per the repo's convention.

## Pull requests

- Keep PRs **small and single-purpose** — easier to review, faster to land.
- PR description covers the *why*, the approach, and how it was tested.
Link related issues.
- Push work-in-progress to back it up / open a draft PR; mark ready when it is.
- Tag a release once merged, with [semantic versioning](https://semver.org) (`v1.4.0`): MAJOR breaking / MINOR feature / PATCH fix.

## Exclude from commits

- **Secrets** — API keys, tokens, passwords, `.env` files.
If one lands in history, rotate it; removing the commit isn't enough.
- **Generated/build artifacts, caches, virtualenvs** — `.gitignore` them.
- **Large binaries** — use Git LFS or store them elsewhere.

Keep a real `.gitignore` from the start so this never becomes a problem (`setup-python` has a starter list for Python projects).

