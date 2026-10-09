#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-08
# Status      : ad-hoc — instrument for one fix; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Real-renderer check of canopy's request/ack pacer (F-CANOPY-055, F-CANOPY-058, F-CANOPY-068).

A scratch Dash app, served by dash 4.2.0 (the JuniperCanopy1 environment) and driven in headless
Chromium, wires one poll lane in one of two ways, using canopy's ids:

  pacer  the fix (canopy branch ``fix/f055-f058-f068-request-ack-pacer``): ``metrics-store-interval``
         (1 s) clocks a clientside pacer whose JavaScript is canopy's own ``poll_pacer_js``, imported
         from ``--canopy-src``. It writes ``metrics-store-request``; the feeder's ONLY Input is that
         request; the display mode is State of the feeder and an Input of the pacer; the feeder writes
         the data and ``metrics-store-ack``.
  guard  the control, canopy ``main`` before the fix: the feeder takes the lane's ``n_intervals`` and
         the display mode as Inputs, with ``running=[(lane.disabled, True, False)]``, and canopy's strand
         watchdog on a 5 s ``slow-update-interval`` (verbatim logic from ``main`` ``3029d07d``).

Both arms carry canopy's fused CAN-000/tab gate (clientside; writes the lane ``Boolean(apply-in-flight)``
on every tab or clamp change, mount included).

The feeder sleeps a round trip drawn per request from a seeded normal (mean ``--rtt-ms``, sd 450 ms,
clipped to 888-5,345 ms, Phase 11's measured in-flight range), then answers ``{"seq": k}`` with a
server-side counter ``k``. One request in ``--strand`` mode sleeps ``--strand-ms`` instead, standing in
for a request that never gets a response.

Measurement. The server logs each request's ``k`` and its start and end. The page logs every value of
the data store it applies (a clientside callback appends to ``window.__applied``). A response the server
completed whose ``k`` never applied, while a later ``k`` did, was EVICTED. Fires of the watchdog (guard
arm) are counted in the page; stale re-issues (pacer arm) are read off the requests' ``reason``.

Phases, each fixed before the first run:
  idle      ``--idle-s`` seconds with no trigger (default 600: the item-24 test of 10 idle minutes on a
            healthy lane whose cycle is near the old watchdog's 5 s sampling period).
  triggers  for each of the four F-058 triggers, ``--trigger-reps`` times: wait until a request is in
            flight (the server's in-flight count reads 1 and the request is >=300 ms old), then fire it from
            the page: a tab switch away and back; the Apply clamp set then released 400 ms later; a
            display-mode change (window <-> full); and the clamp release alone. 6 s settle after each.
  strand    (pacer arm only, with ``--strand``) one request sleeps ``--strand-ms`` (default 45,000); the
            phase then waits for recovery.

Verdict rule (fixed before the first run): the pacer arm PASSES if (a) no response is evicted in any
phase; (b) in idle, no stale re-issue and every completed response applied except at most the one in
flight at the end; (c) each trigger leaves the next response applied; and (d) in strand, a ``stale``
request is issued between 30 s and 32 s after the stranded one and the lane applies again within 10 s of
it. The control arm is expected to FAIL (b), on watchdog fires or evictions; if it does not, the check
could not tell the arms apart in that run, and that is reported, not hidden.

Usage (JuniperCanopy1):
  python util/ad-hoc/2026-10-08_f055_f058_f068_pacer_renderer_check.py --arm pacer --canopy-src <worktree>/src --out <dir>
  python util/ad-hoc/2026-10-08_f055_f058_f068_pacer_renderer_check.py --arm guard --out <dir>
"""

import argparse
import json
import os
import random
import socket
import subprocess  # nosec B404 - launches this same script as the app server
import sys
import threading
import time
import urllib.request
from pathlib import Path

LANE = "metrics-store-interval"
REQ = "metrics-store-request"
ACK = "metrics-store-ack"
DATA = "metrics-panel-metrics-store"
MODE = "metrics-panel-display-mode-store"
CLAMP = "apply-in-flight"
TABS = "visualization-tabs"
STALE_MS = 30000
WATCHDOG_JS = """
function(n, disabled, applyInFlight) {
    var NU = window.dash_clientside.no_update;
    if (!disabled || Boolean(applyInFlight)) { window.__metricsStoreDisabledSince = null; return NU; }
    var now = Date.now();
    if (!window.__metricsStoreDisabledSince) { window.__metricsStoreDisabledSince = now; return NU; }
    if (now - window.__metricsStoreDisabledSince < %d) { return NU; }
    window.__metricsStoreDisabledSince = null;
    (window.__fires = window.__fires || []).push(Date.now());
    return false;
}
""" % STALE_MS
GATE_JS = """
function(inFlight, activeTab) { return Boolean(inFlight); }
"""
RECORD_JS = """
function(data) {
    if (data && typeof data.seq === 'number') { (window.__applied = window.__applied || []).push([data.seq, Date.now()]); }
    return window.dash_clientside.no_update;
}
"""


# --------------------------------------------------------------------------------------------- app
def build_app(arm, canopy_src, rtt_ms, seed, strand_ms):
    from dash import Dash, Input, Output, State, dcc, html

    rng = random.Random(seed)
    lock = threading.Lock()
    log = {"requests": [], "in_flight": 0, "strand_armed": False, "k": 0}

    app = Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Interval(id=LANE, interval=1000, n_intervals=0),
            dcc.Interval(id="slow-update-interval", interval=5000, n_intervals=0),
            dcc.Store(id=DATA, data=None),
            dcc.Store(id=MODE, data={"mode": "window", "window_size": 100}),
            dcc.Store(id=CLAMP, data=False),
            dcc.Store(id=REQ, data={"seq": 0}),
            dcc.Store(id=ACK, data=None),
            dcc.Store(id="sink", data=None),
            dcc.Tabs(id=TABS, value="metrics", children=[dcc.Tab(label="Training Metrics", value="metrics"), dcc.Tab(label="About", value="about")]),
        ]
    )

    def serve(reason, req_seq, req_stale=None):
        with lock:
            log["k"] += 1
            k = log["k"]
            strand = log["strand_armed"]
            log["strand_armed"] = False
            rtt = strand_ms if strand else min(5345, max(888, rng.gauss(rtt_ms, 450)))
            rec = {"k": k, "start": time.time() * 1000, "end": None, "reason": reason, "req_seq": req_seq, "strand": strand, "req_stale": req_stale}
            log["requests"].append(rec)
            log["in_flight"] += 1
        try:
            time.sleep(rtt / 1000.0)
        finally:
            with lock:
                rec["end"] = time.time() * 1000
                log["in_flight"] -= 1
        return k

    if arm == "pacer":
        sys.path.insert(0, canopy_src)
        from frontend.dashboard_manager import poll_pacer_js  # noqa: E402

        app.clientside_callback(poll_pacer_js(REQ, STALE_MS, extra_input=True), Output(REQ, "data"), [Input(LANE, "n_intervals"), Input(MODE, "data")], [State(REQ, "data"), State(ACK, "data")], prevent_initial_call=True)

        @app.callback(Output(DATA, "data"), Output(ACK, "data"), Input(REQ, "data"), State(MODE, "data"), prevent_initial_call=False)
        def feed(req, _mode):
            req = req if isinstance(req, dict) else {}
            k = serve(req.get("reason"), req.get("seq"), req.get("stale"))
            return {"seq": k}, {"seq": req.get("seq")}

    else:

        @app.callback(Output(DATA, "data"), Input(LANE, "n_intervals"), Input(MODE, "data"), running=[(Output(LANE, "disabled"), True, False)], prevent_initial_call=False)
        def feed(_n, _mode):
            return {"seq": serve("guard", None)}

        app.clientside_callback(WATCHDOG_JS, Output(LANE, "disabled", allow_duplicate=True), Input("slow-update-interval", "n_intervals"), [State(LANE, "disabled"), State(CLAMP, "data")], prevent_initial_call=True)

    app.clientside_callback(GATE_JS, Output(LANE, "disabled"), [Input(CLAMP, "data"), Input(TABS, "value")], prevent_initial_call=False)
    app.clientside_callback(RECORD_JS, Output("sink", "data"), Input(DATA, "data"))

    @app.server.route("/__log")
    def _log():
        with lock:
            return json.dumps(log)

    @app.server.route("/__strand")
    def _strand():
        with lock:
            log["strand_armed"] = True
        return "armed"

    return app


# --------------------------------------------------------------------------------------------- driver
def _get(url):
    with urllib.request.urlopen(url, timeout=10) as resp:  # nosec B310 - loopback scratch server
        return resp.read().decode()


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_in_flight(base, min_age_ms=300, timeout_s=15):
    end = time.time() + timeout_s
    while time.time() < end:
        log = json.loads(_get(base + "/__log"))
        open_ = [r for r in log["requests"] if r["end"] is None]
        if len(open_) == 1 and time.time() * 1000 - open_[0]["start"] >= min_age_ms:
            return open_[0]["k"]
        time.sleep(0.05)
    return None


def drive(args):
    from playwright.sync_api import sync_playwright

    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ, PACER_CHECK_PORT=str(port))
    cmd = [sys.executable, __file__, "--serve", "--arm", args.arm, "--rtt-ms", str(args.rtt_ms), "--seed", str(args.seed), "--strand-ms", str(args.strand_ms)]
    if args.canopy_src:
        cmd += ["--canopy-src", args.canopy_src]
    server = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)  # nosec B603 - this script, fixed args
    marks = []
    try:
        for _ in range(100):
            try:
                _get(base + "/__log")
                break
            except OSError:
                time.sleep(0.2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(base + "/")
            page.wait_for_function("() => window.dash_clientside !== undefined", timeout=30000)
            t0 = time.time() * 1000
            marks.append(("start", t0))
            time.sleep(args.idle_s)
            marks.append(("idle_end", time.time() * 1000))

            def set_store(cid, value):
                # a page-side setProps on the store, as a callback output would
                page.evaluate("([cid, value]) => { window.dash_clientside.set_props(cid, {data: value}); return true; }", [cid, value])

            triggers = []
            if args.trigger_reps:
                for rep in range(args.trigger_reps):
                    for kind in ("tab", "apply", "mode", "release"):
                        k = wait_in_flight(base)
                        t = time.time() * 1000
                        if kind == "tab":
                            page.evaluate("() => window.dash_clientside.set_props('%s', {value: 'about'})" % TABS)
                            time.sleep(0.3)
                            page.evaluate("() => window.dash_clientside.set_props('%s', {value: 'metrics'})" % TABS)
                        elif kind == "apply":
                            set_store(CLAMP, {"in_flight": True, "since": int(t)})
                            time.sleep(0.4)
                            set_store(CLAMP, False)
                        elif kind == "mode":
                            set_store(MODE, {"mode": "full" if rep % 2 == 0 else "window", "window_size": 100})
                        else:
                            set_store(CLAMP, False)
                        triggers.append({"kind": kind, "rep": rep, "t": t, "k_in_flight": k})
                        time.sleep(6)
            marks.append(("triggers_end", time.time() * 1000))
            strand = None
            if args.strand and args.arm == "pacer":
                wait_in_flight(base, min_age_ms=0)
                # arm: the NEXT request strands
                _get(base + "/__strand")
                strand = {"armed_at": time.time() * 1000}
                time.sleep(args.strand_ms / 1000.0 + 12)
            marks.append(("end", time.time() * 1000))
            applied = page.evaluate("() => window.__applied || []")
            fires = page.evaluate("() => window.__fires || []")
            browser.close()
        log = json.loads(_get(base + "/__log"))
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
    return {"arm": args.arm, "args": vars(args), "marks": marks, "triggers": triggers, "strand": strand, "applied": applied, "fires": fires, "requests": log["requests"]}


# --------------------------------------------------------------------------------------------- scoring
def _is_stale(r):
    """A stale re-issue: the request's own flag (canopy#731 commit 2 onwards), else its reason (commit 1)."""
    if r.get("req_stale") is not None:
        return r["req_stale"] is True
    return r.get("reason") == "stale"


def score(run):
    marks = dict(run["marks"])
    recorded_k = {k for k, _t in run["applied"]}
    applied_at = {k: t for k, t in run["applied"]}
    reqs = run["requests"]
    # Pacer arm: application is ALSO read off the acks. The pacer writes seq n+1 with reason "tick" or
    # "extra" only after reading ack n, and the feeder writes the ack and the data in one response, so such
    # a request proves response n applied. Needed because the page's recording callback (Input: the data
    # store) can be coalesced away: when the pacer issues the next request within a few ms of a response,
    # the new feeder request claims the data store, the recorder waits behind it, and its two pending runs
    # collapse into one (observed once, at a 10 ms gap, the shortest of the run). Reported separately.
    # Since canopy#731's commit 3 a LOST "extra" request is re-issued as "extra" while unacknowledged, so the
    # request's own ``stale`` flag (logged as ``req_stale``) is the proof; runs before it, which logged no flag,
    # fall back to the reason (commit 1 never re-issued an "extra" as stale).
    def _proves_ack(r):
        if r.get("req_stale") is not None:
            return r["req_stale"] is False
        return r.get("reason") in ("tick", "extra")

    acked_seq = {r["req_seq"] - 1 for r in reqs if _proves_ack(r) and isinstance(r.get("req_seq"), int)}
    acked_k = {r["k"] for r in reqs if isinstance(r.get("req_seq"), int) and r["req_seq"] in acked_seq}
    applied_k = recorded_k | acked_k
    max_applied = max(applied_k) if applied_k else 0
    done = [r for r in reqs if r["end"] is not None]
    # The stranded request is evicted by the stale re-issue BY DESIGN; it is reported under "strand".
    evicted = [r for r in done if r["k"] not in applied_k and r["k"] < max_applied and not r["strand"]]

    def in_window(r, a, b):
        return a <= r["start"] < b

    phases = {"idle": (marks["start"], marks["idle_end"]), "triggers": (marks["idle_end"], marks["triggers_end"]), "strand": (marks["triggers_end"], marks["end"])}
    out = {
        "arm": run["arm"],
        "requests": len(reqs),
        "completed": len(done),
        "applied": len(applied_k),
        "applied_recorded_in_page": len(recorded_k),
        "applied_by_ack_only": sorted(acked_k - recorded_k),
        "evicted_total": len(evicted),
        "fires": len(run["fires"]),
        "phases": {},
    }
    for name, (a, b) in phases.items():
        pr = [r for r in reqs if in_window(r, a, b)]
        pe = [r for r in evicted if in_window(r, a, b)]
        stale = [r for r in pr if _is_stale(r)]
        inflight_overlap = 0
        ordered = sorted(reqs, key=lambda r: r["start"])
        for i, r in enumerate(ordered):
            if in_window(r, a, b) and i and any(o["end"] is None or o["end"] > r["start"] for o in ordered[:i] if not o["strand"]):
                inflight_overlap += 1
        fires = [f for f in run["fires"] if a <= f < b]
        cycles = sorted(applied_at[r["k"]] for r in pr if r["k"] in applied_at)
        gaps = [y - x for x, y in zip(cycles, cycles[1:])]
        out["phases"][name] = {
            "requests": len(pr),
            "evicted": len(pe),
            "stale": len(stale),
            "requested_while_another_in_flight": inflight_overlap,
            "fires": len(fires),
            "median_applied_gap_ms": sorted(gaps)[len(gaps) // 2] if gaps else None,
            "reasons": {str(k): sum(1 for r in pr if r.get("reason") == k) for k in sorted({str(r.get("reason")) for r in pr})},
        }
    trig = []
    for t in run["triggers"]:
        nxt = [r for r in done if r["start"] > t["t"]]
        nxt = min(nxt, key=lambda r: r["start"]) if nxt else None
        cur_applied = t["k_in_flight"] in applied_k if t["k_in_flight"] else None
        trig.append({**t, "in_flight_applied": cur_applied, "next_applied": (nxt["k"] in applied_k) if nxt else None})
    out["triggers"] = trig
    if run.get("strand"):
        stranded = [r for r in reqs if r["strand"]]
        st = stranded[0] if stranded else None
        reissue = min((r for r in reqs if _is_stale(r) and st and r["start"] > st["start"]), key=lambda r: r["start"], default=None)
        recovered = min((applied_at[r["k"]] for r in reqs if reissue and r["k"] in applied_at and r["start"] >= reissue["start"]), default=None)
        out["strand"] = {
            "stranded_k": st["k"] if st else None,
            "stranded_applied": (st["k"] in applied_k) if st else None,
            "reissue_after_ms": (reissue["start"] - st["start"]) if (st and reissue) else None,
            "applied_after_reissue_ms": (recovered - reissue["start"]) if (reissue and recovered) else None,
        }
    idle = out["phases"]["idle"]
    idle_done = [r for r in done if in_window(r, *phases["idle"])]
    idle_unapplied = [r for r in idle_done if r["k"] not in applied_k]
    verdict = {
        "a_no_eviction": out["evicted_total"] == 0,
        "b_idle_clean": idle["stale"] == 0 and idle["fires"] == 0 and idle["evicted"] == 0 and len(idle_unapplied) <= 1,
        "c_triggers_next_applied": all(t["next_applied"] for t in trig) if trig else None,
    }
    if "strand" in out:
        s = out["strand"]
        verdict["d_strand_recovers"] = bool(s["reissue_after_ms"] and 30000 <= s["reissue_after_ms"] <= 32000 and s["applied_after_reissue_ms"] is not None and s["applied_after_reissue_ms"] <= 10000)
    out["verdict"] = verdict
    out["PASS"] = all(v for v in verdict.values() if v is not None)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=("pacer", "guard"), required=True)
    ap.add_argument("--canopy-src", default=None)
    ap.add_argument("--rtt-ms", type=float, default=3600.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--idle-s", type=float, default=600.0)
    ap.add_argument("--trigger-reps", type=int, default=3)
    ap.add_argument("--strand", action="store_true")
    ap.add_argument("--strand-ms", type=float, default=45000.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--score", default=None, help="re-score a saved run JSON")
    args = ap.parse_args()
    if args.serve:
        app = build_app(args.arm, args.canopy_src, args.rtt_ms, args.seed, args.strand_ms)
        app.run(host="127.0.0.1", port=int(os.environ["PACER_CHECK_PORT"]), debug=False, threaded=True)
        return 0
    if args.score:
        print(json.dumps(score(json.loads(Path(args.score).read_text())), indent=1))
        return 0
    if args.arm == "pacer" and not args.canopy_src:
        ap.error("--arm pacer needs --canopy-src")
    run = drive(args)
    result = score(run)
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%S")
        (out / f"{stamp}_{args.arm}_run.json").write_text(json.dumps(run, indent=1))
        (out / f"{stamp}_{args.arm}_score.json").write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return 0 if result["PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
