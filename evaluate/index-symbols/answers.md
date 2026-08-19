# Index symbols answers

What a build working from the brief should arrive at, and the wrong turns to watch for.
Nothing here is stated in the brief: each item is something the skills should produce.

## The shape

Two sources, one shape out.

| shape | one row is | how it is reached |
|---|---|---|
| holdings | a constituent as its source describes it | read the packaged dataset, or fetch and parse the published file |
| symbols | one symbol | keep the home listing, sort, drop duplicates |

**The two adapters differ entirely inside and agree exactly at their edge.** Each returns the same frame of symbols, so nothing downstream ever asks which one ran, and the second source costs the rest of the program nothing.
An adapter that returns the dataset's records from one command and parsed rows from the other has pushed its source's shape outward, and every later build pays for it.

**A stock's home listing is a judgement the adapter makes.** The dataset gives several Yahoo symbols per stock, one per exchange, and its own bare `symbol` field matches the home one where that listing exists.
Prefer the match, fall back to the first, and keep the rule in the adapter — it is a fact about the data source, not about the domain.

Sorting and dropping duplicates happens **in the frame**, not by routing the symbols through a Python `set` and back.
A set loses the order the brief asks for, so it has to be re-sorted anyway, and the frame does both in one pass.

## What should not exist yet

Two external services is a real boundary, so naming an adapter layer is earned here.
Two things still are not.

- **No `port/`.** A port exists so a pure core can call outward without importing the adapter, and here each command calls its own adapter directly.
The trigger is a core that must not know which source ran, and nothing in this build needs that — the two adapters are peers reached from different commands, not two implementations something chooses between.
- **No `operate/`.** A use case that orchestrates a single transform is that transform.

Also absent unless the brief asked: caching, a retry policy, a configuration layer, an abstraction over "sources" that both adapters register with.

Introducing a port here is the plausible mistake rather than the obvious one, which is what makes it worth grading: the two adapters *do* share a signature, and that resemblance is not the same as a caller who needs the choice hidden.

## The HTTP adapter

- `httpx` is the pick over `requests`.
- Set a timeout. A published holdings file is somebody else's server, and a hung request with no deadline is the failure that wastes the most time.
- The adapter owns its outcome: a fund that 404s, times out, or returns something unparseable becomes an error naming the fund, not a status code or a library exception escaping into the driver.
- Parse the response **into the frame**, rather than splitting strings into lists and building a frame from them afterwards.

## Verification

This is where the test suite is founded, and the next two builds inherit whatever shape it takes, so it carries more weight than the amount of code under test suggests.

- The suite lives apart from the source, with its own directory for the cases, its shared helpers and any data files it loads.
- Tests of a dependency's own behaviour sit a level apart from tests of your code, because they fail for a different reason and on somebody else's schedule.
- Every test names the behaviour it claims rather than the function it calls, and arrives at its starting state through its parameters rather than building it inline.
- **The default run must not touch the network.** Capture a real holdings response once, keep it as a data file the tests load, and parse that; mark the tests that genuinely reach out so they stay out of the default run.

Worth their own cases: a US stock whose bare symbol appears among its listings and a foreign one where it does not, an unknown name from each source, and a fund whose request fails.

## Wrong turns

- **A `port` or an `operate` layer**, covered above.
- **A network call for the index source.** `pytickersymbols` ships its data; reaching for HTTP means the adapter was written before the library was read.
- **Two shapes out of two adapters**, leaving the driver or the transform to reconcile them.
- **String-wrangling the holdings file** into lists and dicts before it reaches a frame.
- **Letting a request failure surface as `httpx`'s own exception**, which makes the calling code depend on the library the adapter exists to hide.
- **Tests that hit the network by default**, which turn an unrelated outage into a failing suite.
- **Silently dropping an unmatched name**, which turns a typo into an empty report much later.
