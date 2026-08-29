# Index symbols brief

Build me a command-line tool called `trade` that turns an index of stocks into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Indices

Any number of indices, expanded by `get-symbols`.
Some are indices proper and others are a fund, an ETF, an investor or a ranking — anything standing for a set of symbols.
I call them all indices, since the tool treats them alike and the difference never reaches me.

They come from two kinds of place, and I should not have to remember which.

- Some ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings online, so expanding one is a request and a parse.

Every index I have listed belongs to exactly one of the two, so there is nothing to choose between and nothing for me to tell you.
An index I have not listed is tried as an ETF symbol as a last resort, and is an error only once that has failed too.
Tell me which of the two went wrong, since an index that is no ETF and a request that would not come are different problems and only one of them is my typo.

I will not be careful about case, spacing or punctuation when I type one.
`S&P 500`, `S&P-500`, `SP500` and `sp-500` are all the same index to me, and `dow-jones` is the same as `DOW JONES`.
The full stop is the exception, since it separates a London listing from its symbol rather than being punctuation I was careless with.
`SMGB.L` and `SMGBL` are two different things and must never collapse into one.
I do want them written back the way they are properly spelled, a symbol in capitals and an index as it is usually written.

When I give several, one failure fails the whole run, whether that index was unknown or its holdings would not come.
A short list I might not notice is worse than no list at all.

That makes a moment's flakiness expensive, so do not give up on the first refusal.
A request that times out, is refused, or comes back complaining about the far end is worth trying again shortly.
A refusal that tells me the thing does not exist is a real answer, and I want that one straight away rather than after a wait.

Some of these places will not answer unless a caller leaves them a way to reply to it.
Let me set that address myself rather than shipping one inside the tool, since it is mine to give and mine to change.

They reach the command whichever way suits what I am doing at the time.

- Written out as arguments.
- Read from a file I name.
- Piped or redirected in on standard input, so `trade index catalogue | grep ARK | trade index get-symbols` just works.

Give it nothing by any of the three and that is an error, not an empty list, since an index is the whole of what the command is for.

## Funds

Forty-nine funds across four families, none of them in the packaged dataset, all publishing their holdings online.

- **ARK Invest.** `ARKF`, `ARKG`, `ARKK`, `ARKQ`, `ARKW` and `ARKX`.
- **Fundstrat Granny Shots.** `GRNI`, `GRNJ` and `GRNY`.
- **VanEck, listed in London.** `CURE.L`, `CYBO.L`, `DAPP.L`, `DFNS.L`, `ESPO.L`, `GDIG.L`, `GDX.L`, `GDXJ.L`, `HDRO.L`, `JEDI.L`, `NUCL.L`, `OIHV.L`, `PIKA.L`, `QNTM.L`, `REMX.L`, `REUS.L`, `SMH.L` and `VEGI.L`.
- **VanEck, listed in the US.** `BBH`, `CRAK`, `DAPP`, `EMET`, `ESPO`, `GDX`, `GDXJ`, `IBOT`, `MOAT`, `MOTI`, `MVAL`, `NLR`, `OIH`, `PPH`, `REMX`, `SMH`, `SMHC`, `SMHX`, `SMOT` and `WARP`.
- **Wedbush.** `IVEP` and `IVES`.

Work out where each of them publishes.
VanEck's two ranges are separate funds under one manager, so expect to find them in different places.

Every London fund takes a `.L` suffix and every US one stays bare, which is how the tool already spells a London listing when it hands me symbols back.
Six of those symbols appear in both ranges, where the London fund and the US fund sharing one are separate funds with separate books.
The suffix is what tells the two apart, and I want it on all eighteen rather than only on those six, because an index I have put in a script should not change the day VanEck lists something that collides with it.

Each answers to its own symbol, so `trade index get-symbols ARKK` and `trade index get-symbols IVES` work where `trade index get-symbols ARK` does not.
All forty-nine appear in `catalogue` beside the packaged ones, each under the spelling that reaches it.

Those forty-nine are the funds I follow, not the limit of what I can ask for.
Any other ETF symbol should expand as well, so `trade index get-symbols TAN` gives me a solar fund named nowhere in this brief.
It spells the same way as the rest, bare for a US listing and `.L` for a London one.
No issuer publishes anybody else's funds, so that one will not come from an issuer — look for somewhere that carries ETFs generally and covers both listings.
When it is what answers, just give me the symbols; I do not need telling that the index was not one of mine.
For one of my forty-nine I want the whole book.
For anything else the largest holdings are enough, so do not pay for completeness there at the cost of the funds I actually follow.

A fund whose holdings I cannot retrieve is an error saying so, not a fund that came back empty.

## Investors

Four investors who disclose what they hold rather than running a fund whose book is published.

- Berkshire Hathaway.
- Duquesne Family Office.
- NVIDIA.
- Situational Awareness.

Each reports its US positions to the SEC once a quarter, so give me the most recent report and never an older one.
When it was filed is of no interest to me, so nothing needs to show the date or let me choose by it.
A report covers more than plain stock, so the same judgement that keeps untradeable rows out of a fund's holdings applies here too.

They answer to what they are called rather than to a symbol, so `trade index get-symbols berkshire-hathaway` works.

## Rankings

Two lists that rank companies rather than hold them, and I want to expand them the same way as everything else.

- `large-companies`, the listed companies ranked by market capitalisation.
- `large-etfs`, the ETFs ranked the same way.

These are far longer than any fund, thousands of rows rather than tens, and they are worldwide rather than one country's market.
Give me the top thousand of each and no more, since below that they are too small to be worth scanning.
That thousand is part of what the two mean rather than something I want to set each time.

## Symbols

The Yahoo Finance symbol for each constituent, sorted with duplicates dropped.
Give me several indices and I want one list back, so two funds holding the same stock give it to me once.

I only want symbols I could go and trade.
A published holdings file carries rows that are not stocks at all, and I do not want those reaching me.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.
Not every publisher says which exchange a holding trades on.
Where a file leaves it out and there is nothing to work it out from, I would rather have nothing than a symbol that could name a different company — a gap I can see beats a holding I cannot tell apart from a real one.

Hold them in a `polars` frame, ready to show, rather than assembling the output a line at a time on the way out.

One symbol per line and nothing else, always, so `grep`, `sort` and `xargs` all work on them without my thinking about it.

## Commands

The tool is `trade`, and its commands are grouped by what they are about rather than sitting flat under it.
This build fills the first group, `index`.
More groups follow in the builds after this one, so the shape has to take them without this group's surface moving or being renamed.

Two commands in the group, because finding out what I can expand is a different question from expanding one.

- `trade index get-symbols [INDEX...]` gives me the symbols those indices hold.
- `trade index catalogue` gives me the indices I follow.

`catalogue` is how I remind myself which indices I have set up rather than a list of everything that works, since any ETF symbol expands whether it appears there or not.
Everything this brief lists belongs in it, the packaged ones and the funds and the investors and the rankings alike.
It writes one index per line, sorted, the same as the symbols do, so I can grep it.

Every index in it has to expand, and expand to something.
One I can read in `catalogue` and cannot use is worse than one you never offered me, so check them all before you tell me it is done.
I care what each gives back, not that the command exited cleanly.

## Output

- `trade index catalogue` has one column, `index`.
- `trade index get-symbols` has one column, `symbol`.

Columns come back in **alphabetical order**, whatever order I have listed them in when describing them.
It is one less thing to remember, and it means a column added later lands somewhere predictable instead of on the end.

The plain form is comma-separated with **no heading row**, so a one-column result is just the values one per line and pipes straight into whatever comes next.
Same bytes whether I am at a terminal, in a pipe or in a script — I would rather know what I am getting than have it guessed for me.

`--pretty` is the plain answer made readable, never a different answer — same rows, same columns, in the same order, and that holds in every group added later.
Where a group has something a colour can say better than a character, it may say it that way, but it may not add, drop or rearrange a thing.

It is the only place a heading appears, and the heading is the column's own name, the same word the plain form would have put there had it carried a heading row.
I read one and script against the other, so I do not want to translate between two spellings of one column.
It also closes with a count, so I know how many came back.

## Arguments and options

`get-symbols` takes any number of indices as arguments, or none at all where they arrive on standard input or from `--input`.
`catalogue` takes no input of any kind, since there is nothing to give it.

Every option has a long form and a single-letter short form.
An option meaning the same thing keeps the same spelling everywhere it appears — in both commands here, and in every group added after this one.

Two are common to every command in the tool:

- `-o`, `--output PATH` writes to that file instead of standard output.
- `-p`, `--pretty` shows a `rich` table instead of the plain default.

One belongs to `get-symbols` alone, and keeps its spelling wherever a later group takes an input:

- `-i`, `--input PATH` reads the indices from that file rather than from standard input.

## Examples

Expanding an index.

```bash
trade index get-symbols sp-500
trade index get-symbols "S&P 500"
trade index get-symbols ARKK ARKW ARKG
trade index get-symbols berkshire-hathaway
trade index get-symbols large-companies
trade index get-symbols TAN
trade index get-symbols ARKK -p
trade index get-symbols ARKK -o ark.txt
trade index get-symbols sp-500 > sp-500.txt
trade index get-symbols -i indices.csv
trade index get-symbols < indices.csv
trade index get-symbols ftse-100 | grep '\.L$'
comm -12 <(trade index get-symbols ARKK) <(trade index get-symbols ARKW)
diff <(trade index get-symbols SMH) <(trade index get-symbols SMH.L)
```

Finding out what I can expand.

```bash
trade index catalogue
trade index catalogue | grep ARK | trade index get-symbols
```

## Working style

Create it as its own new git repository, at a path I will give you.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, structuring it, writing the code and testing it.
**Work only from your skills.**
Don't draw on anything in your saved memory, and don't open the answers file sitting beside this brief — each would hand you what a good build looks like, which is the thing I am trying to find out.

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.

Write it in a functional style.
