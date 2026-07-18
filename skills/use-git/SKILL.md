---
name: use-git
description: >-
  Conventions for using git well — branch strategy, commit granularity, commit
  message format, rebase vs merge, pushing/PRs, and what never to commit. Use
  whenever committing, branching, writing commit messages, opening pull
  requests, or managing git history in any repository and any language, even if
  the user just says "commit this", "make a branch", or "clean up the history".
  Language-agnostic. Mechanics of running commit/push/PR flows are provided by
  the commit-commands plugin; this skill defines the conventions those flows
  should follow.
---

# Using git

Conventions for keeping history clean and reviewable.
These are defaults for repos without an established workflow — **an existing repo's conventions (its commit style, branch model, PR process) always win.**

> Behavioral guardrail: ordinary pushes of your own branch are fine (see
> [Pushing](#pushing)), but **force-pushing, rebasing shared history, and
> destructive commands** (`reset --hard`, `clean -fd`) require explicit sign-off.

## Branches

- Work on **short-lived feature branches** off the main/trunk branch; keep them small and merge often.
  Long-running branches drift and cause painful merges.
- Name branches `type/short-description`, kebab-cased: `feat/user-search`, `fix/null-login`, `chore/bump-deps`, `docs/readme`.
- Keep a branch focused on one piece of work.

## Commits

- **Atomic commits:** one logical change each.
  The build/tests should pass at each commit so history is bisectable and revertable.
  Don't bundle an unrelated refactor into a feature commit.
- Commit locally often; tidy up before sharing (see history hygiene).

### Commit message format

Every commit uses [Conventional Commits](https://www.conventionalcommits.org): a `type(scope): subject` header, where the type is required and the scope optional.
Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, `style`.
Append `!` after the type/scope for a breaking change (`feat(api)!: ...`).

The subject is imperative, ≤ ~50 chars, no trailing period.
Then a blank line and a body wrapped at ~72 cols explaining **why**, not just what (the diff shows what):

```
feat(search): rank users by recent activity

Sort results by last-active so the people you interact with most surface
first. Falls back to alphabetical when activity data is missing.
```

Short, self-evident changes can be header-only.
Reference issues/PRs in the body (`Closes #123`).

**No trailer footers.** Do not append `Co-authored-by:`, `Generated with ...`, or similar attribution/tool footers to commit messages.

## Pushing

Push freely — it backs work up and shows progress, with little downside. **Push after each atomic commit**, since each already leaves the branch in a coherent, working state; only batch when a commit is a deliberate mid-sequence step that would push the branch through a briefly-broken state.
Always push before stepping away or opening/updating a PR.

Pushing your own branch needs no sign-off; force-pushing, rebasing shared history, and destructive commands still do.

## Rebase vs merge

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

## What never to commit

- **Secrets** — API keys, tokens, passwords, `.env` files.
  If one lands in history, rotate it; removing the commit isn't enough.
- **Generated/build artifacts, caches, virtualenvs** — `.gitignore` them.
- **Large binaries** — use Git LFS or store them elsewhere.

Keep a real `.gitignore` from the start so this never becomes a problem.

## Releases

Tag releases with [semantic versioning](https://semver.org) (`v1.4.0`): MAJOR breaking / MINOR feature / PATCH fix.
