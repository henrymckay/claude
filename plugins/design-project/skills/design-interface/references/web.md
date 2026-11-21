# Design the interface on the web

The technology-neutral system is in `SKILL.md`; this is how it lands in a built web front end: Vite, React and TypeScript, Tailwind with shadcn/ui, ECharts for every chart, candles included (`write-entry-points` owns the `web/` folder and its data module, `write-typescript` how its code is written, and the examples here pass its compiler settings, linter and formatter).

## Tokens

The tokens live in `web/src/index.css` as CSS variables, light under `:root` and dark under `.dark`, under shadcn/ui's name for a role where it has one; Tailwind reads them through `@theme inline`, so `bg-card` and `text-up` follow the scheme.

| House role | Variable |
|---|---|
| `background` | `--background` |
| `surface` | `--card` |
| `raised` | `--popover` |
| `sunken` | `--muted`, `--secondary` and `--accent` |
| `text` | `--foreground`, and each `*-foreground` but the two below |
| `text-2`, `grid`, `axis`, `up`, `down`, the status colours | the role's own name: `--text-2`, `--grid`, `--up`, `--good` |
| `muted` | `--muted-foreground` |
| `border`, `input` | `--border`, `--input` |
| `accent` | `--primary` and `--ring` |
| `on-accent` | `--primary-foreground` |
| `critical` | `--destructive` |
| series 1 to 8 | `--chart-1` to `--chart-8` |

**shadcn/ui's `--accent` is a hover surface, not the house accent**, so it takes `sunken`'s value; giving it the blue paints every hovered menu item blue.

```css
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";
@import "@fontsource-variable/inter";

@custom-variant dark (&:is(.dark *));

:root {
  --background: #f6f6f3;
  --card: #fcfcfb;
  --primary: #2a78d6;
  --up: #2a78d6;
  --down: #e34948;
  --radius: 0.75rem;
  color-scheme: light;
}

.dark {
  --background: #0d0d0d;
  --card: #1a1a19;
  --primary: #3987e5;
  --up: #3987e5;
  --down: #e66767;
  color-scheme: dark;
}

@theme inline {
  --font-sans: "Inter Variable", system-ui, -apple-system, "Segoe UI", sans-serif;
  --color-background: var(--background);
  --color-card: var(--card);
  --color-primary: var(--primary);
  --color-up: var(--up);
  --color-down: var(--down);
}

@layer base {
  body {
    @apply bg-background text-foreground font-sans antialiased;
  }
}
```

Every role in `SKILL.md`'s table goes in all three blocks; the excerpt shows the shape.
`--radius` of 0.75rem is the card's 12 px, and shadcn/ui derives the smaller radii from it.
Put `tabular-nums` on every element holding a number, or on the tile, table and chart wrappers once.

## Scheme

Set the class before React loads, from an inline script in `index.html`'s `<head>`, so the first paint is already in the right scheme:

```html
<meta name="color-scheme" content="light dark" />
<script>
  (function () {
    var dark = matchMedia("(prefers-color-scheme: dark)").matches;
    try {
      var saved = localStorage.getItem("theme");
      if (saved === "dark" || saved === "light") dark = saved === "dark";
    } catch (e) {}
    document.documentElement.classList.toggle("dark", dark);
  })();
</script>
```

A small context provider holds the scheme, toggles the class, saves the choice in a `try` (storage can be blocked) and follows the system's change while the viewer has saved none.
Charts read the tokens through one `useTokens()` hook keyed on the scheme, returning the house roles by name, each read with `getComputedStyle(document.documentElement).getPropertyValue(...)` from its variable in the table above, so every chart re-themes when the scheme flips.

## Components

Add shadcn/ui's components as the screens need them (`npx shadcn@latest add --yes card tabs table toggle-group skeleton tooltip badge`, with `popover` and `command` for a searchable picker; `--yes` skips the confirmation an unattended run cannot answer), keeping the `shadcn` command and any font it adds out of the runtime dependencies, then build `SKILL.md`'s shared pieces from them.
Icons are `lucide-react`, which shadcn/ui already uses, so one stroke weight.

## ECharts

Register only the charts and components used, from `echarts/core`, in `lib/charts.ts`, so the bundle carries a few hundred kilobytes, not the whole library:

```ts
import type {
  EChartsOption,
  XAXisComponentOption,
  YAXisComponentOption,
} from "echarts";
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  CanvasRenderer,
]);

export type Tokens = Readonly<
  Record<
    | "axis"
    | "border"
    | "down"
    | "grid"
    | "muted"
    | "raised"
    | "surface"
    | "text"
    | "up",
    string
  >
>;

const FONT = "Inter Variable, system-ui, sans-serif";

/** Build the option every chart starts from. */
export function frame(t: Tokens): EChartsOption {
  return {
    animation: false,
    textStyle: { color: t.muted, fontFamily: FONT, fontSize: 11 },
    tooltip: {
      backgroundColor: t.raised,
      borderColor: t.border,
      textStyle: { color: t.text, fontFamily: FONT, fontSize: 12 },
    },
  };
}

/** Build a category axis of the given labels. */
export function xAxis(
  t: Tokens,
  labels: readonly string[],
): XAXisComponentOption {
  return {
    axisLabel: { color: t.muted },
    axisLine: { lineStyle: { color: t.axis } },
    axisTick: { show: false },
    data: [...labels],
    type: "category",
  };
}

/** Build a value axis. */
export function yAxis(t: Tokens): YAXisComponentOption {
  return {
    axisLabel: { color: t.muted },
    splitLine: { lineStyle: { color: t.grid } },
    type: "value",
  };
}
```

- **Pass `{ notMerge: true }` to `setOption` when the scheme changes**, or ECharts merges the new colours into the old option and some keep the old scheme.
- **Resize from a `ResizeObserver` on the chart's container**, since a window resize misses a card that changed width when the layout reflowed.
- **Colour each series from `--chart-<n>`, or `--up` and `--down`.**
- **A treemap or a calendar heatmap is ECharts too** — `TreemapChart`, or `HeatmapChart` on a `CalendarComponent` with a `VisualMapComponent` as its legend (ECharts 6.1.0) — never shapes drawn in the DOM, which lose the tooltip, the theme and the legend.

## Candles

Candles are ECharts' `candlestick` series, with volume as bars in a second grid on the same days, in `lib/candles.ts` beside `lib/charts.ts`, so a price chart adds no library, no second theme and no logo:

```ts
import type { EChartsOption } from "echarts";
import { CandlestickChart } from "echarts/charts";
import { DataZoomComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { frame, type Tokens, xAxis, yAxis } from "@/lib/charts.ts";

echarts.use([CandlestickChart, DataZoomComponent]);

export interface Bar {
  readonly close: number;
  readonly day: string;
  readonly high: number;
  readonly low: number;
  readonly open: number;
  readonly volume: number;
}

/** Build a candle chart with a volume pane beneath it. */
export function candles(t: Tokens, bars: readonly Bar[]): EChartsOption {
  const days = bars.map((bar) => bar.day);
  return {
    ...frame(t),
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    dataZoom: [{ type: "inside", xAxisIndex: [0, 1] }],
    grid: [{ bottom: "30%" }, { bottom: 24, height: "18%" }],
    series: [
      {
        data: bars.map((bar) => [bar.open, bar.close, bar.low, bar.high]),
        itemStyle: {
          borderColor: t.up,
          borderColor0: t.down,
          color: t.up,
          color0: t.down,
        },
        type: "candlestick",
      },
      {
        data: bars.map((bar) => bar.volume),
        itemStyle: { color: t.muted },
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
      },
    ],
    xAxis: [
      xAxis(t, days),
      { ...xAxis(t, days), axisLabel: { show: false }, gridIndex: 1 },
    ],
    yAxis: [
      { ...yAxis(t), scale: true },
      { ...yAxis(t), gridIndex: 1, splitNumber: 2 },
    ],
  };
}
```

- **A bar is `[open, close, low, high]`**, in that order, not the OHLC order the data arrives in.
- **The axis is a category of the bars' ISO dates**, so no viewer's offset moves a bar and a day with no trading leaves no gap.
An intraday bar takes its period's start in UTC as the category, labelled in the viewer's zone with the zone named on the axis title, so a closed session leaves no gap either.
- **Draw the bar still forming apart from the final ones** (`design-pipeline`, Keep open and final records apart): give its data item its own `itemStyle` at reduced `opacity` and say `forming, as of 14:05` in its tooltip, so a reader never takes a half-made bar for a closed one.
- **Compute a moving average or any indicator in the data module** and draw it as a `line` series, since the series has none built in.
- **Reach for a finance library only once a requirement names indicators, drawing tools or a live feed**: KLineChart (Apache-2.0, 10.1.1) ships both, at the cost of a second canvas engine outside the tokens.
Lightweight Charts (Apache-2.0, 5.3.0) suits a series too long for ECharts to pan smoothly, but its licence requires a credit and link to TradingView on the page, and its default corner logo reads as a promise of the vendor's full product, so put the credit in the footer and set `layout.attributionLogo` to `false`.
TradingView's Advanced Charts may not sit in a public repository (versions and terms read 2026-11-18 from each project's repository and docs).

## Formatting

`lib/format.ts` builds every formatter once from `Intl`:

```ts
const INTEGER = new Intl.NumberFormat("en-GB");
const COMPACT = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
  notation: "compact",
});
const DAY = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  timeZone: "UTC",
  year: "numeric",
});

/** Write a number compactly, such as 1.2M. */
export function formatCompact(value: number): string {
  return COMPACT.format(value);
}

/** Write an ISO date as a day, such as 12 Nov 2026. */
export function formatDay(iso: string): string {
  return DAY.format(Date.parse(iso));
}

/** Write a whole number with thousands separators. */
export function formatInteger(value: number): string {
  return INTEGER.format(value);
}

/** Write a change in percent with its sign, such as +1.25%. */
export function formatPercent(change: number): string {
  return `${change > 0 ? "+" : ""}${change.toFixed(2)}%`;
}
```
