---
name: be-oop
description: >-
  Object-oriented design done well — when to reach for classes, composition over
  inheritance, encapsulation, SOLID, and the classic design patterns (with their
  simpler Python forms). Use when designing or reviewing class hierarchies,
  working in an OOP codebase or framework (subclassing, overriding hooks),
  modelling stateful long-lived objects, or when the user mentions OOP, classes,
  inheritance, interfaces, SOLID, or a design pattern by name — even if not
  explicitly. This is an opt-in style skill: the house default is functions-first
  (see write-python, be-functional), so use OOP where it genuinely fits.
  Language-agnostic principles here; Python idioms in references/python.md.
---

# Being object-oriented

OOP earns its place when a problem is about **things with identity, state, and behaviour** — objects that live over time, or a hierarchy meant to be *extended*.
The house default is functions-first (see `write-python`, `be-functional`); this skill is for when OOP is genuinely the right tool and how to do it well.
This file is the language-agnostic mindset; Python idioms live in `references/python.md`.

**This is opt-in.** Reach for it when designing classes, working in an OOP framework (subclassing, overriding hooks), modelling stateful long-lived objects, or building a hierarchy others will extend.
For pure data transformation and stateless logic, prefer functions.

## When to reach for OOP

- **Extending a framework** — the API expects a subclass or an overridden hook.
- **Stateful, long-lived objects with identity** — a connection, a session, a simulation entity — where "the same object, changing over time" is the model.
- **A hierarchy open to new variants** — when you expect new *kinds* of thing to be added (the OOP-friendly side of the expression problem; see `be-functional`, "Extensibility: choose your axis of change").
- **Encapsulating an invariant** — a class can guard its state so it's never invalid.

If none of these hold, a function (or a plain dataclass + functions) is simpler.

## Core principles

1. **Composition over inheritance.** Prefer building objects from other objects (has-a) over deep inheritance (is-a).
   Inheritance couples you to a base class's internals and is rigid; composition stays flexible.
   Reserve inheritance for genuine subtype relationships, not code reuse.

2. **Encapsulation.** Hide internal state behind a narrow public interface so the object controls its own invariants.
   Expose intent (methods), not raw fields to be poked; a leading underscore marks internals (see `write-python`).

3. **Program to an interface, not an implementation.** Depend on an abstraction so implementations are swappable.
   In Python that's usually a `typing.Protocol` (structural), not a base class.

4. **Keep hierarchies shallow.** One or two levels.
   Deep trees are fragile and hard to follow; if you're reaching for a third level, reconsider with composition.

5. **Immutable where you can.** Even in OOP, prefer immutable value objects (frozen dataclasses) for data; reserve mutability for things that genuinely model changing state.

## SOLID

The classic OOP design-principle set.
Several principles span paradigms — cross-references noted so you see they aren't OOP trivia:

- **S — Single Responsibility.** One reason to change per class.
  (General — cf. cohesive modules in `write-python`, small functions in `be-functional`.)
- **O — Open/Closed.** Open to extension, closed to modification.
  (Covered in depth by `be-functional`'s expression-problem section — add behaviour by adding code, not editing existing code.)
- **L — Liskov Substitution.** A subtype must work anywhere its base does, honouring the base's contract (don't strengthen preconditions or weaken postconditions).
  The genuinely OOP one — a broken override here is a real bug.
- **I — Interface Segregation.** Many small, focused interfaces beat one fat one; a client shouldn't depend on methods it doesn't use.
  In Python, small `Protocol`s.
- **D — Dependency Inversion.** Depend on abstractions, not concretions, and inject dependencies rather than hard-wiring them.
  (This *is* the dependency injection in `be-functional` — pass collaborators in.)

## Design patterns — and their simpler forms

Patterns are shared vocabulary, but many classic (GoF) patterns are workarounds for features Python already has.
Recognise the pattern, then reach for the **simplest form** that solves it (KISS/YAGNI — see `write-python`); don't cargo-cult a Java-style class where a function does.

Patterns that usually **collapse** in Python:

| Pattern | Simpler Python form |
|---|---|
| Strategy | pass a **function** |
| Command | a **function** (or `functools.partial`) |
| Factory | a **function** or `classmethod` |
| Singleton | a **module** (imported once) |
| Observer | a list of **callbacks** / pub-sub |
| Template Method | pass in the varying **functions**, or a base hook |
| Iterator | a **generator** / `__iter__` |
| Visitor | `functools.singledispatch` or `match` (see `be-functional`) |

Patterns that stay **genuinely useful** as classes:

- **Adapter** — wrap an incompatible interface to fit the one you need.
- **Decorator** (structural) — wrap an object to add behaviour transparently.
- **Composite** — treat a tree of objects uniformly (nodes and leaves share an interface).
- **State** — behaviour changes with internal state (a state machine).
- **Facade** — a simple interface over a complex subsystem.

## Things to avoid

- **Inheritance for code reuse** — use composition; inherit only for true is-a.
- **Deep hierarchies and god classes** — split responsibilities.
- **Getters/setters for everything** — expose behaviour, or a `@property` for computed/validated access; don't Java-ify plain data.
- **Mutable global singletons** — hard to test and reason about; inject instead.
- **Premature abstraction** — no base class or interface until there's a second implementation (YAGNI; see `write-python`).

## Language idioms

- **Python** → `references/python.md` (dataclasses, `Protocol` vs ABC, properties, class/staticmethods, dunders, and patterns in Python).
