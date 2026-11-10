---
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger]
---

Tidy this up:

```python
TAX_RATE = 0.2
totals = {}

def total(orders):
    for o in orders:
        totals[o["customer"]] = totals.get(o["customer"], 0) + o["net"] * (1 + TAX_RATE)
    return totals
```
