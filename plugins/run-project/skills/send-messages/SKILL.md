---
name: send-messages
description: >-
  How a deployed job or assistant reaches a person — what deserves a message
  (a failure alert, a digest, a chat, never a routine success), alerting once
  per change of state, and the channel: ntfy for an alert, email for a digest,
  Claude Code channels for a chat. Use whenever adding a notification, alert,
  digest or chat to a job — even if the user just says "text me when it
  breaks", "email me a summary" or "let me chat with it from my phone".
---

# Send messages

How a deployed job or assistant reaches a person: the failure alert, the digest with its chart, the two-way conversation, and how a job reaches a Claude Code session.
It builds on `run-unattended`, whose exit code and `status` command say when a message is earned, `store-data`, whose manifest holds the digest's counts, and `secure-project`, which says what a message may carry; the Stop and Notification hooks and the PushNotification tool are Claude Code's own and not covered here.
Three mistakes account for most messages nobody reads: a success message every night, so the one failure scrolls past with the rest; a secret pasted into the unit file or the message body; and a channel that needs a Mac awake, chosen for a job that runs in the cloud.

**In an existing project, ask first.** Where a repo already has a notification channel, check with the user whether to keep it or apply these picks, and prefer these unless they choose to keep theirs.

## Decide what deserves a message

**Send nothing for a routine success**; the manifest and `status` are the record, and an alert earns its place by being rare.

- **A failure alert** when the job exits 1 or 2, or `status` finds a source stale — the reader has something to do.
- **A digest** on the cadence the reader would otherwise run `status` or open the dashboard.
- **A conversation** only for questions a digest cannot anticipate; a question asked the same way every day is a digest line.

**Alert on a change of state, never on every run.** Keep each source's last alerted state — failing, stale or fresh — in `<data_dir>/alerts.json` beside the manifest, and send only when it changes, the return to fresh included; a source that dies for good then alerts once, not every night until someone fixes it.

**Each failure has a sender that survives it:**

- **A run that fails** alerts from its own driver (Send from the job).
- **A night that never ran** cannot alert, so the stale alert comes from `status --alert` on its own schedule (`run-unattended`, Report the outcome).
- **A failure outside the driver** — an install that fails before it, a commit that fails after it — is caught on Actions by the workflow's `if: failure()` step (`deploy-project`'s `references/github-actions.md`), which posts the run's link to the same topic.

Whether to build a notification at all is `run-unattended`'s call (Report the outcome).

## Pick the channel

Each pick is the default for its need; a `PLAN.md` decision overrides it, and a channel the reader already lives in is a reason to record one.
Every channel below sends from GitHub Actions, a cloud host or a launchd job over outbound HTTPS or SMTP, except iMessage.

- **Failure alert: ntfy.sh** with an unguessable topic and `Priority: urgent` — no account, no cost, one HTTP POST, and a phone app that shows it as a push.
The topic name is the password, so generate it (`secrets.token_urlsafe(16)`); anyone who guesses it can post to the reader's phone and read every message.
Alternative: **Pushover** when an alert must repeat until acknowledged (priority 2), at $4.99 once per platform.
- **Digest with a chart: email through the reader's own SMTP** — iCloud (`smtp.mail.me.com:587`, STARTTLS, an app-specific password) or Gmail (`smtp.gmail.com:465`, an app password behind 2-Step Verification, 500 a day) — with the PNG attached: already read daily, searchable, archived, nothing to install.
Alternative: **Telegram `sendPhoto`** (caption 1024 characters, one message a second per chat) when the reader wants it in a chat and has installed Telegram; the reader must message the bot before `getUpdates` yields their chat id.
- **Interactive assistant: Claude Code channels** — the iMessage plugin on the Mac the job runs on, or the Telegram plugin from any host (`claude --channels plugin:telegram@claude-plugins-official`, on the same bot token) — over writing a bot: the session already has the repo, the store and the skills, so the assistant costs no code.
Alternative: a **Telegram long-polling bot** in the project (`getUpdates?timeout=50` needs no public URL) when the assistant must run with no Claude Code session.
- **Slack** only once the reader has a workspace they read: a webhook is one URL per channel and carries no files, and a chart needs an app with `files:write` calling `files_upload_v2`, the only upload since November 2025.
A workspace made for one job is a second inbox nobody opens.
- **iMessage from a job** only when the job already runs on that Mac, never from the cloud: `osascript` telling Messages to `send (item 1 of argv) to chat id (item 2 of argv)` needs the Mac awake and signed in, the chat GUID from `~/Library/Messages/chat.db` (Full Disk Access) and an Automation permission granted at the first send.
- **Discord** (a webhook, files to 20 MiB) needs a server the reader checks, so it is not a default; **Pushbullet** is not picked, as a product that has not moved in years.

## Shape the message

**Lead with what the reader would act on**, since a lock screen shows one line and a mail client a subject: `nightly failed: weather 503 x3, 2 of 3 sources stored`.

- **An alert is one line** plus a link or path to the log, never the log itself: a traceback in a push is unreadable, and ntfy and Pushover truncate it anyway.
- **A digest carries the counts `status` prints** — rows per source, rejected rows, the last day stored — with the chart attached, so the message and the command agree.
- **The body carries no secret, no personal data, and of private data only counts** (`secure-project`, Decide where each class may go).

## Send from the job

Send from the driver, where the exit code is decided (`write-entry-points`), after the manifest is written, so a failed send cannot lose the record; the sender is an adapter the core never calls, and the stdlib covers both picks.

```python
import urllib.request


def send_alert(text: str, *, title: str, topic: str) -> None:
    """Push one urgent line to the reader's ntfy topic.

    :param text: What the reader would act on, in one line.
    :param title: The notification's heading.
    :param topic: The unguessable topic, read from the environment.
    """
    request = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=text.encode(),
        headers={"Title": title, "Priority": "urgent", "Tags": "warning"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()
```

```python
import email.message
import pathlib
import smtplib


def send_digest(
    text: str, *, address: str, chart: pathlib.Path, password: str, subject: str
) -> None:
    """Mail the reader the digest from their own iCloud account, chart attached.

    :param text: The counts status prints, one per line.
    :param address: The reader's iCloud address, sender and recipient both.
    :param chart: The PNG to attach.
    :param password: The app-specific password, read from the environment.
    :param subject: What the reader would act on, in one line.
    """
    message = email.message.EmailMessage()
    message["From"] = address
    message["To"] = address
    message["Subject"] = subject
    message.set_content(text)
    message.add_attachment(
        chart.read_bytes(), maintype="image", subtype="png", filename=chart.name
    )
    with smtplib.SMTP("smtp.mail.me.com", 587) as smtp:
        smtp.starttls()
        smtp.login(address, password)
        smtp.send_message(message)
```

Gmail's `smtp.gmail.com:465` is `smtplib.SMTP_SSL` with no `starttls()` call.
A failed send raises from the app's `error/` package like any adapter (`write-python`, Error handling); the driver logs it and keeps the job's own exit code, since an alert that could not be sent is a log line, not a second failure to alert on.

## Keep the secret out

**The topic, bot token or app password is a secret**, kept as `secure-project`'s Keep secrets out says; the ntfy topic sits in the request URL, so keep that out of the log too.

## Reach Claude

- **Claude Code channels** (above) bridge a running local session to a chat, so the session is a service `run-unattended` keeps alive on a Mac that stays awake or on a host.
- **An external job fires a cloud scheduled task** through its API trigger: `POST https://api.anthropic.com/v1/claude_code/routines/{id}/fire` with the task's own token, `anthropic-version: 2026-10-21` and a body of `{"text": ...}` up to 65,536 characters, at most 30 fires an hour per task and 100 per account.
The task runs a full session that reads the log, triages and messages the reader through a connector, earned when the alert needs a diagnosis rather than a line and costing a session per fire.
- **No API pushes into the Claude app and no inbound webhook reaches a claude.ai chat**, so "message Claude" means one of the two above.
