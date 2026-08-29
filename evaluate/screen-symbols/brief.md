# Screen symbols brief

Carry on from the `trade` tool, whose `demark` group counts setups, sequentials and combos over a list of symbols.
If you are starting without it, read those briefs alongside this one and build them together rather than finishing each and coming back.
A screen has nothing to screen on otherwise, and a tool built as though each group were the last has to be taken apart to make room for the next.

Now I want to point it at a whole index and be told which symbols are worth a look.

A fourth group, `screen`, beside the three already there.
Nothing about how I use any of them changes: the same commands, the same options, the same output.
Behind that, move whatever this build needs moved — if a group was written as though it would be the last, this is where that gets put right rather than worked around.

## What a screen is

Several conditions at once, each naming an indicator on a timeframe and the range I want that indicator inside, and back come only the symbols where **every** one of them holds.

The one I run most is two conditions: an early sell setup on the weekly, and a late buy setup on the daily, both true of the same symbol on the same day.
Neither on its own tells me anything, which is the whole point — a condition I can check by eye is not worth a command.

A screen matching nothing is an answer, not a failure.
Most days most screens match nothing, and that is what I am asking.

## Conditions

Each is a name and two bounds, given once per condition I want.

`NAME` is an indicator on a timeframe, spelled as the column it produces: `daily_setup`, `weekly_sequential`, `monthly_combo` and the rest of the nine.
Both bounds are inclusive, and naming the same value twice asks for exactly that one.

I expect several in a run and every one has to hold.
Give me none at all and the screen is every symbol I asked about, which is a slow way of spelling `trade demark count` but should not be an error.

`--where` decides which timeframes are worth fetching.
I never want to say that twice, so there is no separate option for it here.

## Dates

Two bounds, spelled and defaulting exactly as they do in the `demark` group: inclusive, `--end` today, `--start` that same day alone.

They bound what I am shown, not what has to be fetched.
An indicator on a date is only right if the candles before it were counted too, so screening one day still needs a run of candles behind it, and screening a year needs that year and more.
Work out how much for yourself — I am telling you the dates I care about, not the dates you need.

## Symbols

Any number of them, the same three ways the other groups take them: as arguments, from a file I name with `-i`, or on standard input.
They are symbols, not indices, so `trade index get-symbols sp-500 | trade screen find …` is how I point one at an index.

## Reusing counts

I can hand it indicator values I already have instead of symbols to go and fetch and count.
What it reads is what a `trade demark` command writes, so the two are ends of one file.
Screening the S&P is slow in the fetching and free in the screening, so let me pay once and try as many sets of conditions against it as I like.

It replaces the symbols entirely rather than narrowing them, so it does not go with arguments, `-i` or anything on standard input — the file already says which symbols and which dates it holds.
Don't take both and guess which I meant.

A condition naming an indicator the file does not carry is an error saying so, not an empty screen.
The two read very differently and only one of them is my mistake.

## Commands

One in the group for now.

- `trade screen find` gives me the symbols matching every condition.

## Output

One row per date and symbol that matched, carrying a column for each condition I set, named after that condition.
So `--where daily_setup 7 9 --where weekly_setup -3 -1` gives me `daily_setup`, `date`, `symbol` and `weekly_setup`, alphabetically as everywhere else.

Wide here, where the `demark` group is long, because a screen answers about a symbol and I want its answer on one line.
That the columns depend on the conditions is the point rather than a problem: the conditions are what I asked, and they are what I want to see.

The values in those columns are the indicator's own, carried across unchanged, so they read the way the `demark` group writes them.

It goes out the same two ways as everything else, and `-p` gives me the `rich` table, with the same colour for the sign that the `demark` group uses.

## Arguments and options

`find` takes any number of symbols as arguments, or none at all where they arrive on standard input, from `--input`, or already worked out in `--load`.

Every option has a long form and a single-letter short form, and an option meaning the same thing keeps the same spelling in every command of the tool.

- `-o`, `--output PATH` writes to that file instead of standard output.
- `-p`, `--pretty` shows a `rich` table instead of the plain default.
- `-i`, `--input PATH` reads the symbols from that file rather than from standard input.
- `-l`, `--load PATH` reads worked-out indicator values instead, as above.
- `-s`, `--start DATE` and `-e`, `--end DATE` bound what comes back.
- `-w`, `--where NAME LOWER UPPER`, given once per condition.

No `--timeframe` here: the conditions already name the timeframes they are about, and I am not saying that twice.

## Examples

```bash
trade screen find AAPL --where daily_setup 7 9
trade screen find -i sp500.txt --where daily_setup 7 9 --where weekly_setup -3 -1
trade index get-symbols sp-500 | trade screen find --where daily_setup 9 9
trade index get-symbols ftse-100 | trade screen find --where weekly_combo 11 13 -p
trade demark count -i sp500.txt -o counts.csv
trade screen find --load counts.csv --where daily_setup 7 9
trade screen find --load counts.csv --where weekly_combo 11 13 --where daily_setup -9 -9
trade screen find -i sp500.txt --where daily_setup 8 9 -s 2026-01-01 -e 2026-03-01
trade screen find -i sp500.txt --where daily_setup 9 9 | cut -d, -f3 | trade symbol get-candles
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
