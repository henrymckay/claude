# DeMark counts brief

Carry on from the `trade` tool, the one whose `symbol` group fetches daily, weekly and monthly candles for a list of symbols.
If you are starting without it, build that much first, since the counts have nothing to run over otherwise.

Now I want DeMark counts over those candles, so I can start scanning a whole index with them.

A third group, `demark`, beside the `index` and `symbol` groups already there.
Nothing in either of them moves or is renamed to make room for it.

Symbols reach it exactly the way `trade symbol get-candles` already takes them, as arguments, from a file I name, or on standard input, and a symbol I have handed you twice coming back once.
They are symbols, not indices: an index reaches this group the same way it reaches `trade symbol get-candles`, by being expanded first.

## Dates and timeframes

Two bounds and a timeframe, spelled exactly as `trade symbol get-candles` spells them.

- `-s`, `--start DATE` is the earliest date I want back.
- `-e`, `--end DATE` is the latest.
- `-i`, `--interval` picks a timeframe, given once per timeframe I want.

Both bounds are inclusive, and naming the same date twice asks for that one day.
Leave `--end` off and it **defaults to today**; leave `--start` off and it means that same day alone, since a single day is what I want most of the time.
Leave `--interval` off and I get all three.

The dates decide which candles I am reported on, and they are not the whole story of what has to be fetched — a count is only right if the candles before it were counted too.

I only ever want rows for days the market actually traded, so a weekend or a holiday is not a row.
On a day the market has not traded, today means the most recent day it did.

## Filtering

**Not here.**

What I am ultimately after is a symbol with an early sell setup on the weekly *and* a late buy setup on the daily, both true at once — a claim about a symbol across several rows rather than a bound on any one column, and a build of its own.
It comes in the build after this one, so leave it out entirely: no option, no column of its own, and no filtering behind the fetch bounds above.

## Commands

Four in the group.

- `trade demark count` reports all three counts together.
- `trade demark count-setup`, `trade demark count-sequential` and `trade demark count-combo` each report one on its own.

Every one of them takes symbols the three ways above, carries the same options, and answers the same way.

## Output

One row per date, symbol, timeframe and count, carrying that count.
Five columns, the same five every run: `count`, `date`, `indicator`, `interval` and `symbol`, alphabetically as everywhere else.

`indicator` says which count the row is — `setup`, `sequential` or `combo`.
`interval` is spelled the way `trade symbol get-candles` spells it, `daily`, `weekly` or `monthly`.

Long rather than a column per count on each timeframe, because I am asking for one timeframe as often as three and I do not want the shape of what comes back to depend on which options I gave.

It goes out the same ways `trade symbol get-candles` already goes, spelled the same way — plainly to standard output for piping, to a file I name, or rendered down the page with `rich` when I want to read it myself.

The `rich` one differs in more than styling.
Plain output carries the sign, where the `rich` table shows every count positive and lets the colour say which it is, red for a sell and green for a buy.

The `rich` table is long too.
A column per count on each timeframe is what a screen wants, and a screen is its own build.

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
trade demark count-setup AAPL
trade demark count-sequential NVDA -i weekly
trade demark count-combo NVDA
trade demark count AAPL -i daily -i weekly
trade demark count AAPL -s 2026-01-01 -e 2026-03-01
trade demark count < symbols.txt
trade demark count -f symbols.txt -t
trade index get-symbols sp-500 | trade demark count
trade index get-symbols dow-jones | trade demark count -o counts.csv
trade index get-symbols sp-500 | trade demark count-setup -i daily | awk -F, '$1 >= 8'
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
