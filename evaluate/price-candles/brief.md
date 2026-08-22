# Price candles brief

Carry on from the symbols tool, the one that expands an index name into the symbols it holds.
If you are starting without it, build that much first, since I still want to name an index rather than list it out.

Now I want the price candles behind those symbols, so I can start computing on them.

## Tickers

Any number of them, given whichever way suits what I am doing at the time.

- Written out as arguments.
- Read from a file I name.
- Piped or redirected in on standard input, so `demark symbols dow-jones | demark candles` just works.

An index name stands in for its constituents, the way the symbols command already resolves it.

I will hand you the same ticker twice without meaning to, since two funds hold the same stock and I have piped both in.
I want it back once.

## Candles

One row per ticker, timeframe and date, carrying the open, high, low and close.

All three timeframes come back on every run.
I am reading them against each other, so a run that served me one of them is a run I have to do three times.

Give me the prices at the precision a price chart shows rather than whatever tail a float carries.
Four decimal places is more than I need and everything past it is noise I have to read around.

A day a ticker did not trade is not a row.
Markets keep different holidays, so asking for a London stock and a New York one together covers days one of them was shut, and I want that gap absent rather than sitting there empty.

Give them to me in a settled order, so I can diff two runs and read what changed.

If I name a ticker and nothing comes back for it, that fails the run and tells me which one, the same way one unknown name fails the symbols command.
A short table is the dangerous outcome, because nothing downstream can tell it apart from a stock that genuinely stopped trading.

## Prices

Fetch them with `yfinance`, at each timeframe directly.
It serves daily, weekly and monthly, so there is no need to derive one from another.
Prices should be split-adjusted but not dividend-adjusted, so the numbers match what a price chart shows.
Fetch fresh on every run and don't build a cache.

Candles follow what a chart shows.
Every past week and month is a **completed** candle, and only the most recent one is still in progress.
I never want a week rebuilt as it stood partway through.

## Output

The same two ways the symbols already go, to standard output for piping and to a file I name.

Whatever lands on standard output has to be readable by the tools I already have, without my writing a parser for it first.
Several columns now where the symbols had one, so that stops being obvious and needs deciding.

When I want to read it myself rather than pipe it, a `rich` table down the page, the way the symbols command already gives me one.

## Examples

```bash
demark candles AAPL
demark candles AAPL MSFT NVDA
demark symbols dow-jones | demark candles
demark candles < tickers.txt
demark candles AAPL -o aapl.csv
demark symbols ftse-100 | demark candles > ftse.csv
demark symbols ARKK | demark candles | grep AAPL
```

## Working style

Keep going in the repository the symbols tool left, and let its structure change as this build earns it.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, structuring it, writing the code and testing it.
**Work only from your skills.**
Don't draw on anything in your saved memory, and don't open the answers file sitting beside this brief — each would hand you what a good build looks like, which is the thing I am trying to find out.

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.

Write it in a functional style.
