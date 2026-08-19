# Report brief

Carry on from the counts tool.
Now I want to read the counts as a table and scan a whole index for the names that are late in one.

## Filters

Every column but the symbol, so the date and each count on each timeframe.

One option per filterable column, taking a lower bound and an upper bound, both inclusive.
Give the same value twice to ask for exactly that one.

```bash
demark counts AAPL --daily-setup -13 -8
demark counts AAPL --daily-setup -9 -9
demark counts AAPL --date 2026-01-01 2026-03-01
```

I expect to set several at once in a single run, and every one of them has to hold.
Because counts are signed, one option per column covers both directions and I never have to say which direction I mean.

The date is a filter like any other, and it decides which candles I am reported on.
Leave it alone and it **defaults to today**.

I only ever want rows for days the market actually traded, so a weekend or a holiday is not a row.
On a day the market has not traded, today means the most recent day it did.

## Table

A column for the date and a column for the symbol, then one for each count on each timeframe.
A row per symbol, and a row per date as well where I have asked for a range.

The same table has to go three ways.

- Rendered prettily at the terminal with `rich`.
- Written to a file I name.
- Written plainly to standard output, so I can pipe it into another command or redirect it.

The pretty one differs in more than styling.
Plain output carries the sign, where the `rich` table shows every count positive and lets the colour say which it is, red for a sell and green for a buy.

## Dates on a coarser candle

A date in the past reports the count of the **completed** candle covering it.
Ask about a Wednesday and the weekly column gives me that whole week as it finished, never the week rebuilt as it stood partway through.

## Other uses

I also want to re-filter or re-render a table I have already produced, without paying to fetch the prices again.

## Working style

Keep going in the same repository, and let its structure change as this rung earns it.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
