---
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger]
---

Add tests for this function.

```python
def total_by_customer(orders: list[tuple[str, float]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for customer, amount in orders:
        totals[customer] = totals.get(customer, 0.0) + amount
    return totals
```
