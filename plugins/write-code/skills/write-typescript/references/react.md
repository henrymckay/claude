# Write TypeScript with React

The rules in `SKILL.md` hold here; this is how they land in a React 19 front end built with Vite, Tailwind and shadcn/ui, whose folder and data module `write-entry-points` lays out and whose look is `design-interface`'s.
React's own rules come first: components and hooks are pure, props and state are never mutated, and hooks are called only at the top level of a component or another hook (react.dev, Rules of React, read 2026-11-21); the linter's React rules hold them, React Compiler's checks among them.

## Components

- **One exported function component per file, by name with its `<Component>Props` interface**, private subcomponents beside it, props destructured in the signature and `children` typed `React.ReactNode`; no `React.FC`, which adds nothing the props interface lacks.
- **A component renders; it does not compute.** Shaping data for a screen — a pivot, a sort, a total, a label — is a pure function in `lib/`, tested there (`write-tests`); a view past a couple of hundred lines that wires data, formats it and lays out tables is three files.
- **JSX that repeats becomes a component, and classes that repeat become a variant of one**, since a copied block drifts: a pager copied into two screens, or the same cell classes on every table, is one component not yet extracted.
- **A screen loaded on demand takes its named export through `lazy`**, so it needs no default export:

```tsx
import { lazy } from "react";

export const Reports = lazy(() =>
  import("@/views/reports.tsx").then((module) => ({ default: module.Reports })),
);
```

## State

- **Keep the least state that can produce the screen, and compute the rest during render** — a filtered list, a total, a label are expressions over state, never state of their own (react.dev, Choosing the State Structure).
- **One `status` union over several booleans**, so impossible pairs such as loading and failed cannot be represented, and the error carries what went wrong.
- **Store an id, not a copy** of a selected item, so an edit to the list reaches the selection.
- **State a person can link to — the screen, a filter, a selected item — lives in the URL**, read through one hook over `useSyncExternalStore` or the router, so a reload or a shared link reopens the same view.
- **Reset a component's state by giving it a `key`**, never by an effect that watches a prop.

## Effects

**An effect synchronises with something outside React** — a chart instance, a subscription, a timer, a socket — and nothing else.
Data derived from props or state is computed in render, and work caused by a click runs in the click's handler (react.dev, You Might Not Need an Effect).

- **Its dependencies are complete**, as the linter's `exhaustive-deps` checks, and its cleanup undoes what it started; a value the effect reads without wanting to re-run on comes through `useEffectEvent`, never a ref copied in render or a missing dependency.

```tsx
import { useEffect, useEffectEvent, useRef } from "react";

export interface MeasuredProps {
  readonly onResize: (width: number) => void;
}

/** Report the element's width whenever it changes. */
export function Measured({ onResize }: MeasuredProps) {
  const box = useRef<HTMLDivElement>(null);
  const handleResize = useEffectEvent((width: number) => {
    onResize(width);
  });

  useEffect(() => {
    const element = box.current;
    if (element === null) {
      return undefined;
    }
    const observer = new ResizeObserver(([entry]) => {
      if (entry !== undefined) {
        handleResize(entry.contentRect.width);
      }
    });
    observer.observe(element);
    return () => {
      observer.disconnect();
    };
  }, []);

  return <div ref={box} className="h-full w-full" />;
}
```

## Configuration

**Read the front end's settings once, in `lib/config.ts`, from `import.meta.env`, parsed by a schema**, so a missing variable fails at start with its name rather than as a request to `undefined/orders`; only variables prefixed `VITE_` reach the page, and every one of them is public, so none holds a secret (`secure-project`):

```ts
import { z } from "zod";

const Config = z.object({ VITE_API_BASE: z.url() });

export const config = Config.parse(import.meta.env);
```

## Data fetching

**Fetch server data with TanStack Query**, over requests in effects, whenever more than one screen reads the same data, the data polls, or a screen must keep its last answer while the next loads — react.dev itself points there rather than at effects (Synchronizing with Effects, Fetching data).
One trial dashboard hand-rolled module-level caches, a poll and three copies of a stale-response guard, which is that library rebuilt with its bugs.

- **Every request lives in the data module** `write-entry-points` names, returning parsed types (`SKILL.md`, Check, never assert), and exports a `queryOptions` per query, so its key and function are written once and a component never builds a URL.
- **One `QueryClient`, made in `main.tsx`, with a `staleTime` set**, since the default of zero refetches on every mount and every return to the tab; a change goes through `useMutation`, whose success invalidates the keys it touched.
- **Each query takes the `signal` TanStack Query passes**, which aborts when the query becomes out of date or inactive (tanstack.com, Query Cancellation).
- **The screen renders every status**: pending, error and data, with the empty case its own state (`design-interface`, States); the error is a sentence for the person, never the exception's text, which for a schema failure is a JSON list of issues.

```ts
import { queryOptions } from "@tanstack/react-query";
import { config } from "@/lib/config.ts";
import { fetchOrders } from "@/lib/data.ts";

/** The latest orders, refreshed every minute. */
export const ordersQuery = queryOptions({
  queryKey: ["orders"],
  queryFn: ({ signal }) => fetchOrders(config.VITE_API_BASE, { signal }),
  refetchInterval: 60_000,
});
```

```tsx
import { useQuery } from "@tanstack/react-query";
import { ordersQuery } from "@/lib/queries.ts";

/** List the latest orders. */
export function OrderList() {
  const orders = useQuery(ordersQuery);

  if (orders.status === "pending") {
    return <output>Loading orders…</output>;
  }
  if (orders.status === "error") {
    return <p role="alert">Orders could not load. Try again in a minute.</p>;
  }
  if (orders.data.length === 0) {
    return <p>No orders yet.</p>;
  }
  return (
    <ul>
      {orders.data.map((order) => (
        <li key={order.id}>{order.id}</li>
      ))}
    </ul>
  );
}
```

A single screen that fetches once may use an effect instead, aborting its request in the cleanup as react.dev's example ignores a stale one, written once as a hook rather than copied into each screen.

## Errors

**A render error reaches one error boundary at the root**, which shows a sentence and a way to reload instead of a blank page; React still needs a class component for a boundary (react.dev, Component), the one class a front end writes, and `createRoot`'s `onUncaughtError` reports what it caught.
A failed request is not a render error: it is the query's `error` status, shown in place by the screen that asked.

## Accessibility

**Use the element that already does the job** — `button` for an action, `a` for a place, `label` for every input, `table` with `th scope` for tabular data — and ARIA only where no element exists, since a `role` promises the keyboard behaviour that comes with it (W3C ARIA Authoring Practices, No ARIA is better than bad ARIA).

- **Every `button` has a `type`**, and one with only an icon has an `aria-label`, its icon `aria-hidden`.
- **A dialog, menu, popover or combobox is shadcn/ui's**, built on primitives that trap and restore focus and handle the keys; a hand-made `role="dialog"` in one trial had neither.
- **A clickable table row keeps a real link or button inside it**, since a row's `onClick` has no keyboard path.
- **A chart drawn on a canvas has `role="img"` and an `aria-label`** stating what it shows, with the figures reachable as text elsewhere on the screen (`design-interface`).
- **Tests find elements by role and name** (`write-tests`), which fails when the markup stops being accessible; the linter's `jsx-a11y` plugin catches the static cases.

## Styling

- **Tailwind classes in the component, merged with the `cn()` helper `shadcn init` writes** where some are conditional; inline `style` only for geometry computed at run time.
- **Every class name appears whole in the source**: Tailwind finds classes by scanning the files as text, so `` `bg-${tone}-500` `` is never generated (tailwindcss.com, Detecting classes in source files); map a prop to complete class strings instead.
- **Colour comes from the house tokens** (`design-interface`'s web reference), never a palette class such as `text-red-500`, so dark mode and a token change reach every screen.
- **A component with variants declares them with `cva`**, as shadcn/ui's own do, so a variant is a prop with a closed set of values, and sets `defaultVariants`, since `VariantProps` makes every variant optional:

```tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils.ts";

const chip = cva("inline-flex items-center rounded-md px-2 text-xs", {
  variants: {
    tone: {
      good: "bg-good/15 text-good",
      warning: "bg-warning/15 text-warning",
      critical: "bg-critical/15 text-critical",
    },
  },
  defaultVariants: { tone: "good" },
});

export interface StatusChipProps extends VariantProps<typeof chip> {
  readonly label: string;
  readonly className?: string;
}

/** Show a short status in its tone. */
export function StatusChip({ label, tone, className }: StatusChipProps) {
  return <span className={cn(chip({ tone }), className)}>{label}</span>;
}
```

- **shadcn/ui's components are the project's own code**, added with `npx shadcn@latest add` into `components/ui/` and edited there; they are not upgraded like a dependency.

## Memoisation

**Turn React Compiler on in a new project and write no `useMemo`, `useCallback` or `memo` by hand**: the compiler memoises what each component reads, and hand-placed hooks with wrong dependencies were the trial's memoisation bugs (react.dev, React Compiler 1.0, stable since 2025-10-07; `write-entry-points` wires it).
In a project without the compiler, memoise only what a profile shows slow; in one that has it, leave existing memoisation alone unless a test covers its removal, as react.dev advises.
