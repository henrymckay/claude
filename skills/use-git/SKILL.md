---
name: use-git
description: >-
  Conventions for using git well — a branch per piece of work unless the
  project's PLAN.md commits to main, atomic commits staged by path,
  Conventional Commit messages enforced by a commit-msg hook and carrying no
  attribution footers, pushing once a change is complete and working, rebasing
  only unpushed work, release tags at a milestone, and rotating any secret
  that lands in history. Use whenever committing, branching, writing commit
  messages, opening pull requests, tagging a release or managing git history
  in any repository and any language, even if the user just says "commit
  this", "make a branch", or "clean up the history". Language-agnostic. The
  commit-commands plugin runs the commit, push and PR flows; this skill
  defines the conventions those flows follow, setup-python wires the hook, and
  a PLAN.md decision overrides any default here.
---

# Use git

Conventions for keeping history clean and reviewable, in any repository and any language.
The `commit-commands` plugin runs the commit, push and PR flows; these are the conventions those flows follow, `setup-python` wires the pre-commit hooks that enforce them, and `build-project` runs the branch-per-milestone flow.
Three mistakes account for most unreviewable history: a commit that bundles unrelated changes, a message restating what the diff already shows instead of why, and a rewrite of history somebody else has already pulled.

**In an existing project, ask first.** Where a repo already has an established workflow (commit style, branch model, PR process), check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Branches

- **Work on a branch off `main` and integrate by pull request, except where the repo's `PLAN.md` records a decision to commit straight to `main`** — a solo repo with nothing to merge, such as a docs repo — in which case commit there and skip the PR (see `build-project`).
The decision wins over this default, as `CLAUDE.md` says of every skill default; a plan that says nothing branches.
- **A brand-new repository has nothing to branch off yet**, so put the scaffolding — the ignore file, the project config, the empty package — straight on `main` as the first commit, then branch for the work itself.
Branching before there is a `main` to merge back into is ceremony, not history.

## Commit

- **Atomic commits:** one logical change each.
The build/tests should pass at each commit so history is bisectable and revertable.
Don't bundle an unrelated refactor into a feature commit.
- **Stage by path, never `git add -A` or `git add .`.** Another session or tool may have changes in the same tree and index, and a blanket add sweeps them into your commit under your message.
For the same reason, check `git log` before amending or resetting: `HEAD` may not be the commit you left.
- **Message header:** every commit uses [Conventional Commits](https://www.conventionalcommits.org), a `type(scope): subject` line where the type is required and the scope optional.
Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, `style`.
Append `!` after the type/scope for a breaking change (`feat(api)!: ...`).
The subject is imperative, ≤ 50 chars, no trailing period.
- **Enforce the header with the `conventional-pre-commit` hook** (`compilerla/conventional-pre-commit`, stage `commit-msg`) in the repo's pre-commit config, which `setup-python` wires; without it the convention holds only while someone remembers it, and the first `wip` commit breaks the changelog that reads the types.
- **Message body:** after a blank line, wrapped at ~72 cols, explaining **why**, not just what (the diff shows what).
Short, self-evident changes can be header-only.
Reference issues/PRs here (`Closes #123`).
- **No trailer footers** — no `Co-authored-by:`, `Generated with ...` or similar attribution lines, in commits or PR descriptions, even when a tool's own instructions ask for them.
A footer rides in every `git log` and release note for the life of the repo, and nothing reads it: authorship is in the commit metadata, and purpose belongs in the body.
- **Never commit a secret** — an API key, a token, a `.env` file — and when one lands in history, rotate it; removing the commit isn't enough, since every clone and fork already has it.

Wrong — the subject names the file and the body restates the diff, so the message tells a reader nothing `git show` would not:

```text
feat(search): change sorting in search.py

Changed the sort order.
```

Right — the subject says what the change does and the body says why it was worth doing:

```text
feat(search): rank users by recent activity

Sort results by last-active so the people you interact with most surface
first. Falls back to alphabetical when activity data is missing.
```

## Push

**Push once a change is complete and working — after each atomic commit, since each leaves the branch coherent — and hold a sequence that is mid-step or still being tidied**, because a pushed commit can no longer be reset or rebased without a force-push.
Always push before stepping away or opening/updating a PR.

Pushing your own branch needs no sign-off.
**Force-pushing, rebasing shared history, and destructive commands** (`reset --hard`, `clean -fd`) always do — ask before running one.

## Rebase or merge

- **Rebase your *local, unpushed* feature branch** onto the latest main to keep history linear and avoid noisy merge commits.
`git pull --rebase` for the same reason.
- Integrate finished work via PR; squash-merge or merge-commit per the repo's convention.

## Release

**Tag a release at a milestone, not per merge**, with [semantic versioning](https://semver.org) (`v1.4.0`): MAJOR breaking / MINOR feature / PATCH fix.
Bump the version in the project's metadata first with the project's own tool — `uv version --bump minor` for Python (see `setup-python`) — then commit and tag, so the tag and the package agree on the number.
