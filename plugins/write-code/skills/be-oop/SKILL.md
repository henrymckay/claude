---
name: be-oop
description: >-
  Object-oriented design done well — when classes earn their place, value
  objects, structural interfaces, Liskov, mixins, and which design patterns
  collapse to a function. Use when designing or reviewing class hierarchies,
  working in an OOP framework, modelling long-lived stateful objects, or when
  the user names OOP, inheritance, SOLID or a pattern. Opt-in: reach for OOP
  where it genuinely fits, not by default.
---

# Be object-oriented

OOP (object-oriented programming) earns its place when a problem is about **things with identity, state, and behaviour** — objects that live over time, or a hierarchy meant to be *extended*.
The house default is functions-first (`be-functional`); this skill is for when OOP is genuinely the right tool.
Three mistakes account for most bad OOP: reaching for inheritance where composition fits, wrapping a single function in a class, and exposing state the object should be guarding.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**This is opt-in.** Reach for OOP where it genuinely fits (below), not by default.

## When to use

- **Extending a framework** — the API expects a subclass or an overridden hook.
- **Stateful, long-lived objects with identity** — a connection, a session, a simulation entity — where "the same object, changing over time" is the model.
- **A hierarchy open to new variants** that others will add (`be-functional`, Choose axis of change).
- **Encapsulating an invariant** a class guards so its state is never invalid.

If none of these hold, a function (or a plain dataclass + functions) is simpler.

## Core principles

- **A value object is immutable** even inside an OOP design; mutability is reserved for the object whose changing state *is* the model.
- **A structural interface over a base class**: a `Protocol` where the language has one, so an implementation never has to inherit to qualify; an abstract base class only where you own every implementation and they share code as well as a contract.
- **Liskov is the SOLID principle that bites**: a subtype must work anywhere its base does, so an override that strengthens a precondition or weakens a postcondition is a bug the type checker can't see.
The other four follow from `be-functional`'s injection and axis-of-change rules.
- **A mixin is behaviour-only**, named with a `Mixin` suffix (`SerializableMixin`), and becomes composition the moment it carries its own state or lifecycle, since two stateful mixins fight over `__init__`.

## Design patterns

Many GoF (Gang of Four) patterns work around features a language with first-class functions and modules already has: recognise the pattern, then take the simplest form that solves it, never a class where a function does.

Patterns that usually **collapse**:

- **Command** → a **function** (or `functools.partial`).
- **Factory** → a **function** or `classmethod`.
- **Iterator** → a **generator** / `__iter__`.
- **Observer** → a list of **callbacks**.
- **Singleton** → a **module**, or a value read once at the composition root and injected (see `structure-python`); module-level mutable state is never the answer.
- **Strategy** → pass a **function**.
- **Template Method** → pass in the varying **functions**, or a base hook.
- **Visitor** → `functools.singledispatch` or `match` (see `be-functional`).

Patterns that stay classes, since each wraps or holds state: **Adapter**, **Composite**, **Decorator** (structural), **Facade** and **State**.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (dataclasses for state, `Protocol` vs ABC, mixins and the MRO, the collapsed patterns in Python).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
