---
name: write-typescript
description: >-
  In-code conventions for TypeScript that tooling can't decide — strict
  settings, interfaces and unions, unknown checked at the boundary, naming,
  modules, errors and async, with React and Cloudflare Worker references. Load
  it before the first line of any TypeScript or TSX, even a component answered
  inline. Use whenever writing, editing or reviewing TypeScript — even if the
  user just says "add a screen" or "fix this component". Not for the scaffold
  or toolchain, which is write-entry-points'.
---

# Write TypeScript

The judgement calls that make TypeScript correct and readable — the decisions `tsc`, the linter and the formatter leave to you.
It is the baseline that `be-functional`, `be-oop` and `write-tests` layer on in TypeScript, as `write-python` is in Python; React lives in `references/react.md`, a Cloudflare Worker in `references/workers.md`, the scaffold and the toolchain's files in `write-entry-points`' TypeScript reference, and how a screen looks in `design-interface`.
Three mistakes account for most of what goes wrong: telling the compiler what a value is instead of checking it — `as Row[]` on parsed JSON, `!` on a lookup — so a wrong shape surfaces three screens later as `undefined`; leaving the strict checks out of one package's `tsconfig` while writing as if they were on; and linting without type information, so a floating promise or an unhandled variant passes.

**In an existing project, ask first.** Where a codebase already has an established style, check with the user whether to match it or apply this skill, and prefer this skill unless they choose to match.

## Compiler, linter and formatter

`tsc` type-checks, `oxlint` lints with type information and Prettier formats; leave them what they decide, and write code that passes all three with no suppression.
The versions checked here: TypeScript 7.0.2, oxlint 1.94.0 with `oxlint-tsgolint` 7.0.2007, Prettier 3.10.1 (2026-11-21); `write-entry-points`' TypeScript reference holds the files.

**Every `tsconfig` in the repository sets `strict` and the checks below, the Worker's and the tests' included.**
TypeScript 7 turns `strict` on by default, but write it, since a reader and an older tool see the file, not the default; a package whose checks are left out still collects non-null assertions written as if they were on, each checking nothing.

- **`noUncheckedIndexedAccess`** — an index or record lookup is `T | undefined`, so a miss is handled where it happens instead of read as a value.
- **`noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noUnusedLocals`, `noUnusedParameters`.**
- **`verbatimModuleSyntax` and `erasableSyntaxOnly`** — a type-only import says `import type`, and no syntax with runtime behaviour of TypeScript's own (`enum`, `namespace`, constructor parameter properties) compiles, so a file means the same with its types stripped, which is how Vite, Vitest and Node run it.

`exactOptionalPropertyTypes` stays off: under it a component that forwards an optional prop it received (`className={className}`) fails to compile, which is why TypeScript keeps it out of `strict`.

**Lint with oxlint in type-aware mode**, its correctness, suspicious and perf categories as errors plus the rules this skill names, the `no-unsafe-*` family among them, since `response.json()` and `JSON.parse` return `any`, which no assertion rule sees.
ESLint with `typescript-eslint` is the mature alternative, but `typescript-eslint` 8.73 declares TypeScript below 6.1 and cannot read TypeScript 7, which ships no compiler API before 7.1 (typescript-eslint.io dependency versions; devblogs.microsoft.com, TypeScript 7.0, read 2026-11-21); reach for it, on TypeScript 6.0.3, only for a rule oxlint lacks, at the cost of a second compiler.

**Prettier formats**, over `oxfmt`, still `0.x` with no stable release, and Biome, which departs from Prettier's output on purpose.
The one layout decision left to you: an object literal whose first property starts on a new line stays expanded, so open one that way when its siblings are long, as `write-python` uses the trailing comma.

## Types

- **Annotate every exported function's parameters and return type**, and let locals and inline callbacks infer, so a change that alters what a function returns fails at the function rather than at each caller.
- **`interface` for an object shape, `type` for everything else** — unions, functions, mapped and derived types — the handbook's own heuristic and what the linter's `consistent-type-definitions` holds; one interface extending another also checks faster than an intersection (typescriptlang.org, Everyday Types).
- **Fields `readonly`, and every array parameter `readonly T[]`**, so the compiler stops a function changing what its caller owns; return a new array instead.
A type inferred from a schema is mutable, so export it as `Readonly<z.infer<typeof Schema>>`.
- **A closed set is a union of string literals, derived from an `as const` array where code lists it**, never an `enum`, which `erasableSyntaxOnly` rejects.
- **`satisfies` checks a literal against a type without widening it**, so a lookup keyed by a union fails to compile when the union grows a member, and its values keep their literal types:

```ts
export const STATUSES = ["queued", "running", "done"] as const;

export type Status = (typeof STATUSES)[number];

export const STATUS_LABELS = {
  queued: "Waiting",
  running: "In progress",
  done: "Finished",
} satisfies Record<Status, string>;

export function isStatus(value: string): value is Status {
  return STATUSES.some((status) => status === value);
}
```

- **A variant that carries data is a discriminated union on `kind`**, taken apart with a `switch` that ends in a `never` check, which turns a forgotten variant into a compile error; the linter's `switch-exhaustiveness-check` reports it too, and its `consistent-return` fails a value-returning `switch` left without the `default`:

```ts
export type Shape =
  | { readonly kind: "circle"; readonly radius: number }
  | { readonly kind: "square"; readonly side: number };

export function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "square":
      return shape.side ** 2;
    default:
      return assertNever(shape);
  }
}

function assertNever(value: never): never {
  throw new TypeError(`Unhandled variant: ${JSON.stringify(value)}`);
}
```

- **Brand an identifier that must not mix** with another of the same base type, so the compiler catches a swapped pair; branding is the playground's nominal-typing pattern, not a language feature, so each brand costs a type predicate and a constructor, which together are the one place the brand is made:

```ts
export type UserId = string & { readonly __brand: "UserId" };

function isUserId(raw: string): raw is UserId {
  return /^u_[a-z0-9]+$/.test(raw);
}

export function toUserId(raw: string): UserId {
  if (!isUserId(raw)) {
    throw new RangeError(`Not a user id: ${raw}`);
  }
  return raw;
}
```

## Check, never assert

**Every value from outside the program is `unknown` until a check proves its shape**: a response body, `JSON.parse`, a URL parameter, `localStorage`, a message from a worker, a caught error.
Where a platform API hands back `any`, declare the variable `unknown` (`const body: unknown = await response.json()`) or pass it straight to the schema; the linter's `no-unsafe-assignment` fails `const rows: Row[] = await response.json()`, which compiles.
**No `as` but `as const`, and no `!`** — the linter's `consistent-type-assertions` set to `never` and `no-non-null-assertion` hold both.
An assertion is a claim the compiler stops checking, so the wrong shape travels until something reads a field that is not there; a type predicate is a claim too, so it holds the check that makes it true, as `isUserId` does above.

**Parse each outside value with a `zod` schema at the adapter that receives it**, and take its type from the schema with `z.infer`, so the check and the type are one fact.
Hand-written guards drift field by field, until a data module narrows some fields of a row and casts the next one beside them.
`valibot` is the smaller alternative, under a kilobyte for a few schemas against Zod's few kilobytes; reach for it where bundle size is a measured budget.

- **Wrong** — `return (await response.json()) as Order[];` compiles, and a renamed field is `undefined` in every screen.
- **Right** — the schema rejects the response at the edge, naming the field:

```ts
import { z } from "zod";
import { HttpError } from "@/lib/errors.ts";

const Order = z.object({
  id: z.string(),
  placedAt: z.iso.datetime({ offset: true }),
  totalMinor: z.int(),
  currency: z.string().length(3),
});

export type Order = Readonly<z.infer<typeof Order>>;

export async function fetchOrders(
  base: string,
  { signal }: { readonly signal: AbortSignal },
): Promise<readonly Order[]> {
  const response = await fetch(new URL("orders", base), { signal });
  if (!response.ok) {
    throw new HttpError(`orders: HTTP ${response.status}`, {
      status: response.status,
    });
  }
  return z.array(Order).parse(await response.json());
}
```

**Decide per field whether a gap rejects or falls back**, in the schema: a required field rejects the whole response, since a quiet default is a wrong figure; an optional one is `.optional()` or `.catch(...)` with the fallback named.
`String(row.name)` on an unchecked field turns a missing value into the text `"undefined"`.

**Narrow with the language where no schema is needed** — `typeof`, `in`, `instanceof`, a comparison, a type predicate — and use `??`, never `||`, for a default, since `||` replaces `0` and `""` too.
`new URL(path, base)` resolves like a link, so the base keeps its trailing slash and the path has none, or the base's last segment is dropped, as `write-python`'s `urljoin` idiom says.

## Time and money

- **An instant crosses the wire as an ISO 8601 string with its offset, a calendar day as a `YYYY-MM-DD` string**, and becomes a `Date` only to format it.
`new Date("2026-11-21")` is midnight UTC, which a viewer west of Greenwich sees as 20 November; a day stays a string, and every formatter passes `timeZone` explicitly (`Intl.DateTimeFormat`).
- **Money is an integer of minor units with its currency, never a floating-point sum** (`0.1 + 0.2` is `0.30000000000000004`), formatted by `Intl.NumberFormat` with `style: "currency"`; amounts past 2^53 minor units arrive as decimal strings.
A currency's minor units are not always hundredths — the yen has none, the Bahraini dinar three — so divide by the power of ten its formatter's `resolvedOptions().maximumFractionDigits` gives.

## Comments and docs

**Every exported function, type and component gets a `/** … */` summary line**, imperative, saying what the name does not, since the editor shows it at every call site; add `@throws` for an error a caller should handle, and a sentence only for a unit, a side effect or an invariant the signature cannot state.
Types stay out of the comment, as `write-python`'s docstrings keep them out.

Write self-documenting code instead of `//` comments, as `write-python`'s Comments says.
**A suppression names its rule and its reason** — `// oxlint-disable-next-line typescript/no-explicit-any -- the library's own type` — and the configuration reports one that no longer suppresses anything; `@ts-expect-error` with a reason, never `@ts-ignore`, since the first fails to compile once the error it hid is gone.

## Modules and imports

- **Named exports only**, except where a tool requires a default: a configuration file and a Worker's handler.
A `.tsx` file exports components alone, with constants and variants in a sibling `.ts`, or Vite's Fast Refresh reloads the whole page on each edit; the linter's `only-export-components` holds it.
A default export takes whatever name each importer gives it, so a rename misses importers and a search for the name misses uses; `React.lazy` takes a named export too (`references/react.md`).
- **No barrel files** — an `index.ts` re-exporting a folder — since Vite then fetches and transforms every file in the folder for one import (vite.dev, Performance, read 2026-11-21); import the file that defines the name.
- **Import with the file's extension, through the `@/` alias for anything under `src/`** outside the importing file's folder: `import { fetchOrders } from "@/lib/data.ts"`.
Vite resolves an explicit path without probing, and `shadcn` writes its components against the same alias; files `shadcn add` writes keep their imports as written.
- **Name files in kebab case, after the one thing they export** — `order-table.tsx` for `OrderTable` — which is what `shadcn add` writes; macOS's file system ignores case, so a rename that changes only case is invisible to git there.
- **No mutable state at module level**, except a cache built behind a function the tests can reset: a module is loaded once per page, and once per isolate in a Worker, so state there leaks across tests and requests.

## Naming

Values and functions in camelCase, types, interfaces and components in PascalCase, and a module-level constant that is a literal table or a fixed value in UPPER_SNAKE_CASE.
The verb and noun rules are `write-python`'s Naming, in camelCase: `fetchOrders`, `parseCsv`, `buildIndex`, and a bare noun only for a cheap value.
A component's props are `<Component>Props`, exported beside it, so a reader finds a component's contract by its name.

## Arguments

TypeScript has no keyword arguments, so **a function takes its subject positionally and everything else in an options object**, destructured in the signature; two parameters of the same type swap silently, and a bare `true` says nothing at the call site:

```ts
export interface RenderOptions {
  readonly table?: boolean;
  readonly width?: number;
}

export function render(
  rows: readonly string[],
  { table = false, width = 80 }: RenderOptions = {},
): string {
  const lines = rows.map((row) => row.slice(0, width));
  return table
    ? lines.map((line) => `| ${line} |`).join("\n")
    : lines.join("\n");
}
```

Order the options alphabetically in the interface and at each call site, as `write-python`'s Ordering says, unless they follow the data flow.

## Errors

**Throw only `Error` and its subclasses, defined in one `errors.ts`** per package, each named for what went wrong and carrying its `cause`; the linter's `only-throw-error` holds the first half.

```ts
export class HttpError extends Error {
  override readonly name = "HttpError";
  readonly status: number;

  constructor(
    message: string,
    { status, cause }: { readonly status: number; readonly cause?: unknown },
  ) {
    super(message, { cause });
    this.status = status;
  }
}
```

- **The error model is `write-python`'s**: an adapter converts a library's failure at its seam, a driver decides what the person sees — a screen's error state, a Worker's error response — and nothing in between catches.
- **A caught value is `unknown`**; narrow it with `instanceof` before reading it, and rethrow what you did not expect.
- **Return `T | undefined` only for a lookup miss the caller always branches on**; every other failure throws, and no `Result` library (`neverthrow`, Effect) is used, since it changes every caller's shape to carry what a thrown error carries for free.
- **Never swallow a rejection**: `.catch(() => undefined)` turns a failed poll into a page that silently stops updating.

## Async

- **Every promise is awaited, returned or passed on**; `void` marks one deliberately left, only where its own handler catches, and the linter's `no-floating-promises` and `no-misused-promises` hold the rest.
- **Every request takes an `AbortSignal` from its caller** — an effect's cleanup, a query's signal, a Worker request's — and a timeout joins it with `AbortSignal.any([signal, AbortSignal.timeout(ms)])`, so leaving a screen cancels its requests.
- **`Promise.allSettled` where one failing request must not lose the others' answers**, since `Promise.all` rejects on the first.

## Simplicity

`write-python`'s Simplicity holds in TypeScript as written.

## Avoid

- **Any abstraction before a second case**, as `write-python` says; a `utils.ts` of unrelated helpers is one in waiting, the `lib/utils.ts` that `shadcn init` writes for `cn()` excepted.
- **A class where a function and a closure do** (`be-functional`), and `namespace`, `enum` and decorators, which `erasableSyntaxOnly` or the house rules exclude; a `declare namespace` that only augments a library's types, as a Worker's main-module declaration does, is a type and allowed.
- **`any`** — `unknown` and a check, or a generic.
- **`Object.keys` over a typed object to look values up**: its keys are `string[]`, so the lookup needs the assertion this skill forbids; iterate `Object.entries` or the `as const` list instead.

## Language specifics

Read the file for what you're writing:

- **React** → `references/react.md` (components and props, state, effects, configuration, data fetching, errors, accessibility, styling with Tailwind and shadcn/ui, memoisation).
- **Cloudflare Workers** → `references/workers.md` (the handler, generated types, request state, errors as responses, `waitUntil`).

Add a new `references/<framework>.md` when you work in another rather than adding its specifics to this file.
