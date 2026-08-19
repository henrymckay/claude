# Index symbols brief

Build me a command-line tool called `symbols` that turns the name of a collection of stocks into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One or more names, given as arguments to `expand`.
Each might name an index, a fund, an ETF or anything else standing for a collection of symbols.

Those collections come from two places, and I should not have to remember which.

- Some ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings online, so expanding one is a request and a parse.

Every name belongs to exactly one of the two, so there is nothing to choose between and nothing for me to tell you.
A name belonging to neither is an error.
When I name several and one of them fails, whether it is unknown or its holdings will not come, fail the whole run rather than hand me a short list I might not notice.

## Funds

Ten collections across three families, none of them in the packaged dataset, all publishing their holdings online.

- **ARK Invest** — `ARKK`, `ARKQ`, `ARKW`, `ARKG`, `ARKF` and `ARKX`.
- **Fundstrat Granny Shots** — `GRNY`, `GRNJ` and `GRNI`.
- **Wedbush** — `IVES`.

Work out where each of them publishes.

Each one answers to its own ticker, so `symbols expand ARKK` and `symbols expand IVES` work where `symbols expand ARK` does not, and `list` shows all ten beside the packaged ones.
I will not be careful about case when I type one, though I want them written back to me the way they are properly spelled — a ticker in capitals, an index as its usual name.

A fund whose holdings I cannot retrieve is an error saying so, not a fund that came back empty.

## Symbols

The Yahoo Finance symbol for each constituent, sorted with duplicates dropped.
Name several collections and I want one list back, so two funds holding the same stock give it to me once.

I only want symbols I could go and trade.
A published holdings file carries rows that are not stocks at all, and I do not want those reaching me.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.

Give me them as a `polars` frame that is ready to show, rather than something assembled a line at a time on the way out.

By default write them to standard output, one per line, so I can pipe them on or redirect them.

## Commands

Two, because finding out what I can expand is a different question from expanding one.

- `expand NAME...` gives me the symbols those collections hold.
- `list` gives me the names I can expand.

`list` is how I find out which names work, since an unknown one is only an error.
It writes one name per line and sorted, the same as the symbols do, so I can grep it.

## Options

One, spelled the way the tools I already use spell it, and it works on both commands.

- `-o`, `--output PATH` writes to that file instead of standard output.

## Using it

```bash
symbols expand dow-jones
symbols expand ARKK
symbols expand ARKK ARKW ARKG
symbols expand dow-jones > dow-jones.txt
symbols expand ARKK -o ark.txt
symbols list
symbols list | grep ARK
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

Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.
Tell me when the build is finished.

Write it in a functional style.
