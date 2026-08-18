# 🎯 Evals

Each eval is a realistic build brief and the design it should produce, for
testing whether the skills actually lead somewhere good.

- `brief.md` — what a user would ask for. States requirements and withholds
  design: every architectural decision is one the skills are meant to supply.
- `answers.md` — the design a skilled build arrives at, why each seam falls
  where it does, and the wrong turns to watch for. Each wrong turn is a real
  failure from a previous run, not a hypothetical.

## Run one

Give `brief.md` to a fresh session — no memory, no prior context, no sight of
`answers.md` — and let it build. Then grade the result against `answers.md`.

Where the build goes wrong, the interesting question is never "what did it get
wrong" but **which skill let it**: a rule that was missing, one that was
buried in a paragraph, or one phrased softly enough to read past. Fix the
skill, not the transcript.

## Evals

- [`demark`](demark) — a command-line tool reporting DeMark counts for stock
  tickers across timeframes. Exercises dataframe modelling (one long frame, no
  loop over groups), where to cut a pure core, what earns a named type, and
  composable entry points.
