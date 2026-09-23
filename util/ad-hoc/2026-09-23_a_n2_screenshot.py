#!/usr/bin/env python3
"""
A-N2 (item 18): the literal "render" -- screenshot canopy's dashboard after a run, one fresh browser context each.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-23_a_n2_drive.py (the API-level loop); evidence in
         reports/2026-09-23_canopy-a-n2-generate-stage-train-render/<case>/dashboard*.{png,txt,json}

Run with the JuniperCanopy1 interpreter (it carries playwright 1.59.0; JuniperCascor1 does not):

  /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/2026-09-23_a_n2_screenshot.py <case-dir-name> [--settle 45] [--name dashboard]

What it touches: it opens the page and looks. Its only input is one click on the header "x" of the
first-visit "Welcome to Juniper Canopy" modal (every fresh browser context gets it, it covers the
Training Metrics panel, and Escape does not close it) -- a UI-only dialog, no request. It clicks
nothing else, so it cannot stage, start or select anything. The dashboard's own mount does run its callbacks (the
hydration reads GET /api/selection); that is the page doing what it does for any operator.

It also samples the top status bar and the Network Information panel at fixed times after load
(<name>_timeline.json), because the first capture after the control run showed the status bar at its
mount defaults ("Stopped | Idle | Step 0 | Hidden Units 0") while /api/status said COMPLETED with 10
hidden units, and a single screenshot cannot say whether that bar is late or never updates.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

ML_ROOT = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE = ML_ROOT / "reports" / "2026-09-23_canopy-a-n2-generate-stage-train-render"
URL = "http://127.0.0.1:8061/dashboard/"
PROBES = {
    "top_status": "#top-status-display",
    "top_phase": "#top-phase-display",
    "top_epoch": "#top-epoch-display",
    "top_hidden_units": "#top-hidden-units-display",
    "network_info": "#network-info-panel",
}


def _sample(page) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for key, selector in PROBES.items():
        try:
            loc = page.locator(selector)
            out[key] = loc.first.inner_text(timeout=2000).strip().replace("\n", " | ")[:400] if loc.count() else None
        except Exception as exc:  # recorded, not raised: a missing element is itself evidence
            out[key] = f"<error {type(exc).__name__}>"
    return out


def _dismiss_welcome(page) -> str:
    """Close the first-visit welcome modal with its header "x" (Escape does not close it: measured
    on the control's first capture). UI-only: the modal's close button sends no request."""
    try:
        modal = page.locator(".modal.show").filter(has_text="Welcome to Juniper Canopy")
        modal.first.wait_for(state="visible", timeout=10_000)
        modal.first.locator(".btn-close").first.click(timeout=5_000)
        modal.first.wait_for(state="hidden", timeout=5_000)
        return "closed"
    except Exception as exc:  # recorded, not raised
        return f"not closed ({type(exc).__name__})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir")
    parser.add_argument("--settle", type=float, default=45.0, help="seconds after load before the screenshot")
    parser.add_argument("--name", default="dashboard", help="file-name prefix for the outputs")
    args = parser.parse_args()
    out = EVIDENCE / args.case_dir
    out.mkdir(parents=True, exist_ok=True)
    console: list[str] = []
    timeline: list[dict[str, object]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1100})
        page = context.new_page()
        page.on("console", lambda msg: console.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console.append(f"[pageerror] {exc}"))
        t0 = time.time()
        resp = page.goto(URL, wait_until="load", timeout=60_000)
        page.wait_for_timeout(3000)
        dismissed = _dismiss_welcome(page)
        marks = sorted({5.0, 15.0, 30.0, args.settle})
        for mark in marks:
            remaining = mark - (time.time() - t0)
            if remaining > 0:
                page.wait_for_timeout(int(remaining * 1000))
            timeline.append({"t_s": round(time.time() - t0, 1), **_sample(page)})
        page.screenshot(path=str(out / f"{args.name}.png"), full_page=True)
        text = page.inner_text("body")
        (out / f"{args.name}_text.txt").write_text(f"# {URL} status={resp.status if resp else None} captured {time.time() - t0:.1f}s after navigation\n\n{text}\n")
        (out / f"{args.name}_console.txt").write_text("\n".join(console) + "\n")
        (out / f"{args.name}_timeline.json").write_text(json.dumps({"welcome_modal": dismissed, "samples": timeline}, indent=2) + "\n")
        context.close()
        browser.close()
    print(json.dumps(timeline, indent=2))
    print(f"wrote {out / (args.name + '.png')} ({len(console)} console lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
