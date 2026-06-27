---
name: example-agent
description: Template/example subagent. Replace with a one-line summary of what this agent specializes in and WHEN to delegate to it.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a specialised subagent. Replace this system prompt with the agent's
role, scope, and operating rules.

- State clearly what the agent should and shouldn't do.
- Keep tool access (frontmatter `tools`) to the minimum it needs.
- The `description` frontmatter is what the main agent matches on to decide
  when to delegate — make it specific.
