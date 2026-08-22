# Index symbols brief

Build me a command-line tool called `trade` that turns the name of a collection of stocks into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One or more names, given as arguments to `expand`.
Each might name an index, a fund, an ETF or anything else standing for a collection of symbols.

Those collections come from two kinds of place, and I should not have to remember which.

- Some ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings online, so expanding one is a request and a parse.

Every name I have listed belongs to exactly one of the two, so there is nothing to choose between and nothing for me to tell you.
A name I have not listed is tried as an ETF ticker as a last resort, and is an error only once that has failed too.
Tell me which of the two went wrong, since a name that is no ETF and a request that would not come are different problems and only one of them is my typo.

I will not be careful about case, spacing or punctuation when I type a name.
`S&P 500`, `S&P-500`, `SP500` and `sp-500` are all the same index to me, and `dow-jones` is the same as `DOW JONES`.
I do want them written back the way they are properly spelled, a ticker in capitals and an index under its usual name.

When I name several, one failure fails the whole run, whether that name was unknown or its holdings would not come.
A short list I might not notice is worse than no list at all.

That makes a moment's flakiness expensive, so do not give up on the first refusal.
A request that times out, is refused, or comes back complaining about the far end is worth trying again shortly.
A refusal that tells me the thing does not exist is a real answer, and I want that one straight away rather than after a wait.

Some of these places will not answer unless a caller leaves them a way to reply to it.
Let me set that address myself rather than shipping one inside the tool, since it is mine to give and mine to change.

## Funds

Forty-eight collections across four families, none of them in the packaged dataset, all publishing their holdings online.

- **ARK Invest.** `ARKK`, `ARKQ`, `ARKW`, `ARKG`, `ARKF` and `ARKX`.
- **Fundstrat Granny Shots.** `GRNY`, `GRNJ` and `GRNI`.
- **VanEck, listed in London.** `CURE.L`, `CYBO.L`, `DAPP.L`, `DFNS.L`, `ESPO.L`, `GDIG.L`, `GDX.L`, `GDXJ.L`, `HDRO.L`, `JEDI.L`, `NUCL.L`, `OIHV.L`, `PIKA.L`, `QNTM.L`, `REMX.L`, `REUS.L`, `SMH.L` and `VEGI.L`.
- **VanEck, listed in the US.** `BBH`, `CRAK`, `DAPP`, `EMET`, `ESPO`, `GDX`, `GDXJ`, `IBOT`, `MOAT`, `MOTI`, `MVAL`, `NLR`, `OIH`, `PPH`, `REMX`, `SMH`, `SMHC`, `SMHX`, `SMOT` and `WARP`.
- **Wedbush.** `IVES`.

Work out where each of them publishes.
VanEck's two ranges are separate funds under one manager, so expect to find them in different places.

Every London fund takes a `.L` suffix and every US one stays bare, which is how the tool already spells a London listing when it hands me symbols back.
Six tickers are claimed by both ranges and a London fund never holds the same stocks as the US fund sharing its ticker.
I still want the suffix on all eighteen rather than only on those six, because a name I have put in a script should not change the day VanEck lists something that collides with it.

Each answers to its own ticker, so `trade index expand ARKK` and `trade index expand IVES` work where `trade index expand ARK` does not.
All forty-eight appear in `catalogue` beside the packaged ones, each under the name that reaches it.

Those forty-eight are the funds I follow, not the limit of what I can ask for.
Any other ETF ticker should expand as well, so `trade index expand TAN` gives me a solar fund named nowhere in this brief.
It spells the same way as the rest, bare for a US listing and `.L` for a London one.
No issuer publishes anybody else's funds, so that one will not come from an issuer — look for somewhere that carries ETFs generally and covers both listings.
When it is what answers, just give me the symbols; I do not need telling that the name was not one of mine.
For one of my forty-eight I want the whole book.
For anything else the largest holdings are enough, so do not pay for completeness there at the cost of the funds I actually follow.

A fund whose holdings I cannot retrieve is an error saying so, not a fund that came back empty.

## Investors

Three investors who disclose what they hold rather than running a fund whose book is published.

- Berkshire Hathaway.
- Duquesne Family Office.
- Situational Awareness.

Each reports its US positions to the SEC once a quarter, so give me the most recent report and never an older one.
When it was filed is of no interest to me, so nothing needs to show the date or let me choose by it.
A report covers more than plain stock, so the same judgement that keeps untradeable rows out of a fund's holdings applies here too.

They answer to their names rather than to a ticker, so `trade index expand berkshire-hathaway` works.

## Rankings

Two lists that rank companies rather than hold them, and I want to expand them the same way as everything else.

- `largest-companies`, the listed companies ranked by market capitalisation.
- `largest-etfs`, the ETFs ranked the same way.

These are far longer than any fund, thousands of rows rather than tens, and they are worldwide rather than one country's market.
Give me the top thousand of each and no more, since below that they are too small to be worth scanning.
That thousand is part of what the two names mean rather than something I want to set each time.

## Symbols

The Yahoo Finance symbol for each constituent, sorted with duplicates dropped.
Name several collections and I want one list back, so two funds holding the same stock give it to me once.

I only want symbols I could go and trade.
A published holdings file carries rows that are not stocks at all, and I do not want those reaching me.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.
Not every publisher says which exchange a holding trades on.
Where a file leaves it out and there is nothing to work it out from, I would rather have nothing than a symbol that could name a different company — a gap I can see beats a holding I cannot tell apart from a real one.

Hold them in a `polars` frame, ready to show, rather than assembling the output a line at a time on the way out.

One symbol per line and nothing else, always, so `grep`, `sort` and `xargs` all work on them without my thinking about it.
Same bytes whether I am at a terminal, in a pipe or in a script — I would rather know what I am getting than have it guessed for me.

When I do want to read them myself, a flag gives me a `rich` table down the page instead, with a heading and a count at the end so I know how many came back.

## Commands

The tool is `trade`, and its commands are grouped by what they are about rather than sitting flat under it.
This build fills the first group, `index`.
More groups follow in the builds after this one, so the shape has to take them without this group moving or being renamed.

Two commands in the group, because finding out what I can expand is a different question from expanding one.

- `trade index expand NAME...` gives me the symbols those collections hold.
- `trade index catalogue` gives me the names I follow.

`catalogue` is how I remind myself which collections I have set up rather than a list of everything that works, since any ETF ticker expands whether it appears there or not.
Everything this brief names belongs in it, the packaged indices and the funds and the investors and the rankings alike.
It writes one name per line, sorted, the same as the symbols do, so I can grep it.

Every name in it has to expand, and expand to something.
A name I can read in `catalogue` and cannot use is worse than one you never offered me, so check them all before you tell me it is done.
I care what each gives back, not that the command exited cleanly.

## Options

Two, spelled the way the tools I already use spell them, and both work on both commands.

- `-o`, `--output PATH` writes to that file instead of standard output.
- `-t`, `--table` shows a `rich` table instead of the one-per-line default.

## Examples

```bash
trade index expand dow-jones
trade index expand sp-500
trade index expand "S&P 500"
trade index expand ARKK
trade index expand ARKK ARKW ARKG
trade index expand SMH
trade index expand SMH.L
trade index expand berkshire-hathaway
trade index expand largest-etfs
trade index expand dow-jones > dow-jones.txt
trade index expand ARKK -o ark.txt
xargs trade index expand < indices.csv
trade index expand TAN
trade index expand largest-companies
trade index catalogue
trade index catalogue | grep ARK
trade index catalogue | grep ARK | xargs trade index expand
trade index expand ARKK -t
trade index expand ftse-100 | grep '\.L$'
comm -12 <(trade index expand ARKK) <(trade index expand ARKW)
```

## Working style

Create it as its own new git repository, at a path I will give you.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, structuring it, writing the code and testing it.
**Work only from your skills.**
Don't draw on anything in your saved memory, and don't open the answers file sitting beside this brief — each would hand you what a good build looks like, which is the thing I am trying to find out.

Write it in a functional style.

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.
