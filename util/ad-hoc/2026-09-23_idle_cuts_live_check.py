#!/usr/bin/env python
"""The idle dispatch cuts on a live leg: structure, the replay-session gate, and latency against the parent.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 8, cheap cuts);
         util/ad-hoc/2026-09-23_canopy_timer_park_ab.py (the in-page A/B that motivated the cuts)

The A/B parked two timers inside one page. This checks the BUILD that removes one and gates the other,
against a leg serving its exact parent, on the same trio (cascor :8202, data :8101):

  CONTROL  --control-url  (the parent: dead ``metrics-panel-update-interval``, ungated weight drain)
  CUTS     --cuts-url     (the cuts branch)

Windows alternate C1 X1 C2 X2 C3, each a FRESH browser: load, the Training Metrics tab, settle, then
measure. Per window it records:
  * structure: whether ``metrics-panel-update-interval`` is in ``paths.strs``; the weight drain's
    ``disabled`` and its ``n_intervals`` at the start and 10 s later;
  * response-delivery latency L over ``--measure`` seconds, the Phase 7 definition (``window.fetch``
    call to the page-side ``.json()`` resolve), for ``_dash-update-component`` responses;
  * console errors.
In X1 only, after the latency window, it drives the SESSION PATH. It writes ``replay-player-session``
= ``{snapshot_id: "idle-cuts-live-check"}`` (setProps on the Store; a fake id, so the server callbacks
that read the session make read-only requests that 404) and waits for the drain to enable and tick.
Then it writes ``{snapshot_id: null}`` and waits for the drain to disable and stop.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN.
  STRUCTURE  PASS if every X window has no dead timer, the drain disabled and 0 ticks over 10 s, AND
             every C window has the dead timer present and the drain ticking (the control is the parent).
  SESSION    PASS if, after the write, ``disabled`` is false within 15 s and the drain ticks >= 5 times
             in the next 10 s; and after the clear, ``disabled`` is true within 15 s and 0 ticks in the
             next 10 s.
  LATENCY    CONSISTENT if X1 < min(C1, C2) AND X2 < min(C2, C3) on L p50; INCONSISTENT if X1 >
             max(C1, C2) OR X2 > max(C2, C3); MIXED otherwise.
  ERRORS     the X windows' console errors are no more than the C windows' (per window, summed).

PREDICTIONS -- FIXED BEFORE THE FIRST RUN: STRUCTURE PASS; SESSION PASS; LATENCY CONSISTENT, with the
X/C ratio of L p50 between 0.60 and 0.85 (the in-page A/B measured 0.58-0.68 for parking the drain);
ERRORS no worse.

Usage:
    JUNIPER_E2E_BROWSER_GPU=1 LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_idle_cuts_live_check.py --control-url http://127.0.0.1:8055 \\
        --cuts-url http://127.0.0.1:8056 \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_idle_cuts_live_check.json
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


DEAD = "metrics-panel-update-interval"
DRAIN = "replay-player-panel-weight-drain"
SESSION = "replay-player-session"

FETCH_HOOK = """
(() => {
  if (window.__lcFetch) return;
  window.__lcFetch = [];
  const orig = window.fetch;
  window.fetch = function (input, init) {
    const url = (typeof input === 'string') ? input : (input && input.url) || '';
    const t0 = performance.now();
    const p = orig.apply(this, arguments);
    if (url.indexOf('_dash-update-component') < 0) return p;
    return p.then((res) => {
      const j = res.json.bind(res);
      res.json = function () { return j().then((b) => { window.__lcFetch.push([t0, performance.now()]); return b; }); };
      return res;
    });
  };
})();
"""

PROBE = """(ids) => { const s = window.store && window.store.getState ? window.store.getState() : null; if (!s) return null;
  const strs = s.paths && s.paths.strs ? s.paths.strs : {}; const out = {};
  for (const id of ids) { const path = strs[id]; let node = s.layout;
    if (path) { for (const k of path) { if (node == null) break; node = node[k]; } }
    out[id] = path ? (node && node.props ? {present: true, n: node.props.n_intervals, disabled: node.props.disabled === true} : {present: true}) : {present: false}; }
  return out; }"""


def _p50(xs):
    xs = sorted(xs)
    return round(xs[len(xs) // 2], 1) if xs else None


def _window(pw, url, label, args, w3, f027, setprops, session_path):
    os.environ["JUNIPER_E2E_CANOPY_URL"] = url
    w3.CANOPY = url  # open_dashboard navigates to the module-level CANOPY
    errors = []
    browser, _ctx, page = w3.open_dashboard(pw, [])
    page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
    rec = {"label": label, "url": url, "serving": w3.serving_commit()}
    try:
        page.evaluate(FETCH_HOOK)
        f027.ensure_no_modal(page)
        f027.open_tab(page, "Training Metrics")
        page.wait_for_timeout(int(args.settle * 1000))
        s0 = page.evaluate(PROBE, [DEAD, DRAIN])
        page.wait_for_timeout(10_000)
        s1 = page.evaluate(PROBE, [DEAD, DRAIN])
        rec["structure"] = {"start": s0, "after_10s": s1, "dead_present": s0[DEAD]["present"],
                            "drain_disabled": s0[DRAIN].get("disabled"), "drain_ticks_10s": (s1[DRAIN].get("n") or 0) - (s0[DRAIN].get("n") or 0)}
        f0 = page.evaluate("window.__lcFetch.length")
        page.wait_for_timeout(int(args.measure * 1000))
        lat = [b - a for a, b in page.evaluate("(i) => window.__lcFetch.slice(i)", f0)]
        rec["latency"] = {"n": len(lat), "p50_ms": _p50(lat)}
        if session_path:
            sp = {}
            sp["write"] = page.evaluate(setprops, {"id": SESSION, "payload": {"data": {"snapshot_id": "idle-cuts-live-check", "playing": False}}})
            t = time.time()
            enabled_after = None
            while time.time() - t < 15:
                if page.evaluate(PROBE, [DRAIN])[DRAIN].get("disabled") is False:
                    enabled_after = round(time.time() - t, 1)
                    break
                page.wait_for_timeout(250)
            sp["enabled_after_s"] = enabled_after
            n_a = page.evaluate(PROBE, [DRAIN])[DRAIN].get("n") or 0
            page.wait_for_timeout(10_000)
            sp["ticks_10s_enabled"] = (page.evaluate(PROBE, [DRAIN])[DRAIN].get("n") or 0) - n_a
            sp["clear"] = page.evaluate(setprops, {"id": SESSION, "payload": {"data": {"snapshot_id": None}}})
            t = time.time()
            disabled_after = None
            while time.time() - t < 15:
                if page.evaluate(PROBE, [DRAIN])[DRAIN].get("disabled") is True:
                    disabled_after = round(time.time() - t, 1)
                    break
                page.wait_for_timeout(250)
            sp["disabled_after_s"] = disabled_after
            n_b = page.evaluate(PROBE, [DRAIN])[DRAIN].get("n") or 0
            page.wait_for_timeout(10_000)
            sp["ticks_10s_cleared"] = (page.evaluate(PROBE, [DRAIN])[DRAIN].get("n") or 0) - n_b
            rec["session_path"] = sp
    finally:
        browser.close()
    rec["console_errors"] = errors[:20]
    rec["console_error_count"] = len(errors)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--control-url", required=True)
    ap.add_argument("--cuts-url", required=True)
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--measure", type=float, default=60.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    w3 = _load("_w3drv", "e2e_w3_params_driver.py")
    f027 = _load("_f027drv", "e2e_f027_redrive.py")
    setprops = _load("_f039supt", "e2e_f039_supersession_test.py").SETPROPS
    log = w3.log

    from playwright.sync_api import sync_playwright

    plan = [("C1", args.control_url, False), ("X1", args.cuts_url, True), ("C2", args.control_url, False), ("X2", args.cuts_url, False), ("C3", args.control_url, False)]
    res = {"probe": Path(__file__).name, "control_url": args.control_url, "cuts_url": args.cuts_url, "settle_s": args.settle, "measure_s": args.measure, "windows": []}
    with sync_playwright() as pw:
        for label, url, sp in plan:
            rec = _window(pw, url, label, args, w3, f027, setprops, sp)
            res["windows"].append(rec)
            st = rec["structure"]
            log(f"  {label} {url} sha={(rec['serving'] or {}).get('git_sha', '')[:8]} dead={st['dead_present']} drain_disabled={st['drain_disabled']} drain_ticks_10s={st['drain_ticks_10s']} "
                f"L50={rec['latency']['p50_ms']} n={rec['latency']['n']} errors={rec['console_error_count']} session={rec.get('session_path')}")

    w = {r["label"]: r for r in res["windows"]}
    xs, cs = [w["X1"], w["X2"]], [w["C1"], w["C2"], w["C3"]]
    structure = all((not r["structure"]["dead_present"]) and r["structure"]["drain_disabled"] is True and r["structure"]["drain_ticks_10s"] == 0 for r in xs) and all(
        r["structure"]["dead_present"] and r["structure"]["drain_ticks_10s"] > 0 for r in cs
    )
    sp = w["X1"].get("session_path") or {}
    session = sp.get("enabled_after_s") is not None and (sp.get("ticks_10s_enabled") or 0) >= 5 and sp.get("disabled_after_s") is not None and sp.get("ticks_10s_cleared") == 0
    l = {k: w[k]["latency"]["p50_ms"] for k in w}
    if None in l.values():
        latency = "VOID"
    elif l["X1"] < min(l["C1"], l["C2"]) and l["X2"] < min(l["C2"], l["C3"]):
        latency = "CONSISTENT"
    elif l["X1"] > max(l["C1"], l["C2"]) or l["X2"] > max(l["C2"], l["C3"]):
        latency = "INCONSISTENT"
    else:
        latency = "MIXED"
    ratio = None if None in l.values() else round(((l["X1"] + l["X2"]) / 2) / ((l["C1"] + l["C2"] + l["C3"]) / 3), 2)
    errors_ok = sum(r["console_error_count"] for r in xs) / 2 <= sum(r["console_error_count"] for r in cs) / 3
    res["verdicts"] = {"STRUCTURE": "PASS" if structure else "FAIL", "SESSION": "PASS" if session else "FAIL", "LATENCY": latency, "X_over_C_p50": ratio, "ERRORS_no_worse": errors_ok}
    log(f"=> {json.dumps(res['verdicts'])}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
