# Screen symbols brief

Carry on from the `trade` tool, whose `demark` group counts setups, sequentials and combos over a list of symbols.
If you are starting without it, build that much first, since a screen has nothing to screen on otherwise.

Now I want to point it at a whole index and be told which symbols are worth a look.

A fourth group, `screen`, beside the three already there.
Nothing in any of them moves or is renamed to make room for it.

## What a screen is

Several conditions at once, each naming an indicator on a timeframe and the range I want that indicator inside, and back come only the symbols where **every** one of them holds.

The one I run most is two conditions: an early sell setup on the weekly, and a late buy setup on the daily, both true of the same symbol on the same day.
Neither on its own tells me anything, which is the whole point — a condition I can check by eye is not worth a command.

A screen matching nothing is an answer, not a failure.
Most days most screens match nothing, and that is what I am asking.

## Symbols

Any number of them, the same three ways the other groups take them: as arguments, from a file I name with `-f`, or on standard input.
They are symbols, not indices, so `trade index get-symbols sp-500 | trade screen find …` is how I point one at an index.

## Conditions

- `-w`, `--where NAME LOWER UPPER`, given once per condition I want.

`NAME` is an indicator on a timeframe, spelled as the column it produces: `daily_setup`, `weekly_sequential`, `monthly_combo` and the rest of the nine.
Both bounds are inclusive, and naming the same value twice asks for exactly that one.

I expect several in a run and every one has to hold.
Give me none at all and the screen is every symbol I asked about, which is a slow way of spelling `trade demark count` but should not be an error.

`--where` decides which timeframes are worth fetching.
I never want to say that twice, so there is no separate option for it here.

## Dates

- `-s`, `--start DATE` is the earliest date I want back.
- `-e`, `--end DATE` is the latest.

Spelled and defaulting exactly as they do in the `demark` group: inclusive, `--end` today, `--start` that same day alone.

They bound what I am shown, not what has to be fetched.
An indicator on a date is only right if the candles before it were counted too, so screening one day still needs a run of candles behind it, and screening a year needs that year and more.
Work out how much for yourself — I am telling you the dates I care about, not the dates you need.

## Reusing a run

- `-l`, `--load PATH` screens a table I have already produced instead of fetching anything.

It replaces the symbols entirely rather than narrowing them, so it does not go with arguments, `-f` or anything on standard input — the table already says which symbols and which dates it holds.
Don't take both and guess which I meant.

This is the thing I said I would come back to.
Screening the S&P is slow and I will want to try three sets of conditions against one run of it, so let me save what came back and screen that.
What it reads is what this group writes, so `-o` and `-l` are two ends of the same file.

That bounds what it can do, and I would rather live with the bound than have two output shapes.
A saved run holds only the columns I asked for and only the rows that passed, so loading one lets me **tighten** a condition and never loosen one or add an indicator I did not ask for the first time.
When I mean to try several sets against one run, I save it wide open — every indicator I might want, with bounds that exclude nothing — and narrow from there.
A condition naming a column the file does not have is an error saying so, not an empty screen.

## Output

One row per date and symbol that matched, carrying a column for each condition I set, named after that condition.
So `--where daily_setup 7 9 --where weekly_setup -3 -1` gives me `daily_setup`, `date`, `symbol` and `weekly_setup`, alphabetically as everywhere else.

Wide here, where the `demark` group is long, because a screen answers about a symbol and I want its answer on one line.
That the columns depend on the conditions is the point rather than a problem: the conditions are what I asked, and they are what I want to see.

The values in those columns are the indicator's own, carried across unchanged, so they read the way the `demark` group writes them.

It goes out the same two ways as everything else, and `-t` gives me the `rich` table, with the same colour for the sign that the `demark` group uses.

## Commands

One in the group for now.

- `trade screen find` gives me the symbols matching every condition.

## Examples

```bash
trade screen find AAPL --where daily_setup 7 9
trade screen find -f sp500.txt --where daily_setup 7 9 --where weekly_setup -3 -1
trade index get-symbols sp-500 | trade screen find --where daily_setup 9 9
trade index get-symbols ftse-100 | trade screen find --where weekly_combo 11 13 -t
trade screen find -f sp500.txt --where daily_setup 7 9 -o hits.csv
trade screen find --load hits.csv --where daily_setup 9 9
trade screen find -f sp500.txt --where daily_setup 8 9 -s 2026-01-01 -e 2026-03-01
trade screen find -f sp500.txt --where daily_setup 9 9 | cut -d, -f3 | trade symbol get-candles
```

## Working style

Keep going in the repository the `demark` group left, and let its structure change as this build earns it.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, structuring it, writing the code and testing it.
**Work only from your skills.**
Don't draw on anything in your saved memory, and don't open the answers file sitting beside this brief — each would hand you what a good build looks like, which is the thing I am trying to find out.

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.

Write it in a functional style.
