#!/usr/bin/env python
"""F-CANOPY-058 live: does a mid-request re-enable of a ``running=``-guarded lane start an eviction cascade on canopy?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation (canopy E2E arc, Phase 10: F-CANOPY-058's live confirmation) -- REFUTED
        before its first run; see the block below
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9, F-CANOPY-058;
         util/ad-hoc/2026-09-23_f055_r1_laneB_repro.py (the synthetic-app repro this confirms or refutes);
         util/ad-hoc/2026-09-23_status_bar_apply_census.py (the watched/executed method, reused)

REFUTED BEFORE ITS FIRST RUN (2026-09-24, round 2 of the ledger's validation, Lane R2-B; the mechanism
re-derived by the orchestrator in the dash 4.2.0 renderer source). Do NOT run it as written. It has never run
against canopy, and everything below this block is the text as written, kept as provenance.
  1. The eviction count. An answer that carries no props leaves ``executed`` inside the same synchronous
     dispatch that put it there: the executed-callbacks observer ends in ``removeExecutedCallbacks``
     (``dash_renderer.dev.js:2627``), and only ``applyProps``, which runs only for a result with props,
     dispatches in between. The store subscription below registers after the renderer's own observer, so it
     never sees such a request in ``executed`` and scores it EVICTED. On a synthetic app, 13 of 13
     ``no_update`` answers read EVICTED, and 13 of 13 data answers APPLIED. On the idle trio, where the feeder
     answers ``no_update``, the baseline would VOID and every trigger would go unscored.
  2. "a ``no_update`` answer is a 204" (INSTRUMENT, below) is false. In dash 4.2.0 a callback with outputs
     sets ``has_update = ... or has_output`` (``_callback.py:602``), so it never raises ``PreventUpdate``: the
     answer is HTTP 200 with an empty ``response``, which the renderer still resolves to ``{}``.
  3. The fire detector reads the lane at the poll of the reset, after the fire's own ``false`` write, not at
     the poll before. On canopy's watchdog JavaScript over a 40 s lane it counted 0 of 2 real fires.
  4. T-apply is scored even with nothing in flight (``release_mid_request`` is never used); ``took()`` skips
     the "still in flight" check promised below; and T-tab's second click lands ~4.5 s after the first, not
     1.0 s, because ``open_tab`` waits 3.5 s.
  Fix direction (the ledger's Phase 9, Still owed item 0): record the executed transition itself (wrap
  ``window.store.dispatch`` and log ``addExecutedCallbacks`` by ``executionPromise``, or install a shim with
  ``add_init_script`` before the renderer builds its store); detect a fire from the lane's state BEFORE the
  reset; then pass a synthetic check with and without ``no_update`` answers before any live run. Evidence:
  util/ad-hoc/2026-09-24_ledger_r2_laneB_{census,watchdog}_synth_{app,drive}.py, and Lane R2-B's findings 1,
  2 and 7 in reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md.

THE TWO CLAIMS. F-CANOPY-058 says that dash-renderer's ``completeJob()`` releases a ``running=`` guard on
every HTTP outcome, an EVICTED request's included. So anything that re-enables the guarded lane while a
request is in flight restarts its timer; the restarted tick evicts the in-flight request, and that request's
late completion re-enables the lane under its successor. The two chains then keep evicting each other, and
the lane's responses stop applying for minutes. That rests on source plus a synthetic Dash app on the real
renderer; it has never been seen on canopy. canopy's own comment on the guarded feeder
(``dashboard_manager.py``, ``update_metrics_store``, qualification 2) says the opposite: a mid-fetch gate write
"re-enables the clock and reopens the eviction window for that cycle. Self-healing, bounded to one cycle, and
UNMEASURED." This measures it.

TARGET. canopy#613's guarded lane, on the leg under test: ``metrics-store-interval`` (1 s) ->
``update_metrics_store`` -> ``metrics-panel-metrics-store.data``, with
``running=[(Output("metrics-store-interval", "disabled"), True, False)]``. Its ``disabled`` has two more
writers: the fused CAN-000/tab gate (Inputs ``apply-in-flight.data`` and ``visualization-tabs.active_tab``;
it writes ``Boolean(apply-in-flight)`` to this global lane on every fire, mount included) and the strand
watchdog (slow lane, 5 s samples; it writes ``false`` after 30 s of sampled ``disabled``).

INSTRUMENT (in-page, one browser, one fresh context):
  * per-request, renderer units: each unique callback object of the feeder (``output`` exactly
    ``metrics-panel-metrics-store.data``; the WS-append writer's ``@``-suffixed output is excluded) is tracked
    from entering ``watched`` to entering ``executed`` (APPLIED) or leaving ``watched`` without entering it
    (EVICTED). dash-renderer moves a resolved request from ``watched`` to ``executed`` in one dispatch, and a
    store subscription sees every dispatch, so a record gone from ``watched`` with no ``executed`` was evicted.
    This does NOT depend on the response's content, which on an idle fixture is the same every time: a
    ``no_update`` answer is a 204, which ``handleServerside`` resolves as ``{}`` (``:976-979``), and the
    observer moves it to ``executed`` like any other. The copy it adds is a SPREAD of the watched entry, so
    records are keyed by ``executionPromise``, exactly as the observer matches them (``:2695-2701``).
  * the lane's ``disabled`` / ``n_intervals`` transitions, timestamped.
  * the watchdog: every change of ``window.__metricsStoreDisabledSince`` (100 ms poll). A reset to null after
    >= 29.5 s, with the lane ``disabled`` at the poll before, is a FIRE (it writes ``false``); a reset with the
    lane enabled is the watchdog seeing a healthy sample.
  * wire: Playwright request/response listeners on the feeder's requests, for in-flight detection.

TRIGGERS. Each fires only while a feeder request has been in flight for >= 1.5 s (polled every 100 ms, up to
90 s; else MISSED). A trigger TOOK if the lane was ``disabled`` just before it and read ``false`` within 1.0 s
after it while that request was still in flight; else NO-EFFECT (unscored).
  T-gate   ``setProps(apply-in-flight, 0)``. The gate's Input changes and nothing is clamped
           (``Boolean(0)`` is false), so the gate rewrites this lane ``false``. The mechanism alone; no backend
           call, no tab change.
  T-tab    click "About", then "Training Metrics" 1.0 s later: the real UI path, two gate writes.
  T-apply  ``setProps(apply-in-flight, {in_flight: true, since})`` (the clamp), hold 4 s, then wait for a
           request >= 1.0 s in flight (up to 30 s) and ``setProps(apply-in-flight, false)`` (the release). The
           release is the trigger scored. A real Apply would PATCH the trio's cascor, which is off limits; the
           clamp Store is what the gate reads.
  T-mode   ``setProps(metrics-panel-display-mode-store, {mode: "window", window_size: current + 1})``: the
           feeder's SECOND Input. ``getUniqueIdentifier`` ignores which Input fired, so a mid-flight change
           creates a same-identity request and evicts the in-flight one, exactly as a tick would (canopy's own
           comment, qualification 3). It re-enables nothing itself; the evicted request's late completion does.
           The mode stays "window", so the feeder's WS gating is unchanged. Added after Lane B1 of the Phase 9
           ledger's validation reproduced it in a synthetic app (0 applied, against 23 in the control).
           TOOK = the Store reads the new value 1.0 s later.
  idle     600 s with no trigger, for the watchdog.

WINDOWS. Settle 45 s after load on the default tab (Training Metrics); baseline 120 s; after each trigger a
150 s window; idle 600 s. The order is baseline, T-gate, T-tab, T-apply, idle, T-mode: the mode change goes
last, so no earlier window runs with a different window size.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN. f = APPLIED / tracked requests that entered ``watched`` in the
window and resolved (APPLIED or EVICTED) by its end.
  baseline   APPLIES if f >= 0.75 with >= 8 resolved; else VOID-BASELINE, and no trigger is scored.
  trigger    CASCADE    >= 6 resolved and f <= 0.25
             CONTAINED  f >= 0.75
             PARTIAL    otherwise (>= 6 resolved)
             VOID       fewer than 6 resolved
             MISSED / NO-EFFECT as above
  idle       FIRES = watchdog fires; DISCARDS = EVICTED. Reported, not scored against a threshold.
Descriptive, never scored: the longest run of consecutive EVICTED, the time from the trigger to the first
APPLIED, and the baseline cadence (median gap between APPLIED).

PREDICTIONS -- FIXED BEFORE THE FIRST RUN.
  * baseline: APPLIES, cadence 5.5-9 s (F-CANOPY-035's 5.5-7.3 s; the Phase 9 census's ~7.5 s).
  * F-CANOPY-058 predicts CASCADE for T-gate, T-tab, T-apply and T-mode. The feeder's comment predicts
    CONTAINED for the three gate writes ("bounded to one cycle"). For T-mode it predicts one eviction and
    says nothing about a cascade.
  * idle: Lane B's model (37-44 false fires an hour at a 7 s cycle) predicts about 6 fires in 600 s, each
    followed by EVICTED records. The Phase 9 census saw no fire in 210 s, weak evidence of a lower rate.
A CONTAINED result does not refute the synthetic repro; it refutes the finding ON CANOPY at this page's
latency, which is what the P1 rests on. A CASCADE confirms it.

HARD RULES this driver obeys: it never POSTs or PATCHes cascor or juniper-data, never touches :8051, and
drives exactly one browser. Point it at a verify leg with ``JUNIPER_E2E_CANOPY_URL``.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8061 python3 util/ad-hoc/2026-09-24_f058_trigger_census.py \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-24_f058_trigger_census_<sha>.json
"""

import argparse
import importlib.util
import json
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


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")
SETPROPS = _f039.SETPROPS
log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal

FEED = "metrics-panel-metrics-store.data"
LANE = "metrics-store-interval"

INSTALL = """(cfg) => {
  const st = window.store;
  if (!st || typeof st.subscribe !== 'function') return {found: false};
  const FEED = cfg.feed, LANE = cfg.lane, T0 = Date.now();
  const R = window.__f058 = {t0: T0, reqs: [], lane: [], since: [], notifications: 0};
  const track = new Map();
  let seq = 0, lastDisabled, lastN;
  const outOf = (c) => String(((c && c.callback) || {}).output || '');
  // KEY BY THE PROMISE, NOT THE OBJECT. On resolution the watched observer moves a request to `executed`
  // as a SPREAD COPY ({...currentCb, executionResult}), matching it by `executionPromise`
  // (dash_renderer.dev.js:2695-2701, dash 4.2.0). Keyed by object identity, every applied request
  // would read as evicted.
  const key = (c) => c.executionPromise || c;
  const laneProps = (s) => { const p = s.paths && s.paths.strs ? s.paths.strs[LANE] : null; let node = s.layout;
    if (!p) return null; for (const k of p) { if (node == null) return null; node = node[k]; } return node && node.props ? node.props : null; };
  const sample = () => {
    const s = st.getState(); R.notifications += 1; const now = Date.now() - T0;
    const cb = s.callbacks || {};
    const watched = (cb.watched || []).filter((c) => outOf(c) === FEED);
    const executed = (cb.executed || []).filter((c) => outOf(c) === FEED);
    for (const c of watched) { const k = key(c); if (!track.has(k)) { const r = {seq: ++seq, tW: now, tE: null, tGone: null}; track.set(k, r); R.reqs.push(r); } }
    for (const c of executed) { const r = track.get(key(c)); if (r && r.tE === null) r.tE = now; }
    const inW = new Set(watched.map(key));
    for (const [k, r] of track) { if (r.tE === null && r.tGone === null && !inW.has(k)) r.tGone = now; }
    const lp = laneProps(s);
    if (lp && (lp.disabled !== lastDisabled || lp.n_intervals !== lastN)) { R.lane.push([now, lp.disabled === true, lp.n_intervals]); lastDisabled = lp.disabled; lastN = lp.n_intervals; }
  };
  sample();
  st.subscribe(sample);
  let lastSince = window.__metricsStoreDisabledSince || null;
  setInterval(() => {
    const v = window.__metricsStoreDisabledSince || null;
    if (v !== lastSince) { R.since.push([Date.now() - T0, lastSince ? lastSince - T0 : null, v ? v - T0 : null, lastDisabled === true]); lastSince = v; }
  }, 100);
  return {found: true, t0: T0};
}"""

LANE_NOW = "() => { const r = window.__f058; return r && r.lane.length ? r.lane[r.lane.length - 1] : null; }"
MODE_NOW = """() => { const s = window.store.getState(); const p = s.paths && s.paths.strs ? s.paths.strs['metrics-panel-display-mode-store'] : null;
  let node = s.layout; if (!p) return null; for (const k of p) { if (node == null) return null; node = node[k]; } return node && node.props ? node.props.data : null; }"""
PAGE_NOW = "() => Date.now() - window.__f058.t0"


def _resolved(reqs, lo_ms, hi_ms):
    """Requests that entered watched in [lo, hi) and resolved (APPLIED or EVICTED) by hi."""
    out = []
    for r in reqs:
        if lo_ms <= r["tW"] < hi_ms:
            if r["tE"] is not None and r["tE"] <= hi_ms:
                out.append(("A", r))
            elif r["tGone"] is not None and r["tGone"] <= hi_ms:
                out.append(("E", r))
    return out


def _stats(reqs, lo_ms, hi_ms):
    res = _resolved(reqs, lo_ms, hi_ms)
    applied = [r for k, r in res if k == "A"]
    run = best = 0
    for k, _r in sorted(res, key=lambda kr: kr[1]["tW"]):
        run = run + 1 if k == "E" else 0
        best = max(best, run)
    gaps = sorted(b["tE"] - a["tE"] for a, b in zip(sorted(applied, key=lambda r: r["tE"]), sorted(applied, key=lambda r: r["tE"])[1:]))
    first = min((r["tE"] for r in applied), default=None)
    return {
        "resolved": len(res),
        "applied": len(applied),
        "evicted": len(res) - len(applied),
        "f": round(len(applied) / len(res), 3) if res else None,
        "longest_evicted_run": best,
        "first_applied_ms_after_start": (first - lo_ms) if first is not None else None,
        "cadence_ms_median": gaps[len(gaps) // 2] if gaps else None,
    }


def baseline_verdict(st: dict) -> str:
    if st["resolved"] >= 8 and st["f"] is not None and st["f"] >= 0.75:
        return "APPLIES"
    return "VOID-BASELINE"


def trigger_verdict(st: dict) -> str:
    if st["resolved"] < 6:
        return "VOID"
    if st["f"] <= 0.25:
        return "CASCADE"
    if st["f"] >= 0.75:
        return "CONTAINED"
    return "PARTIAL"


def watchdog_fires(since_log, threshold_ms: int = 29500):
    """Resets of __metricsStoreDisabledSince to null after >= threshold, with the lane disabled at the poll before."""
    fires = []
    for t, prev, new, lane_disabled_before in since_log:
        if new is None and prev is not None and (t - prev) >= threshold_ms and lane_disabled_before:
            fires.append(t)
    return fires


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--baseline", type=float, default=120.0)
    ap.add_argument("--window", type=float, default=150.0)
    ap.add_argument("--idle", type=float, default=600.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": serving_commit(), "args": vars(args), "triggers": []}
    log(f"canopy {CANOPY} serving {json.dumps(res['serving'])}")
    pending = {}

    def _is_feed(req) -> bool:
        return "_dash-update-component" in req.url and str((req.post_data_json or {}).get("output") or "") == FEED

    def on_request(req):
        if _is_feed(req):
            pending[req] = time.time()

    def on_response(resp):
        pending.pop(resp.request, None)

    def wait_in_flight(page, min_age_s: float, timeout_s: float):
        """Block until a feeder request has been in flight >= min_age_s AND the lane reads disabled. Returns page ms or None."""
        end = time.time() + timeout_s
        while time.time() < end:
            now = time.time()
            if any(now - t >= min_age_s for t in list(pending.values())):
                lane = page.evaluate(LANE_NOW)
                if lane and lane[1] is True:
                    return page.evaluate(PAGE_NOW)
            page.wait_for_timeout(100)
        return None

    def took(page, t_ms: float) -> bool:
        page.wait_for_timeout(1000)
        lane = page.evaluate("() => window.__f058.lane")
        before = [e for e in lane if e[0] <= t_ms]
        after = [e for e in lane if t_ms < e[0] <= t_ms + 1000]
        return bool(before) and before[-1][1] is True and any(e[1] is False for e in after)

    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, [])
        try:
            page.on("request", on_request)
            page.on("response", on_response)
            ensure_no_modal(page)
            page.wait_for_timeout(int(args.settle * 1000))
            install = page.evaluate(INSTALL, {"feed": FEED, "lane": LANE})
            if not install.get("found"):
                log("!! window.store not reachable")
                return 2
            res["install"] = install
            t_base = page.evaluate(PAGE_NOW)
            page.wait_for_timeout(int(args.baseline * 1000))
            res["baseline_window_ms"] = [t_base, t_base + args.baseline * 1000]

            for name in ("T-gate", "T-tab", "T-apply"):
                rec = {"name": name}
                if name == "T-apply":
                    t_clamp = wait_in_flight(page, 1.5, 90)
                    rec["clamp_ms"] = t_clamp
                    rec["clamp"] = page.evaluate(SETPROPS, {"id": "apply-in-flight", "payload": {"data": {"in_flight": True, "since": int(time.time() * 1000)}}}) if t_clamp is not None else None
                    page.wait_for_timeout(4000)
                    t = wait_in_flight(page, 1.0, 30)
                    rec["release_mid_request"] = t is not None
                    if t is None:
                        t = page.evaluate(PAGE_NOW)
                    rec["release"] = page.evaluate(SETPROPS, {"id": "apply-in-flight", "payload": {"data": False}})
                else:
                    t = wait_in_flight(page, 1.5, 90)
                    if t is None:
                        rec.update(verdict="MISSED")
                        res["triggers"].append(rec)
                        log(f"  {name}: MISSED")
                        continue
                    if name == "T-gate":
                        rec["action"] = page.evaluate(SETPROPS, {"id": "apply-in-flight", "payload": {"data": 0}})
                    else:
                        open_tab(page, "About")
                        page.wait_for_timeout(1000)
                        open_tab(page, "Training Metrics")
                rec["t_ms"] = t
                rec["took"] = took(page, t)
                page.wait_for_timeout(int(args.window * 1000))
                res["triggers"].append(rec)
                log(f"  {name}: at {t:.0f} ms, took={rec['took']}")

            t_idle = page.evaluate(PAGE_NOW)
            page.wait_for_timeout(int(args.idle * 1000))
            res["idle_window_ms"] = [t_idle, t_idle + args.idle * 1000]

            rec = {"name": "T-mode", "mode_before": page.evaluate(MODE_NOW)}
            t = wait_in_flight(page, 1.5, 90)
            if t is None or not isinstance(rec["mode_before"], dict):
                rec.update(verdict="MISSED")
                log("  T-mode: MISSED")
            else:
                new = dict(rec["mode_before"], mode="window", window_size=int(rec["mode_before"].get("window_size") or 100) + 1)
                rec["action"] = page.evaluate(SETPROPS, {"id": "metrics-panel-display-mode-store", "payload": {"data": new}})
                rec["t_ms"] = t
                page.wait_for_timeout(1000)
                rec["mode_after"] = page.evaluate(MODE_NOW)
                rec["took"] = rec["mode_after"] == new
                page.wait_for_timeout(int(args.window * 1000))
                log(f"  T-mode: at {t:.0f} ms, took={rec['took']}")
            res["triggers"].append(rec)
            raw = page.evaluate("() => window.__f058")
        finally:
            browser.close()

    res["raw"] = raw
    reqs = raw["reqs"]
    b = _stats(reqs, *res["baseline_window_ms"])
    b["verdict"] = baseline_verdict(b)
    res["baseline"] = b
    log(f"  BASELINE {json.dumps(b)}")
    for rec in res["triggers"]:
        if rec.get("verdict") == "MISSED":
            continue
        st = _stats(reqs, rec["t_ms"], rec["t_ms"] + args.window * 1000)
        if b["verdict"] != "APPLIES":
            st["verdict"] = "UNSCORED (baseline void)"
        elif not rec["took"]:
            st["verdict"] = "NO-EFFECT"
        else:
            st["verdict"] = trigger_verdict(st)
        rec["stats"] = st
        log(f"  {rec['name']} {json.dumps(st)}")
    lo, hi = res["idle_window_ms"]
    idle = _stats(reqs, lo, hi)
    fires = [t for t in watchdog_fires(raw["since"]) if lo <= t < hi]
    idle.update(watchdog_fires=len(fires), watchdog_fire_ms=fires)
    res["idle"] = idle
    log(f"  IDLE {json.dumps(idle)}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
