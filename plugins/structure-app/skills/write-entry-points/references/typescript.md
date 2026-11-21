# Write entry points in TypeScript

The language-agnostic principles are in `SKILL.md`; this is how they land for the two TypeScript drivers the house builds — a web front end with Vite and a Cloudflare Worker — and the toolchain both share.
`write-typescript` sets how the code inside them is written; this file sets up the folders, the files and the commands it relies on.
The versions checked here, on 2026-11-21: Node 24.19.0 with npm 11.17.0, TypeScript 7.0.2, Vite 8.3.8, `@vitejs/plugin-react` 6.3.0, oxlint 1.94.0 with `oxlint-tsgolint` 7.0.2007, Prettier 3.10.1, Vitest 5.1.1, wrangler 4.166.0 and `@cloudflare/vitest-plugin` 1.9.0.

## Node

- **Node comes from `setup-python`'s `nodejs-wheel` in a project that has Python**, run as `uv run npm …`, so no system Node is needed; a project with no Python uses the current Node LTS and states it under `engines` in `package.json`.
- **`package-lock.json` is committed and installs use `npm ci`**, which installs exactly the lock and fails where it disagrees with `package.json`, as `uv.lock` pins the Python.
- **Each driver is its own package** — `web/` and `api/` or `trigger/` — with its own `package.json`, lock and `tsconfig.json`, so a Worker never type-checks against the browser's DOM and the front end never against the Worker's runtime.

## Scaffold the front end

Start from the tools' own generators, then tighten what they leave loose: `npm create vite@latest web -- --template react-ts` writes TypeScript 7 and oxlint but leaves `strict` to TypeScript's default and none of `write-typescript`'s further checks on, and lints without type information or React's dependency rules.
Tailwind's Vite plugin and `npx shadcn@latest init` follow, with the flags `write-entry-points`' Python reference gives for an unattended run.

**`web/tsconfig.app.json`** carries `write-typescript`'s compiler settings, and the `@/` alias shadcn/ui's components import through:

```jsonc
{
  "compilerOptions": {
    "target": "es2024",
    "lib": ["ES2024", "DOM", "DOM.Iterable"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "types": ["vite/client"],
    "paths": { "@/*": ["./src/*"] },
    "noEmit": true,
    "skipLibCheck": true,
    "allowImportingTsExtensions": true,
    "moduleDetection": "force",

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true
  },
  "include": ["src"]
}
```

`types` defaults to none from TypeScript 6 on, so a package's ambient types — `vite/client` here, the generated Worker types below — are listed by name (devblogs.microsoft.com, TypeScript 7.0).
`tsconfig.node.json`, which checks `vite.config.ts`, takes the same strict block with `"types": ["node"]` and no DOM.

**`web/vite.config.ts`** turns React Compiler on and sets the tests' runner and coverage, two levels as `write-tests` holds them; the compiler runs as a Babel preset through `@rolldown/plugin-babel`, since `@vitejs/plugin-react` 6 dropped its inline Babel option (react.dev, React Compiler installation, read 2026-11-21):

```ts
import { fileURLToPath } from "node:url";
import babel from "@rolldown/plugin-babel";
import tailwindcss from "@tailwindcss/vite";
import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),
    tailwindcss(),
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    exclude: ["src/**/*.slow.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/components/ui/**"],
      thresholds: {
        "src/lib/**": { branches: 100 },
        branches: 80,
      },
    },
  },
});
```

`branches: 80` stands for the package's last measured figure, raised as each milestone closes; `src/lib/**` holds the pure modules, every branch covered; shadcn/ui's generated components are left out of the floor.
Install the compiler's two packages with `npm install -D babel-plugin-react-compiler @rolldown/plugin-babel`; a build with it on emits `react.memo_cache_sentinel` in each compiled component, the check that it ran.

## Lint and format

**`.oxlintrc.json`**, the same in every TypeScript package, holds `write-typescript`'s rules; `typeAware` needs `oxlint-tsgolint` installed beside `oxlint`, and `reportUnusedDisableDirectives` fails a suppression that no longer suppresses anything:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": [
    "eslint",
    "typescript",
    "unicorn",
    "oxc",
    "import",
    "react",
    "jsx-a11y",
    "vitest"
  ],
  "categories": {
    "correctness": "error",
    "suspicious": "error",
    "perf": "error"
  },
  "options": {
    "typeAware": true,
    "denyWarnings": true,
    "reportUnusedDisableDirectives": "error"
  },
  "rules": {
    "import/no-default-export": "error",
    "react/button-has-type": "error",
    "react/exhaustive-deps": "error",
    "react/no-array-index-key": "error",
    "react/only-export-components": "error",
    "react/react-in-jsx-scope": "off",
    "react/rules-of-hooks": "error",
    "typescript/consistent-type-assertions": [
      "error",
      { "assertionStyle": "never" }
    ],
    "typescript/consistent-type-definitions": ["error", "interface"],
    "typescript/no-explicit-any": "error",
    "typescript/no-floating-promises": "error",
    "typescript/no-misused-promises": "error",
    "typescript/no-non-null-assertion": "error",
    "typescript/no-unsafe-argument": "error",
    "typescript/no-unsafe-assignment": "error",
    "typescript/no-unsafe-call": "error",
    "typescript/no-unsafe-member-access": "error",
    "typescript/no-unsafe-return": "error",
    "typescript/only-throw-error": "error",
    "typescript/prefer-promise-reject-errors": "error",
    "typescript/switch-exhaustiveness-check": "error",
    "typescript/use-unknown-in-catch-callback-variable": "error"
  },
  "overrides": [
    {
      "files": ["*.config.ts", "src/index.ts"],
      "rules": { "import/no-default-export": "off" }
    }
  ]
}
```

The `no-unsafe-*` rules sit in oxlint's pedantic category, off unless named, and they are what fail `const rows: Row[] = await response.json()`, which compiles and passes every assertion rule; `only-export-components` keeps Vite's Fast Refresh from reloading the page.
Run against a file of deliberate mistakes, this configuration reported each one: an `as` on parsed JSON and the unsafe assertion behind it, an `any` assigned to a typed variable, a `!`, an `any` parameter, a non-exhaustive `switch`, a floating promise, a promise passed to `onClick`, a missing effect dependency, a hook called conditionally, an index key, a `button` with no `type`, an `img` with no `alt` and a default export.
React Compiler's own checks — a `setState` inside an effect, a ref read during render, an impure call during render — are in oxlint's `react` plugin under `correctness`, so they need no ESLint plugin.
`react/react-in-jsx-scope` is off because React 17's JSX transform no longer needs React in scope.

**Prettier formats with its defaults and no configuration file**; a `.prettierignore` lists the build output, the lock file and generated types such as `worker-configuration.d.ts`.

## Scripts

Every TypeScript package exposes the same scripts, and `check` is the gate `build-project` runs, so linting cannot be skipped in one package and run in another, as one trial's front end skipped it:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "typecheck": "tsc -b",
    "lint": "oxlint",
    "format": "prettier --write .",
    "test": "vitest run",
    "coverage": "vitest run --coverage",
    "check": "tsc -b && oxlint && prettier --check . && vitest run --coverage"
  }
}
```

A Worker's package swaps `dev` and `build` for `wrangler dev` and `wrangler deploy --dry-run`, and its `typecheck` for `wrangler types && tsc --noEmit`, so a binding added to the configuration reaches the types before they are checked.
The dependency audit `secure-project` asks for is `npm audit --omit=dev` in each package, and `review-project`'s check for current releases is `npm outdated`.

## The Worker

**`wrangler.jsonc`**, Cloudflare's recommended format for a new Worker, names the entry module, a current `compatibility_date` and every binding, with each secret listed under `secrets.required` so the generated `Env` holds it:

```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "myapp-api",
  "main": "src/index.ts",
  "compatibility_date": "2026-11-15",
  "kv_namespaces": [{ "binding": "COUNTS", "id": "<namespace id>" }],
  "vars": { "ALLOWED_ORIGIN": "https://example.com" },
  "secrets": { "required": ["UPSTREAM_TOKEN"] },
}
```

- **`wrangler types` writes `worker-configuration.d.ts`** — `Env` from the bindings, and the runtime's own types for the compatibility date — and the Worker's `tsconfig.json` lists it under `types` with `"lib": ["ES2024"]` and no DOM; commit it, and re-run it whenever the configuration changes, as the `typecheck` script does.
- **`nodejs_compat` is on by default from the compatibility date 2026-08-04**, so a Worker dated after it needs no flag for Node's built-in modules (developers.cloudflare.com, Node.js compatibility, read 2026-11-21).
- **The Worker's tests run as two Vitest projects**: `unit`, the handler built from fakes beside its module under `node`, and `runtime`, the few that need a binding or the scheduled handler, in `test/` through `@cloudflare/vitest-plugin`; `exports.default` from `cloudflare:workers` is typed once a declaration names the main module:

```ts
import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: "unit",
          environment: "node",
          include: ["src/**/*.test.ts"],
        },
      },
      {
        plugins: [
          cloudflareTest({ wrangler: { configPath: "./wrangler.jsonc" } }),
        ],
        test: { name: "runtime", include: ["test/**/*.test.ts"] },
      },
    ],
  },
});
```

```ts
declare namespace Cloudflare {
  interface GlobalProps {
    mainModule: typeof import("./index.ts");
  }
}
```

That file is `src/global-props.d.ts`; a runtime test then calls `exports.default.fetch(url)` and reads and writes bindings through `env`, both imported from `cloudflare:workers`, as `write-tests`' TypeScript reference shows for the handler alone.
A required secret missing from `.dev.vars` is reported as a warning when the tests start, not an error.
