#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""F-CANOPY-058 census v2, live: does a mid-request re-enable of canopy#613's guarded lane evict, and cascade?

Replaces ``util/ad-hoc/2026-09-24_f058_trigger_census.py``, which was refuted before its first run (ledger
Phase 9, Instruments). Its four defects and their repairs:

  1. It scored every answer without props EVICTED (a store subscriber never sees such an answer in
     ``executed``). Repaired: the shim (``2026-10-04_f058_census_v2_shim.py``) reads the lifecycle at the
     DISPATCH, installed at init. An answer is A whatever it carries; X is a request pruned from ``watched``
     before it resolved.
  2. Its fire detector read the lane after the fire's own write. Repaired: a fire is the watchdog's
     ``AddExecuted`` with ``disabled: false``, recorded with the lane's value BEFORE that dispatch.
  3. T-apply was scored with nothing in flight, and ``took()`` skipped its in-flight check. Repaired: every
     trigger fires only while a feeder request has been in flight >= 1.5 s, and TOOK requires the trigger's
     own effect WHILE THAT REQUEST IS STILL OPEN (below).
  4. Its window and floor assumed a 1 Hz lane. Repaired: sized to the lane's measured ~7.5 s self-clocked
     cadence (Phase 9), below.

The shim was checked first on a synthetic app with canopy's wiring, both ways
(``2026-10-04_f058_census_v2_synth_check.py``): data answers and ``no_update`` answers each scored 13 of 13
answered, 0 evicted, with no trigger; a mid-request second-Input change scored every later request evicted in
both modes; the gate's mount write, landing while a 3 s first request was in flight, started a cascade at page
load; and every watchdog fire was caught at the write with the lane disabled before it.

TARGET (canopy ``main``): ``metrics-store-interval`` -> ``update_metrics_store`` ->
``metrics-panel-metrics-store.data``, ``running=[(Output("metrics-store-interval", "disabled"), True, False)]``.

TRIGGERS, each fired only while a feeder request has been in flight >= 1.5 s (polled every 100 ms, up to
120 s; else MISSED):
  T-gate   ``set_props(apply-in-flight, {data: 0})``: the fused gate's Input changes and it writes this lane
           ``false``. TOOK = the shim records a gate write of ``false`` with the lane ``true`` before it, while
           the request is still open.
  T-tab    a DOM click on the "About" tab, then on "Training Metrics" 1.0 s later (page timestamps): two gate
           writes, the real UI path. The click is the one ``e2e_f027_redrive.open_tab`` uses, without its 3.5 s
           settle, which would put the re-enable outside TOOK's horizon; its ``ensure_no_modal`` runs first,
           because the welcome modal intercepts every click while it is open. TOOK as T-gate, within 2.5 s.
  T-apply  ``set_props(apply-in-flight, {data: {in_flight: true, since}})`` (the clamp), hold 4 s, then wait for
           a request in flight >= 1.0 s (up to 60 s) and ``set_props(apply-in-flight, {data: false})`` (the
           release, which is the trigger). The clamp Store is what the gate reads; a real Apply would PATCH
           the trio's cascor. TOOK as T-gate, for the release.
  T-mode   ``set_props(metrics-panel-display-mode-store, {data: {mode: "window", window_size: w + 1}})``, the
           feeder's SECOND Input. TOOK = a new feeder request enters ``watched`` within 1.0 s while the old one
           is still open.
  idle     600 s, no trigger, for the watchdog.

WINDOWS (fixed before the first run): settle 45 s; baseline 240 s (~30 requests at ~7.5 s); each trigger
window 180 s from the trigger (~24 requests); idle 600 s. Order: baseline, T-gate, T-tab, T-apply, idle,
T-mode (the mode change last, so no earlier window runs at another window size).

VERDICT RULE (fixed before the first run). Counted over feeder requests that ENTERED ``watched`` in the
window and ended (A or X) by its end. ``late`` = the window's second half.
  baseline  CLEAN    resolved >= 15 and evicted <= 1
            DIRTY    resolved >= 15 and evicted >= 2 (reported; triggers are still scored)
            VOID     resolved < 15
  trigger   CASCADE    resolved >= 6 and (evicted / resolved >= 0.75, or late's evicted / late's resolved >= 0.5)
            CONTAINED  resolved >= 6, evicted <= 2, and late has no eviction
            PARTIAL    resolved >= 6, otherwise
            VOID       resolved < 6;  MISSED / NO-EFFECT as above (a NO-EFFECT is reported, never scored)
  idle      FIRES (watchdog fires, each with the lane disabled before it) and EVICTED, reported, not scored.

PREDICTIONS (fixed before the first run).
  * baseline CLEAN, cadence 5.5–9 s. The synthetic app's mount cascade (a gate mount write while the first
    request is in flight) would instead show as a DIRTY baseline from page load.
  * F-CANOPY-058 predicts CASCADE for T-gate, T-tab, T-apply and T-mode. canopy's own comment on the feeder
    ("Self-healing, bounded to one cycle") predicts CONTAINED for the three gate writes.
  * idle: Lane B's model (37-44 false fires an hour at a 7 s cycle) predicts ~6 fires in 600 s; the Phase 9
    census saw none in 210 s.
  * What could make the census answer otherwise: a feeder that answers before the next tick (server time
    under the 1 s period) cannot be evicted by a re-enable, so every trigger would read CONTAINED or
    NO-EFFECT. The cadence and each request's in-flight time are recorded, so that case is visible.

HARD RULES: it never POSTs or PATCHes cascor or juniper-data, never touches :8051, drives one browser, and
reads ``JUNIPER_E2E_CANOPY_URL``. Its only request outside the browser is a GET of the leg's ``/v1/health``,
for the commit it serves.

Usage (canopy env; ``--adhoc-dir`` is juniper-ml's ``util/ad-hoc``, where ``e2e_f027_redrive.py`` lives, and
defaults to this file's own directory):
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:<port> env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB \\
        /opt/miniforge3/envs/JuniperCanopy1/bin/python <this file> --out <transcript.json> [--adhoc-dir <dir>]
"""

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    """Load a module by path (a dated name cannot be imported); registered first, as a dataclass would need."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_shim = _load("f058_census_v2_shim", HERE / "2026-10-04_f058_census_v2_shim.py")
SHIM, classify, window_stats = _shim.SHIM, _shim.classify, _shim.window_stats

CANOPY = os.environ.get("JUNIPER_E2E_CANOPY_URL", "")
FEED = "metrics-panel-metrics-store.data"
LANE = "metrics-store-interval"
SETPROPS = "([id, props]) => window.dash_clientside.set_props(id, props)"
NOW = "() => Date.now() - window.__f058v2.t0"
OPEN_SINCE = """(minAge) => { const R = window.__f058v2; if (!R) return null; const now = Date.now() - R.t0; const open = new Map();
  for (const [t, k, id] of R.req) { if (k === 'W') { if (!open.has(id)) open.set(id, t); } else if (k === 'A' || k === 'X') open.delete(id); }
  let best = null; for (const [id, t] of open) if (now - t >= minAge && (best === null || t < best[1])) best = [id, t];
  return best ? {now, id: best[0], since: best[1]} : null; }"""
MODE_NOW = """() => { const s = window.store.getState(); const p = s.paths && s.paths.strs ? s.paths.strs['metrics-panel-display-mode-store'] : null;
  let n = s.layout; if (!p) return null; for (const k of p) { if (n == null) return null; n = n[k]; } return n && n.props ? n.props.data : null; }"""
# e2e_f027_redrive.open_tab's click, without its settle: a DOM click reaches the tab whatever overlays it.
CLICK_TAB = """(label) => { const t = [...document.querySelectorAll('[role=tab]')].find(x => x.textContent.trim() === label);
  if (!t) return null; t.click(); return Date.now() - window.__f058v2.t0; }"""


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def served_sha() -> str:
    """The commit the leg serves, from its own ``/v1/health`` (a checkout is not a deployment)."""
    try:
        with urllib.request.urlopen(f"{CANOPY}/v1/health", timeout=5) as r:  # nosec B310 - the operator's local leg
            body = json.loads(r.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return f"<unreadable: {type(exc).__name__}>"
    return str(body.get("git_sha") or (body.get("details") or {}).get("git_sha") or "<none>")


def ended_by(raw, rid, t_ms):
    """True if request ``rid`` had ended (A or X) at page time ``t_ms``."""
    return any(r[2] == rid and r[1] in ("A", "X") and r[0] <= t_ms for r in raw["req"])


def took_gate(raw, t_ms, rid, horizon_ms=1000):
    """A gate write of false, with the lane true before it, in (t, t+horizon], while request rid was still open."""
    for t, before, v in raw["gate"]:
        if t_ms < t <= t_ms + horizon_ms and before is True and v is False and not ended_by(raw, rid, t):
            return True
    return False


def took_mode(raw, t_ms, rid, horizon_ms=1000):
    """A new feeder request entered watched in (t, t+horizon] while request rid was still open."""
    for t, kind, other, _p in raw["req"]:
        if kind == "W" and other != rid and t_ms < t <= t_ms + horizon_ms and not ended_by(raw, rid, t):
            return True
    return False


def baseline_verdict(st):
    if st["resolved"] < 15:
        return "VOID"
    return "CLEAN" if st["evicted"] <= 1 else "DIRTY"


def trigger_verdict(st, late):
    if st["resolved"] < 6:
        return "VOID"
    frac = st["evicted"] / st["resolved"]
    late_frac = (late["evicted"] / late["resolved"]) if late["resolved"] else 0.0
    if frac >= 0.75 or late_frac >= 0.5:
        return "CASCADE"
    if st["evicted"] <= 2 and late["evicted"] == 0:
        return "CONTAINED"
    return "PARTIAL"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--baseline", type=float, default=240.0)
    ap.add_argument("--window", type=float, default=180.0)
    ap.add_argument("--idle", type=float, default=600.0)
    ap.add_argument("--adhoc-dir", default=str(HERE), help="juniper-ml util/ad-hoc, for e2e_f027_redrive.ensure_no_modal")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not CANOPY or ":8051" in CANOPY:
        raise SystemExit("set JUNIPER_E2E_CANOPY_URL to a verify leg (never :8051)")
    redrive = _load("e2e_f027_redrive", Path(args.adhoc_dir) / "e2e_f027_redrive.py")

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "served_sha": served_sha(), "args": vars(args), "triggers": []}
    log(f"leg {CANOPY} serves {res['served_sha']}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--enable-gpu"] if os.environ.get("JUNIPER_E2E_BROWSER_GPU") == "1" else [])
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        ctx.add_init_script(script=f"window.__f058cfg = {json.dumps({'feed': FEED, 'lane': LANE})};")
        ctx.add_init_script(script=SHIM)
        page = ctx.new_page()
        try:
            page.goto(CANOPY, wait_until="domcontentloaded")
            # The welcome modal is closed during the settle, so neither its close nor its overlay lands in a window.
            page.wait_for_timeout(5000)
            redrive.ensure_no_modal(page)
            page.wait_for_timeout(int(max(args.settle - 5.0, 0.0) * 1000))
            res["installed"] = page.evaluate("() => window.__f058v2 && window.__f058v2.installed")
            if not res["installed"]:
                log("!! shim not installed")
                return 2
            t_base = page.evaluate(NOW)
            page.wait_for_timeout(int(args.baseline * 1000))
            res["baseline_window_ms"] = [t_base, t_base + args.baseline * 1000]

            def wait_open(min_age_ms, timeout_s):
                end = time.time() + timeout_s
                while time.time() < end:
                    o = page.evaluate(OPEN_SINCE, min_age_ms)
                    if o:
                        return o
                    page.wait_for_timeout(100)
                return None

            for name in ("T-gate", "T-tab", "T-apply", "idle", "T-mode"):
                rec = {"name": name}
                if name == "idle":
                    t = page.evaluate(NOW)
                    page.wait_for_timeout(int(args.idle * 1000))
                    res["idle_window_ms"] = [t, t + args.idle * 1000]
                    continue
                if name == "T-tab":
                    redrive.ensure_no_modal(page)
                if name == "T-apply":
                    o = wait_open(1500, 120)
                    rec["clamp"] = page.evaluate(SETPROPS, ["apply-in-flight", {"data": {"in_flight": True, "since": int(time.time() * 1000)}}]) if o else None
                    page.wait_for_timeout(4000)
                o = wait_open(1500 if name != "T-apply" else 1000, 120 if name != "T-apply" else 60)
                if not o:
                    rec["verdict"] = "MISSED"
                    res["triggers"].append(rec)
                    log(f"  {name}: MISSED")
                    if name == "T-apply":
                        page.evaluate(SETPROPS, ["apply-in-flight", {"data": False}])
                    continue
                rec.update(t_ms=o["now"], open_request=o["id"], open_since_ms=o["since"])
                if name == "T-gate":
                    page.evaluate(SETPROPS, ["apply-in-flight", {"data": 0}])
                elif name == "T-apply":
                    page.evaluate(SETPROPS, ["apply-in-flight", {"data": False}])
                elif name == "T-tab":
                    rec["clicks_ms"] = [page.evaluate(CLICK_TAB, "About")]
                    page.wait_for_timeout(1000)
                    rec["clicks_ms"].append(page.evaluate(CLICK_TAB, "Training Metrics"))
                    if None in rec["clicks_ms"]:
                        log(f"  !! T-tab: a tab was not found ({rec['clicks_ms']})")
                elif name == "T-mode":
                    mode = page.evaluate(MODE_NOW) or {"mode": "window", "window_size": 100}
                    rec["mode_before"] = mode
                    page.evaluate(SETPROPS, ["metrics-panel-display-mode-store", {"data": dict(mode, mode="window", window_size=int(mode.get("window_size") or 100) + 1)}])
                page.wait_for_timeout(int(args.window * 1000))
                res["triggers"].append(rec)
                log(f"  {name}: fired at {rec['t_ms']} ms on request {rec['open_request']}")
            raw = page.evaluate("() => window.__f058v2")
        finally:
            browser.close()

    res["raw"] = raw
    recs = classify(raw["req"])
    b = window_stats(recs, *res["baseline_window_ms"])
    b["verdict"] = baseline_verdict(b)
    res["baseline"] = b
    log(f"BASELINE {json.dumps(b)}")
    for rec in res["triggers"]:
        if rec.get("verdict") == "MISSED":
            continue
        t, rid = rec["t_ms"], rec["open_request"]
        rec["took"] = took_mode(raw, t, rid) if rec["name"] == "T-mode" else took_gate(raw, t, rid, 2500 if rec["name"] == "T-tab" else 1000)
        st = window_stats(recs, t, t + args.window * 1000)
        late = window_stats(recs, t + args.window * 500, t + args.window * 1000)
        st["verdict"] = trigger_verdict(st, late) if rec["took"] else "NO-EFFECT"
        st["late"] = late
        rec["stats"] = st
        log(f"{rec['name']} took={rec['took']} {json.dumps(st)}")
    lo, hi = res["idle_window_ms"]
    idle = window_stats(recs, lo, hi)
    idle["fires"] = [f for f in raw["fires"] if lo <= f[0] < hi]
    res["idle"] = idle
    log(f"IDLE {json.dumps(idle)}")
    res["all_fires"] = raw["fires"]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
