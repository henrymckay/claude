# Symbol data brief

Carry on from the `trade` tool, the one whose `index` group expands a collection name into the symbols it holds.
If you are starting without it, build that much first, since I still want to name an index rather than list it out.

Now I want the tool to say things about the symbols themselves — what they cost, what they are, and how to find one when I do not know its ticker.

## Commands

A second group, `symbol`, beside the `index` group already there.
Nothing in the first group moves or is renamed to make room for it.

- `trade symbol candles [TICKER...]` gives me the price candles behind those tickers.
- `trade symbol info [TICKER...]` gives me what each ticker is.
- `trade symbol lookup QUERY` finds tickers I could then ask about.

## Tickers

`candles` and `info` take any number of them, given whichever way suits what I am doing at the time.

- Written out as arguments.
- Read from a file I name.
- Piped or redirected in on standard input, so `trade index expand dow-jones | trade symbol candles` just works.

An index name stands in for its constituents, the way `trade index expand` already resolves it.

I will hand you the same ticker twice without meaning to, since two funds hold the same stock and I have piped both in.
I want it back once.

If I name a ticker and nothing comes back for it, that fails the run and tells me which one, the same way one unknown name fails `trade index expand`.
A short table is the dangerous outcome, because nothing downstream can tell it apart from a stock that genuinely stopped trading.
This holds for `candles` and for `info` alike.

`lookup` is the exception to all of it: what it takes is the thing I am searching for, which is not a ticker and does not arrive any of those ways.
A search that matches nothing is an answer rather than a failure, since not finding something is what searching for it risks.

## Candles

One row per ticker, timeframe and date, carrying the open, high, low and close.

All three timeframes come back on every run.
I am reading them against each other, so a run that served me one of them is a run I have to do three times.

Give me the prices at the precision a price chart shows rather than whatever tail a float carries.
Four decimal places is more than I need and everything past it is noise I have to read around.

A day a ticker did not trade is not a row.
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

What each ticker *is*, rather than what it costs.

One row per ticker, carrying its symbol, its short name and its long name, the exchange and the market it trades on, its currency, what kind of instrument it is, its market capitalisation, and its sector and industry.
Eleven columns, the same eleven every run.

Yahoo hands back a couple of hundred fields per ticker and I want those eleven.
Which eleven is mine to change and I should be able to change it without opening any code.

Not every ticker carries every field — an index has no sector and a currency pair has no market capitalisation.
I want those empty rather than the column missing, because I am reading a whole scan down the page and a column that comes and goes is worse than one with holes in it.

I ask about six kinds of thing and expect the same shape back from all of them: a stock, an ETF, an index, a future, a coin and a currency pair.
`NVDA`, `SMH`, `^NDX`, `GC=F`, `BTC-USD` and `GBP=X` are the six I check with.

## Lookup

Finding a ticker when I do not know it.

Give it something to search for and it gives me back what Yahoo matches: the symbol, the name, the exchange it trades on, what kind of instrument it is, and where Yahoo ranked it.
Leave them in Yahoo's ranking, since that ranking is most of what a search is for.

Let me narrow it to one kind of instrument, or leave it alone and take every kind.
The kinds are the ones `info` reports, plus mutual funds.

A hundred matches unless I ask for more, since I am looking for something rather than listing everything.

Searching is also how I enumerate a whole asset class, because Yahoo spells the kind into the symbol: `^` finds indices, `=X` currencies, `=F` futures and `-USD` coins.
That is a fact about Yahoo rather than something to build around, but it is why the count is mine to raise and why the kind is a filter I set rather than something guessed from what I typed.

## Output

The same two ways `trade index expand` already goes, to standard output for piping and to a file I name.
All three commands answer the same way as each other.

Whatever lands on standard output has to be readable by the tools I already have, without my writing a parser for it first.
Several columns now where the symbols had one, so that stops being obvious and needs deciding.

When I want to read it myself rather than pipe it, a `rich` table down the page, the way `trade index expand` already gives me one.

## Examples

```bash
trade symbol candles AAPL
trade symbol candles AAPL MSFT NVDA
trade index expand dow-jones | trade symbol candles
trade symbol candles < tickers.txt
trade symbol candles AAPL -o aapl.csv
trade index expand ftse-100 | trade symbol candles > ftse.csv

trade symbol info NVDA
trade symbol info NVDA SMH '^NDX' 'GC=F' 'BTC-USD' 'GBP=X'
trade index expand ARKK | trade symbol info
trade index expand largest-companies | trade symbol info -o scan.csv

trade symbol lookup nvidia
trade symbol lookup '^' --kind index
trade symbol lookup '=X' --kind currency
trade symbol lookup 'VANECK UCITS' --kind etf --count 200
trade symbol lookup nvidia --kind stock | trade symbol candles
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
