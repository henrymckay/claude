# DeMark counts brief

Carry on from the `trade` tool, the one whose `symbol` group fetches daily, weekly and monthly candles for a list of tickers.
If you are starting without it, build that much first, since the counts have nothing to run over otherwise.

Now I want DeMark counts over those candles, and a table I can scan a whole index with.

A third group, `demark`, beside the `index` and `symbol` groups already there.
Nothing in either of them moves or is renamed to make room for it.

Tickers reach it exactly the way `trade symbol candles` already takes them, as arguments, from a file I name, or on standard input — including an index name standing in for its constituents, and a ticker I have handed you twice coming back once.

## Filters

Every column but the symbol, so the date and each count on each timeframe.

One option per filterable column, taking a lower bound and an upper bound, both inclusive.
Give the same value twice to ask for exactly that one.

```bash
trade demark count AAPL --daily-setup -13 -8
trade demark count AAPL --daily-setup -9 -9
trade demark count AAPL --date 2026-01-01 2026-03-01
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

It goes out the same ways `trade symbol candles` already goes, spelled the same way — plainly to standard output for piping, to a file I name, or rendered down the page with `rich` when I want to read it myself.

The `rich` one differs in more than styling.
Plain output carries the sign, where the `rich` table shows every count positive and lets the colour say which it is, red for a sell and green for a buy.

## Commands

Four in the group.

- `trade demark count` reports all three counts together.
- `trade demark setup`, `trade demark sequential` and `trade demark combo` each report one on its own.

Every one of them takes tickers the three ways above, carries the same filters, and answers the same ways.

## Output

The same table, the same two options and the same plain form the other groups already answer with — comma-separated, no heading row, columns in alphabetical order, `-o` to a file I name and `-t` for a `rich` table.

**The column names for this group are not settled.**
I will pin them down the way I have for `index` and `symbol`; until I do, take what the Table section describes above and treat neither the names nor their spelling as fixed.

## Not in this build

I also want to re-filter or re-render a table I have already produced, without paying to fetch the prices again.
I have not settled how that should reach me, so leave it out — no option, no command and no file format decided for it.
It is written down here so that neither of us forgets it, not so that you build it.

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

## Examples

```bash
trade demark count AAPL
trade demark count AAPL MSFT NVDA
trade demark setup AAPL
trade demark sequential NVDA --weekly-sequential 11 13
trade demark combo NVDA
trade index expand sp-500 | trade demark count --daily-setup -9 -9
trade index expand dow-jones | trade demark count -o counts.csv
trade demark count < tickers.txt
trade demark count AAPL --date 2026-01-01 2026-03-01 --monthly-setup 8 9
```

## Working style

Keep going in the repository the `symbol` group left, and let its structure change as this build earns it.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, structuring it, writing the code and testing it.
**Work only from your skills.**
Don't draw on anything in your saved memory, and don't open the answers file sitting beside this brief — each would hand you what a good build looks like, which is the thing I am trying to find out.

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.

Write it in a functional style.
