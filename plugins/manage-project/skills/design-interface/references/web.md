# Design the interface on the web

The technology-neutral system is in `SKILL.md`; this is how it lands in a built web front end: Vite, React and TypeScript, Tailwind with shadcn/ui, ECharts for charts and Lightweight Charts for candles (`write-entry-points` owns the `web/` folder and its data module).

## Tokens

The tokens live in `web/src/index.css` as CSS variables, light under `:root` and dark under `.dark`, using shadcn/ui's names where it has one for the role and the house role name where it has none; Tailwind reads them through `@theme inline`, so `bg-card`, `text-muted-foreground` and `text-up` all follow the scheme.

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
Charts read the tokens with `getComputedStyle(document.documentElement).getPropertyValue("--grid")` in a hook keyed on the scheme, so every chart re-themes when it flips and none holds a hex value of its own.

## Components

Add only the shadcn/ui components the screens use (`npx shadcn@latest add card tabs table toggle-group skeleton tooltip badge`, with `popover` and `command` for a searchable picker), then build the shared pieces once: a tile (label, value, context line, a skeleton while loading), a titled chart card of fixed height, a table that scrolls inside its card, a status chip for the data's age, and an error note.
Icons are `lucide-react`, which shadcn/ui already uses; one icon set keeps one stroke weight.

## ECharts

Register only the charts and components used, from `echarts/core`, so the bundle carries a few hundred kilobytes rather than the whole library:

```ts
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

type Tokens = Record<"axis" | "border" | "grid" | "muted" | "raised" | "text", string>;

const font = "Inter Variable, system-ui, sans-serif";

export const frame = (t: Tokens) => ({
  animation: false,
  textStyle: { color: t.muted, fontFamily: font, fontSize: 11 },
  tooltip: {
    backgroundColor: t.raised,
    borderColor: t.border,
    textStyle: { color: t.text, fontFamily: font, fontSize: 12 },
  },
});

export const xAxis = (t: Tokens) => ({
  axisLabel: { color: t.muted },
  axisLine: { lineStyle: { color: t.axis } },
  axisTick: { show: false },
});

export const yAxis = (t: Tokens) => ({
  axisLabel: { color: t.muted },
  splitLine: { lineStyle: { color: t.grid } },
  type: "value" as const,
});
```

- **Pass `{ notMerge: true }` to `setOption` when the scheme changes**, or ECharts merges the new colours into the old option and some keep the old scheme.
- **Resize from a `ResizeObserver` on the chart's container**, since a window resize misses a card that changed width when the layout reflowed.
- **Colour each series from `--chart-<n>`, or `--up` and `--down`**, never ECharts' default palette.

## Lightweight Charts

Candles take Lightweight Charts, with volume in a second pane on the same time axis:

```ts
import { CandlestickSeries, HistogramSeries, createChart } from "lightweight-charts";

const chart = createChart(container, {
  autoSize: true,
  grid: { horzLines: { color: t.grid }, vertLines: { color: t.grid } },
  layout: { background: { color: t.surface }, fontFamily: font, textColor: t.muted },
  rightPriceScale: { borderColor: t.grid },
  timeScale: { borderColor: t.grid },
});
const candles = chart.addSeries(CandlestickSeries, {
  borderVisible: false,
  downColor: t.down,
  upColor: t.up,
  wickDownColor: t.down,
  wickUpColor: t.up,
});
const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" } }, 1);
```

- **Create the chart once and re-theme it** with `chart.applyOptions` and each series' `applyOptions` when the scheme changes; recreating it loses the viewer's zoom.
- **Times are UTC seconds**, and a daily bar's time is its date at midnight UTC, or the axis labels drift by the viewer's offset.
- **Leave its attribution logo on**: the library's licence asks for the attribution it shows.

## Formatting

One `format.ts` holds every formatter, built once from `Intl`, so a number reads the same in a tile, a table and a tooltip:

```ts
const integer = new Intl.NumberFormat("en-GB");
const compact = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1, notation: "compact" });
const day = new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", timeZone: "UTC", year: "numeric" });

export const formatCompact = (n: number) => compact.format(n);
export const formatDay = (iso: string) => day.format(Date.parse(iso));
export const formatInteger = (n: number) => integer.format(n);
export const formatPercent = (x: number) => `${x > 0 ? "+" : ""}${x.toFixed(2)}%`;
```
