# Index symbols answers

The design a good build reaches, and the wrong turns that miss it.
None of it appears in the brief — each line is something the skills alone should produce.

## The shape

Seven sources, one pipeline, and the join between them happens before anything is reduced.

| shape | one row is | how it is reached |
|---|---|---|
| holdings | one constituent of one collection | read the packaged dataset, or fetch and parse the published file |
| symbols | one symbol | concatenate every collection's holdings, keep what is tradeable, sort, drop duplicates |

**Concatenate first, reduce once.** Every named collection produces holdings, those frames stack into one, and only then does it become a sorted list of distinct symbols.
Reducing each collection to symbols and merging the results afterwards deduplicates twice and sorts twice, and it puts the join in the driver where the loop over names lives rather than in the core where the data does.

**The adapters differ entirely inside and agree exactly at their edge.** Each returns holdings in the same frame, whatever its source published, so the concatenation is a stack rather than a reconciliation.
An adapter that returns the dataset's records from one source and parsed rows from the other has pushed its source's shape outward, and every later build pays for it.

**Holdings stay a frame the whole way.** The published file becomes a frame at the boundary and never leaves it, so sorting and dropping duplicates are one pass of expressions rather than a trip through a Python `set` — which loses the order the brief asks for and has to be re-sorted anyway.

**Names are matched loosely but written back canonically.**
Case, spacing and punctuation are all things a caller gets wrong and none of them tell one collection from another, so `sp-500`, `SP500` and `S&P 500` all reach the same index.
An ETF ticker and an index name are both just names to the lookup, so one normalisation covers matching for both rather than each source inventing its own.
The canonical spelling is what `catalogue` prints, a ticker in capitals and an index under its usual name.

**A stock's home listing is a judgement the adapter makes.** The dataset gives several Yahoo symbols per stock, one per exchange, and its own bare `symbol` field *is* the home one — right even where it does not appear among the listings, as it does not for 12 of the FTSE 100.
So take it, and fall back to the first listing only where it is absent, which is the handful of constituents that would otherwise be lost.
Checking it against the listings first changes no value and costs a pass; falling back while it exists returns a Frankfurt or US line for Barratt Redrow, ICG and Rio Tinto.
Keep the rule in the adapter — it is a fact about the data source, not about the domain.

**The port is a protocol the adapter modules satisfy, not a record of callables.**
Two calls have to come from the *same* source — what a place offers, and what one of its collections holds — and a record bundling two functions lets a caller build a chimera out of two adapters, which type-checks.
A module cannot be mixed with itself, and a module satisfies a structural protocol exactly as an instance does, so nothing has to become a class and the composition root hands over the adapter modules themselves.
The cost to accept is that a protocol's method name *is* the contract, so every adapter spells it the same — which is right, since a caller reaches a port precisely because it does not care which one answers.

**Pure frame work belongs to the core even when the adapter noticed it was needed.**
A frame in, a frame out, no IO: that is a transform, and three adapters left to their own devices grow three versions of one reshape, none of them under the core's tests.
The adapter owns the *decision* and the core owns the *operation* — that ARK spells a ticker the Bloomberg way is knowledge about ARK, and moving it inward teaches the core about publishers.

What counts as *tradeable* is the core's call rather than the adapter's, so cash lines and their like are dropped by one rule in one place instead of once per source.
The adapter is answerable for reading its file correctly; the core is answerable for what deserves to come back.

## What the build earns

**A `port`.** Expanding several names, stacking their holdings and failing the run if any one of them fails is an operation, and it calls outward for holdings while staying pure — which is what a port is for.
The payoff is that the whole expansion becomes testable against a fake source with no network, rather than only through the driver.

Two adapters sharing a signature is *not* what earns it, and a build that says so has the right answer for the wrong reason: one adapter and the same operation would earn it just as much.

**An `operate` layer.** There are two use cases here, not one: expanding names and listing them.
Both orchestrate the same sources and both call outward through the port while staying pure, so the layer has something to hold and a second caller to hold it for.
The count is what decides it, not the ceremony — one use case would be a function beside the transforms; two that share how the sources are gathered are a layer, and the shared gathering is the thing a later build inherits.

**`adapt` naming its own members.** Which sources exist is a fact about what the adapter layer ships, so it returns the mapping and every driver reads the same one.
Enumerate them in a driver instead and the next driver copies the list, so adding a source edits every entry point rather than the package that gained it.
That is not the composition root moving: the driver still chooses to use the set and still injects it into the operation.

## What should not exist yet

- **No caching, no retry policy, no configuration layer**, and no registry that sources sign up to — thirty-two named collections across seven sources is still a lookup, not a plugin system.

## The boundary

The brief names the collections and leaves finding them to the build, so the first work is research: no two of the six publishers agree on where their data sits, what it is called, or how often it changes.

- `httpx` is the pick over `requests`.
- Send a browser-like user agent.
`ark-funds.com` answers a default client with a 403, so a build that never sets one works against Wedbush and Fundstrat but not ARK — worse than failing everywhere, because it looks like it works.
- Set a timeout.
A published holdings file is somebody else's server, and a hung request with no deadline is the failure that wastes the most time.
- The adapter owns its outcome: a fund that 404s, times out, or returns something unparseable becomes an error naming the fund, not a status code or a library exception escaping into the driver.
- Split getting the document from making sense of it.
Retrieval is a few lines that never change; the parse is where a publisher's quirks live and where the work grows, so fused they lengthen together and the one line saying what the adapter returns sinks under them.
Apart, a saved response tests the parse with no stub for the fetch.
- Where each publisher serves its file is **data**, not a literal in code — one entry per fund, with the host held once rather than repeated against each of them.
It is read by the adapter that fetches them, since where an outside service lives is the edge's knowledge and not the core's.
- Parse the response **into the frame** where the response is rows and columns — a CSV is read by the frame library, not split on commas and reassembled.
Where the source hands back records or markup and one field is wanted, pulling that field out and building a one-column frame is both simpler and cheaper: routing the whole record through the frame materialises every nested column you did not ask for, at a cost of two orders of magnitude here.
- A holdings file is not a list of shares.
Cash lines, placeholder rows and a trailing disclaimer all appear in them, so the adapter hands on what the file gave it and the core decides what deserves to come back.
One rule covering cash lines, options and a trailing disclaimer alike beats a row filter in every adapter plus a tradeability rule after it — the second filter is the same judgement written four more times.

## The surface

Two commands, split by what they do rather than by where the symbols come from.
Resolving a name is the tool's job, so `expand` takes the name alone; finding out which names exist is a different question, so `catalogue` is its own command rather than a flag that switches what `expand` does.

`catalogue` is what makes a bare error acceptable on an unmatched name — without it the tool would owe the caller near matches, since there would be no other way to discover a valid name.

- Two renders, not one styled two ways.
`rich` dropping colour when piped does not make a bordered table parseable, so the default form is its own render emitting one symbol and nothing else.
- **No terminal detection.** The brief asks for the same bytes everywhere, so `Console.is_terminal` decides nothing here — a build that reaches for it has followed a habit past an instruction.
- `-o` writes whichever form is in force, so `-o` alone saves lines and `-o -t` saves the table.
A path does not silently override the flag.
- One symbol per line is right here because there is one column, and it is what `grep`, `xargs` and `wc -l` all expect.
A boolean `--table` covers the two forms this build has; the moment a second column arrives it will want naming a format instead, which is the next build's problem to notice.
- Several names expanding into one list, deduplicated across them, since `ARKK` and `ARKW` hold much the same stocks and asking for both should not say so twice.
- One name failing the whole run.
A short list is the dangerous outcome, because nothing downstream can tell it apart from a collection that genuinely shrank.
- Diagnostics, progress and errors to standard error, so a redirect captures symbols alone.
- A non-zero exit on any failure, an unknown name or a fetch that would not come, so `&&` and `set -e` behave.
- A `--help` that explains the tool without recourse to a README.
- `catalogue` writing one name per line, so `symbols catalogue | grep ARK` answers "what can I expand that looks like this".

**Where a good build should push back.** Two things, and both should end in the brief being followed.

`write-entry-points` says to vary the form with the destination, the way `ls` prints columns at a terminal and one entry per line into a pipe, and the brief asks for the opposite — one form always, a flag to change it.
The brief is right for this tool and the build should say why rather than either detecting quietly or arguing the point: output that changes with context is output a script cannot rely on, and the pretty form here is the rare case rather than the common one.

`-o PATH` does nothing that `> PATH` does not already do, so it earns its place only by convention — `curl` and `sort` carry it, and a caller who expects it will look for it.
Saying so and building it anyway is the right answer; refusing it is not, and neither is building it without noticing.

## Verification

This is where the test suite is founded, and the next two builds inherit whatever shape it takes, so it carries more weight than the amount of code under test suggests.

- The suite lives apart from the source, with its own directory for the cases, its shared helpers and any data files it loads.
- Tests of a dependency's own behaviour sit a level apart from tests of your code, because they fail for a different reason and on somebody else's schedule.
- Every test names the behaviour it claims rather than the function it calls, and arrives at its starting state through its parameters rather than building it inline.
- **The default run must not touch the network.** Capture a real holdings response once, keep it as a data file the tests load, and parse that; mark the tests that genuinely reach out so they stay out of the default run.

Worth their own cases: a US stock whose bare symbol appears among its listings and a foreign one where it does not, a name typed with the wrong case, spacing and punctuation, an unknown name from each source, and a fund whose request fails.

## Wrong turns

- **Detecting the terminal anyway**, because the skill says to, leaving output that differs between a terminal and a pipe when the brief asked for neither.
- **Rendering once and letting `rich` decide.** Unstyled output is not machine output; the box drawing survives the colour being dropped.
- **Emitting whatever the holdings file had in its symbol column**, cash rows and disclaimer text included, because the parse trusted the file to hold only shares.
- **Treating a 403 as an empty fund.** A refused request and a fund with no holdings are different outcomes and only one of them is the caller's problem.
- **A network call for a name the packaged dataset already holds.** `pytickersymbols` ships its data; reaching for HTTP means the adapter was written before the library was read.
- **Two shapes out of two adapters**, leaving the driver or the transform to reconcile them.
- **Making the caller say where to look.** The tool knows which names it ships and which it fetches, so a command or a required flag per source asks the user to hold knowledge the program already has.
- **String-wrangling the holdings file** into lists and dicts before it reaches a frame.
- **Letting a request failure surface as `httpx`'s own exception**, which makes the calling code depend on the library the adapter exists to hide.
- **Tests that hit the network by default**, which turn an unrelated outage into a failing suite.
- **Silently dropping an unmatched name**, which turns a typo into an empty report much later.
The brief asks for an error, and an empty frame written to standard output is not one.
