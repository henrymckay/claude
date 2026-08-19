# DeMark counts brief

Carry on from the candles tool.
Now I want DeMark counts over those candles, and a table I can scan a whole index with.

Tickers reach it the way the candles tool already takes them, as arguments, from a file I name, or on standard input.

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

## Commands

- Report all three counts together.
- Report one count on its own, with a command each for setup, sequential and combo.

I also want to re-filter or re-render a table I have already produced, without paying to fetch the prices again.

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

It can also be cut short before it gets there, and I want all three ways that happens.

- A setup completes in the opposite direction.
- The same setup recycles, meaning another setup completes in the same direction, and the new one replaces the countdown in progress.
- The setup's own true range is broken, meaning a later candle trades beyond the extreme of the nine candles that made the setup, against the direction the countdown is pointing.

### Combo

The same countdown rule, except counting begins with the setup rather than waiting for it to complete.
Also runs to 13, and is cut short the same three ways.

## Notation

Buy counts are positive and sell counts negative, on one continuum that wraps buy to sell to buy.
A single number then carries both the direction and how far along the count is, so one pair of bounds picks out either end.
`8 9` finds late buys and `-9 -8` finds late sells, neither needing a flag to say which I meant.

Zero sits in the middle and means nothing is running, whether that is no setup on the candle or no countdown open.
A countdown that reaches 13 is finished, so the candles after it read zero until the next one opens.

The `rich` table is the one exception, showing every count positive and leaving the colour to carry the direction.

## Dates on a coarser candle

A date in the past reports the count of the **completed** candle covering it.
Ask about a Wednesday and the weekly column gives me that whole week as it finished, never the week rebuilt as it stood partway through.

## Working style

Keep going in the same repository, and let its structure change as this build earns it.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
