---
name: be-oop
description: >-
  Object-oriented design done well — when to reach for classes, value objects
  as frozen dataclasses, structural interfaces, Liskov as the principle that
  bites, mixins, and which classic design patterns collapse to a function or a
  module. Use when designing or reviewing class hierarchies, working in an OOP
  codebase or framework (subclassing, overriding hooks), modelling stateful
  long-lived objects, or when the user mentions OOP, classes, inheritance,
  interfaces, mixins, SOLID, or a design pattern by name — even if not
  explicitly. This is an opt-in style skill: reach for OOP where it genuinely
  fits, not by default. Language-agnostic principles here; Python idioms in
  references/python.md. Layers on write-python (the in-code baseline);
  be-functional is the functional counterpart.
---

# Be object-oriented

OOP (object-oriented programming) earns its place when a problem is about **things with identity, state, and behaviour** — objects that live over time, or a hierarchy meant to be *extended*.
The house default is functions-first (see `write-python`, `be-functional`); this skill is for when OOP is genuinely the right tool and how to do it well.
Three mistakes account for most bad OOP: reaching for inheritance where composition fits, wrapping a single function in a class, and exposing state the object should be guarding.

**Language-agnostic here.** The Python specifics live in `references/python.md`.

**This is opt-in.** Reach for OOP where it genuinely fits (below), not by default.

## When to use

- **Extending a framework** — the API expects a subclass or an overridden hook.
- **Stateful, long-lived objects with identity** — a connection, a session, a simulation entity — where "the same object, changing over time" is the model.
- **A hierarchy open to new variants** — when you expect new *kinds* of thing to be added (the OOP-friendly side of the expression problem; see `be-functional`, "Choose axis of change").
- **Encapsulating an invariant** — a class can guard its state so it's never invalid.

If none of these hold, a function (or a plain dataclass + functions) is simpler.

## Core principles

Composition over inheritance, encapsulation, programming to an interface and shallow hierarchies need no rule here; the house additions are these.

- **A value object is a frozen dataclass** even inside an OOP design (see `write-python`); mutability is reserved for the object whose changing state *is* the model.
- **A structural interface over a base class**: a `Protocol` where the language has one, so an implementation never has to inherit to qualify; an abstract base class only where you own every implementation and they share code as well as a contract.
- **Liskov is the SOLID principle that bites**: a subtype must work anywhere its base does, so an override that strengthens a precondition or weakens a postcondition is a bug the type checker can't see.
The other four follow from `be-functional`'s injection and axis-of-change rules.
- **A mixin is behaviour-only**, named with a `Mixin` suffix (`SerializableMixin`), and becomes composition the moment it carries its own state or lifecycle, since two stateful mixins fight over `__init__`.

## Design patterns

Patterns are shared vocabulary, but many GoF (Gang of Four) patterns work around features a language with first-class functions and modules already has.
Recognise the pattern, then take the simplest form that solves it — never a Java-style class where a function does.

Patterns that usually **collapse** — what each is, then the simpler form:

- **Strategy** — swap one of a family of interchangeable algorithms at runtime → pass a **function**.
- **Command** — package an action as an object to store, queue, or undo → a **function** (or `functools.partial`).
- **Factory** — centralise how objects get created → a **function** or `classmethod`.
- **Singleton** — one shared instance for the whole program → a **module**, or a value read once at the composition root and injected (see `structure-python`); module-level mutable state is never the answer.
- **Observer** — notify dependents when state changes → a list of **callbacks** / pub-sub.
- **Template Method** — fix an algorithm's skeleton but vary specific steps → pass in the varying **functions**, or a base hook.
- **Iterator** — traverse a collection without exposing its internals → a **generator** / `__iter__`.
- **Visitor** — add an operation across a type hierarchy without editing the classes → `functools.singledispatch` or `match` (see `be-functional`).

Patterns that stay **genuinely useful** as classes:

- **Adapter** — wrap an incompatible interface to fit the one you need.
- **Decorator** (structural) — wrap an object to add behaviour transparently.
- **Composite** — treat a tree of objects uniformly (nodes and leaves share an interface).
- **State** — behaviour changes with internal state (a state machine).
- **Facade** — a simple interface over a complex subsystem.

## Language specifics

Read the file for the language you're working in:

- **Python** → `references/python.md` (dataclasses for state, `Protocol` vs ABC, mixins and the MRO, enums, the collapsed patterns in Python).

Add a new `references/<language>.md` when you work in another language rather than adding its specifics to this file.
