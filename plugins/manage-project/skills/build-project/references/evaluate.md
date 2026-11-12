# Evaluate the running surface

How `SKILL.md`'s evaluator step runs: the brief the evaluator gets, the screenshots it takes, and what it hands back.
The criteria themselves are `design-interface`'s, Look at it running for a screen and Set the bar for the rest.

## Brief the evaluator

Spawn it fresh, on `sonnet` at medium effort (`choose-model`), and give it only what a stranger opening the product would have plus the standard, never the builder's account of what it built, since an evaluator told what to expect tends to find it:

- **What it is**, in one line from the plan's Goal, and the screen list or interface from the plan's Interface.
- **How to start it** — the launch command and its port, or the command to run — and where the screenshots go (`evaluation/round-<n>/` in the project, git-ignored).
- **The criteria**, pasted in, since the evaluator may not have `design-interface` loaded.
- **What to return**: one line per criterion, `pass` or `fail`, with its evidence — the screenshot file, the command and what it printed, the measured time — and for each fail the smallest change that would pass it; nothing else.
- **What it may not do**: edit the project, take any outward action, or stop the server it did not start.

## Screenshot a screen

A PEP 723 script, run with `uv run --script shoot.py <url> <out>` under `setup-python`'s toolchain, takes every screen at desktop and phone width in both schemes once the page signals `data-ready` (`write-entry-points`, Dashboard), and reports any page error and any sideways scroll:

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
                page.goto(url)
                page.wait_for_selector("html[data-ready='1']", timeout=30_000)
                views = page.eval_on_selector_all(
                    "[data-view]", "nodes => nodes.map(n => n.dataset.view)"
                )
                for view in views or ["main"]:
                    if views:
                        page.click(f"[data-view='{view}']")
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

- **Mark each screen's navigation with `data-view="<screen>"`**, so the script and the smoke test find the screens without knowing the framework.
- **The scheme comes from the browser's `color_scheme`**, which the page follows by default (`design-interface`, Light and dark), so the script never clicks the toggle.
- **The phone check compares the document's `scrollWidth` with the window's width**, so a page wider than 390 px reports itself rather than hiding in a full-page screenshot.

## Run a headless browser without touching the system

- **Install Playwright's headless shell into the project**, with `PLAYWRIGHT_BROWSERS_PATH` set to a git-ignored `.browsers/` folder and `uv run --with playwright python -m playwright install --only-shell chromium`, so nothing lands in the user's caches and nothing updates itself later.
- **Where Playwright has no build for the system** — Playwright 1.65 refuses macOS 13 — set `CHROME` to the installed Chrome's binary (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` on a Mac): Playwright launches it headless with a throwaway profile, `--disable-component-update` stops it fetching components, and the application folder is only read, never written (its modification time was unchanged across runs on 2026-11-12).
- **Never install a browser at user or system scope**, and never through a package manager that updates it in place.

## Judge a command or an API

A command-line tool is judged from a session the evaluator runs in a scratch folder against a small real store: `--help` at the root and for each command, the everyday invocation in each output form, two wrong invocations (a bad option, a missing input), and the exit code of each.
An API is judged from its docs page, screenshotted as above, and from a request to each route with good and bad parameters.
The transcript of the session is the evidence, saved beside the screenshots.

## Report the rounds

Each round's report gives the criteria passed and failed, what the builder changed, and the round's cost: the evaluator's and the fixing builder's tokens from the Agent tool's usage line, priced at `choose-model`'s rates.
After the third round, list the criteria still failing with the evaluator's evidence and the change it proposed, and let the milestone report carry them as open.
