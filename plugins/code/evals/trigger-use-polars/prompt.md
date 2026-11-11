---
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger]
---

Convert this to polars:

```python
readings.groupby("sensor").apply(lambda g: g.assign(delta=g["value"].diff()))
```
