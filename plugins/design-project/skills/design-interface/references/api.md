# API

How an HTTP API reads to the developer calling it: its names, its units, its errors, its pages and its docs.
The principles are in `SKILL.md`; `write-entry-points` owns the API's shape — the CLI's options as query parameters, rows as a JSON array, ranges bounded by date, one handler mapping errors to statuses, no version prefix until a second client — `secure-project` what it must guard, and `deploy-project` where it runs; this file is how that shape reads.

## Name it

- **Paths are the plan's nouns in the plural, lower case and hyphenated** (`/readings`, `/usage-events`), with the item's key as the next segment (`/readings/station-12`), never a verb (`/get-readings`); the same nouns as the command line and the dashboard, from the plan's Terms.
- **Fields are `snake_case`, the stored columns' own names**, so a row reads the same in the store, the CSV and the JSON, and a consumer moving between them renames nothing.
- **One name and one unit per quantity across every route**: a temperature is `temperature_c` everywhere; where a unit is not obvious from the name and the docs, it goes in the name (`duration_seconds`, `volume_shares`).
- **Times are ISO 8601 in UTC with `Z`** (`2026-11-20T14:00:00Z`), dates `YYYY-MM-DD`, a period named by its start with its length beside it (`period_start`, `interval: "1h"`); never epoch numbers, which a reader cannot check by eye.
- **Money and exact decimals are strings** (`"1234.50"`) beside their currency, since a JSON number is a binary float to most parsers and loses the cents (`write-python`, Time and money).
- **A missing value is `null`, never `0`, `""` or an omitted key**, so "not known" and "zero" stay different; a record still forming says so in a field (`is_final: false`, `design-pipeline`), never by a value that looks final.

## Answer

- **A list is a JSON array of rows** (`write-entry-points`), each row whole; a response that needs more than the rows — the data's age, the next page — carries it in headers, so the body stays the array every client already parses.
- **Say how fresh the answer is**: `Last-Modified` set to the last run that wrote the data and `Cache-Control: max-age` up to the next scheduled run, so a client and the host's cache both know when asking again is worth it (`deploy-project`, Serve an API); a `/status` route returns the run manifest's last row per source, the same fields `status` prints.
- **Page a large range with a cursor, never an offset**: a `limit` with a default and a maximum, and a `Link: <…>; rel="next"` header carrying an opaque cursor of the last key returned, so a client follows links rather than building URLs, and a row arriving mid-walk is neither skipped nor repeated.

## Fail clearly

**Every error is one shape, RFC 9457's problem details**, served as `application/problem+json` (rfc-editor.org/rfc/rfc9457):

```json
{
  "detail": "end 2026-13-01 is not a date; use YYYY-MM-DD.",
  "status": 422,
  "title": "Invalid range",
  "type": "https://example.org/problems/invalid-range"
}
```

- **`title` is the kind of error and never changes for it; `detail` is this occurrence, saying what was wrong and what would be right**, in the command line's what-why-fix voice (`references/cli.md`, Write the errors).
- **`type` is a link to the docs' section on that error**, so a developer who meets it reads the fix.
- **No stack trace, query, path or secret in any field**; the server's log keeps them (`secure-project`).
- **A framework's own error shape is replaced at the one handler** (`write-entry-points`, HTTP surface), validation errors included, so a client parses one shape whatever went wrong.

## Write the docs

The API's docs are its README, and the first thing a developer judges it by:

- **A title, a one-paragraph description of what the data is and how fresh, the base URL, and how to authenticate** where it does, at the top.
- **Every route with a summary line, each parameter with its type, default and bounds, an example request and its real response**, cut to three rows, and every error it can return with its `type`.
- **Generated from the code's own schema** — OpenAPI from the framework where it has one, so the docs cannot drift from the routes — then given the summaries, descriptions and examples by hand, since a generated page with none is a list of names.
- **A `curl` line per route that runs as written** against the deployed base URL, so the docs are also the smoke test.
- **Versioned only when `write-entry-points` earns a version**; until then the docs say the API may change and name where changes are announced.

## Judge it

The evaluator screenshots the docs page as `build-project`'s `references/evaluate.md` says and runs each route with good and bad parameters, scoring pass or fail with the transcript as evidence:

1. **Docs** — title, description, base URL; every route with a summary, parameters with bounds, a real example and its errors.
2. **Names** — paths and fields match the Terms and the store's columns; one name and unit per quantity.
3. **Values** — UTC ISO times, string decimals for money, `null` for missing, forming records marked.
4. **Errors** — every bad request answers in the problem shape with a `detail` that says what would be right, and nothing internal leaks.
5. **Freshness** — `Last-Modified` and `Cache-Control` present and true to the last run; `/status` agrees with the command's `status`.
6. **Paging** — a range past `limit` returns a working `next` link, and walking it returns every row once.
7. **Examples run** — each `curl` line in the docs returns what the docs show.
