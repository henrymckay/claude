# Write tests in TypeScript

The language-agnostic principles are in `SKILL.md`; this is how they land in TypeScript with Vitest, Testing Library and `fast-check`.
`write-typescript` sets the code's conventions, and `write-entry-points`' TypeScript reference sets up the runner, its environments and coverage.

## Pick a layout

- **A test sits beside the module it covers**, `order-table.tsx` beside `order-table.test.tsx`, so a file moved or deleted takes its test with it; a Worker's tests through the runtime sit in its own `test/`, run as a second Vitest project (`write-entry-points`).
- **The shared beats live in `src/test/`**: `given.ts` for builders and fixtures, `then.ts` for domain assertions, `reference.ts` for an oracle.
- **The default environment is `node`**; a file that renders a component opts into `jsdom` with `// @vitest-environment jsdom` on its first line, so a pure test never pays for a simulated browser (vitest.dev, Test Environment, read 2026-11-21).

## Given, when, then

**Name a test with the claim it checks, `when <action>, then <outcome>`**, as a string, since Vitest prints it on failure: `test("when the orders load, then each is listed", …)`.

**Givens arrive through Vitest's test context**, declared with `test.extend`, never built in the body or held in a module-level variable; a fixture may take another, and a plain value is a fixture too:

```ts
import { expect, test as base } from "vitest";

interface Given {
  readonly prices: readonly number[];
  readonly expectedTotal: number;
}

const test = base.extend<Given>({
  prices: [120, 80, 300],
  expectedTotal: 500,
});

function total(prices: readonly number[]): number {
  return prices.reduce((sum, price) => sum + price, 0);
}

test("when totalled, then the prices sum", ({ prices, expectedTotal }) => {
  const summed = total(prices);
  expect(summed).toBe(expectedTotal);
});
```

**A fixture whose value is itself a function, such as a fake clock, is wrapped in one**, `now: async ({}, provide) => provide(() => fixed)`, since Vitest calls a function given as a fixture to build it.
**A fixture that builds its value names its callback `provide`**, as in `async ({ prices }, provide) => { await provide(…) }`, never the `use` Vitest's docs show: Vitest passes it by position, and the linter's `rules-of-hooks` reads a call to `use` as React's hook outside a component and fails the file (oxlint 1.94.0, measured).

`toEqual` for a value, `toStrictEqual` where an `undefined` field must differ from an absent one; a domain claim several tests share is a function in `then.ts` that calls `expect` itself.

## Many inputs

**A table of independent cases is `test.for`**, each row reported on its own, its values typed from an `as const` array:

```ts
import { expect, test } from "vitest";

function grade(score: number): "pass" | "fail" {
  return score >= 50 ? "pass" : "fail";
}

test.for([
  [49, "fail"],
  [50, "pass"],
  [100, "pass"],
] as const)("when %i is graded, then it is a %s", ([score, expected]) => {
  expect(grade(score)).toBe(expected);
});
```

**A property is `fast-check`**, run inside a test with `fc.assert`, its arbitraries shaped toward the states the property must reach as `SKILL.md` says:

```ts
import * as fc from "fast-check";
import { expect, test } from "vitest";

function sortAscending(values: readonly number[]): readonly number[] {
  return values.toSorted((left, right) => left - right);
}

test("when sorted, then the values are the input's, each at most the next", () => {
  fc.assert(
    fc.property(fc.array(fc.integer()), (values) => {
      const sorted = sortAscending(values);
      const inOrder = sorted.slice(1).every((value, index) => {
        const before = sorted[index] ?? value;
        return before <= value;
      });
      expect(inOrder && sameMembers(sorted, values)).toBe(true);
    }),
  );
});

function sameMembers(
  left: readonly number[],
  right: readonly number[],
): boolean {
  const counts = new Map<number, number>();
  for (const value of left) counts.set(value, (counts.get(value) ?? 0) + 1);
  for (const value of right) counts.set(value, (counts.get(value) ?? 0) - 1);
  return [...counts.values()].every((count) => count === 0);
}
```

The property checks the output is a reordering of the input as well as ordered, since `() => []` is ordered too; it asserts with `expect` rather than returning a boolean, since the linter's `vitest/expect-expect` fails a test with no assertion in it.

## Components

**Render through Testing Library, act through `userEvent`, and find elements by role and name**, as a person and a screen reader do; `getByTestId` only where nothing a person perceives identifies the element (testing-library.com, Queries, priority).
`userEvent.setup()` before the render, since it simulates the whole interaction where `fireEvent` dispatches one event (Testing Library, user-event, read 2026-11-21).

**The network is the boundary a component test fakes**: spy on `fetch` with a recorded response, made fresh on every call, since a body is read once and a refetch or a retry calls again, so the data module, its schema and the screen all run for real.
A query client per test with retries off, since TanStack Query otherwise retries a failure three times with a delay before the error screen appears:

```tsx
// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test as base, vi } from "vitest";
import { OrderList } from "@/views/order-list.tsx";

interface Given {
  readonly ordersServed: readonly unknown[];
}

const test = base.extend<Given>({
  ordersServed: [
    {
      id: "o-1",
      placedAt: "2026-11-20T09:30:00Z",
      totalMinor: 1250,
      currency: "GBP",
    },
  ],
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function renderScreen(): void {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <OrderList />
    </QueryClientProvider>,
  );
}

test("when the orders load, then each is listed", async ({ ordersServed }) => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
    Response.json(ordersServed),
  );
  renderScreen();
  const items = await screen.findAllByRole("listitem");
  expect(items.map((item) => item.textContent)).toEqual(["o-1"]);
});

test("when the API fails, then the screen says so", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(null, { status: 503 }),
  );
  renderScreen();
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toBe(
    "Orders could not load. Try again in a minute.",
  );
});
```

A screen whose data module reads `lib/config.ts` gets its variables in a test from `.env.test`, which Vite loads when Vitest runs, holding a placeholder base such as `https://api.example.test/`.
Record the response once with a script beside the data, as `SKILL.md` says, and load it in the fixture once a body is longer than a line.
A whole screen in a real browser is the smoke test per screen `SKILL.md` asks for, which `write-entry-points` runs against the built app.

## A Worker

**Test the handler as the function it is**, built from fakes in the `node` environment, so most of its behaviour needs no runtime:

```ts
import { expect, test as base } from "vitest";
import { createFetch, type Store } from "./handler.ts";

interface Given {
  readonly store: Store;
}

const test = base.extend<Given>({
  store: { readCount: async (key) => (key === "visits" ? 3 : undefined) },
});

test("when a known key is asked for, then its count comes back", async ({
  store,
}) => {
  const response = await createFetch(store)(
    new Request("https://worker.test/?key=visits"),
  );
  expect(await response.json()).toEqual({ key: "visits", count: 3 });
});

test("when the key is malformed, then a problem is returned", async ({
  store,
}) => {
  const response = await createFetch(store)(
    new Request("https://worker.test/?key=Bad%20Key"),
  );
  expect(response.status).toBe(422);
  expect(response.headers.get("Content-Type")).toBe("application/problem+json");
});
```

What only the runtime shows — a binding, a cache, `waitUntil`, the scheduled handler — gets a few tests through `@cloudflare/vitest-plugin` in the Worker's `test/`; its predecessor `@cloudflare/vitest-pool-workers` is deprecated and stops at Vitest 4 (npm, read 2026-11-21).

## Coverage and speed

Vitest measures with its `v8` provider, and both levels live in its configuration (`write-entry-points`): every branch for the pure modules under `src/lib/` and a package floor for the rest, each failing the run when missed.
The exhaustiveness guard is the one branch a test cannot reach, and the `v8` provider has no exclusion by pattern, so here alone `SKILL.md`'s rule against line-by-line exclusion bends: `/* v8 ignore next -- @preserve */`, the form Vitest documents, goes on the line above the `default:` that calls `assertNever` and above `assertNever` itself; a hint inside the `default:` leaves the branch counted, and one without `-- @preserve` can be stripped when the file is transformed (vitest.dev, Coverage, read 2026-11-21; Vitest 5.1.1, measured).
Tag a slow test by its file name, `*.slow.test.ts`, and leave that pattern out of the default run.

## Run

```bash
npm test
npm test -- src/lib/format.test.ts
npm test -- -t "when the orders load"
npm run coverage
```
