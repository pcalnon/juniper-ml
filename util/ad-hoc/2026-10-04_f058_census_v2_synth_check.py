#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — instrument check; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Known-answer check of the census v2 shim on the synthetic app, both ways, BEFORE any live run.

Each case launches ``2026-10-04_f058_census_v2_synth_app.py`` with its own settings, installs the shim at init,
optionally fires one trigger while a feeder request has been in flight >= 1.5 s, and checks the shim's counts
against an answer fixed here, before the run:

  data-control      FEED_MODE=data,     LAT 3 s, no trigger, 45 s  ->  evicted == 0, answered >= 5, all with props
  noupdate-control  FEED_MODE=noupdate, LAT 3 s, no trigger, 45 s  ->  evicted == 0, answered >= 5, props only on the first
  data-mode         FEED_MODE=data,     LAT 3 s, second-Input change mid-request, 45 s after  ->  evicted >= 1
  noupdate-mode     FEED_MODE=noupdate, LAT 3 s, second-Input change mid-request, 45 s after  ->  evicted >= 1
  mount-cascade     FEED_MODE=data,     LAT 3 s, the gate firing at mount (canopy's wiring), 45 s  ->  evicted >= 1
  watchdog          FEED_MODE=data,     LAT 20 s, STRAND_MS 8000, 70 s  ->  fires >= 1, each with the lane
                    disabled before it; evicted >= 1 after the first fire

The controls start the gate after load (``GATE_AT_MOUNT=0``): with canopy's wiring the gate's mount write lands
while the first 3 s request is in flight and starts a cascade at page load, which is the ``mount-cascade`` case.

v1 failed the second case (13 of 13 ``no_update`` answers read EVICTED) and counted 0 of 2 real fires.

Usage (canopy env; the app listens on ``SYNTH_PORT``, default 9491):
    env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB /opt/miniforge3/envs/JuniperCanopy1/bin/python <this file> [case ...]
"""

import importlib.util
import json
import os
import socket
import subprocess  # nosec B404 - launches the local synthetic app only
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_sibling(name: str):
    """Load this census's ``2026-10-04_f058_census_v2_<name>.py`` beside this file (a dated name cannot be imported)."""
    spec = importlib.util.spec_from_file_location(f"f058_census_v2_{name}", HERE / f"2026-10-04_f058_census_v2_{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_shim = _load_sibling("shim")
SHIM, classify, window_stats = _shim.SHIM, _shim.classify, _shim.window_stats

APP = HERE / "2026-10-04_f058_census_v2_synth_app.py"
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
PORT = int(os.environ.get("SYNTH_PORT", "9491"))
SETPROPS = "([id, props]) => window.dash_clientside.set_props(id, props)"
# Independent of the shim's A/X classification: every distinct value the feed Store takes. A subscriber is
# fine for this, because a value that changed STAYS changed; only a transient `executed` entry is invisible
# to a subscriber.
STORE_VALUES = r"""
(() => { const V = window.__storeVals = []; const d = Object.getOwnPropertyDescriptor(window, 'store');
  Object.defineProperty(window, 'store', {configurable: true, enumerable: true, get() { return d.get(); }, set(v) { d.set(v);
    v.subscribe(() => { const s = v.getState(); const p = s.paths && s.paths.strs ? s.paths.strs['metrics-panel-metrics-store'] : null;
      let n = s.layout; if (p) for (const k of p) { if (n == null) break; n = n[k]; } const val = n && n.props ? JSON.stringify(n.props.data) : null;
      if (V[V.length - 1] !== val) V.push(val); }); }}); })();
"""
IN_FLIGHT = """(minAge) => { const R = window.__f058v2; if (!R) return null; const now = Date.now() - R.t0; const open = new Map();
  for (const [t, k, id] of R.req) { if (k === 'W') { if (!open.has(id)) open.set(id, t); } else if (k === 'A' || k === 'X') open.delete(id); }
  for (const t of open.values()) if (now - t >= minAge) return now; return null; }"""


def port_free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def run_case(name, env, trigger, watch_s, expect):
    from playwright.sync_api import sync_playwright

    if not port_free(PORT):
        raise SystemExit(f"port {PORT} is taken; refusing")
    proc_env = dict(os.environ, PORT=str(PORT), **env)
    for k in ("LD_LIBRARY_PATH", "LIBTORCH", "LIBTORCH_LIB"):
        proc_env.pop(k, None)
    proc = subprocess.Popen([PY, str(APP)], env=proc_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603
    try:
        for _ in range(100):
            if not port_free(PORT):
                break
            time.sleep(0.2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context()
            ctx.add_init_script(script="window.__f058cfg = {feed: 'metrics-panel-metrics-store.data', lane: 'metrics-store-interval'};")
            ctx.add_init_script(script=SHIM)
            ctx.add_init_script(script=STORE_VALUES)
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{PORT}/")
            page.wait_for_timeout(8000)
            t_trig = None
            if trigger == "mode":
                deadline = time.time() + 30
                while time.time() < deadline and t_trig is None:
                    t_trig = page.evaluate(IN_FLIGHT, 1500)
                    if t_trig is None:
                        page.wait_for_timeout(100)
                if t_trig is not None:
                    page.evaluate(SETPROPS, ["metrics-panel-display-mode-store", {"data": {"mode": "window", "window_size": 101}}])
            page.wait_for_timeout(int(watch_s * 1000))
            raw = page.evaluate("() => window.__f058v2")
            store_vals = page.evaluate("() => window.__storeVals")
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    recs = classify(raw["req"])
    lo = 0 if t_trig is None else t_trig
    st = window_stats(recs, lo, 10**12)
    first_fire = raw["fires"][0][0] if raw["fires"] else None
    after_fire = window_stats(recs, first_fire, 10**12) if first_fire is not None else None
    result = {"case": name, "installed": raw["installed"], "errors": raw["errors"], "trigger_ms": t_trig, "stats": st, "fires": raw["fires"], "after_first_fire": after_fire, "lane_writes": len(raw["lane"]), "gate_writes": raw["gate"][:3], "store_distinct_nonnull": len([v for v in store_vals if v not in (None, "null")])}
    ok = expect(result)
    result["PASS"] = ok
    return result


def main() -> int:
    cases = [
        # The controls start the gate after load (GATE_AT_MOUNT=0): see "mount-cascade".
        ("data-control", {"FEED_MODE": "data", "LAT": "3", "GATE_AT_MOUNT": "0"}, None, 45,
         lambda r: r["stats"]["evicted"] == 0 and r["stats"]["answered"] >= 5 and r["stats"]["answered_with_props"] == r["stats"]["answered"] and r["store_distinct_nonnull"] >= r["stats"]["answered_with_props"]),
        ("noupdate-control", {"FEED_MODE": "noupdate", "LAT": "3", "GATE_AT_MOUNT": "0"}, None, 45,
         lambda r: r["stats"]["evicted"] == 0 and r["stats"]["answered"] >= 5 and r["stats"]["answered_with_props"] <= 1),
        ("data-mode", {"FEED_MODE": "data", "LAT": "3", "GATE_AT_MOUNT": "0"}, "mode", 45, lambda r: r["trigger_ms"] is not None and r["stats"]["evicted"] >= 1),
        ("noupdate-mode", {"FEED_MODE": "noupdate", "LAT": "3", "GATE_AT_MOUNT": "0"}, "mode", 45, lambda r: r["trigger_ms"] is not None and r["stats"]["evicted"] >= 1),
        # canopy's wiring as is: the gate's mount write re-enables the lane while the first request is in flight.
        ("mount-cascade", {"FEED_MODE": "data", "LAT": "3", "GATE_AT_MOUNT": "1"}, None, 45, lambda r: r["stats"]["evicted"] >= 1),
        ("watchdog", {"FEED_MODE": "data", "LAT": "20", "STRAND_MS": "8000", "GATE_AT_MOUNT": "0"}, None, 70,
         lambda r: len(r["fires"]) >= 1 and all(f[1] is True for f in r["fires"]) and (r["after_first_fire"] or {}).get("evicted", 0) >= 1),
    ]
    only = set(sys.argv[1:])
    out = []
    for name, env, trig, watch, expect in cases:
        if only and name not in only:
            continue
        r = run_case(name, env, trig, watch, expect)
        out.append(r)
        print(json.dumps(r, default=str))
    print("ALL PASS" if all(r["PASS"] for r in out) else "SOME FAILED")
    return 0 if all(r["PASS"] for r in out) else 1


if __name__ == "__main__":
    sys.exit(main())
