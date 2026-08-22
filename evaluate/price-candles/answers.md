# Price candles answers

The design a good build reaches, and the wrong turns that miss it.
None of it appears in the brief — each line is something the skills alone should produce.

## The shape

A second source, and the first shape the core genuinely owns.

| shape | one row is | how it is reached |
|---|---|---|
| symbols | one symbol | rung 1, unchanged |
| candles | a ticker's candle in one timeframe | fetch each timeframe directly |

**There is no resample step.** `yfinance` serves daily, weekly and monthly, so the adapter returns one long frame already carrying a timeframe column, and Yahoo's own week and month alignment is used rather than a reinvented one.
Deriving coarser candles from dailies is a transform the problem does not need, and it adds a seam that then has to be threaded through every later rung.

**Timeframe is a column, not something the caller stitches together.** The adapter makes one call per interval because the API has no other shape, concatenates them itself, and hands back a single frame.
A `concat` over a comprehension is only the per-group-loop mistake when the groups are computation; here each group is its own network call.

**The stamp is the candle's start, and naming it so is what makes the completed-candle rule true rather than checked.**
Yahoo stamps a weekly candle on the Monday and a monthly one on the first of the month, so the column is `start` — the beginning of the period the row covers, not a day the row is about.
Call it `date` and the next rung reads it as one, at which point asking a Wednesday for its weekly figure needs a rule nobody wrote down.

**The adapter spells the columns in the domain's words, in one expression over the whole schema.**
Yahoo publishes CamelCase and a space in `Adj Close`; the frame leaving the adapter carries neither.
Rename through `polars.all().name.map(...)` rather than a dict naming every column, so a field the source adds arrives spelled correctly instead of waiting for someone to find the dict — the same reason `use-polars` prefers a selector to a hand-written list.

**Volume comes back too, though the brief names only the open, high, low and close.**
`structure-python` settles an adapter's columns against the **source**, not today's caller: volume is published, the domain has a name for it, and the costs are asymmetric — dropping a column later is one line in the core, where widening means revisiting the adapter, its tests and the recorded response.
"Build what the brief asks for and no more" bounds the *surface* — no option nobody asked for, no stage nobody wanted — and the shape an adapter declares is not part of that surface.

## What the build earns

**A second port, and with it an `operate` package.** The symbols build already defines a port for holdings; fetching candles is a second thing the core needs from outside, so it gets its own rather than being bent through the first.
Two use cases is also where the operations stop being loose functions, so the package the last build did not earn is earned here.

**A format option, replacing the previous rung's `--table` boolean.**
One column made the boolean honest: there were two forms and a flag picked between them.
Five columns means the machine form has to be *named* — whether it has a header, what separates the fields, what happens to a value carrying the separator — and once that is a decision, a flag called `--table` is answering a question it never asks.
So the option takes a format, `csv` by default because that is the form the tools beside it already read, and `table` for the `rich` render.
This is the previous rung's own note coming due, and it reaches back: the symbols command grows the same option rather than keeping its boolean, because a tool whose second command re-spells its first command's options is one nobody can use from memory.

## What should not exist yet

- **No date range, no filtering, no counts.** The brief asks for candles, and a `--from`/`--to` pair added now is a guess at the next build rather than a requirement of this one.
- **No caching.** Candles change daily and the brief says nothing about storing them, so a build that adds a cache has invented a requirement and a cache invalidation problem with it.
- **No timeframe option.** The brief names three and asks for all three every run; an option to pick one is a capability nobody wanted, on a public surface that then has to keep it.
- **No abstraction over price sources.** The core needs candles from outside, which is a port; one named source behind it is not a family, and a registry, a provider protocol or a `--source` flag is machinery for a set that has one member and no way to gain another.

## The boundary

This is where `pandas` meets `polars` and the rung is mostly judged on it.

**Every default `yfinance.download` carries is wrong for this build, and each one fails quietly.**

- `auto_adjust` defaults to **`True`**, which is the dividend-adjusted close — precisely what the brief rules out.
Pass `False`.
Measured over one month of `AAPL`, the two closes differ by up to 0.95, so a build that leaves the default is not slightly off; it is answering a different question with numbers that look right.
- `period` defaults to **one month** when no `start`/`end` is given.
Not naming it returns twenty-odd daily candles and looks exactly like a fetch that worked.
With no date range on the surface, the adapter asks for the source's full history and says so.
- `progress` defaults to **on**, writing a bar to standard error — a library narrating on a channel the driver owns, which is the same objection `structure-python` makes to a library calling `logging.basicConfig`.
Off.
- `timeout` is already ten seconds and `rounding` already exists.
Both are things `structure-python` and `write-python` would have you add; go and look before writing either yourself.

**`auto_adjust=False` also brings `Adj Close` back**, sitting in the frame beside `Close` and holding the rejected number under a name nobody will question.
Select the columns you declared rather than keeping what arrived.

**A ticker Yahoo has nothing for does not raise.**
It comes back as a block of columns full of `NaN` — an empty frame if it was the only one asked for — and the only sign is a line on the library's own logger.
So the adapter compares what came back against what it asked for, because nothing else in the program can: once the nulls are gone the ticker has simply vanished, and the short table that results is indistinguishable from a stock that stopped trading.
This is the previous rung's all-or-nothing rule arriving from a source that will not raise for you.

**The download is a dense grid over the union of every ticker's trading days**, not one row per candle.
Ask for a London stock and a New York one and every day either market was shut carries a row for the other.
Those nulls are what the reshape exists to remove, and a fixture holding one ticker never contains one.

**The null test is over the candle, not the row.**
`.drop_nulls()` is the reflex and it is wrong twice: it throws away a real candle wherever the source left a single field off, and it never says which absence was meant.
Drop where the price fields are *all* null — that is "this ticker did not trade" — and leave a candle with a gap in it for the core to judge.
On one live three-month fetch of two tickers, four rows were absent candles and one was a real candle with no close, and the reflex cannot tell them apart.

**The one thing that must happen in `pandas` is dissolving an index `polars` cannot represent** — and it is a single `stack` on the **ticker** level.
The columns arrive as a `MultiIndex` of `Price` over `Ticker`, and stacking that one level lands directly on the shape you want: a row index of date and ticker, a column per field.
Melting all the way to long and pivoting back on the `polars` side reaches the same frame after two more reshapes.

**`reset_index()` is not forced, and reaching for it costs twice.**
`polars.from_pandas(frame, include_index=True)` brings both index levels across as columns, so calling `reset_index` first is one more `pandas` operation doing what the converter already does — and omitting that argument instead **drops the date and the ticker silently**, leaving the values with nothing to say which row is which.

**The stamp arrives as a timestamp, not a date.**
The index is `datetime64[s]` and converts to a `polars` `Datetime`, so a midnight value that prints like a date is not equal to one.
Cast it at the boundary; the next rung joins a daily row against a weekly one on exactly this column.

**`polars.from_pandas` needs `pyarrow`, and not only in a corner case.**
Recent `pandas` backs a string column with arrow, so the ticker column alone is enough to raise `ImportError` without it.
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
The frame leaves the adapter sorted by ticker and start, because every window the next rung writes reads the frame in its current row order and nothing raises on an unsorted input.
The brief asking for a settled order is the same requirement arriving from the other end, and satisfying it in the renderer satisfies only the half that shows.

**`threads` is on by default, so one call is many requests.**
An index expansion is five hundred tickers in a single `download`, which is where a publisher's rate limit is found rather than in any test.

## The surface

Tickers arrive three ways and the tool must not care which: as arguments, from a named file, or on standard input.
That last one is the whole point of the build — it is what makes `symbols dow-jones | candles` work, and a tool that only reads arguments has to be wrapped by the caller to get there.

Read standard input when no tickers are named, rather than behind a flag that says to.
A flag would mean the pipeline only composes for someone who already knows the flag exists.

**Normalise the tickers once, where they arrive.**
Three input routes are three chances for whitespace, case and repetition to differ, and the brief asks for a symbol back once however many times it was given.
Doing it at the boundary is what stops each route growing its own version.

Candles go out the same two ways the symbols already do, and the options are spelled the way they already were — the destination is `-o`/`--output`, and an input path is spelled after it.
Spelling the same idea differently between two commands of one tool is the cheapest possible thing to get wrong and the most irritating to live with.

**Where a good build should push back.** A named input file does nothing that `< file` does not, exactly as `-o` mirrors `>` in the previous build — worth saying, worth building anyway.

## Verification

Pin the `yfinance` behaviours the adapter leans on, in a dependency test kept apart from your own and marked slow because it hits the network:

- The column `MultiIndex` and its level names, `Price` over `Ticker`, on one ticker as well as several.
- That stacking the ticker level yields one row per date and ticker.
- That a weekly candle is stamped on the Monday and a monthly one on the first.
- That `auto_adjust=False` returns `Adj Close` beside `Close` and that the two differ, since the whole requirement rests on picking between them.
- That a ticker Yahoo has nothing for returns `NaN` rather than raising.
- That the index converts to a `Datetime` rather than a `Date`.

**The default run must not touch the network.**
Record one response covering two tickers on different exchanges, keep it beside the tests as a data file, and parse that.
One exchange is the fixture that never has a null in it, so it is the fixture under which the dense grid, the drop rule and the missing-ticker check all pass by accident.

**A recorded response is by definition one that worked**, so run the real surface once before calling the build done and read the **counts** — three timeframes against the tickers asked for.
A ticker that came back empty has passed every check the program can make on itself.

## Wrong turns

- **Resampling dailies into weeks and months**, a transform invented for a problem the data source already solves.
- **A call per timeframe stitched together by the caller**, leaving the core to concatenate what the adapter should have returned whole.
- **Taking `yfinance`'s defaults**, so the closes are dividend-adjusted and the history is one month, and every test still passes.
- **Keeping `Adj Close`**, which leaves the number the brief rejected in the frame beside the one it asked for.
- **A bare `.drop_nulls()`**, which throws away a real candle in order to remove a phantom one.
- **A silently short result** where a ticker returned nothing, because the library reported it on a logger instead of raising.
- **Forwarding `**kwargs` to `yfinance.download`**, which makes the library's signature the adapter's interface and hands back the one argument the adapter existed to fix.
- **`reset_index()` before converting** — or converting without `include_index=True`, which loses the date and the ticker outright.
- **A `Datetime` stamp left uncast**, so a value printing as a date fails to join against one.
- **A leaky adapter**: tidying in `pandas` past what the `MultiIndex` forces, reaching back into the original frame mid-chain, typing the incoming frame as `object` with a `# type: ignore`, or letting the upstream's empty shape reach the core.
- **Reading stdin only when a flag says so.** Taking a path where one is named and standard input otherwise is what makes the two commands compose.
- **Carrying the previous rung's `--table` boolean onto five columns**, so the machine form was never named and nobody decided whether it has a header.
- **Interval strings written into the adapter**, where the table of domain name against library argument belongs in `data/adapt/`.
- **Sorting in the renderer**, which leaves the frame the core computes on in whatever order the source happened to return.
