# Index symbols brief

Build me a command-line tool that expands the name of a stock index into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Indices

One or more index names, given as arguments.

Resolve them with `pytickersymbols`, which ships its own dataset, so this should cost no network call.
Tell me plainly when a name matches nothing, rather than handing back an empty list.

## Symbols

The Yahoo Finance symbol for each constituent, one per line, sorted with duplicates removed.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.

I want the symbols to go two ways.

- To standard output, so I can pipe them into another command or redirect them to a file.
- To a file I name.

## Working style

Create it as its own new git repository, at a path I will give you.
Build what this brief asks for and no more.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
