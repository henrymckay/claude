# Symbol data answers

The design a good build reaches, and the wrong turns that miss it.
None of it appears in the brief — each line is something the skills alone should produce.

**Grade against `../index-symbols/answers.md` as well as this file.**
Everything that one declares still stands: the two ports and two operations, the `error` package and its decorators, the three driver packages, the pair of renderers, and the transports resolving to one input.
This file records only what this build adds to them or changes about them, so a build diverging from that file diverges here too, and nothing in it is repeated for being still true.

## The shape

A second source, three shapes out of it, and the first shapes the core genuinely owns.

| shape | one row is | how it is reached |
|---|---|---|
| symbols | one symbol | the index build, unchanged |
| candles | a symbol's candle in one timeframe | fetch each timeframe directly |
| descriptions | one symbol's description | one call per symbol, a declared schema over each response |
| matches | one instrument a search found | one call, already a frame |

**Three commands over one source is one adapter, not three.**
`get-candles`, `get-info` and `look-up` are three calls to Yahoo through one library, so they are three functions in a `yfinance_` package sharing its failure conversion, its column spelling and its declared-shape rule.
Splitting them into three adapter packages triples the decorator, the naming and the tests to buy a boundary that does not exist — there is one outside system here, and it breaks all at once.

What they do **not** share is the parse: a `MultiIndex` frame, a dict of a couple of hundred keys and a frame indexed by symbol have nothing in common past the library that returned them.

**There is no resample step.** `yfinance` serves daily, weekly and monthly, so the adapter returns one long frame already carrying a timeframe column, and Yahoo's own week and month alignment is used rather than a reinvented one.
Deriving coarser candles from dailies is a transform the problem does not need, and it adds a seam that then has to be threaded through every later build.

**Timeframe is a column, not something the caller stitches together.** The adapter makes one call per timeframe because the API has no other shape, concatenates them itself, and hands back a single frame.
A `concat` over a comprehension is only the per-group-loop mistake when the groups are computation; here each group is its own network call.

**The date the brief asks for is the one Yahoo already gives, so nothing re-stamps it.**
A weekly candle arrives stamped on the Monday and a monthly one on the first, which is exactly what the brief says the column means — so the adapter carries the value across rather than computing it.
That holds only once the request is aligned to the period, as the boundary section works out: ask across a period boundary and the stamp can arrive on a day the period did not begin.
The failure is a build that reads "date" as a day the row is *about* and shifts the stamp to the period's end, or spreads a weekly row over its five days, either of which invents a transform to satisfy a requirement already met.

**The adapter spells the columns in the domain's words, in one expression over the whole schema.**
Yahoo publishes CamelCase and a space in `Adj Close`; the frame leaving the adapter carries neither.
Rename through `polars.all().name.map(...)` rather than a dict naming every column, so a field the source adds arrives spelled correctly instead of waiting for someone to find the dict — the same reason `use-polars` prefers a selector to a hand-written list.

**Alphabetical column order is the declared schema, not a sort at the end.**
The adapter declares its output in that order once and every renderer selects it unchanged, so nothing sorts column names on the way out.
A renderer reordering columns is doing at the edge what the shape should already guarantee, and it has to be written again in the next group.
It is one constant per shape rather than a list per consumer, which is what makes the plain form readable back: the next group loads a saved file with no heading row, and the names and dtypes it parses with are this same declaration.

## What should not exist yet

- **No caching.** Candles change daily and the brief says nothing about storing them, so a build that adds a cache has invented a requirement and a cache invalidation problem with it.
- **No abstraction over price sources.** The core needs candles from outside, which is a port; one named source behind it is not a family, and a registry, a provider protocol or a `--source` flag is machinery for a set that has one member and no way to gain another.
- **No adjustment option.** The brief settles that prices are split-adjusted and not dividend-adjusted, so a `--adjust` flag offers a choice nobody asked for and puts back the decision the adapter exists to make.
- **No filtering, and no counts.** The bounds size the *fetch*; they are not a general row filter, and the moment one is written the next build's filter has to be reconciled with it.
- **No paging.** `--count` is the most the caller wants, which is not the same as a number to go and reach.
- **No index resolution in this group.** The brief is explicit that these commands take symbols, so an operation reaching for the holdings port to expand a name it was handed has added a stage nobody asked for — and made half the catalogue unchartable, since most of what it names is tradeable itself.

## What this build declares

**On top of the two ports and two operations the index build already has:**

```python
Info = collections.abc.Callable[[collections.abc.Iterable[str]], polars.DataFrame]

class Candles(typing.Protocol):
    def __call__(
        self,
        symbols: collections.abc.Iterable[str],
        *,
        end: datetime.date | None,
        start: datetime.date | None,
        timeframes: collections.abc.Iterable[transform.Timeframe],
    ) -> polars.DataFrame: ...

class Lookup(typing.Protocol):
    def __call__(
        self, query: str, *, count: int, kind: transform.Kind | None
    ) -> polars.DataFrame: ...

def get_candles(
    symbols: collections.abc.Iterable[str],
    *,
    end: datetime.date | None,
    fetch: port.Candles,
    start: datetime.date | None,
    timeframes: collections.abc.Iterable[transform.Timeframe],
) -> polars.DataFrame: ...

def get_info(
    symbols: collections.abc.Iterable[str], *, fetch: port.Info
) -> polars.DataFrame: ...

def look_up(
    query: str, *, count: int, fetch: port.Lookup, kind: transform.Kind | None
) -> polars.DataFrame: ...
```

**Three ports, not one covering the library.**
The index build bundles two calls into `Publisher` because they must come from the same place — you ask who claims `ARKK`, then ask *that* publisher for it.
Candles, descriptions and search have no such tie: nothing says they must come from one source, and one `yfinance_` module satisfies three separate ports at once anyway.
Bundling them buys nothing and costs a fake for `get_info` that has to implement candles and search as well.

**The form follows the call, by the rule the last build set.**
`Info` is an alias because it takes one positional argument.
`Candles` and `Lookup` carry keyword-only options, and `collections.abc.Callable` cannot express those at all, so they are protocols declaring `__call__` — and a plain module-level function satisfies one, so no adapter grows a class.

Both ways of making them aliases cost more than the shorter declaration saves.
Flattening the options to positional arguments buys the alias with four positional parameters at every call site, which `write-python` rules out on its own.
Collapsing them into one positional record buys it with a `Request` type per port — the input grammar modelled as a type, and a construction standing between every caller and the call.

**The options stay on the operation.**
Binding `start`, `end` and `timeframes` into the adapter with `functools.partial` at the composition root type-checks, and makes both protocols plain aliases, which is why it is tempting.
It is still wrong: it fuses a dependency fixed at startup with data that changes every invocation, so the injected value must be rebuilt per call and the operation can never run twice with different bounds against one adapter.
Worse, it moves the use case into the driver — every second driver, a dashboard included, rebuilds the same partial, which is the duplication `operate` exists to prevent.

**`get_candles` looks like a forwarding call and is not one.**
It is one line today because the fetch is the whole use case, and the next build calls it rather than the port — which is what an operation over a single port call earns its place by, and what a group reaching past it to `fetch` would give up.
That is also the second cost of currying the bounds into the adapter: the next build would inherit an adapter fixed to one caller's dates rather than a stage it can reuse.

**Nothing here composes with `get_symbols`.**
The brief makes this group take symbols, so no operation in it resolves an index, and the pipe that expands one runs between two processes rather than inside the driver.
A driver calling `get_symbols` and then `get_candles` has rebuilt the stage the brief removed.

## The boundary

This is where `pandas` meets `polars`, and it is most of what this build is judged on.

**One `yfinance` call serves each command**, and finding which is the first work of the build:

| command | call | what comes back |
|---|---|---|
| `get-candles` | `yfinance.download` | one frame carrying every symbol, its columns a `MultiIndex` of `Price` over `Ticker` |
| `get-info` | `yfinance.Ticker(symbol).get_info()` | a `dict` per symbol, so one request each |
| `look-up` | `yfinance.Lookup(query).get_<kind>(count)` | a frame indexed by symbol, one method per kind |

A wide frame, a dict and a narrow frame: the three agree on nothing but their library, so the adapter is three parses sharing a package rather than one parse generalised over them.
Each also carries defaults that are wrong for this brief and quiet about it, which is what the rest of this section is.

**Every default `yfinance.download` carries is wrong for this build, and each one fails quietly.**

- `auto_adjust` defaults to **`True`**, which is the dividend-adjusted close — precisely what the brief rules out.
Pass `False`.
Measured over one month of `AAPL`, the two closes differ by up to 0.95, so a build that leaves the default is not slightly off; it is answering a different question with numbers that look right.
- `period` defaults to **one month** when no `start`/`end` is given.
Not naming it returns twenty-odd daily candles and looks exactly like a fetch that worked.
Where the caller named no bounds, the adapter asks for the source's full history rather than letting that default stand.
- `progress` defaults to **on**, writing a bar to standard error — a library narrating on a channel the driver owns, which is the same objection `structure-python` makes to a library calling `logging.basicConfig`.
Off.
- `timeout` is already ten seconds, so `structure-python`'s instruction to set one is met by the library rather than by a wrapper — go and look before writing what is already there.
- `rounding` exists and is **not** the brief's four decimal places.
It rounds to the precision Yahoo suggests for the instrument, which is two for `AAPL` and two for `BTC-USD`, so the same column carries a different precision depending on who was asked.
Round in the frame, to the figure the brief named, for the same reason the schema is declared rather than inferred.

**`auto_adjust=False` also brings `Adj Close` back**, sitting in the frame beside `Close` and holding the rejected number under a name nobody will question.
Select the columns you declared rather than keeping what arrived.

**A symbol Yahoo has nothing for does not raise.**
It comes back as a block of columns full of `NaN` — an empty frame if it was the only one asked for — and the only sign is a line on the library's own logger.
So the adapter compares what came back against what it asked for, because nothing else in the program can: once the nulls are gone the symbol has simply vanished, and the short table that results is indistinguishable from a stock that stopped trading.
This is the index build's all-or-nothing rule arriving from a source that will not raise for you.

**The download is a dense grid over the union of every symbol's trading days**, not one row per candle.
Ask for a London stock and a New York one and every day either market was shut carries a row for the other.
Those nulls are what the reshape exists to remove, and a fixture holding one symbol never contains one.

**The null test is over the candle, not the row.**
`.drop_nulls()` is the reflex and it is wrong twice: it throws away a real candle wherever the source left a single field off, and it never says which absence was meant.
Drop where the price fields are *all* null — that is "this symbol did not trade" — and leave a candle with a gap in it for the core to judge.
On one live three-month fetch of two symbols, four rows were absent candles and one was a real candle with no close, and the reflex cannot tell them apart.

**The one thing that must happen in `pandas` is dissolving an index `polars` cannot represent** — and it is a single `stack` on the **`Ticker`** level.
The columns arrive as a `MultiIndex` of `Price` over `Ticker`, and stacking that one level lands directly on the shape you want: a row index of date and symbol, a column per field.
Melting all the way to long and pivoting back on the `polars` side reaches the same frame after two more reshapes.

**`reset_index()` is not forced, and reaching for it costs twice.**
`polars.from_pandas(frame, include_index=True)` brings both index levels across as columns, so calling `reset_index` first is one more `pandas` operation doing what the converter already does — and omitting that argument instead **drops the date and the symbol silently**, leaving the values with nothing to say which row is which.

**The stamp arrives as a timestamp, not a date.**
The index is `datetime64[s]` and converts to a `polars` `Datetime`, so a midnight value that prints like a date is not equal to one.
Cast it at the boundary; the next build joins a daily row against a weekly one on exactly this column.

**`polars.from_pandas` needs `pyarrow`, and not only in a corner case.**
Recent `pandas` backs a string column with arrow, so the one string column it carries is enough to raise `ImportError` without it.
It is a dependency of the conversion.

**Which interval string means which timeframe is reference data**, one row each in `data/adapt/`, read by the adapter that passes them.
It is a table of your domain's names against a library's argument, and three rows was never what decided the question.

**The adapter names the arguments it passes and does not forward `**kwargs`.**
A pass-through makes `yfinance`'s signature into your interface, so every caller can reach for anything the library takes — including `auto_adjust`, the one argument the brief made the adapter answerable for.
Closing that seam is what the adapter is for.

**Convert at the boundary and never reach back into the original frame.**
Everything after the `stack` is an expression.

**The adapter declares its own output shape and returns it whatever happens**, including when the download comes back empty or `None`, so no later code branches on what the library felt like returning.

**Sorting is correctness, not presentation.**
The frame leaves the adapter sorted by symbol and date, because every window the next build writes reads the frame in its current row order and nothing raises on an unsorted input.
The brief asking for a settled order is the same requirement arriving from the other end, and satisfying it in the renderer satisfies only the half that shows.

**`threads` is on by default, so one call is many requests.**
An index expansion is five hundred symbols in a single `download`, which is where a publisher's rate limit is found rather than in any test.

**`end` is exclusive in `yfinance` and inclusive in the brief, and the difference is one day.**
`start=2026-06-01, end=2026-06-30` returns candles up to the 29th, and naming the same date for both returns an **empty frame** — which is exactly the "give me just this day" the brief says must work.
So the adapter adds a day to the bound it was handed, in the one place that knows the two conventions differ.
Passing it straight through loses the last candle of every run without saying so, and answers nothing at all for a single day.

**A coarse candle is fetched by its period, not by the caller's dates**, and the two coarse intervals fail differently, neither of them loudly.

`1wk` aggregates the daily candles inside the range and stamps the result with the week's Monday whatever it actually covered.
Asked for the week of 13 July 2026 from the Wednesday to the Friday, `AAPL` comes back stamped `2026-07-13` — the right date — opening at 317.62 and bottoming at 317.32, where the whole week opened at 317.02 and bottomed at 311.91.
It is the partial week the brief forbids wearing a complete week's date, and no field on the row says so.
The week is returned however little of it the range touches: a start on the Friday still yields a row stamped on the Monday.

`1mo` does not truncate, it disappears.
The month comes back only when the range starts on or before its first calendar day — `2026-07-01` returns July and `2026-07-02` returns an empty frame, with nothing to distinguish that from a symbol having no data.
For the month still in progress it is worse than empty: a start after the first returns a row stamped `2026-08-28`, the last trading day rather than the period's first, carrying values that match no calendar month and do not change with the start asked for.
A build that trusts the stamp has a monthly candle dated to a Friday.

None of it is documented: `start` is described as inclusive and `end` as exclusive, with no mention of alignment anywhere, and the weekly interval does not even honour the exclusivity — so this is found by measuring or it is not found at all.

So each timeframe's bounds are widened to the periods containing them before the request is built, and daily is that same derivation returning the dates it was given rather than a branch that skips it.
Widening the end makes the extra day added for exclusivity harmless here — a weekly request ending on the following Monday still returns only the week asked for — so the two corrections compose rather than fighting.

**Widening per timeframe is what keeps the bounds parameters of the fetch rather than a filter.**
Each request then returns exactly the periods intersecting what the caller asked for, with nothing to trim afterwards — where widening once to the coarsest timeframe would drag extra daily rows in and need a filter to take them out again.
Which day a week begins on is the domain's knowledge and not the library's, so the widening is a core function — but it is *called* from the adapter, because the port carries one pair of bounds for every timeframe asked for and only the adapter has fanned them out into a request each.
That is the port's declared shape deciding where a derivation lives, and it is the shape the next build's warm-up margin takes on top of it.

### What `get-info` returns

**The key set varies by instrument, so a field is *absent* rather than empty.**
`get_info()` gives 187 keys for `NVDA` and 71 for `^NDX`, and four of the eleven the brief asks for — country, industry, sector and market capitalisation — are simply not in the dict for an ETF, an index, a future or a currency pair.
Subscripting raises `KeyError` on the symbols the brief explicitly says it checks with.
This is the index build's packaged-record trap arriving from a different library, which is the point: an adapter's seam is every library it touches, and a dict one hands back is a record like any other.

**Declare the schema, and declare market capitalisation a float.**
Let `polars` infer it and the same column comes back a different type depending on who was asked: a batch of indices infers `Null`, a batch of stocks infers `Int64`, and concatenating two such runs raises `SchemaError`.
`use-polars` says to declare a dtype where the contents were not chosen — here the contents are chosen by *which symbols the caller gave*, which is the sharpest version of that rule there is and the one no fixture catches, because a fixture picks its symbols.

**Which eleven fields is reference data**, in `data/adapt/`, because the brief says the set is the user's to change without opening code.
A list in the module fails that requirement outright rather than merely being untidy.

**A symbol Yahoo has nothing for returns a one-key dict.**
It does not raise, exactly as the download does not, so `get-info` needs the same check of what came back against what was asked for — written once and shared, since it is the same rule twice.

**There is no batch call.** `Ticker(...).get_info()` is one request per symbol, so `trade index get-symbols large-companies | trade symbol get-info` is a thousand of them.
That is the one-call-per-group case `use-polars` blesses, and it is where a rate limit is met.

### What `look-up` returns

**`Lookup` rather than `Search`, and the brief's own options say which.**
`yfinance.Search` takes a `max_results` and hands back quotes mixed with news, lists and navigation links, with no way to ask for one kind of instrument.
`yfinance.Lookup` has a method per kind and a `count` on each — which is `--kind` and `--count` exactly, so the option surface the brief describes is the tell for which call was meant.
A build reaching for `Search` because the command searches has matched the English rather than the requirement, and then has to filter the kind itself out of a field the results may not carry.

**`--count` is a ceiling, not a target.**
A search for `nvidia` capped at 250 comes back with 56, because that is what Yahoo matched.
A build that pages to make up the difference has invented a requirement out of a number that was always an upper bound.

**`count` defaults to 25 where the brief says a hundred.**
Every one of those methods takes `count=25`, so an adapter that omits it answers a quarter of what was asked for — the same quiet default as `auto_adjust`, arriving in the one command where a short answer is indistinguishable from a genuine result.

**Do not reach the method by an interpolated name.**
`yfinance.Lookup` spells them `get_all`, `get_cryptocurrency`, `get_currency`, `get_etf`, `get_future`, `get_index`, `get_mutualfund` and `get_stock` — note it is `get_cryptocurrency`, not `get_crypto`.
That is one method per kind the brief names, plus `get_all` for the caller who names none.
A `getattr(lookup, f"get_{kind}")` turns that fixed, known set into a string nothing checks, so the wrong guess is an `AttributeError` in front of the user rather than an error at import.
`write-python` is explicit that a fixed known set is a lookup rather than a mechanism; a mapping from your own kind to the method is the same number of lines and fails where it should.

**The kind is a closed set, so it is an enum** — in the core, in the port and in the option — not a string the driver passes through and the adapter interpolates.

**The result is a frame indexed by symbol**, so `include_index=True` again, and it carries columns the brief did not ask for; select what you declared.

**A search matching nothing is an answer, not a failure**, which is where the declared-dtype rule bites a third time: the empty frame still has to carry `String` columns, or it will not concat or join and the emptiness surfaces as a schema error somewhere else entirely.

## Failure

One more class and one more decorator, over the machinery the index build already declared.

**Nothing new is needed to report it.**
The `error` package the last build declared already holds the classes and `handle`, so this group adds one class and one decorator and invents no mechanism:

```python
class UnknownSymbolError(TradeError):
    """Raised when the price source has nothing for the symbol asked for."""
```

**`check_complete` is that decorator, and it lives in `yfinance_`.**
A decorator sees the arguments and the return value together, which is exactly what this check needs — the symbols that were asked for, against the symbols the frame came back with — so the comparison is a decorator on `get_candles` and `get_info` rather than a check written into both.
It imports nothing from `yfinance`, which makes it the same case as a driver's own helper sitting in a framework package: both its callers are here, so it stays beside them and lifts out the day a third source needs it.

That it applies to two functions in one package is the whole argument for it being shared, and the argument against a third adapter package per call — one boundary, one failure vocabulary, one check.

The three ports carry their own `:raises:` for the same reason `Publisher` does, and `Info` carries it in a string literal beneath the assignment, being an alias with no docstring to hang it on.

## The surface

Symbols arrive the three ways indices already do — as arguments, from a named file, or on standard input — so the resolution is inherited rather than invented here, and a build writing a second one has missed that it already owns one.
What is new is the pipe it spans: `trade index get-symbols dow-jones | trade symbol get-candles` is two groups composing, which is what the three ways were for and what neither group could show alone.
It is also what keeps a later group's `--load` meaning something genuinely different: a value at a different stage rather than a fourth spelling of this one.

**Normalise the symbols once, where they arrive.**
Three input routes are three chances for whitespace, case and repetition to differ, and the brief asks for a symbol back once however many times it was given.
Doing it at the boundary is what stops each route growing its own version.

Candles go out the same two ways the symbols already do, and every option the brief spells is spelled once for the whole tool rather than per command.
Spelling the same idea differently between two commands of one tool is the cheapest possible thing to get wrong and the most irritating to live with.

**A repeated `--timeframe` is one column, not three code paths.**
The option collects into a list, the adapter makes one call per member and concatenates, and the value lands in the `timeframe` column — so the axis the brief exposes as an option is the same axis `use-polars` insists stays data.
The failure is a branch per timeframe, or three boolean flags, or a function returning a column per timeframe: each turns a grouping key into control flow, and each is the per-group loop the previous section already ruled out, arriving this time through the option parser.

**The bounds are parameters of the fetch, not of a filter**, which the widening sharpens rather than softens: the adapter changes the bounds it passes on, and still nothing filters rows afterwards.
A build that fetches everything and filters afterwards is correct and grows with the data; one that filters what it already narrowed has written a reconciliation the next build has to undo when it widens again for its warm-up.

**`look-up` taking a different kind of input is not an inconsistency to iron out.**
It searches for a symbol rather than being given one, so the three-ways rule does not apply and forcing it to would mean a search reading from standard input.
What must stay identical across all three is the *output* — the same plain form, the same `-o`, the same `-p` — because that is the half a caller composes with.

**One pair of renderers for the whole tool, not a pair per group.**
The brief fixes the plain form and the two options once and then says every command answers the same way, so the plain render and the `rich` render are written here, in the driver layer, and the third group registers commands against them rather than growing its own.
The tell that this was missed is a second `rich.Table` construction appearing in the next build: the table differs by which frame it is handed, and nothing else.

**So the decoration is a column spec, not a second table builder.**
The index build's renderer took a frame; this one has to be told that `close` colours against `open`, that `volume` draws a bar scaled within its symbol, and that `market_cap` groups its digits — so what the driver hands over beside the frame is a per-column description of how to show it, plain for every column that says nothing.
Giving `get-candles` its own table because it needs more than `get-symbols` did is the failure the shared renderer exists to prevent, and it arrives here rather than in the next build.
The heading stays `full_exchange_name` for the same reason it stays a column name at all: the two forms name one set of columns, and a render that retitles them has invented a second vocabulary for the caller to hold.

**The bar is scaled within the symbol, which is a domain choice wearing a rendering hat.**
Scaled across the whole table, a heavy day for a thinly traded symbol vanishes beside a liquid one and the bar answers a question nobody asked; scaled within the symbol it answers *is this a big day for this stock*, which is the only reading that survives five hundred of them in one table.
It sits beside the number rather than replacing it — a bar alone is a value nobody can read back, and `--pretty` is the plain answer made readable rather than a different answer.

**Direction is derived at render time, never stored.**
Green and red come from comparing `close` against `open` where the table is built; a `direction` column computed in the core is the added column `--pretty` may not have, and the next build makes the same point from the other side when its signed counts refuse to become one.

**The group is a sub-application, not a prefix.**
`index` and `symbol` are two `typer` sub-applications registered on one root, so the third build adds a third by registering it rather than by editing either.
Two commands spelled `symbol-candles` and `symbol-info` at the root reach the same invocation and give that up, along with a `trade symbol --help` that lists the group alone.

**That is what turns the last build's `command.py` into a `command/` package** — a module per group owning its own sub-app and its commands, and `command/__init__.py` mounting each on the root app.
The root app itself stays in `driver.py`, where every framework package keeps it, so nothing in `command/` is imported by the thing it decorates and no cycle appears.
This is the one place the skill reads two ways, saying both that `driver.py` holds the app object and that `command/__init__.py` holds the main one; the reading that keeps `driver.py` importing no other driver module is the one that works.

**The driver function resolving the transports gains its second and third callers here**, which is the first evidence it was worth writing as one rather than inlining it into the single command that needed it.
`get-candles` and `get-info` share it rather than each growing its own precedence, and the next group inherits it instead of writing a third.

**Where a good build should push back.** Nothing new here: `-i` mirroring `< file` and `-o` mirroring `>` were both argued in the previous build and settled there, so a build reopening either has not read what it inherited.

## Verification

Pin the `yfinance` behaviours the adapter leans on, in a dependency test kept apart from your own and marked slow because it hits the network:

- The column `MultiIndex` and its level names, `Price` over `Ticker`, on one symbol as well as several.
- That stacking the `Ticker` level yields one row per date and symbol.
- That a weekly candle is stamped on the Monday and a monthly one on the first.
- That `auto_adjust=False` returns `Adj Close` beside `Close` and that the two differ, since the whole requirement rests on picking between them.
- That a symbol Yahoo has nothing for returns `NaN` rather than raising.
- That the index converts to a `Datetime` rather than a `Date`.
- That `get_info()` omits keys rather than nulling them, on an ETF and an index as well as a stock, and returns a near-empty dict for a symbol that does not exist.
- That `Lookup` spells its methods as it does, since the one the domain word suggests is not the one that exists.
- That each of them caps at 25 unless told otherwise, which is the default that makes a search look answered.
- That `end` excludes its own date on every interval, and that an equal `start` and `end` return nothing — the two facts the inclusive bounds are built on.
- That a `1wk` request starting mid-week returns a week built from the days asked for and stamped as though it were whole, and that a `1mo` one starting after the first returns nothing for a completed month and a row stamped on the last trading day for the current one. Neither raises, and the monthly stamp is the one fact that breaks the tool's own rule about what a `date` means.

**The default run must not touch the network.**
Record one response covering two symbols on different exchanges, keep it beside the tests as a data file, and parse that.
One exchange is the fixture that never has a null in it, so it is the fixture under which the dense grid, the drop rule and the missing-symbol check all pass by accident.

**A recorded response is by definition one that worked**, so run the real surface once before calling the build done and read the **counts** — the three timeframes against the symbols asked for when all three are named, eleven columns against every kind of instrument.
A symbol that came back empty has passed every check the program can make on itself.
The six the brief names — a stock, an ETF, an index, a future, a coin and a currency pair — are the run that matters, because five of them are missing fields the sixth has.

## Wrong turns

- **Resampling dailies into weeks and months**, a transform invented for a problem the data source already solves.
- **A `direction` or `change` column carrying what the colour says**, which is the one thing `--pretty` is forbidden to do.
- **One bar scale across the whole table**, so a heavy day for a thinly traded symbol renders as nothing beside a liquid one.
- **Passing the caller's dates straight into a weekly or monthly request**, which answers with a partial week wearing a whole week's date, or with no month at all.
- **A call per timeframe stitched together by the caller**, leaving the core to concatenate what the adapter should have returned whole.
- **Taking `yfinance`'s defaults**, so the closes are dividend-adjusted and the history is one month, and every test still passes.
- **Keeping `Adj Close`**, which leaves the number the brief rejected in the frame beside the one it asked for.
- **A bare `.drop_nulls()`**, which throws away a real candle in order to remove a phantom one.
- **A silently short result** where a symbol returned nothing, because the library reported it on a logger instead of raising.
- **The missing-symbol check written into both functions**, where a decorator over the arguments and the return does it once.
- **A second error hierarchy for this source**, when one boundary's vocabulary is the tool's.
- **Forwarding `**kwargs` to `yfinance.download`**, which makes the library's signature the adapter's interface and hands back the one argument the adapter existed to fix.
- **`reset_index()` before converting** — or converting without `include_index=True`, which loses the date and the symbol outright.
- **A `Datetime` stamp left uncast**, so a value printing as a date fails to join against one.
- **A leaky adapter**: tidying in `pandas` past what the `MultiIndex` forces, reaching back into the original frame mid-chain, typing the incoming frame as `object` with a `# type: ignore`, or letting the upstream's empty shape reach the core.
- **Reading stdin only when a flag says so.** Taking a path where one is named and standard input otherwise is what makes the two commands compose.
- **A renderer per command**, so eight columns and one column are rendered by two functions that agree only by accident.
- **A heading row on the plain form**, which turns `trade index get-symbols dow-jones | trade symbol get-candles` into a request for a symbol literally spelled `symbol`.
- **Leaking `yfinance`'s interval spelling into the `timeframe` column**, so `1wk` reaches a caller who was promised `weekly` and the adapter's reference table has been published as the interface.
- **Interval strings written into the adapter**, where the table of domain name against library argument belongs in `data/adapt/`.
- **Sorting in the renderer**, which leaves the frame the core computes on in whatever order the source happened to return.
- **Subscripting a field `get_info()` does not always carry**, so an ETF or an index fails on a raw `KeyError` where a stock passed.
- **Letting `polars` infer the market capitalisation**, so the column's type depends on which symbols were asked about and two runs will not concatenate.
- **The eleven fields written into the adapter**, when the brief made the set the user's to change without opening code.
- **`getattr(lookup, f"get_{kind}")`**, which trades a checked mapping for a runtime `AttributeError` — and `get_crypto`, which is what that guess produces and is not a method.
- **Three adapter packages for one library**, tripling the failure conversion and the naming to draw a boundary that is not there.
- **Treating a search that matched nothing as a failure**, when not finding something is what searching for it risks.
- **An operation taking names where its seam begins at symbols**, so it rebuilds its own input and carries ports it never calls.
- **Passing `--end` straight to `yfinance`**, so every run quietly loses its last candle and a single-day request returns nothing.
- **A flag per timeframe**, or a branch per timeframe behind one flag, turning the `timeframe` axis into control flow.
- **Paging a search to reach `--count`**, which was a ceiling all along.
