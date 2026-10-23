#!/usr/bin/env python3
"""Is this canopy leg's dashboard alive in the browser? The duplicate-output collision across dash versions.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 30 (found while standing up its legs on turing)
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 14, F-CANOPY-069);
              util/ad-hoc/2026-10-20_turing_canopy_leg.bash (the legs, one per dash version)
License:      MIT License

WHAT IT MEASURES, per leg:
  - the dash version the leg serves (from the renderer bundle URL the page loads) and the version pip reports;
  - the output ids in GET /dashboard/_dash-dependencies that more than one callback claims (the server side of the
    collision: canopy's ``allow_duplicate`` ids are ``<id>.<prop>@sha256(inputs)``, so two callbacks with the same
    output AND the same inputs get the same id);
  - every "Duplicate callback outputs" error the renderer logs at load (the client side: dash 3.x's renderer leaves
    the callback graph EMPTY on any validation error, ``computeGraphs`` in dash_renderer);
  - whether anything fires: the welcome modal (a mount callback), the Parameters tables' rows (a mount callback), and
    a POST to _dash-update-component within --click-seconds of a click on the theme toggle.
Bootstrap's CDN stylesheet is aborted in the browser (turing's per-app filter never answers Chrome; see
2026-10-20_item30_fixwave_redrive.py). It does not take part in any of the above.

Usage:
    <venv with playwright>/bin/python -I util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py \\
        --base http://127.0.0.1:8062 --label dash-4.4.1 --out reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import time
import urllib.request


def http_json(url: str, timeout: float = 20.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 -- loopback test leg
        return json.loads(r.read().decode())


def duplicate_output_ids(deps: list) -> list:
    outs = collections.Counter()
    for d in deps:
        o = d["output"]
        parts = o[2:-2].split("...") if o.startswith("..") else [o]
        for p in parts:
            outs[p] += 1
    return sorted(k for k, v in outs.items() if v > 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True, help="JSON file; one record per label, merged")
    ap.add_argument("--settle-seconds", type=float, default=20.0)
    ap.add_argument("--click-seconds", type=float, default=30.0)
    args = ap.parse_args()
    base = args.base.rstrip("/")
    rec: dict = {"label": args.label, "base": base, "probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    health = http_json(base + "/v1/health")
    rec["serving"] = {k: health.get(k) for k in ("version", "git_sha", "demo_mode")}
    deps = http_json(base + "/dashboard/_dash-dependencies")
    rec["callbacks"] = len(deps)
    dups = duplicate_output_ids(deps)
    rec["duplicate_output_ids"] = dups
    rec["duplicate_owners"] = [{"output": d["output"][:240], "inputs": [f"{i['id']}.{i['property']}" for i in d["inputs"]]} for d in deps if any(k in d["output"] for k in dups)]

    from playwright.sync_api import sync_playwright

    errors, reqs = [], []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, channel="chrome", args=["--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width": 1600, "height": 1100})
        ctx.route("https://cdn.jsdelivr.net/**", lambda route, req: route.abort())
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text[:600]) if m.type == "error" and "Duplicate callback" in m.text else None)
        page.on("request", lambda r: reqs.append((time.time(), r.url)) if "_dash-update-component" in r.url or "dash_renderer" in r.url else None)
        t0 = time.time()
        page.goto(base + "/dashboard/", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(int(args.settle_seconds * 1000))
        renderer = next((u for _t, u in reqs if "dash_renderer" in u), "")
        m = re.search(r"dash_renderer\.(v\d+_\d+_\d+)", renderer)
        rec["dash_renderer_bundle"] = m.group(1).replace("_", ".")[1:] if m else renderer[-80:]
        rec["duplicate_errors_logged"] = len(errors)
        rec["duplicate_errors"] = errors[:6]
        rec["welcome_modal_opened"] = bool(page.evaluate("""() => [...document.querySelectorAll('[role=dialog]')].some(d => (d.className||'').includes('show'))"""))
        rec["update_posts_before_click"] = sum(1 for _t, u in reqs if "_dash-update-component" in u)
        page.evaluate("""() => { const b=document.getElementById('welcome-modal-close'); if(b) b.click(); }""")
        page.wait_for_timeout(1500)
        page.evaluate("""() => { const t = [...document.querySelectorAll('[role=tab]')].find(x => x.textContent.trim() === 'Parameters'); if (t) t.click(); }""")
        page.wait_for_timeout(6000)
        rec["parameters_network_table_rows"] = page.evaluate("""() => (document.getElementById('parameters-panel-network-table')||{querySelectorAll:()=>[]}).querySelectorAll('tr').length""")
        n0 = sum(1 for _t, u in reqs if "_dash-update-component" in u)
        t_click = time.time()
        page.evaluate("""() => { const b=document.getElementById('dark-mode-toggle'); if (b) b.click(); }""")
        posted_at = None
        while time.time() - t_click < args.click_seconds:
            n1 = sum(1 for _t, u in reqs if "_dash-update-component" in u)
            if n1 > n0:
                posted_at = round(time.time() - t_click, 1)
                break
            page.wait_for_timeout(500)
        rec["click_posted_after_s"] = posted_at
        page.wait_for_timeout(2000)
        rec["theme_store_after_click"] = page.evaluate("localStorage.getItem('dark-mode-store')")
        rec["page_seconds"] = round(time.time() - t0, 1)
        b.close()
    alive = rec["parameters_network_table_rows"] > 0 and posted_at is not None
    rec["verdict"] = "ALIVE" if alive else "INERT"
    print(json.dumps(rec, indent=2))
    merged = {}
    if os.path.exists(args.out):
        try:
            with open(args.out, encoding="utf-8") as fh:
                merged = json.load(fh)
        except (OSError, ValueError):
            merged = {}
    merged[args.label] = rec
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2)
    print(f"{args.label}: {rec['verdict']} (dups={len(dups)}, errors={len(errors)}, rows={rec['parameters_network_table_rows']}, click_post={posted_at}) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
