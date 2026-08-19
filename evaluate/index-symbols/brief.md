# Index symbols brief

Build me a command-line tool that turns the name of an index or a fund into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One name per run, given as the only argument.

I get symbols from two places, and I want a command for each, so what I type says where to look rather than a flag on a shared command.

- **Indices** come from `pytickersymbols`, which ships its own dataset, so expanding one should cost no network call.
- **Funds** publish their holdings over HTTPS, so expanding one is a request and a parse.

Tell me plainly when a name matches nothing, rather than handing back an empty list.

## Funds

<!-- The funds to expand over HTTPS, and where each publishes its holdings, go here. -->

## Symbols

The Yahoo Finance symbol for each constituent, sorted with duplicates dropped.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.

Give me them as a `polars` frame that is ready to show, rather than something assembled a line at a time on the way out.

I want them to go two ways.

- To standard output, so I can pipe them into another command or redirect them to a file.
- To a file I name.

## Commands

One per source, and the tool has to sit in a pipeline like anything else.

```bash
demark index dow-jones
demark index dow-jones > dow-jones.txt
demark index dow-jones --output dow-jones.txt
demark fund vanguard-ftse-100 | demark candles
```

## Working style

Create it as its own new git repository, at a path I will give you.
Build what this brief asks for and no more.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
