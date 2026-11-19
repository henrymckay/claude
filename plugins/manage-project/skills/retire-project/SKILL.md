---
name: retire-project
effort: high
description: >-
  How to tear a project down when it is retired — the teardown read from its
  dependency record, what runs stopped first, data archived before any store
  goes, credentials revoked at the issuer, each removal confirmed by a
  command, irreversible steps confirmed one by one, and the plan and records
  kept. Use whenever retiring, decommissioning or deleting a project or what
  it created — even if the user just says "tear it down", "shut this project
  off" or "delete everything it made".
---

# Retire the project

Taking a finished or abandoned project off every account it touched, in an order that loses nothing worth keeping and leaves nothing running, billing or able to sign in.
It reads `DEPENDENCIES.md`, which `build-project` keeps, and the Teardown line `plan-project` writes under Runs on; `secure-project` says what a credential's revocation must reach, `deploy-project` and `run-unattended` say how each artefact was put up, so its removal is read from them, and `use-git` keeps the repository's history.
Three mistakes account for most bad teardowns: a store deleted before its data was archived, a credential's stored copies deleted while the credential itself still works at the issuer, and a step reported done that never took, such as a schedule that still fires.

- **Wrong** — the token is removed from the repository's secrets and the keychain, and the teardown is reported complete; the token still opens the database to anyone holding an old copy.
- **Right** — the token is revoked in the database's own console, a request made with it is refused, and only then are its stored copies deleted.

**In an existing project, ask first.** Where a repo already has its own runbook or teardown notes, check with the user whether to follow them or apply this skill, and prefer this skill unless they choose to keep theirs.

## Start from the record

- **Read the checklist off `DEPENDENCIES.md`**: each account's holdings and how each is removed, each credential and where it is revoked, each tool installed for the project alone.
- **Without a record, build one first** from the repository, its workflows and settings, each host's own listing of what the account holds, the keychain and the scheduler's units, and show it to the user before removing anything; a teardown from memory misses whatever it never knew about.
- **Read the plan's Teardown line** for what is kept and what stays standing; where the plan has none, ask, recommending that the plan, the records and every store's data are kept.

## Ask before each step

**Every step is an outward action**, so none runs in autonomous mode or a scheduled run; such a run writes the checklist into its report for the user and stops.

- **One go-ahead covers the reversible steps together** — disabling a schedule, pausing a service, archiving a repository.
- **Each irreversible step needs its own confirmation when it is reached**, naming the thing and what it holds — deleting a store, a bucket, a repository, an account or a service account, or revoking a credential — since none can be taken back, and a yes to "the teardown" is not a yes to each.
An account the owner uses for anything else is never closed; only the project's resources on it are removed.

## Take it down in order

1. **Stop what runs** — disable each scheduled workflow (`gh workflow disable`), unload each launchd or systemd unit, stop each service — so nothing writes while the rest comes down and no failed night alerts the reader.
2. **Take down what serves** — the API, the dashboard's host, a static site — so nothing reads a store about to go.
3. **Archive what is kept** — export each store the Teardown line names to the owner's machine in its own format (`store-data`), and check the archive opens and its row counts match the store's before the store is touched.
4. **Remove the stores, their shares and the other resources each account holds** — buckets, topics, service accounts.
5. **Revoke each credential at its issuer, then delete every stored copy** — the host's secret store, the repository's secrets, the keychain, any `.env`.
6. **Archive the repository** (`gh repo archive`) rather than delete it, unless the owner asks, since it holds the plan and the records.

## Confirm each removal

**A removal counts only once a command shows it gone**: the resource's listing or a request for it answers not found, a request with a revoked credential is refused, a disabled workflow shows as disabled in `gh workflow list --all` and starts no run at its next scheduled time.
Mark each entry in `DEPENDENCIES.md` `removed <date>, confirmed by <command>`, commit the records before the repository is archived, and close `PLAN.md` with a line saying the project was retired, when, and where its archive is.

**Report** each step with the command that confirmed it and what it printed, and everything left standing with the reason; a step not confirmed is reported as not done.
