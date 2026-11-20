# Messages

How an alert, an event push and a digest read, from the lock screen to the screen they open.
The principles are in `SKILL.md`; `send-messages` decides what deserves a message, rations the pushes, picks the channel and sends, and this file decides what each message says and how it looks when it arrives.
A message is the surface its reader meets most, often the only one, so it gets the same design pass as a screen: written into the plan before the sender is built, previewed, and judged.

## Write the push

A push is read on a lock screen, in one glance, often cut short; write it so the first words alone are enough to act on.

- **The title is the verdict**: what happened, to what, in sentence case — `Readings stale for 26 h`, `Usage spike on meter 12, strong`, `Nightly failed: 2 of 3 sources stored`.
Never the app's name or a category alone (`Alert`, `myapp`), which the reader must open to understand.
- **The first line of the body is the evidence and the next step**: the number that justifies the title and what to do — `Source answered 503 three times since 02:04. Tap for the run log.`
The rest of the body is optional detail, since most readers never expand it.
- **Write each part to stand alone when cut**: read the title cut at 40 characters and the body at 100, a house rule of thumb for a phone at its default text size rather than a published limit, and move the verdict forward until both still say it.
- **One tap opens the exact place to act**: the run's log, the event's screen with its item selected, never the dashboard's front page; on ntfy that is the `Click` header, and at most one action button beside it (ntfy allows three), since a second choice on a lock screen is a choice nobody makes.
- **Numbers follow `SKILL.md`'s Numbers and dates**: separators, a fixed number of decimals, a unit, a sign on a change; times on the 24-hour clock in the reader's zone with the zone named (`14:05 GMT`), since a push is read where the reader is, not where the server is.
- **One mark per kind of message, the same every time**: on ntfy a tag that names an emoji shortcode is drawn before the title (docs.ntfy.sh, Publishing, 2026-11-20), so give each kind one fixed tag — `warning` for a failure, `chart_with_upwards_trend` for an event the job found, `memo` for a digest — and no other emoji; the rule against emoji in an interface yields here because the mark is the icon a push otherwise lacks.
- **Priority follows the kind** (`send-messages`, Alert on events the job finds), never the writer's sense of urgency: on Android ntfy's `urgent` vibrates in long bursts and pops over, `high` pops over, `low` shows nothing until the drawer is pulled (docs.ntfy.sh, 2026-11-20), so `urgent` is spent only on the job's own failure.
- **Say when it is over**: a recovery is its own short push with the same subject and the outcome — `Readings fresh again, 3 h late` — so the reader is never left holding an open alarm.

- **Wrong** — title `myapp alert`, body `ERROR: HTTPError('503 Service Unavailable') in fetch_readings at 2026-11-20T02:04:11.392Z`, no link.
- **Right** — title `Readings stale for 26 h`, body `Source answered 503 three times since 02:04 GMT. Tap for the run log.`, `Click` set to the failed run's page, tag `warning`, priority `urgent`.

## Write the digest

A digest is read once a day or once a run, at leisure, in a mail client or a chat; it is a small report, answer first.

- **The subject carries the period and the verdict**: `Readings 20 Nov: 3 events, 1 strong; all sources fresh` — enough to decide whether to open it.
- **The body opens with the answer** — the strongest items, each one line in the push's form — then the counts `status` prints, then the chart, then the link to the dashboard.
- **One chart at most**, rendered from the tokens at a width a phone shows whole (600 px is the house width), titled with what and unit, light scheme, since mail clients rarely follow the reader's dark mode for an image (`references/python.md`, A digest's chart).
- **Plain text first**: a digest that needs HTML to be readable fails in a notification preview, a chat and a screen reader; where it is HTML, a plain-text part says the same.
- **Groups by kind, strongest first, and says what was left out** — `and 14 weaker events, on the dashboard` — so the reader knows the digest is a selection.
- **Fits one phone screen above the chart**; a digest that needs scrolling to reach its answer has its answer in the wrong place.

## Preview before sending

Give every kind of message a preview: a `--preview` option on the command that sends, or a `preview` command, printing exactly what would go out — title, priority, tags, click target, body, and the attachment's path — with nothing sent.
The plan's Interface carries one sample of each kind in that form (`SKILL.md`, Plan the design before the code), the tests assert the preview of a fixed case, and the evaluator judges from previews, so a message is designed and checked without spamming the reader's phone.

## Judge it

Score each kind of message from its preview, pass or fail with the preview as evidence:

1. **Verdict first** — the title alone says what happened and to what, cut at 40 characters.
2. **Evidence and step** — the body's first line holds the number behind the title and what to do, cut at 100.
3. **One action** — the click target opens the place to act, and it resolves.
4. **House numbers** — formatted, with units, times in the reader's zone with the zone named.
5. **Kind** — the tag and priority match the kind's, and only the job's own failure is `urgent`.
6. **Nothing private** — the body holds what `send-messages`' Shape the message allows and nothing more.
7. **Recovery** — a failure kind has a matching recovery message.
8. **Digest** — answer before counts, one chart from the tokens, what was left out named, readable as plain text.

A real send, to the owner's own topic or inbox and only with their go-ahead (an outward action), is screenshotted on the phone or in ntfy's web app at 390 px wide once, before the first release, to catch what a preview cannot: a title the app cuts shorter than the rule of thumb, an emoji tag that did not render.
