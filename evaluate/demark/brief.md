# DeMark brief

Build me a command-line tool that reports DeMark counts for stock tickers across daily, weekly and monthly timeframes.
I use it to scan a watchlist, or a whole index, for the names that are late in a count.

## Tickers

- Tickers, given directly as a list.
- A stock index, named rather than enumerated, and expanded to its constituents.

Resolve index names with `pytickersymbols`.

For picking tickers I would rather learn one compact, glob-style syntax than memorise a separate flag for every case.
Design something intelligent and elegant, and run your design past me before you build it.

## Filters

I filter on two things, the **date** and any **count** column.
Each takes a lower bound, an upper bound or an exact value, and I expect to set several at once in a single run.
Plain options are right here, a pair of bounds per filterable column, rather than a syntax I have to learn.

Because counts are signed, one pair of bounds per column covers both directions and I never have to say which direction I mean.

The date is a filter like any other, and it is what decides which candles I am reported on.
Bound it and I get that day, or that stretch of days.
Leave it alone and it **defaults to today**.

I only ever want rows for days the market actually traded, so a weekend or a holiday is not a row.
On a day the market has not traded, today means the most recent day it did.

## Table

A `rich` table, with a column for each count on each timeframe.
A row per ticker, and a row per date as well where I have asked for a range.
Colour each cell to show whether it is a buy or a sell.

## Other uses

- Sometimes I only want an index's constituent symbols, and nothing else.
- Sometimes I want to re-filter or re-render a table I have already produced, without paying to fetch the prices again.

## Counts

Three counts for every candle, on every timeframe.

### Setup

Compare each candle's close to the close four candles earlier.

- A **sell setup** is a run of consecutive candles each closing *higher* than the close four candles before it.
- A **buy setup** is a run each closing *lower*.

Only one can be active at a time, and the run resets the moment a candle breaks it.
Report the length of the run active on the candle in question.
It runs 1 to 9 and then wraps back to 1.

### Sequential

The countdown that follows a completed setup.
Compare each candle's close to the **high or low two candles earlier**.

- A **sell** countdown counts candles closing at or above the high two candles before them.
- A **buy** countdown counts candles closing at or below the low two candles before them.

Qualifying candles need not be consecutive.
The countdown runs to 13.

A countdown can also be cut short before it gets there, and I want all three ways it happens.

- A setup completes in the opposite direction.
- The same setup recycles, meaning another setup completes in the same direction, and the new one replaces the countdown in progress.
- The setup's own true range is broken, meaning a later candle trades beyond the extreme of the nine candles that made the setup, against the direction the countdown is pointing.

### Combo

The same countdown rule, except counting begins with the setup rather than waiting for it to complete.
Also runs to 13, and is cut short the same three ways.

## Notation

Sell counts are positive and buy counts negative, on one continuum that wraps sell to buy to sell.
A single number then carries both the direction and how far along the count is, so an ordinary numeric bound picks out either end.
`>= 8` finds late sells and `<= -8` finds late buys.

Zero sits in the middle and means nothing is running, whether that is no setup on the candle or no countdown open.
A countdown that reaches 13 is finished, so the candles after it read zero until the next one opens.

## Candles

Fetch candles with `yfinance`, at each timeframe directly.
It serves daily, weekly and monthly, so there is no need to derive one from another.
I need full candles, since the countdowns compare a close against an earlier high or low.
Prices should be split-adjusted but not dividend-adjusted, so the numbers match what a price chart shows.
Fetch fresh on every run and don't build a cache.

Counts follow what a chart shows.
Every past week and month is a **completed** candle, and only the most recent one is still in progress.
So a date in the past reports the count of the completed candle covering it.
I never want a week rebuilt as it stood partway through.

## Working style

Create it as its own new git repository, at a path I will give you.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Lean on them as much as you can.
This run is partly to surface gaps in the skills, so where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
