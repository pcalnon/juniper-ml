#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""What is canopy's page main thread doing at IDLE? A CDP CPU profile, by self time.

WHY. F-CANOPY-035, -052 and -053 are one mechanism: a periodic writer whose re-request
period is shorter than the renderer's APPLY latency has every response discarded.
The 2026-09-22 Lane A2 validation measured that apply latency at its source: the page's
main thread was 66-75% busy in long tasks, and ``fetch()`` -> parsed JSON took
3.2-5.5 s against a ~30 ms network leg, with the dashboard IDLE. Per-writer ``running=``
guards (canopy#613) treat the symptom one store at a time. This asks what the main
thread is spending its time on, so the cause can be named instead of inferred.

It does NOT decide anything about a callback. It reports the JS functions (name, script,
line) that hold the most self time over a window, plus the share of the window that
was idle, program (native) or GC. A result dominated by dash-renderer's own functions
(``getReadyCallbacks``, ``getAllSubsequentOutputsForCallback``, ``getPriority``, the
redux reducers) points at the renderer's bookkeeping scaling with canopy's callback
graph. One dominated by plotly or React reconciliation points at rendering.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8051 LIBTORCH= LD_LIBRARY_PATH= \\
      /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/2026-09-22_canopy_idle_cpu_profile.py \\
      --tab 'Training Metrics' --seconds 20 --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_idle_cpu_profile.json
"""

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")
log = _seg17.log
CANOPY = _seg17.CANOPY


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tab", default="Training Metrics")
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--settle", type=float, default=20.0, help="seconds after the tab click before profiling (let the mount burst pass)")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser, ctx, page = _seg17.open_dashboard(pw, [])
        try:
            _seg17.open_tab(page, args.tab)
            page.wait_for_timeout(int(args.settle * 1000))
            cdp = ctx.new_cdp_session(page)
            cdp.send("Profiler.enable")
            cdp.send("Profiler.setSamplingInterval", {"interval": 1000})  # microseconds
            cdp.send("Profiler.start")
            page.wait_for_timeout(int(args.seconds * 1000))
            prof = cdp.send("Profiler.stop")["profile"]
        finally:
            browser.close()

    nodes = {n["id"]: n for n in prof["nodes"]}
    samples = prof.get("samples") or []
    deltas = prof.get("timeDeltas") or []
    self_us = collections.Counter()
    for sid, dt in zip(samples, deltas):
        self_us[sid] += max(0, dt)
    total = sum(self_us.values()) or 1

    by_fn = collections.Counter()
    by_script = collections.Counter()
    special = collections.Counter()
    for nid, us in self_us.items():
        cf = nodes[nid]["callFrame"]
        fn = cf.get("functionName") or "(anonymous)"
        url = cf.get("url") or ""
        if fn in ("(idle)", "(program)", "(garbage collector)", "(root)"):
            special[fn] += us
            continue
        script = url.rsplit("/", 1)[-1].split("?", 1)[0] or "(native)"
        # Minified bundles put everything on one line; the COLUMN is what locates a frame.
        by_fn[(fn, script, f"{cf.get('lineNumber', -1) + 1}:{cf.get('columnNumber', -1) + 1}")] += us
        by_script[script] += us

    # Inclusive (total) time per frame: a minified renderer's hot path is a few large
    # observer closures whose SELF time is spread over mangled helpers; the frame that
    # CONTAINS the time is what names the stage.
    parent = {}
    for n in prof["nodes"]:
        for c in n.get("children") or []:
            parent[c] = n["id"]
    incl = collections.Counter()
    for nid, us in self_us.items():
        seen = set()
        cur = nid
        while cur is not None:
            cf = nodes[cur]["callFrame"]
            key = (cf.get("functionName") or "(anonymous)", (cf.get("url") or "").rsplit("/", 1)[-1].split("?", 1)[0], cf.get("lineNumber", -1) + 1, cf.get("columnNumber", -1) + 1)
            if key not in seen:
                incl[key] += us
                seen.add(key)
            cur = parent.get(cur)

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "tab": args.tab, "seconds": args.seconds,
           "total_ms": round(total / 1000, 1),
           "special_pct": {k: round(100 * v / total, 1) for k, v in special.items()},
           "top_scripts_pct": [(s, round(100 * v / total, 1)) for s, v in by_script.most_common(15)],
           "top_functions": [{"fn": f, "script": s, "line": ln, "pct": round(100 * v / total, 2), "ms": round(v / 1000, 1)} for (f, s, ln), v in by_fn.most_common(args.top)],
           "top_inclusive": [{"fn": f, "script": s, "line": ln, "col": col, "pct": round(100 * v / total, 2)}
                             for (f, s, ln, col), v in incl.most_common(60) if s.startswith("dash_renderer")][:args.top]}
    log(f"profiled {res['total_ms']} ms of main thread; idle/program/GC: {res['special_pct']}")
    log("top scripts by self time:")
    for s, p in res["top_scripts_pct"]:
        log(f"  {p:6.1f}%  {s}")
    log("top functions by self time:")
    for r in res["top_functions"]:
        log(f"  {r['pct']:6.2f}%  {r['ms']:8.1f} ms  {r['fn'][:48]:48s} {r['script'][:40]}:{r['line']}")
    log("top dash-renderer frames by INCLUSIVE time:")
    for r in res["top_inclusive"]:
        log(f"  {r['pct']:6.2f}%  {r['fn'][:40]:40s} {r['script'][:36]}:{r['line']}:{r['col']}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
