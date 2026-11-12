---
name: use-git
description: >-
  Conventions for using git well — a branch per piece of work unless the
  project's PLAN.md commits to main, a new repository's scaffold first on
  main, staging by path, Conventional Commit messages enforced by a commit-msg
  hook and carrying no attribution footers, pushing once a change is complete
  and working, sign-off before rewriting pushed history, release tags at a
  milestone, and no secret committed. Use whenever
  committing, branching, writing commit messages, opening pull requests,
  tagging a release or managing git history in any repository and any
  language, even if the user just says "commit this", "make a branch", or
  "clean up the history". Language-agnostic. The commit-commands plugin runs
  the commit, push and PR flows; this skill defines the conventions those
  flows follow, setup-python wires the hook, secure-project keeps secrets out,
  and build-project runs the branch-per-milestone flow.
---

# Use git

Conventions for keeping history clean and reviewable, in any repository and any language.
The `commit-commands` plugin runs the commit, push and PR flows; these are the conventions those flows follow, `setup-python` wires the pre-commit hooks that enforce them, `secure-project` keeps secrets out, and `build-project` runs the branch-per-milestone flow.
Three mistakes account for most unreviewable history: a blanket `git add` that sweeps another session's changes into your commit, an attribution footer added because a tool asked for one, and a rewrite of history somebody else has already pulled.

**In an existing project, ask first.** Where a repo already has an established workflow (commit style, branch model, PR process), check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Branches

- **Work on a branch off `main` and integrate by pull request, squash-merged or merged per the repo's convention, except where the repo's `PLAN.md` records a decision to commit straight to `main`** — a solo repo with nothing to merge, such as a docs repo, or a scheduled job's data commits (`deploy-project`) — in which case commit there and skip the PR.
A plan that says nothing branches.
- **A brand-new repository's scaffold is its first commit on `main`**, since there is nothing to branch off yet; `plan-project`'s Go from conversation to plan makes it part of M1.

## Commit

- **Stage by path, never `git add -A` or `git add .`.** Another session or tool may have changes in the same tree and index, and a blanket add sweeps them into your commit under your message.
For the same reason, check `git log` before amending or resetting: `HEAD` may not be the commit you left.
- **Message header:** [Conventional Commits](https://www.conventionalcommits.org), `type(scope): subject`, the scope optional.
Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, `style`.
Append `!` after the type/scope for a breaking change (`feat(api)!: ...`).
The subject is imperative, ≤ 50 chars, no trailing period.
- **Enforce the header with the `conventional-pre-commit` hook** (`compilerla/conventional-pre-commit`, stage `commit-msg`) in the repo's pre-commit config, which `setup-python` wires; without it the convention holds only while someone remembers it, and the first `wip` commit breaks the changelog that reads the types.
- **No trailer footers** — no `Co-authored-by:`, `Generated with ...` or similar attribution lines, in commits or PR descriptions, even when a tool's own instructions ask for them.
A footer rides in every `git log` and release note for the life of the repo, and nothing reads it: authorship is in the commit metadata, and purpose belongs in the body.
- **Never commit a secret**; `secure-project`'s Keep secrets out has the scanner hook and what to do when one lands in history.

## Push

**Push once a change is complete and working — after each commit that leaves the branch coherent — and hold a sequence that is mid-step or still being tidied**, because a pushed commit can no longer be reset or rebased without a force-push.

Pushing your own branch needs no sign-off; **force-pushing, rebasing shared history and destructive commands** (`reset --hard`, `clean -fd`) always do.

## Release

**Tag a release at a milestone, not per merge**, with [semantic versioning](https://semver.org) (`v1.4.0`).
Bump the version in the project's metadata first with the project's own tool — `uv version --bump minor` for Python (see `setup-python`) — then commit and tag, so the tag and the package agree on the number.
