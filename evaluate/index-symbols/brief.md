# Index symbols brief

Build me a command-line tool called `symbols` that turns the name of an index or a fund into the symbols it holds.
This is the first piece of a bigger tool for scanning stocks, so I will keep adding to the same repository.

## Names

One name per run, given as the only argument.

The symbols come from two places, and I should not have to remember which.

- Some names ship with `pytickersymbols`, whose dataset comes with the package, so expanding one costs no network call.
- Others publish their holdings over HTTPS, so expanding one is a request and a parse.

Look locally first, since that is free and instant, and go out to the network only when the name is not there.
Tell me plainly when a name matches neither, and say what close matches you did find.

I do want to be able to override that.
The packaged dataset is a snapshot and goes stale, where a fund's published holdings are authoritative, so let me force either source when I know better.

## Funds

<!-- The funds to expand over HTTPS, and where each publishes its holdings, go here. -->

## Symbols

The Yahoo Finance symbol for each constituent, sorted with duplicates dropped.

A stock lists on several exchanges and carries a symbol for each, so give me the one for its home listing.

Give me them as a `polars` frame that is ready to show, rather than something assembled a line at a time on the way out.

I want them to go two ways.

- To standard output, so I can pipe them into another command or redirect them to a file.
- To a file I name.

## Using it

```bash
symbols dow-jones
symbols vanguard-ftse-100
symbols dow-jones > dow-jones.txt
symbols dow-jones --output dow-jones.txt
symbols dow-jones --source remote
symbols ftse-100 | grep '\.L$'
```

## Working style

Create it as its own new git repository, at a path I will give you.
Build what this brief asks for and no more.

This is the interface I think I want.
Where your skills say a different shape would serve me better, say so and why before you build it, rather than either following me over a cliff or quietly doing something else.

Invoke and follow your skills throughout, for setting the project up, writing the code and testing it.
**Don't draw on anything in your saved memory; work only from your skills.**
Where a skill is silent, ambiguous or steers you wrong, note it as you go rather than quietly working around it.

Write it in a functional style.
