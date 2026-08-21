# Index symbols brief

Build me a command-line tool called `symbols` that turns the name of a collection of stocks into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One or more names, given as arguments to `expand`.
Each might name an index, a fund, an ETF or anything else standing for a collection of symbols.

Those collections come from two kinds of place, and I should not have to remember which.

- Some ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings online, so expanding one is a request and a parse.

Every name belongs to exactly one of the two, so there is nothing to choose between and nothing for me to tell you.
A name belonging to neither is an error.

I will not be careful about case, spacing or punctuation when I type a name.
`S&P 500`, `S&P-500`, `SP500` and `sp-500` are all the same index to me, and `dow-jones` is the same as `DOW JONES`.
I do want them written back the way they are properly spelled, a ticker in capitals and an index under its usual name.

When I name several, one failure fails the whole run, whether that name was unknown or its holdings would not come.
A short list I might not notice is worse than no list at all.

## Funds

Twenty-seven collections across four families, none of them in the packaged dataset, all publishing their holdings online.

- **ARK Invest.** `ARKK`, `ARKQ`, `ARKW`, `ARKG`, `ARKF` and `ARKX`.
- **Fundstrat Granny Shots.** `GRNY`, `GRNJ` and `GRNI`.
- **VanEck.** `CURE`, `CYBO`, `DAPP`, `DFNS`, `ESPO`, `GDIG`, `GDX`, `GDXJ`, `HDRO`, `JEDI`, `NUCL`, `OIHV`, `QNTM`, `REMX`, `REUS`, `SMH` and `VEGI`.
- **Wedbush.** `IVES`.

Work out where each of them publishes.

The VanEck ones are the UCITS funds listed in London, not the US funds that share several of those tickers, and the two do not hold the same stocks.

Each answers to its own ticker, so `symbols expand ARKK` and `symbols expand IVES` work where `symbols expand ARK` does not.
All twenty-seven appear in `catalogue` beside the packaged ones.

A fund whose holdings I cannot retrieve is an error saying so, not a fund that came back empty.

## Investors

Three investors who disclose what they hold rather than running a fund whose book is published.

- Berkshire Hathaway.
- Duquesne Family Office.
- Situational Awareness.

Each reports its US positions to the SEC once a quarter, so what comes back is the most recent report rather than today's position, and that suits me.
A report covers more than plain stock, so the same judgement that keeps untradeable rows out of a fund's holdings applies here too.

They answer to their names rather than to a ticker, so `symbols expand berkshire-hathaway` works.

## Rankings

Two lists that rank companies rather than hold them, and I want to expand them the same way as everything else.

- `largest-companies`, the listed companies ranked by market capitalisation.
- `largest-etfs`, the ETFs ranked the same way.

These are far longer than any fund, thousands of rows rather than tens, and they are worldwide rather than one country's market.

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

Two, because finding out what I can expand is a different question from expanding one.

- `expand NAME...` gives me the symbols those collections hold.
- `catalogue` gives me the names I can expand.

Since an unknown name gets me nothing but an error, `catalogue` is how I find out which names work.
It writes one name per line, sorted, the same as the symbols do, so I can grep it.

## Options

Two, spelled the way the tools I already use spell them, and both work on both commands.

- `-o`, `--output PATH` writes to that file instead of standard output.
- `-t`, `--table` shows a `rich` table instead of the one-per-line default.

## Examples

```bash
symbols expand dow-jones
symbols expand sp-500
symbols expand "S&P 500"
symbols expand ARKK
symbols expand ARKK ARKW ARKG
symbols expand berkshire-hathaway
symbols expand largest-etfs
symbols expand dow-jones > dow-jones.txt
symbols expand ARKK -o ark.txt
symbols catalogue
symbols catalogue | grep ARK
symbols expand ARKK -t
symbols expand ftse-100 | grep '\.L$'
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
