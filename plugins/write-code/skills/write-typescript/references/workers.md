# Write TypeScript for Cloudflare Workers

The rules in `SKILL.md` hold here; this is how they land in a Worker, whose configuration, generated types and test plugin `write-entry-points`' TypeScript reference sets up, and whose place among the hosts is `deploy-project`'s.
A Worker is a driver like any other (`write-entry-points`): the handler reads the request, calls pure functions and renders a response, so the logic is tested without the runtime.

## The handler

- **Export the handler object as the module's one default export, checked with `satisfies ExportedHandler<Env>`**, which types each handler's arguments without widening the object (developers.cloudflare.com, Fetch and Scheduled handlers, read 2026-11-21).
- **`Env` is generated, never written**: `wrangler types` writes it from the configuration's bindings, so a binding renamed there fails to compile here; Cloudflare's best practices say the same (Workers best practices, read 2026-11-21).
- **Build the handler from its dependencies**, so a test passes a fake store or clock without casting an environment; a value read from a binding is checked like any other outside value:

```ts
import { z } from "zod";

export interface Store {
  readonly readCount: (key: string) => Promise<number | undefined>;
}

const Query = z.object({ key: z.string().regex(/^[a-z0-9-]{1,64}$/) });

/** Build the Worker's fetch handler over a store. */
export function createFetch(store: Store) {
  return async (request: Request): Promise<Response> => {
    const url = new URL(request.url);
    const query = Query.safeParse(Object.fromEntries(url.searchParams));
    if (!query.success) {
      return problem(422, "The key must be 1 to 64 letters, digits or dashes.");
    }
    const count = await store.readCount(query.data.key);
    if (count === undefined) {
      return problem(404, `No count for ${query.data.key}.`);
    }
    return Response.json({ key: query.data.key, count });
  };
}

function problem(status: number, detail: string): Response {
  return Response.json(
    { type: "about:blank", status, detail },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}
```

```ts
import { z } from "zod";
import { createFetch, type Store } from "./handler.ts";

const Count = z.coerce.number().int().nonnegative();

function kvStore(namespace: KVNamespace): Store {
  return {
    readCount: async (key) => {
      const value = await namespace.get(key);
      return value === null ? undefined : Count.parse(value);
    },
  };
}

export default {
  fetch: (request, env) => createFetch(kvStore(env.COUNTS))(request),
} satisfies ExportedHandler<Env>;
```

## Requests and state

- **No request's data at module level**: an isolate serves many requests, so a module variable set by one is read by the next (Workers best practices, Do not store request-scoped state in global scope).
- **Every promise is awaited or handed to `ctx.waitUntil`**, and `waitUntil` only for work the response does not depend on, such as writing a cache; it extends the Worker's life by up to 30 seconds after the response, and anything left after that is cancelled (Context API, read 2026-11-21).
- **A key taken from the request is checked with `Object.hasOwn`** before it indexes an object, since `"__proto__" in {}` is `true` and the lookup reaches the prototype.
- **Errors leave as problem details**, RFC 9457, from one function the handler calls, as `design-interface`'s API reference sets; nothing below the handler builds a `Response`, a method the route does not serve answers `405` with an `Allow` header, and a browser's cross-origin call is allowed only from the origins `secure-project`'s Guard what is served names.

## Secrets and settings

- **A secret is set with `wrangler secret put` and read from `env`**, never written into `vars`, which ship in the configuration file; the generated `Env` lists it once the configuration declares it under `secrets.required`.
- **Settings are read from `env` in the handler and passed down as arguments**, as the composition root does in any driver (`write-entry-points`), so no function below the handler sees `env`.
