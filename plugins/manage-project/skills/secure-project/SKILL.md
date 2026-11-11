---
name: secure-project
description: >-
  How a project keeps what is private private — classifying every input and
  output in the plan as public, licensed (with its redistribution terms),
  private or personal, private until the plan says otherwise, and deciding
  from the class which repositories, hosts, logs, messages and outside
  services, an LLM API included, each may reach; credentials for an account
  that holds money or can act (a broker, an exchange, a bank) — read-only by
  default, one per consumer, kept out of the checkout, rotated, and an order
  or a transfer only under a signed-off plan decision with a person
  confirming each one, never in autonomous mode; secrets in general, the
  secret scanner in the pre-commit hooks and what to do when one leaks;
  access control on a served dashboard or API; the dependency audit; and the
  built-in security review in the build gate and the project review. Use
  whenever a project reads data that is not public, holds a credential,
  touches an account with money in it, serves something over the network or
  decides where its data or logs go — even if the user just says "connect it
  to my broker", "this data is private", "who can see the dashboard" or "is
  this safe to push". Layers on plan-project, which records each class and
  decision; deploy-project, store-data, send-messages, run-unattended and
  use-git pick from the class, and build-project and review-project run its
  checks.
---

# Secure the project

What a project's data and credentials may reach, decided in the plan before anything is built, and checked at every gate after.
It layers on `plan-project`, whose Inputs, Outputs and Decisions record each class and each exception; `deploy-project`, `store-data`, `send-messages`, `run-unattended` and `use-git` pick hosts, stores, channels and units from the class rather than assuming a public repository, and `build-project` and `review-project` run the checks in Review it.
Three mistakes account for most exposure: private data following a default built for public data — a public repository, a Pages site, a workflow log; a credential with more power than its job, such as a trading key that can also withdraw, shared by every consumer; and a private value leaking sideways, through a log line, a message, an artifact or a prompt sent to an outside service.

- **Wrong** — the plan says nothing about the broker export, so the nightly commits it to the repository and the dashboard goes to a public host, as the house picks would for weather data.
- **Right** — the plan marks the export private, so the repository is private, the data never leaves the machine and an access-controlled host, and the plan records the one derived figure the owner chose to publish.

**In an existing project, ask first.** Where a repo already has its own security policy, check with the user whether to keep it or apply this skill, and prefer this skill unless they choose to keep theirs.

## Classify the data

**Give every input and output in the plan a class**, on its line in Inputs or Outputs:

- **Public** — anyone may read and redistribute it: an open dataset, a published price whose terms allow it.
- **Licensed** — the project may use it, and pass it on only as its terms allow; record the terms and their source beside it, since a feed that allows derived figures may forbid the raw rows.
- **Private** — the owner's own, for nobody else: balances, positions, trades, unpublished work.
- **Personal** — about an identifiable person, which data-protection law governs whoever holds it: a name with an address, an account number, a health record.

**An input or output with no class is private** until the plan records otherwise, and an output takes the strictest class among the inputs it derives from unless a decision records why it is looser — an aggregate a licence allows, a figure the owner chose to publish.
A class looser than private is the user's call, raised as a question in the plan's batch and never settled in autonomous mode, because the wrong answer cannot be taken back once the data is out.

## Decide where each class may go

| Destination | Public | Licensed | Private | Personal |
|---|---|---|---|---|
| A public repository, its workflow logs and artifacts | yes | as the terms allow | no | no |
| A private repository | yes | yes | yes | only what the project needs |
| A public host: GitHub Pages, a public dashboard, a static bundle | yes | as the terms allow | no | no |
| An access-controlled host or the owner's machine | yes | yes | yes | only what the project needs |
| A log line or a message | yes | counts only | counts only | never |
| An outside service: a hosted database, an LLM API, a connector | yes | as the terms allow | under a plan decision naming it | under a plan decision naming it |
| An issue, skill feedback, a public tracker | yes | no | no | no |

- **A project holding any private or personal data lives in a private repository**, so the public-only free tiers drop out and `deploy-project`'s private-repository picks apply.
- **A public repository's workflow logs and artifacts are readable by anyone signed in to GitHub**, so on one they carry public data only, whatever the code stays.
- **A GitHub Pages site is public even from a private repository** on every plan below Enterprise Cloud, so it serves public data only.
- **Counts only** means the number of rows, a status, a day, never a value: a lock screen, a forwarded mail and an ntfy topic, which anyone who knows its name can read, all outlive the moment they were sent.
- **An LLM API the project's own code calls is an outside service like any other**, and so is a hosted database; the plan names the service, the class sent and the provider's retention terms before any private row goes there.
- **Minimise personal data**: keep only the fields a requirement uses, so the record a breach or a request for deletion reaches is as small as it can be.

## Hold a credential that can act

An account that holds money or can act on it — a broker, an exchange, a bank, a payment service — gets these on top of Keep secrets out:

- **Read-only by default.** Create the key with the narrowest scope the venue offers — read balances and history, no trading, never withdrawal — and with an IP allow-list where the venue has one, which ties the consumer to a fixed address, so such a job runs on the owner's machine rather than a hosted runner whose address changes; a key that can trade is a second credential, created only when a signed-off plan decision names it.
- **One credential per consumer** — the nightly, the dashboard, a person's session — so a leak is revoked in one place and its reach is that consumer's alone.
- **Kept out of the checkout**: in the operating system's keychain through `keyring` on a machine, in the host's secret store on a host; a checkout is copied, synced and archived in ways a `.env` beside it follows.
- **Rotated on the venue's maximum lifetime or every 90 days, whichever comes first**, and revoked at once on any suspicion; the plan's Runs on names the rotation date beside the store.
- **Built against the venue's sandbox or paper account** where it has one, so no test can move real money.
- **An order, a transfer or any other action that moves money needs a signed-off plan decision naming the account, the action and its limits, and a person confirming each action when it happens.** The code prepares the action and stops; the person confirms it in the venue's own interface or by an explicit reply to that one action, since an unattended mistake executes at market speed and cannot be recalled.
- **Never in autonomous mode or a scheduled run**, whatever the plan says: no order, no transfer, no change to the account's settings; the run prepares and lists them for the user.
A tool or connector that can act on such an account counts the same: Claude places nothing through it without the user confirming that action in the conversation.

## Keep secrets out

A secret is anything that grants access: an API key, a token, a password, an unguessable topic or URL.

- **Keep each secret in one store per place it runs**: on a machine, the `.env` the settings read by its absolute path, ignored by git from the first commit and readable by the owner alone (`chmod 600`), or the keychain for a credential that can act; on a host, that host's secret store (`deploy-project`).
- **Never put a secret in** the repository, public or private, a unit file, a static bundle, a URL that is logged, a message body, a commit message, an issue or a prompt; each of those is copied to places nobody tracks.
- **Bind it once at the composition root** and pass it to the adapter that uses it, where the settings type hides it from a `repr` (`structure-python`, Configuration).
- **Scan every commit for secrets** with the `gitleaks` hook in the pre-commit config (`setup-python`, Pre-commit hooks); it stops the commit that holds one, which a review after the push cannot (gitleaks 8.30); `detect-secrets` is the alternative where a baseline of accepted findings must live in the repository:

```yaml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

- **When a secret lands anywhere it should not, rotate it first and clean up second**; deleting the commit, the log or the message does not reach the clones, caches and inboxes that already hold it.

## Guard what is served

- **A dashboard or API showing private or personal data sits behind the host's own access control** — a viewer list, an identity-aware proxy, a token per consumer — or runs on the owner's machine, reached from elsewhere over a private network (`deploy-project`); an unlisted URL is not access control, since links are shared, logged and indexed.
- **An API checks a token per consumer on every request**, compared with `secrets.compare_digest` so its timing gives nothing away, and refuses before it reads the store.
- **A static site or a browser-side app ships everything it shows to every viewer**, so it holds public data only and no token at all.

## Review it

- **Audit the locked dependencies for known vulnerabilities** in every milestone's gate that changes the lock and in every review: under `setup-python`'s toolchain, `uv export --format requirements-txt --no-emit-project > requirements.txt`, then `uvx pip-audit -r requirements.txt --disable-pip`.
- **Run the built-in `/security-review`** on a milestone's branch in `build-project`'s gate whenever the milestone touches a credential, an outside call, a served surface or a class boundary, and on the whole project in `review-project`.
- **Check the plan against this skill**: every input and output classed, every destination allowed for its class, every credential read-only or covered by a decision.

A finding here is a defect when it breaks the class table or a decision, and a question for the user when it needs a class or a decision the plan lacks.
