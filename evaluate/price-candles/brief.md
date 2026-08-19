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

## Candles

One row per ticker, timeframe and date, carrying the open, high, low and close.

I want them to go the same two ways the symbols do, to standard output for piping and to a file I name.

## Prices

Fetch them with `yfinance`, at each timeframe directly.
It serves daily, weekly and monthly, so there is no need to derive one from another.
Prices should be split-adjusted but not dividend-adjusted, so the numbers match what a price chart shows.
Fetch fresh on every run and don't build a cache.

Candles follow what a chart shows.
Every past week and month is a **completed** candle, and only the most recent one is still in progress.
I never want a week rebuilt as it stood partway through.

## Working style

Keep going in the same repository, and let its structure change as this rung earns it.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
