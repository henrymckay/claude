# Index symbols brief

Build me a command-line tool called `symbols` that turns the name of a collection of stocks into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One name per run, given as the only argument.
It might name an index, a fund, an ETF or anything else standing for a collection of symbols.

Those collections come from two places, and I should not have to remember which.

- Some ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings over HTTPS, so expanding one is a request and a parse.

Look locally first, since that is free and instant, and go out to the network only when the name is not there.
A name that matches neither is an error.

## Funds

<!-- The collections to expand over HTTPS, and where each publishes its holdings, go here. -->

## Symbols

The Yahoo Finance symbol for each constituent, sorted with duplicates dropped.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.

Give me them as a `polars` frame that is ready to show, rather than something assembled a line at a time on the way out.

By default write them to standard output, one per line, so I can pipe them on or redirect them.

## Options

Two, and I want them spelled the way the tools I already use spell them.

- `-o`, `--output PATH` writes the symbols to that file instead of standard output.
- `--source local|remote` forces one source and skips looking in the other.

## Using it

```bash
symbols dow-jones
symbols vanguard-ftse-100
symbols dow-jones > dow-jones.txt
symbols dow-jones -o dow-jones.txt
symbols dow-jones --source remote
symbols ftse-100 | grep '\.L$'
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
