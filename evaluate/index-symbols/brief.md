# Index symbols brief

Build me a command-line tool called `symbols` that turns the name of a collection of stocks into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One name per run, given as the only argument to `expand`.
It might name an index, a fund, an ETF or anything else standing for a collection of symbols.

Those collections come from two places, and I should not have to remember which.

- Some ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings over HTTPS, so expanding one is a request and a parse.

Look locally first, since that is free and instant, and go out to the network only when the name is not there.

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

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.

Give me them as a `polars` frame that is ready to show, rather than something assembled a line at a time on the way out.

By default write them to standard output, one per line, so I can pipe them on or redirect them.

## Commands

Two, because finding out what I can expand is a different question from expanding one.

- `expand NAME` gives me the symbols that collection holds.
- `list` gives me the names I can expand.

A name matching neither source is an error, and `list` is how I find out which names do match.

## Options

Both commands take both, spelled the way the tools I already use spell them.

- `-o`, `--output PATH` writes to that file instead of standard output.
- `-s`, `--source local|remote` forces one source on `expand`, and narrows `list` to that source's names.

## Using it

```bash
symbols expand dow-jones
symbols expand ARKK
symbols expand dow-jones > dow-jones.txt
symbols expand dow-jones -o dow-jones.txt
symbols expand dow-jones -s remote
symbols list
symbols list -s remote | grep ARK
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
