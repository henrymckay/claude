# Design the interface in Python

The technology-neutral system is in `SKILL.md`; this is how it lands in a Python dashboard — Dash with Mantine, Shiny, and the Plotly figures both draw — and in a digest's chart image; `write-entry-points` owns each app's structure.

## Tokens

One module, `code/drive/tokens.py`, transcribes `SKILL.md`'s table as one record per scheme, and every theme below is built from it; a changed value is edited in the table, here, and in the Mantine accent ramp when it is the accent.

```python
"""The house design tokens, one Scheme per colour scheme."""

import dataclasses
import typing

FONT: typing.Final = "Inter Variable, Inter, system-ui, -apple-system, sans-serif"


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Scheme:
    """The colour roles of one scheme, named as in the house design system."""

    accent: str
    axis: str
    background: str
    border: str
    down: str
    grid: str
    input: str
    muted: str
    raised: str
    series: tuple[str, ...]
    sunken: str
    surface: str
    text: str
    text_2: str
    up: str


LIGHT: typing.Final = Scheme(
    accent="#2a78d6",
    axis="#c3c2b7",
    background="#f6f6f3",
    border="#e4e3dc",
    down="#e34948",
    grid="#e1e0d9",
    input="#d5d4cb",
    muted="#66655f",
    raised="#fcfcfb",
    series=(
        "#2a78d6",
        "#eb6834",
        "#1baf7a",
        "#eda100",
        "#e87ba4",
        "#008300",
        "#6250d6",
        "#e34948",
    ),
    sunken="#efeeea",
    surface="#fcfcfb",
    text="#0b0b0b",
    text_2="#52514e",
    up="#2a78d6",
)
DARK: typing.Final = Scheme(
    accent="#3987e5",
    axis="#383835",
    background="#0d0d0d",
    border="#ffffff17",
    down="#e66767",
    grid="#2c2c2a",
    input="#ffffff29",
    muted="#a9a8a0",
    raised="#222221",
    series=(
        "#3987e5",
        "#d95926",
        "#199e70",
        "#c98500",
        "#d55181",
        "#008300",
        "#9085e9",
        "#e66767",
    ),
    sunken="#262625",
    surface="#1a1a19",
    text="#f0efec",
    text_2="#c3c2b7",
    up="#3987e5",
)
SCHEMES: typing.Final = {"dark": DARK, "light": LIGHT}


def css(scheme: Scheme) -> str:
    """Return the scheme as CSS custom properties, one --house-<role> per field."""
    return "".join(
        f"--house-{field.name.replace('_', '-')}: {getattr(scheme, field.name)};"
        for field in dataclasses.fields(scheme)
        if field.name != "series"
    )
```

Bundle `Inter` as a `.woff2` under the app's static assets with an `@font-face` rule.

## Plotly

Figures are built without colours and drawn with one of two registered templates, `house_light` and `house_dark`, so a scheme change swaps the template and nothing else:

```python
"""Plotly templates built from the house tokens."""

import plotly.graph_objects
import plotly.io

from mypackage.code.drive import tokens


def build(scheme: tokens.Scheme) -> plotly.graph_objects.layout.Template:
    """Return the Plotly template for one scheme."""
    axis = {
        "gridcolor": scheme.grid,
        "linecolor": scheme.axis,
        "showline": True,
        "ticks": "",
        "zeroline": False,
    }
    candle = plotly.graph_objects.Candlestick(
        decreasing={"fillcolor": scheme.down, "line": {"color": scheme.down}},
        increasing={"fillcolor": scheme.up, "line": {"color": scheme.up}},
    )
    return plotly.graph_objects.layout.Template(
        data={"candlestick": [candle]},
        layout={
            "colorway": list(scheme.series),
            "font": {"color": scheme.muted, "family": tokens.FONT, "size": 12},
            "hoverlabel": {
                "bgcolor": scheme.raised,
                "bordercolor": scheme.border,
                "font": {"color": scheme.text, "family": tokens.FONT},
            },
            "legend": {"font": {"color": scheme.text_2}},
            "margin": {"b": 32, "l": 48, "r": 16, "t": 16},
            "paper_bgcolor": scheme.surface,
            "plot_bgcolor": scheme.surface,
            "xaxis": axis,
            "yaxis": axis,
        },
    )


def register() -> None:
    """Register house_light and house_dark with Plotly."""
    for name, scheme in tokens.SCHEMES.items():
        plotly.io.templates[f"house_{name}"] = build(scheme)
```

- **Register once, from the driver, before the first figure**; a figure names `template="house_light"` and a scheme change sets `layout.template` alone.
- **Turn off the mode bar's clutter and the logo** (`config={"displaylogo": False}`), and set `transition={"duration": 0}`, since animation on an update reads as lag.

## Dash with Mantine

Mantine takes the accent as a ten-shade colour, the house blue at shade 6 for light and 5 for dark, and its `dark` colour as ten neutral shades, `0` the text and `7` the surface:

```python
"""The Mantine theme built from the house tokens."""

import typing

from mypackage.code.drive import tokens

_ACCENT: typing.Final = [
    "#cde2fb",
    "#b7d3f6",
    "#9ec5f4",
    "#86b6ef",
    "#6da7ec",
    "#3987e5",
    "#2a78d6",
    "#256abf",
    "#1c5cab",
    "#184f95",
]
_DARK: typing.Final = [
    "#f0efec",
    "#c3c2b7",
    "#a9a8a0",
    "#898781",
    "#383835",
    "#2c2c2a",
    "#262625",
    "#1a1a19",
    "#121211",
    "#0d0d0d",
]


def build() -> dict[str, object]:
    """Return the theme MantineProvider takes."""
    return {
        "colors": {"accent": _ACCENT, "dark": _DARK},
        "defaultRadius": "md",
        "fontFamily": tokens.FONT,
        "primaryColor": "accent",
        "primaryShade": {"dark": 5, "light": 6},
        "radius": {"lg": "12px", "md": "8px", "sm": "6px"},
    }
```

- **Wrap the layout in `dmc.MantineProvider(theme=theme.build(), defaultColorScheme="auto")`**; `write-entry-points` has the driver that sets the scheme before the first paint.
- **The page and card colours are CSS variables Mantine reads**: put `tokens.css(tokens.LIGHT)` under `:root` and `tokens.css(tokens.DARK)` under `:root[data-mantine-color-scheme="dark"]`, with `--mantine-color-body: var(--house-background)` in both, into a `<style>` in `app.index_string`, so the CSS comes from the tokens rather than a second copy in `assets/`.
- **`dmc.ColorSchemeToggle(id="scheme")` is the toggle**, and its `computedColorScheme` the input a callback re-themes figures from, with a `dash.Patch()` setting each figure's `layout.template` to `house_<scheme>`, so only the template crosses the wire; a trace given an explicit colour keeps it in both schemes, so give one only to a status colour.
- **`dash-ag-grid` takes its theme from the same variables**: `dashGridOptions={"theme": {"function": "themeQuartz.withParams({backgroundColor: 'var(--house-surface)', foregroundColor: 'var(--house-text)', headerBackgroundColor: 'var(--house-sunken)', borderColor: 'var(--house-border)', accentColor: 'var(--house-accent)', fontFamily: 'inherit'})"}}`, so the grid follows the scheme with no callback.

## Shiny

Shiny themes through Bootstrap's Sass variables, compiled by `libsass` (the `shiny[theme]` extra):

```python
"""The Shiny theme built from the house tokens."""

import shiny

from mypackage.code.drive import tokens


def build() -> shiny.ui.Theme:
    """Return the Bootstrap theme for both schemes."""
    light, dark = tokens.LIGHT, tokens.DARK
    return shiny.ui.Theme("shiny").add_defaults(
        body_bg=light.background,
        body_bg_dark=dark.background,
        body_color=light.text,
        body_color_dark=dark.text,
        border_radius="0.5rem",
        border_radius_lg="0.75rem",
        enable_shadows=False,
        font_family_sans_serif=tokens.FONT,
        primary=light.accent,
    )
```

- **Pass it as `shiny.ui.page_navbar(..., theme=theme.build())`, with `shiny.ui.input_dark_mode(id="scheme")` in the navbar as the toggle**; a render function that reads `input.scheme()` redraws its figure with `house_<scheme>`, and Bootstrap's own components follow without code.
- **Cards and value boxes take `surface`** through `--bs-card-bg` under `[data-bs-theme="dark"]`, added with `.add_rules()`, since Bootstrap's dark card otherwise matches the page.

## A digest's chart

A chart attached to a message (`send-messages`) is a PNG drawn by `matplotlib` in the light scheme, which every mail client shows as sent: set `font.family`, `axes.edgecolor` to `axis`, `axes.facecolor` and `figure.facecolor` to `surface`, `grid.color` to `grid`, `text.color` and the tick colours to `muted`, and `axes.prop_cycle` to the series, in `matplotlib.rcParams` from `tokens.LIGHT` once before drawing.
