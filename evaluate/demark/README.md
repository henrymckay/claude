# DeMark

A ladder of briefs building one tool, a rung at a time.

Each rung continues the repository the last one produced, so the build is judged on how it grows as well as how it starts.
Run them in order, grading each against its own `answers.md` before starting the next.

1. [`1-symbols`](1-symbols) expands a stock index into the symbols it contains.
2. [`2-candles`](2-candles) fetches price candles for symbols, on three timeframes.
3. [`3-counts`](3-counts) counts DeMark setups and countdowns over those candles.
4. [`4-report`](4-report) reports the counts as a filtered table on a given date.

Every rung adds one demand the last one did not make.
Rung 1 has one adapter and no core worth the name, so it is where premature structure shows up; rung 2 adds a second adapter and the first real seam; rung 3 adds the logic the whole hexagon exists to protect; rung 4 adds the surface.

Each `answers.md` carries a **What should not exist yet** section.
A single large brief cannot test `structure-python`'s "let it grow into the app", because at that size the full structure is warranted — the ladder is what makes scaffolding it too early a visible failure.
