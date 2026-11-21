# Be functional in TypeScript

The language-agnostic principles are in `SKILL.md`; this is how they land in TypeScript, under `write-typescript`'s conventions.

## Immutability

A record is an interface of `readonly` fields and a list a `readonly T[]` (`write-typescript`, Types), so the compiler refuses a mutation and the code returns a new value instead:

- **Update a record with a spread**, `{ ...order, status: "shipped" }`, and a map with `new Map([...map, [key, value]])`.
- **Reorder with the copying methods** — `toSorted`, `toReversed`, `toSpliced`, `with` — since `sort`, `reverse` and `splice` change the array in place, including one a caller or React state still holds; `readonly T[]` has only the copying ones.
- **Group with `Map.groupBy` or `Object.groupBy`** (ES2024) rather than a loop filling a mutable map:

```ts
export interface Order {
  readonly id: string;
  readonly customer: string;
  readonly totalMinor: number;
}

/** Total each customer's orders, in minor units. */
export function totalByCustomer(
  orders: readonly Order[],
): ReadonlyMap<string, number> {
  const byCustomer = Map.groupBy(orders, (order) => order.customer);
  return new Map(
    [...byCustomer].map(([customer, placed]) => [
      customer,
      placed.reduce((sum, order) => sum + order.totalMinor, 0),
    ]),
  );
}
```

`Object.freeze` adds nothing the types do not already enforce, and `structuredClone` is for the rare deep copy of data that arrived mutable.

## Algebraic data types and pattern matching

A product type is an interface and a sum type a discriminated union, taken apart by an exhaustive `switch` (`write-typescript`, Types).
**Where every branch only returns a value, write the lookup** `SKILL.md` describes as a `Record` over the union, checked with `satisfies`, so a new member fails to compile until it has an entry.

## Specialise and compose

Write the generic function and derive the variants as named functions that call it:

```ts
export interface Page<T> {
  readonly items: readonly T[];
  readonly next: string | undefined;
}

export type FetchPage<T> = (cursor: string | undefined) => Promise<Page<T>>;

/** Collect pages until there are none left or the limit is reached. */
export async function fetchMany<T>(
  fetchPage: FetchPage<T>,
  { limit }: { readonly limit: number },
): Promise<readonly T[]> {
  const collected: T[] = [];
  let cursor: string | undefined;
  do {
    // oxlint-disable-next-line eslint/no-await-in-loop -- each cursor comes from the page before
    const page = await fetchPage(cursor);
    collected.push(...page.items);
    cursor = page.next;
  } while (cursor !== undefined && collected.length < limit);
  return collected.slice(0, limit);
}

/** Fetch the first item, if there is one. */
export async function fetchFirst<T>(
  fetchPage: FetchPage<T>,
): Promise<T | undefined> {
  const [first] = await fetchMany(fetchPage, { limit: 1 });
  return first;
}
```

- **A local accumulator may mutate** inside the function that owns it, as `collected` does above, since nothing outside can see it; the function stays pure to its callers.
- **A named function over a `pipe` or `compose` helper**: it is typed, documented and searchable, and TypeScript infers a long `pipe` poorly, so its errors land far from the step that caused them.
- **A closure is the partial application**: `(cursor) => fetchOrdersPage(base, cursor, { signal })` fixes the base and the signal as `functools.partial` would in Python, leaving a `FetchPage` that `fetchMany` takes, with no library.

## Inject impure dependencies

The clock, randomness, `fetch` and the environment arrive as arguments, as `SKILL.md` says; a module with no layers may default one in place, and a core module never does:

```ts
/** Say how long ago an instant was, to the minute. */
export function describeAge(
  instant: string,
  { now }: { readonly now: Date },
): string {
  const minutes = Math.floor((now.getTime() - Date.parse(instant)) / 60_000);
  return minutes < 1 ? "just now" : `${minutes} min ago`;
}
```

## Libraries

The language covers composition, immutability and dispatch; each library earns its place only for the case named.

- **No `fp-ts` or Effect**: each brings its own `Result` and `pipe`, which change every caller's shape, against `write-typescript`'s error model.
- **No `lodash` or `ramda`** for what the platform has: `Map.groupBy`, `toSorted`, `structuredClone`, `Array.prototype.flatMap`.
- **`immer`** only for a reducer that updates state nested three or more levels deep, where spreads at every level hide the one field that changed; keep the state flat first (`write-typescript`'s React reference, State).
