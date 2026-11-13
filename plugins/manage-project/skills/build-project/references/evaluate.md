# Evaluate the running surface

How `SKILL.md`'s evaluator step runs: the brief the evaluator gets, the screenshots it takes, and what it hands back.
The criteria themselves are `design-interface`'s, Look at it running for a screen and Set the bar for the rest.

## Brief the evaluator

Spawn it fresh, on `sonnet` at medium effort (`choose-model`), with only what a stranger opening the product would have plus the standard, never the builder's account, since an evaluator told what to expect tends to find it:

- **What it is**, in one line from the plan's Goal, and the screen list or interface from the plan's Interface.
- **How to start it** — the launch command and its port, or the command to run — where the screenshots go (`evaluation/round-<n>/` in the project, git-ignored), and the script below, saved as `evaluation/shoot.py`.
- **The criteria**, pasted in, since the evaluator may not have `design-interface` loaded.
- **What to return**: one line per criterion, `pass` or `fail`, with its evidence — the screenshot file, the command and what it printed, the measured time — and for each fail the smallest change that would pass it; nothing else.
- **What it may not do**: edit the project, take any outward action, or stop the server it did not start.

## Screenshot a screen

A PEP 723 script, run with `uv run --script shoot.py <url> <out>`, takes every screen at desktop and phone width in both schemes, driven by the page's `data-view` and `data-ready` signals (`write-entry-points`, Dashboard), and reports any page error and any sideways scroll:

```python
# /// script
# requires-python = ">=3.15"
# dependencies = ["playwright>=1.65"]
# ///
"""Screenshot each screen at two widths in both schemes."""

import os
import pathlib
import sys

import playwright.sync_api

_SIZES = {"desktop": (1440, 900), "phone": (390, 844)}
_READY = "html[data-ready='1']"
_SCHEMES = ("light", "dark")


def _launch(play: playwright.sync_api.Playwright) -> playwright.sync_api.Browser:
    """Launch the headless shell, or the installed Chrome named by CHROME."""
    chrome = os.environ.get("CHROME")
    if chrome is None:
        return play.chromium.launch()
    return play.chromium.launch(
        args=["--disable-background-networking", "--disable-component-update"],
        executable_path=chrome,
    )


def shoot(url: str, out: pathlib.Path) -> None:
    """Write one PNG per screen, width and scheme, and print what went wrong."""
    out.mkdir(parents=True, exist_ok=True)
    with playwright.sync_api.sync_playwright() as play:
        browser = _launch(play)
        for scheme in _SCHEMES:
            for size, (width, height) in _SIZES.items():
                page = browser.new_page(
                    color_scheme=scheme, viewport={"height": height, "width": width}
                )
                page.on("pageerror", lambda error: print(f"page error: {error}"))
                page.on(
                    "console",
                    lambda message: (
                        print(f"console: {message.text}")
                        if message.type == "error"
                        else None
                    ),
                )
                page.goto(url)
                page.wait_for_selector(_READY, timeout=30_000)
                views = page.eval_on_selector_all(
                    "[data-view]:not(html)", "nodes => nodes.map(n => n.dataset.view)"
                )
                for view in views or ["main"]:
                    if views:
                        page.click(f"[data-view='{view}']:not(html)")
                    page.wait_for_selector(_READY, timeout=30_000)
                    page.wait_for_load_state("networkidle")
                    wide = "document.documentElement.scrollWidth > innerWidth"
                    if page.evaluate(wide) is True:
                        print(f"sideways scroll: {view} {scheme} {size}")
                    page.screenshot(
                        full_page=True, path=out / f"{view}-{scheme}-{size}.png"
                    )
                page.close()
        browser.close()


if __name__ == "__main__":
    shoot(sys.argv[1], pathlib.Path(sys.argv[2]))
```

- **The scheme comes from the browser's `color_scheme`**, which the page follows by default (`design-interface`, Light and dark), so the script never clicks the toggle.
- **The sideways-scroll check compares `scrollWidth` with the window's width**, since a full-page screenshot hides a page wider than 390 px.

## Measure what a screenshot cannot

- **Speed** — time a control with `performance.now()` from the click until `data-ready` returns to `1`, five times on the real data, and report the median; on a busy machine, re-run a miss before failing it.
- **Focus** — press Tab through the first screen and screenshot each stop, which shows a focus ring or its absence.
- **Contrast** — the tokens pass by construction, so check only a colour the build added, against the surface it sits on.
- **States** — force each where the evaluator can: point the app at an empty or missing file in a scratch copy of the store, or wait out the staleness threshold with a stubbed clock where the app has one.

## Run a headless browser without touching the system

- **Install Playwright's headless shell into the project**, with `PLAYWRIGHT_BROWSERS_PATH` set to a git-ignored `.browsers/` folder and `uv run --with playwright python -m playwright install --only-shell chromium`, so nothing lands in the user's caches and nothing updates itself later.
- **Where Playwright has no build for the system** (Playwright 1.65 has none for macOS 13), set `CHROME` to the installed Chrome's binary (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` on a Mac): Playwright launches it headless with a throwaway profile, `--disable-component-update` stops it fetching components, and the application itself is only read, never written.
- **Never install a browser at user or system scope**, and never through a package manager that updates it in place.

## Judge a command or an API

A command-line tool is judged from a session the evaluator runs in a scratch folder against a small real store: `--help` at the root and for each command, the everyday invocation in each output form, two wrong invocations (a bad option, a missing input), and the exit code of each.
An API is judged from its docs page, screenshotted as above, and from a request to each route with good and bad parameters.
The session's transcript is the evidence, saved beside the screenshots.

## Report the rounds

Each round's report gives the criteria passed and failed, what the builder changed, and the round's cost, from the Agent tool's usage line for the evaluator and the fixing builder; `SKILL.md` says what happens after the third.
