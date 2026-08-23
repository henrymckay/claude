# Symbol data brief

Carry on from the `trade` tool, the one whose `index` group expands an index into the symbols it holds.
If you are starting without it, build that much first, since I still want to give an index rather than list its symbols out.

Now I want the tool to say things about the symbols themselves — what they cost, what they are, and how to find one when I do not know its symbol.

A second group, `symbol`, beside the `index` group already there.
Nothing in the first group moves or is renamed to make room for it.

## Symbols

`get-candles` and `get-info` take any number of symbols, given whichever way suits what I am doing at the time.

- Written out as arguments.
- Read from a file I name.
- Piped or redirected in on standard input, so `trade index get-symbols dow-jones | trade symbol get-candles` just works.

These are symbols, not indices, and nothing here expands one.
`trade symbol get-candles SMH` gives me the candles for SMH itself, which I can go and buy, never for the twenty-five stocks it holds.
An index reaches these commands by being expanded first, so `trade index get-symbols SMH | trade symbol get-candles` is how I ask for the holdings.

I would rather type the pipe than have the tool guess which of the two I meant.
Most of what my catalogue names is tradeable in its own right, so a guess would be wrong about as often as it was right, and I would not be able to tell which had happened.

I will hand you the same symbol twice without meaning to, since two funds hold the same stock and I have piped both in.
I want it back once.

If I give a symbol and nothing comes back for it, that fails the run and tells me which one, the same way one unknown index fails `trade index get-symbols`.
A short table is the dangerous outcome, because nothing downstream can tell it apart from a stock that genuinely stopped trading.
This holds for `get-candles` and for `get-info` alike.

`look-up` is the exception to all of it: what it takes is the thing I am searching for, which is not a symbol and does not arrive any of those ways.
A search that matches nothing is an answer rather than a failure, since not finding something is what searching for it risks.

## Candles

One row per symbol, timeframe and date, carrying the open, high, low and close.

All three timeframes come back unless I ask for fewer.
I am usually reading them against each other, so a run that served me one of them by default would be a run I have to do three times.

Give me the prices at the precision a price chart shows rather than whatever tail a float carries.
Four decimal places is more than I need and everything past it is noise I have to read around.

A day a symbol did not trade is not a row.
Markets keep different holidays, so asking for a London stock and a New York one together covers days one of them was shut, and I want that gap absent rather than sitting there empty.

Give them to me in a settled order, so I can diff two runs and read what changed.

## Prices

Fetch them with `yfinance`, at each timeframe directly.
It serves daily, weekly and monthly, so there is no need to derive one from another.
Prices should be split-adjusted but not dividend-adjusted, so the numbers match what a price chart shows.
Fetch fresh on every run and don't build a cache.

Candles follow what a chart shows.
Every past week and month is a **completed** candle, and only the most recent one is still in progress.
I never want a week rebuilt as it stood partway through.

## Info

What each symbol *is*, rather than what it costs.

One row per symbol, carrying that symbol, its short name and its long name, the exchange and the market it trades on, its currency, what kind of instrument it is, its market capitalisation, and its sector and industry.
Eleven columns, the same eleven every run.

Yahoo hands back a couple of hundred fields per symbol and I want those eleven.
Which eleven is mine to change and I should be able to change it without opening any code.

Not every symbol carries every field — an index has no sector and a currency pair has no market capitalisation.
I want those empty rather than the column missing, because I am reading a whole scan down the page and a column that comes and goes is worse than one with holes in it.

I ask about six kinds of thing and expect the same shape back from all of them: a stock, an ETF, an index, a future, a coin and a currency pair.
`NVDA`, `SMH`, `^NDX`, `GC=F`, `BTC-USD` and `GBP=X` are the six I check with.

## Lookup

Finding a symbol when I do not know it.

Give it something to search for and it gives me back what Yahoo matches: the symbol, the short name, the exchange it trades on, what kind of instrument it is, and where Yahoo ranked it.
Leave them in Yahoo's ranking, since that ranking is most of what a search is for.

Let me narrow it to one kind of instrument, or leave it alone and take every kind.
The kinds are the ones `get-info` reports, plus mutual funds.

A hundred matches unless I ask for more, since I am looking for something rather than listing everything.

Searching is also how I enumerate a whole asset class, because Yahoo spells the kind into the symbol: `^` finds indices, `=X` currencies, `=F` futures and `-USD` coins.
That is a fact about Yahoo rather than something to build around, but it is why the count is mine to raise and why the kind is a filter I set rather than something guessed from what I typed.

## Commands

Three in the group.

- `trade symbol get-candles [SYMBOL...]` gives me the price candles behind those symbols.
- `trade symbol get-info [SYMBOL...]` gives me what each symbol is.
- `trade symbol look-up QUERY` finds symbols I could then ask about.

## Output

The same table, the same two options and the same plain form `trade index get-symbols` already answers with — comma-separated, no heading row, columns in alphabetical order.
`-o` writes to a file I name and `-p` shows a `rich` table, spelled exactly as they already are.
Several columns now where the symbols had one, and that is the only thing that changes.

- `get-candles` has `close`, `date`, `high`, `low`, `open`, `symbol`, `timeframe` and `volume`.
- `get-info` has `country`, `currency`, `full_exchange_name`, `industry`, `long_name`, `market`, `market_cap`, `quote_type`, `sector`, `short_name` and `symbol`.
- `look-up` has `exchange`, `quote_type`, `rank`, `short_name` and `symbol`.

Yahoo spells its fields in camel case and I do not want to read them that way, so `fullExchangeName` reaches me as `full_exchange_name`.

`timeframe` says which timeframe the row is, in the words I use for them — `daily`, `weekly` and `monthly` — rather than however `yfinance` spells its argument.
That spelling is between you and the library and I should never see it.

`date` is the day the candle's period **begins**: the Monday for a weekly row and the first of the month for a monthly one, not a day somewhere inside the period and not the day it ended.

## Arguments and options

`get-candles` and `get-info` take any number of symbols as arguments, or none at all where the symbols arrive on standard input or from a file.
`look-up` takes exactly one thing to search for.

Every option has a long form and a single-letter short form, and an option meaning the same thing keeps the same spelling in every command of the tool.

Common to every command, as they already are in the `index` group:

- `-o`, `--output PATH` writes to that file instead of standard output.
- `-p`, `--pretty` shows a `rich` table instead of the plain default.

On `get-candles` and `get-info`, which both take symbols:

- `-i`, `--input PATH` reads the symbols from that file rather than from standard input.

On `get-candles`:

- `-s`, `--start DATE` is the earliest date I want back.
- `-e`, `--end DATE` is the latest.
- `-t`, `--timeframe` picks a timeframe, given once per timeframe I want: `-t daily -t weekly`.

Both bounds are **inclusive**, so naming the same date twice asks for that one day and gets it back rather than nothing.
A candle is in range when its `date` is, so a weekly row is in or out by the Monday its week began.
Leave `--start` off and I get as far back as Yahoo will go; leave `--end` off and I get everything up to today.
Here they are the whole of what gets fetched, since there is nothing to work out that needs more than I asked for.
Leave `--timeframe` off and I get all three.

On `look-up`:

- `-k`, `--kind` narrows the search to one kind of instrument; leaving it off searches every kind.
- `-c`, `--count N` is the most matches I want back, a hundred if I do not say.

## Examples

```bash
trade symbol get-candles AAPL
trade symbol get-candles AAPL MSFT NVDA
trade index get-symbols dow-jones | trade symbol get-candles
trade symbol get-candles < symbols.txt
trade symbol get-candles AAPL -o aapl.csv
trade symbol get-candles AAPL -t daily -t weekly
trade symbol get-candles AAPL --timeframe monthly --start 2020-01-01
trade symbol get-candles AAPL MSFT -s 2026-06-01 -e 2026-06-30
trade symbol get-candles -i symbols.txt -t daily
trade index get-symbols ftse-100 | trade symbol get-candles > ftse.csv

trade symbol get-info NVDA
trade symbol get-info NVDA SMH '^NDX' 'GC=F' 'BTC-USD' 'GBP=X'
trade index get-symbols ARKK | trade symbol get-info
trade index get-symbols largest-companies | trade symbol get-info -o scan.csv

trade symbol look-up nvidia
trade symbol look-up '^' --kind index
trade symbol look-up '=X' --kind currency
trade symbol look-up 'VANECK UCITS' --kind etf --count 200
trade symbol look-up nvidia --kind stock | cut -d, -f5 | trade symbol get-candles
```

## Working style

Keep going in the repository the `index` group left, and let its structure change as this build earns it.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, structuring it, writing the code and testing it.
**Work only from your skills.**
Don't draw on anything in your saved memory, and don't open the answers file sitting beside this brief — each would hand you what a good build looks like, which is the thing I am trying to find out.

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.

Write it in a functional style.
