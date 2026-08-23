# Index symbols answers

The design a good build reaches, and the wrong turns that miss it.
None of it appears in the brief — each line is something the skills alone should produce.

## The shape

One packaged dataset and a spread of publishers, one pipeline, and the join between them happens before anything is reduced.

| shape | one row is | how it is reached |
|---|---|---|
| holdings | one constituent of one index | read the packaged dataset, or fetch and parse the published file |
| symbols | one symbol | concatenate every index's holdings, keep what is tradeable, sort, drop duplicates |

**Concatenate first, reduce once.** Every index produces holdings, those frames stack into one, and only then does it become a sorted list of distinct symbols.
Reducing each index to symbols and merging the results afterwards deduplicates twice and sorts twice, and it puts the join in the driver where the loop over indices lives rather than in the core where the data does.

**The adapters differ entirely inside and agree exactly at their edge.** Each returns holdings in the same frame, whatever its source published, so the concatenation is a stack rather than a reconciliation.
An adapter that returns the dataset's records from one source and parsed rows from the other has pushed its source's shape outward, and every later build pays for it.

**Declare a dtype where the contents were not chosen, and nowhere else.**
An empty list infers `Null` rather than an empty `String`, and `Null` raises against a real column on `concat`, on a join key and on every `.str` call, so an adapter's output needs the declaration where a shipped constant does not.
The test that had rows never sees this.

**Holdings stay a frame the whole way.** The published file becomes a frame at the boundary and never leaves it, so sorting and dropping duplicates are one pass of expressions rather than a trip through a Python `set` — which loses the order the brief asks for and has to be re-sorted anyway.

**A helper over a column takes the expression, not the column's name.**
Typed against a name, the same rule cannot reach a literal, another expression's output or a `when/then`, so the normalisation matching a catalogue entry gets written again to match the name the caller typed.
Take a `polars.Expr` and both are one `.pipe()` over one function; leave the `.alias()` to the caller, so it serves twice in one `select`.

**Names are matched loosely but written back canonically.**
Case, spacing and punctuation are all things a caller gets wrong and none of them tell one index from another, so `sp-500`, `SP500` and `S&P 500` all reach the same index.
An ETF symbol and an index are both just text to the lookup, so one normalisation covers matching for both rather than each source inventing its own.
The canonical spelling is what `catalogue` prints, a symbol in capitals and an index as it is usually written.

**A stock's home listing is a judgement the adapter makes.** The dataset gives several Yahoo symbols per stock, one per exchange, and its own bare `symbol` field *is* the home one — right even where it does not appear among the listings, as it does not for 12 of the FTSE 100.
So take it, and fall back to the first listing only where it is absent.
That fallback is small and the field's absence is not: fifty constituents carry no bare symbol and only three list anywhere else, but on those rows the field is *missing* rather than empty, so subscripting it directly does not lose three constituents — it fails two whole indices on a raw `KeyError`.
Checking it against the listings first changes no value and costs a pass; falling back while it exists returns a Frankfurt or US line for Barratt Redrow, ICG and Rio Tinto.
Keep the rule in the adapter — it is a fact about the data source, not about the domain.

**The port is a protocol the adapter modules satisfy, not a record of callables.**
Two calls have to come from the *same* source — what a place offers, and what one of its indices holds — and a record bundling two functions lets a caller build a chimera out of two adapters, which type-checks.
A module cannot be mixed with itself, and a module satisfies a structural protocol exactly as an instance does, so nothing has to become a class and the composition root hands over the adapter modules themselves.
The cost to accept is that a protocol's method name *is* the contract, so every adapter spells it the same — which is right, since a caller reaches a port precisely because it does not care which one answers.

**The port's two calls are named for the work they do, and every adapter spells them the same.**
`get_holdings(index)` and `get_indices()`, each returning a `polars` frame: a verb because nearly every adapter reaches the network to answer, and a bare `holdings()` reads as an attribute a caller may take twice in a loop without noticing what it cost.
The protocol fixes the spelling for all of them, so the adapter answering from packaged data cannot say so in the call and says it in the module name instead.
Both are reached through the injected fetch rather than calling it directly, which is what lets the whole expansion be tested against a recorded response with no network.

**Resolving an index is ordered, and the open source is a fallback rather than another source.**
The sources that know what they offer are asked first, and only an index none of them claims reaches the one that will try any symbol.
Put it in the same mapping and it either claims every index before the others are consulted, or it has to be consulted last anyway — at which point the mapping was never what decided it.

That splits what a source is.
Expanding wants holdings, which anything able to fetch them can give; cataloguing wants the indices themselves, which only a source with a fixed set has.
A port demanding both from everything forces the open one to answer with an empty frame, which is a lie the `catalogue` command then prints nothing for.
So the two calls are two ports, and the composition root hands each operation only the one it needs — `catalogue` never sees the fallback, and `get-symbols` sees it last.

An unmatched index now fails two ways and they are not the same failure.
A symbol that is no ETF is an unknown index; a request that would not come is a retrieval failure.
Reporting the second as the first sends the caller hunting a typo in an index that was right all along, which is the more expensive mistake because the tool sounds certain.

**Pure frame work belongs to the core even when the adapter noticed it was needed.**
A frame in, a frame out, no IO: that is a transform, and three adapters left to their own devices grow three versions of one reshape, none of them under the core's tests.
The adapter owns the *decision* and the core owns the *operation* — that ARK spells a symbol the Bloomberg way is knowledge about ARK, and moving it inward teaches the core about publishers.

What counts as *tradeable* is the core's call rather than the adapter's, so cash lines and their like are dropped by one rule in one place instead of once per source.
The adapter is answerable for reading its file correctly; the core is answerable for what deserves to come back.

**One parse is one chain, and the naming says which steps are the core's.**
Reading, reshaping and converting a library's failure inside one `try` reads as three statements naming two intermediates, and the reshape in the middle stops looking separable — which is how it ends up written once per adapter.
Lift the conversion to a decorator and the parse is a single chain whose middle steps are plainly frame in, frame out, so the ones belonging to the core announce themselves.
Every frame-to-frame step carries its `map_`/`amap_` prefix and is reached with `.pipe()`, the last one included: `symbols(map_keep_tradeable(holdings))` nests where it should pipe *and* drops the prefix, each hiding the other.

**Names are spelled as words.**
`granny_shots` and `market_cap`, not `grannyshots` and `companiesmarketcap`, spelled from what the thing is *called* rather than from however its domain name ran it together.
Take the shortest name that still identifies it, since the layer supplies the rest, and name an adapter for the source it reads rather than whose data it is: `info_13f` says which site breaks, where `sec` names a regulator the code never contacts.

## What the build earns

**A `port`.** Expanding several indices, stacking their holdings and failing the run if any one of them fails is an operation, and it calls outward for holdings while staying pure — which is what a port is for.
The payoff is that the whole expansion becomes testable against a fake source with no network, rather than only through the driver.

Two adapters sharing a signature is *not* what earns it, and a build that says so has the right answer for the wrong reason: one adapter and the same operation would earn it just as much.

**What this build declares.** Two ports and two operations, and every later build adds to these rather than restating them:

```python
Holdings = collections.abc.Callable[[str], polars.DataFrame]


class Publisher(typing.Protocol):
    def get_holdings(self, index: str) -> polars.DataFrame: ...
    def get_indices(self) -> polars.DataFrame: ...


def catalogue_indices(
    *, publishers: collections.abc.Iterable[port.Publisher]
) -> polars.DataFrame: ...


def get_symbols(
    indices: collections.abc.Iterable[str],
    *,
    fallback: port.Holdings,
    publishers: collections.abc.Iterable[port.Publisher],
) -> polars.DataFrame: ...
```

**The two forms are chosen, not mixed by accident.**
`Publisher` is a protocol because its two calls must come from the *same* place, per the shape section above.
`Holdings` is a plain callable alias because the fallback has one call taking one positional argument, and there is nothing to mispair — an alias is then the lighter declaration and a test fake is a lambda where a protocol needs a stub module.
Reach for a protocol where the calls must pair or the call carries keyword arguments, which `collections.abc.Callable` cannot express; reach for an alias otherwise.

**`fallback` is a parameter, not a member of `publishers`** — the ordering above made structural, so the type checker enforces that the open source is never catalogued and never asked first.

**Routing an index to its publisher is a seam, and it is private.**
`be-functional` opens one wherever a new independent input enters, and the publishers' catalogues are exactly that: indices go in, the catalogues arrive from outside, and out come indices paired with whoever serves them.
So it is a function rather than something inlined into the expansion — but not a third public operation, because no driver calls it and both operations need the same gathering behind it:

```python
def _get_publishers(
    indices: collections.abc.Iterable[str],
    *,
    publishers: collections.abc.Iterable[port.Publisher],
) -> dict[str, port.Publisher]:
    """Return the publisher claiming each index, omitting any none claims."""
```

**It returns a `dict` because a frame cannot hold a module**, which is what stops the pairing being a column and makes this one of the few places the tool leaves `polars` on purpose.
Say so where it happens: `use-polars` names two legitimate exits and this is neither, so the next reader takes it for the lapse that rule warns about and puts it back in the frame — where it cannot go.
The indices no publisher claimed need no second return value; they are the keys the mapping does not have, and they are what reaches the fallback.

**The matching itself is pure and belongs in `transform`.**
Deciding that `sp-500`, `SP500` and `S&P 500` are one catalogued index is two frames in and one out, with no IO, so it is testable against no port at all.
Left in the operation it gets written twice — once to route an index to its publisher, and once to compare a typed index against what `catalogue` prints.

**Which publishers exist is `adapt`'s to say, not a driver's.**
The set is a fact about what the adapter layer ships, so `adapt` returns it and the composition root injects it: `operate.catalogue_indices(publishers=adapt.publishers())`.
It is neither a port nor an operation — the core never calls it — which is why it sits outside the declarations above.
Name it with a bare noun: it returns a tuple of modules and touches nothing, and `write-python` reserves noun-only names for exactly that, so the contrast with every `get_` beside it says which calls cost a request.

One language detail neither `write-python` nor `structure-python` mentions: a protocol method's body needs a bare `...` **after** its docstring.
A docstring alone returns `None`, which `pyright` rejects against the declared return type.

**An `operate` layer.** There are two use cases here, not one: expanding names and listing them.
Both orchestrate the same sources and both call outward through the port while staying pure, so the layer has something to hold and a second caller to hold it for.
The count is what decides it, not the ceremony — one use case would be a function beside the transforms; two that share how the sources are gathered are a layer, and the shared gathering is the thing a later build inherits.

**`adapt` naming its own members.** Which sources exist is a fact about what the adapter layer ships, so it returns the mapping and every driver reads the same one.
Enumerate them in a driver instead and the next driver copies the list, so adding a source edits every entry point rather than the package that gained it.
That is not the composition root moving: the driver still chooses to use the set and still injects it into the operation.

## What should not exist yet

- **No caching, no configuration layer**, and no registry that sources sign up to — fifty-three indices across a handful of publishers is still a mapping with one fallback behind it, not a plugin system.

## The boundary

The brief lists the indices and leaves finding them to the build, so the first work is research: no two publishers agree on where their data sits, what it is called, or how often it changes.

- `httpx` is the pick over `requests`.
- The fetch is **one function with its parts named beside it**.
`fetch(url)` performs the request and nothing else, taking as arguments the axes a caller varies and calling `headers()`, `timeout()` and the rest for the ones it does not — each of those a function rather than a module constant, so any can be computed or overridden without a call site changing.
Stack a `handle` decorator per library exception it converts rather than one `try` catching several.
What the decorators cannot do is **classify**: which status the far end answered with is a branch on the response, not on an exception type, so the missing-versus-refused distinction the retry policy consumes is written explicitly in that one function and the decorators cover the library's own failures around it.
- Say who you are, and expect to be refused unevenly where you do not.
A tool name, a version and an address a publisher could reply to is the honest default and what these publishers accept; `www.sec.gov` refuses any user agent carrying no address, and some CDN-fronted services refuse anything that is not a browser string.
Which is which is found by trying, so what matters is setting the header deliberately rather than any one string being right — never setting one works against some publishers and not others, which is worse than failing everywhere because it looks like it works.
- Set a timeout.
A published holdings file is somebody else's server, and a hung request with no deadline is the failure that wastes the most time.
- Retry the transient and only the transient.
A timeout, a refused connection or a 5xx deserves another go after a short backoff, where a 404 is an answer and retrying it turns a mistyped symbol into a slow error instead of a quick one.
That distinction stops being a nicety the moment any symbol can be tried, because a 404 is then the ordinary reply to an index that was never a fund.
Retrying belongs to the fetch alone, so a parse that fails is never attempted twice.
- Retry is what makes the brief's all-or-nothing rule survivable, which is why it is in scope where caching is not.
One failure failing the whole run means the odds of a wasted run climb with every index asked for, so a single transient refusal somewhere among fifty would otherwise be enough to lose all of them.
- The adapter owns its outcome: a fund that 404s, times out, or returns something unparseable becomes an error naming the fund, not a status code or a library exception escaping into the driver.
- One conversion of a library's failures, not one per parse.
Every adapter turns the same exceptions into the same error of yours and differs only in the message, so the `try`/`except`/`raise ... from` is written once as a decorator and applied.
A build with a `try` in every parse has the right behaviour and has hand-written, five times over, the abstraction its skills already gave it.
- Split getting the document from making sense of it.
Retrieval is a few lines that never change; the parse is where a publisher's quirks live and where the work grows, so fused they lengthen together and the one line saying what the adapter returns sinks under them.
Apart, a saved response tests the parse with no stub for the fetch.
- The open ETF source is a third party rather than an issuer, since no issuer publishes anybody else's funds.
`stockanalysis.com` carries US and London listings alike, so the two differ by a path segment rather than by a whole adapter, and a build that reaches for each issuer in turn can serve the forty-eight named funds and still has nothing to answer `TAN` with.
- **A named fund still goes to its issuer, and the third party answers for everything else.**
The general source publishes a fund's largest holdings and stops — twenty-two for `GDX.L`, where VanEck's own file lists fifty-eight — so routing the named funds through it trades most of the answer for a smaller adapter.
That is what makes an issuer worth its price, and VanEck's is real: a workbook rather than a CSV, served only to a caller already holding the cookies its locale's front page sets.
The two ranges still differ by a locale and a slug in one table, so it stays one adapter.
- **An investor's disclosure names its positions by identifier rather than by symbol, so where you read it decides whether you need a second service at all.**
The filing gives a CUSIP, and a CINS wherever the issuer is foreign — a second identifier type to discover before a mapping service answers at all — and those services cap requests per minute, so ninety positions is ten requests and a wait on top of walking the filing index.
A site that has already parsed the filings hands back the symbol, the class and the option type in one table, most recent quarter first.
Take that: the brief asks for the most recent report, not for the filing.
- Where each publisher serves its file is **data**, not a literal in code — one entry per fund, with the host held once rather than repeated against each of them.
It is read by the adapter that fetches them, since where an outside service lives is the edge's knowledge and not the core's.
Each adapter turns an index into its address through one function, and that function **joins** rather than concatenates: `urllib.parse.urljoin` knows what a scheme, an absolute path and a relative segment each mean, where `base + path` guesses at a separator and silently doubles or drops one.
The trap to know is that it reads the base as a *document*, so a base missing its trailing slash loses its last segment and a path carrying a leading one resets to the host — hold the slash on the base and not on the path, and the table stays readable.
- One reader per wire format, shared by every adapter meeting it, then a chain of prefixed transforms.
`polars.read_csv` and `polars.read_excel` for a tabular file and `pandas.read_html` for a page's table converted straight to a frame — which is the one job `pandas` is here for, CSV included going to `polars`.
From the frame onward the parse is method chaining and nothing else: each step a `.pipe()` into a `map_`/`amap_` transform, so the adapter reads as which transforms this publisher needs and in what order, and the transforms themselves live in the core under the core's tests.
- Parse the response **into the frame** where the response is rows and columns — a CSV is read by the frame library, not split on commas and reassembled.
Where the source hands back records or markup and one field is wanted, pulling that field out and building a one-column frame is both simpler and cheaper: routing the whole record through the frame materialises every nested column you did not ask for, at a cost of two orders of magnitude here.
- A holdings file is not a list of shares.
Cash lines, placeholder rows and a trailing disclaimer all appear in them, so the adapter hands on what the file gave it and the core decides what deserves to come back.
One rule covering cash lines, options and a trailing disclaimer alike beats a row filter in every adapter plus a tradeability rule after it — the second filter is the same judgement written four more times.

## The surface

Two commands, split by what they do rather than by where the symbols come from.
Resolving a name is the tool's job, so `get-symbols` takes the name alone; finding out which names exist is a different question, so `catalogue` is its own command rather than a flag that switches what `get-symbols` does.

**The group is a package, not a prefix on two command names.**
The brief says more groups follow, so `index` is a `typer` sub-application registered on the root — which is what lets the next group be added without the root command being touched, and what makes `trade index --help` list this group alone.
Spelling the commands `index-expand` and `index-catalogue` at the root reaches the same invocation and gives up both.

### The driver is three packages, not one

A hollow `cli/` naming what the entry point *is*, over `typer_/` for the parsing and `rich_/` for the presentation.
Swapping either library then touches one package and never the console script, which points at `cli` and so never names the framework behind it.
Collapsing all three into one `cli.py` is the right call for a one-command tool and the wrong one here, because the brief says two more groups follow.

**The app object goes in `typer_/driver.py`, not at the top of the commands module.**
A framework anchor has to exist before anything decorates it, so leaving it beside the commands fixes that file's order and pushes the callback ahead of the thing a reader opened the file for.
Given its own module, the commands stay a flat alphabetical list.

**Every argument and option is a function returning its configuration**, in `argument.py` and `option.py`, referenced from the signature rather than inlined.
At two commands that looks like ceremony; it is the shape that survives the group after this one, where one option set is spelled across seven commands.
It pays immediately too: because every option here carries a short form, each factory names its own flags — so the parameter behind `--input` can be `input_` without the CLI ever seeing the underscore, and no option has to be renamed around a builtin.

**A command's name is its function's name.**
`typer` turns `get_symbols` into `get-symbols`, so passing `name=` is a second place the name lives and the reason someone greps for the command a user typed and finds nothing.

`catalogue` is what makes a bare error acceptable on an unmatched index — without it the tool would owe the caller near matches, since an index it ships is not otherwise discoverable.

- Two renders, not one styled two ways.
`rich` dropping colour when piped does not make a bordered table parseable, so the default form is its own render emitting one symbol and nothing else.
- **No terminal detection.** The brief asks for the same bytes everywhere, so `Console.is_terminal` decides nothing here — a build that reaches for it has followed a habit past an instruction.
- `-o` writes whichever form is in force, so `-o` alone saves lines and `-o -t` saves the table.
A path does not silently override the flag.
- One symbol per line is right here because there is one column, and it is what `grep`, `xargs` and `wc -l` all expect.
The brief reaches it by fixing the plain form as headerless comma-separated values rather than by describing a list, which is the same thing over one column and still a thing over eight — so the renderer written here is the one every later group inherits.
A build that prints bare lines because there happens to be one column has written a renderer that will not survive the next command, and the `--pretty` flag beside it then looks like a choice between two forms when it is a choice between one form and a `rich` table.
- Several indices expanding into one list, deduplicated across them, since `ARKK` and `ARKW` hold much the same stocks and asking for both should not say so twice.
- One index failing the whole run.
A short list is the dangerous outcome, because nothing downstream can tell it apart from an index that genuinely shrank.
- Diagnostics, progress and errors to standard error, so a redirect captures symbols alone.
- A non-zero exit on any failure, an unknown index or a fetch that would not come, so `&&` and `set -e` behave.
- A `--help` that explains the tool without recourse to a README.
- `catalogue` writing one index per line, so `trade index catalogue | grep ARK` answers "what can I expand that looks like this".

**Where a good build should push back.** One thing, and it should end in the brief being followed.

`-o PATH` does nothing that `> PATH` does not already do, so it earns its place only by convention — `curl` and `sort` carry it, and a caller who expects it will look for it.
Saying so and building it anyway is the right answer; refusing it is not, and neither is building it without noticing.

The form-versus-destination question reads like a second one and is not.
`write-entry-points` and the brief agree — fix the form, let an option change it, never let the destination decide — so a build presenting this as a disagreement has misread the skill rather than found one.
`ls` is the exception that skill names, not the pattern it teaches, and it gets away with varying by destination only because both its forms are parseable where a bordered table is not.

## Verification

This is where the test suite is founded, and the next two builds inherit whatever shape it takes, so it carries more weight than the amount of code under test suggests.

- The suite lives apart from the source, with its own directory for the cases, its shared helpers and any data files it loads.
- A recorded response proves the parse and not the source, so the build is not done until the declared surface has been run once against the real thing and the **counts** read.
Seventy-three catalogued indices is seventy-three expansions, and the one returning nothing has passed every check the program can make on itself — which is how a packaged index with no symbols in it ships.
- Tests of a dependency's own behaviour sit a level apart from tests of your code, because they fail for a different reason and on somebody else's schedule.
- Every test names the behaviour it claims rather than the function it calls, and arrives at its starting state through its parameters rather than building it inline.
- **The default run must not touch the network.** Capture a real holdings response once, keep it as a data file the tests load, and parse that; mark the tests that genuinely reach out so they stay out of the default run.

Worth their own cases: a US stock whose bare symbol appears among its listings and a foreign one where it does not, an index typed with the wrong case, spacing and punctuation, one only the fallback resolves, one nothing resolves, and a fund whose request fails.

## Wrong turns

- **Detecting the terminal anyway**, because the skill says to, leaving output that differs between a terminal and a pipe when the brief asked for neither.
- **Rendering once and letting `rich` decide.** Unstyled output is not machine output; the box drawing survives the colour being dropped.
- **Emitting whatever the holdings file had in its symbol column**, cash rows and disclaimer text included, because the parse trusted the file to hold only shares.
- **Treating a 403 as an empty fund.** A refused request and a fund with no holdings are different outcomes and only one of them is the caller's problem.
- **A network call for a name the packaged dataset already holds.** `pytickersymbols` ships its data; reaching for HTTP means the adapter was written before the library was read.
- **Two shapes out of two adapters**, leaving the driver or the transform to reconcile them.
- **Making the caller say where to look.** The tool knows which indices it ships and which it fetches, so a command or a required flag per source asks the user to hold knowledge the program already has.
- **String-wrangling the holdings file** into lists and dicts before it reaches a frame.
- **Letting a request failure surface as `httpx`'s own exception**, which makes the calling code depend on the library the adapter exists to hide.
- **Tests that hit the network by default**, which turn an unrelated outage into a failing suite.
- **Registering the open source alongside the named ones**, so it either swallows every index before a real source is asked or contributes an empty list to `catalogue`.
- **Reporting a failed request as an unknown index**, which turns somebody else's outage into a hunt for a typo that was never there.
- **Subscripting a field the packaged record does not always carry**, so a `KeyError` escapes into the driver and two whole indices fail on a raw traceback instead of an error naming the index.
The seam an adapter closes is every library it touches, and a packaged dataset is one of them.
- **A `try` in every parse**, where one decorator converts the same library failures for all of them.
- **Naming a port's call with a bare noun.** `holdings(name)` reads as an attribute, so it gets called wherever convenient and the same document is fetched twice in one run with nothing in the name to suggest it would be.
- **Building an address with `+`.** It works until a base gains or loses its trailing slash, and then it fails as a 404 that looks like the publisher moved the file.
- **Sending a named fund to the general ETF source** because it answers, when its own issuer publishes the whole book and the general source publishes the top of it.
- **Silently dropping an unmatched index**, which turns a typo into an empty report much later.
The brief asks for an error, and an empty frame written to standard output is not one.
