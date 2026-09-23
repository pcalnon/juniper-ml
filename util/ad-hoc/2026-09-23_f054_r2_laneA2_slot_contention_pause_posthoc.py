#!/usr/bin/env python
"""
F-CANOPY-054 round 2, Lane A2 -- POST-HOC exploratory arms for the slot-contention pause measurement (canopy#670).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (executed by Claude Code, consensus Lane A2)
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: canopy#670 (F-CANOPY-054); main script 2026-09-23_f054_r2_laneA2_slot_contention_pause.py (its docstring,
         sha256 118e13f4ee28f72426fdc8fce1671c93522d0c8cf28e790444c12dde697e863b, holds the pre-registered arms A1-A8)

POST-HOC. Written at 14:20Z, while the main run was in progress and after its smoke trials and first rep were seen.
These arms are exploratory: they were not pre-registered with A1-A8 and must not be pooled with them. The main
script is reused unchanged (imported from its path); this file only adds a second contention structure and a second
click pattern.

QUESTIONS
 X1 Under contention the pause shows nothing for seconds; the likeliest human reaction is to click it again. v2
    applies ONE toggle per run however many clicks are pending (a design choice stated in its source). Two pause
    clicks, 1.5 s apart, both inside the 12-slot contention window of the main arms (12 one-shot 6 s calls).
 X2 The main arms hold the slots with one-shot calls that are never re-requested, so no slot frees until they
    return (the worst case). Slots held by PERIODIC polls free whenever a poll is re-requested (the requestedCallbacks
    observer's wDuplicates step evicts the in-flight one; the FIFO head of `prioritized` gets the slot). 12 polls,
    each on its own 1000 ms dcc.Interval, 3 s latency, enabled together at t_hog; pause click at t_hog + U(1.0,
    2.0) s (seeded per trial). A v1 click survives iff a poll re-request frees a slot before the next replay tick
    replaces the click's request.

VERDICT RULE: the main script's, unchanged, except tp = the FIRST pause click; the delivery check is "play n_clicks
rose by the number of pause clicks"; X2's contention validity check is executing+watched >= 11 at tp (a poll may be
between eviction and re-execution at that instant).

PREDICTIONS (written before the first X trial)
 X1a v1, 12 one-shot hogs, 2 pause clicks : LOST 5/5.
 X1b v2, 12 one-shot hogs, 2 pause clicks : HELD 5/5 (one toggle for two pending clicks).
 X2a v1, 12 periodic polls                : NOT reliably held -- held in 0-3 of 5; the click is kept only in the
                                            trials where a poll re-request precedes the next replay tick.
 X2b v2, 12 periodic polls                : HELD 5/5.

Usage
  LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python <this> run --port 18574 [--reps 5]
"""

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
MAIN_PATH = HERE.with_name("2026-09-23_f054_r2_laneA2_slot_contention_pause.py")
_spec = importlib.util.spec_from_file_location("laneA2_main", MAIN_PATH)
M = importlib.util.module_from_spec(_spec)
sys.modules["laneA2_main"] = M
_spec.loader.exec_module(M)

N_POLLS = 12
POLL_PERIOD_MS = 1000
POLL_LATENCY_S = 3.0
DOUBLE_GAP_S = 1.5
DEFAULT_OUT = M.WORKTREE / "reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_r2_laneA2_slot_contention_pause_posthoc.json"

# name, variant, pattern
XARMS = [("X1a", "v1", "double"), ("X1b", "v2", "double"), ("X2a", "v1", "polls"), ("X2b", "v2", "polls")]

POLL_JS = """([N]) => {
  const t = Date.now();
  const dc = window.dash_clientside;
  for (let i = 0; i < N; i++) { dc.set_props('poll-iv-' + i, {disabled: false}); }
  window.__A2.hog = {t: t, polls: N};
  return t;
}"""


def _make_poll(i):
    def poll(n):
        with M.INFLIGHT_LOCK:
            M.INFLIGHT += 1
        try:
            time.sleep(POLL_LATENCY_S)
        finally:
            with M.INFLIGHT_LOCK:
                M.INFLIGHT -= 1
        return f"poll {i} n={n}"

    poll.__name__ = f"poll_{i}"
    return poll


def serve(port):
    import flask
    from dash import Input, Output, dcc, html
    from werkzeug.serving import make_server

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    builds = {t: M.load_build(t) for t in M.BUILD_SHAS}
    server = flask.Flask("laneA2_posthoc")
    for v in ("v1", "v2"):
        app = M.build_app(server, v, builds)
        app.layout.children.append(html.Div([dcc.Interval(id=f"poll-iv-{i}", interval=POLL_PERIOD_MS, disabled=True, n_intervals=0) for i in range(N_POLLS)]))
        app.layout.children.append(html.Div([html.Div(id=f"poll-out-{i}") for i in range(N_POLLS)]))
        for i in range(N_POLLS):
            app.callback(Output(f"poll-out-{i}", "children"), Input(f"poll-iv-{i}", "n_intervals"), prevent_initial_call=True)(_make_poll(i))

    @server.route("/__inflight")
    def _inflight():
        return str(M.INFLIGHT)

    srv = make_server("127.0.0.1", port, server, threaded=True)
    print(f"serving on 127.0.0.1:{port}", flush=True)
    srv.serve_forever()


def evaluate(arm, rep, d, py, lead):
    name, variant, pattern = arm
    n_pause = 2 if pattern == "double" else 1
    K_min = 12 if pattern == "double" else 11
    W = M.WATCH_S * 1000
    r = {"arm": name, "variant": variant, "pattern": pattern, "rep": rep, "lead_s": round(lead, 3), "py": py}
    why = []
    plays = [c for c in d["clicks"] if c["id"] == f"{M.CID}-replay-play"]
    if len(plays) != 1 + n_pause or not d.get("hog"):
        r.update(verdict="INVALID", invalid=[f"play clicks={len(plays)} hog={bool(d.get('hog'))}"])
        return r
    t_play, tp, t_hog = plays[0]["t"], plays[1]["t"], d["hog"]["t"]
    t_end = tp + W
    rs = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "rs" and isinstance(e["v"], dict)]
    pcs = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "pc"]
    nis = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "ni"]

    def last_before(series, t):
        xs = [v for tt, v in series if tt <= t]
        return xs[-1] if xs else None

    at_tp = last_before(rs, tp)
    playing_seen = [t for t, v in rs if t_play <= t <= tp and v["mode"] == "playing"]
    i_play = next((v["i"] for t, v in rs if playing_seen and t >= playing_seen[0]), None)
    i_hog = (last_before(rs, t_hog) or {}).get("i")
    pc_before, pc_after = last_before(pcs, tp - 1), last_before(pcs, t_end)
    ew = plays[1]["ew"]
    if not at_tp or at_tp["mode"] != "playing":
        why.append(f"mode at tp = {at_tp and at_tp['mode']}")
    if i_play is None or i_hog is None or not i_hog > i_play:
        why.append(f"index did not advance before t_hog ({i_play} -> {i_hog})")
    if not (isinstance(pc_before, int) and isinstance(pc_after, int) and pc_after == pc_before + n_pause):
        why.append(f"play n_clicks {pc_before} -> {pc_after}, expected +{n_pause}")
    if ew is None or ew < K_min:
        why.append(f"executing+watched at tp = {ew} < {K_min}")
    win = [(t, v) for t, v in rs if tp < t <= t_end]
    if any(v["mode"] == "stopped" for t, v in win):
        why.append("mode 'stopped' in window")
    paused = [t for t, v in win if v["mode"] == "paused"]
    ta = paused[0] if paused else None
    if ta is None:
        verdict = "LOST"
    elif any(v["mode"] == "playing" for t, v in win if t > ta):
        verdict = "UNDONE"
    else:
        verdict = "HELD" if len({v["i"] for t, v in rs if ta <= t <= t_end}) == 1 else "UNDONE"
    ctl = [x for x in d["inv"] if x.get("fn") == "ctl"]
    runs_after = [x for x in ctl if x["t"] >= tp]
    first = runs_after[0] if runs_after else None
    trig_play = f"{M.CID}-replay-play.n_clicks"
    next_tick = next((t for t, v in nis if t > tp), None)
    poll_fetch_after = [f["t0"] for f in d["fetch"] if f.get("out", "").startswith("poll-out") and f["t0"] > tp]
    r.update(
        verdict="INVALID" if why else verdict,
        raw_verdict=verdict,
        invalid=why,
        tp=tp,
        latency_s=round((ta - tp) / 1000, 3) if ta else None,
        ew_at_tp=ew,
        mode_at_tp=at_tp and at_tp["mode"],
        final_state=win[-1][1] if win else at_tp,
        first_run_after_click_s=round((first["t"] - tp) / 1000, 3) if first else None,
        first_run_trig=first["trig"] if first else None,
        first_run_pc=first.get("pc") if first else None,
        trigger_lost=(trig_play not in first["trig"]) if first else None,
        next_tick_after_click_s=round((next_tick - tp) / 1000, 3) if next_tick else None,
        next_poll_fetch_after_click_s=round((poll_fetch_after[0] - tp) / 1000, 3) if poll_fetch_after else None,
        errs=d["errs"],
    )
    return r


def run_trial(browser, port, arm, rep):
    name, variant, pattern = arm
    rng = random.Random(f"{name}-{rep}")
    py = {"start": time.time()}
    ctx = browser.new_context(viewport={"width": 1200, "height": 700})
    ctx.add_init_script(M.INSTR_JS)
    page = ctx.new_page()
    play = f"#{M.CID}-replay-play"
    try:
        page.goto(f"http://127.0.0.1:{port}/{variant}/", wait_until="load")
        page.wait_for_function("() => window.__A2 && window.__A2.ready", timeout=15000)
        page.wait_for_function(f"() => {{ const e = document.getElementById('{M.CID}-replay-position'); return e && e.textContent.indexOf('/ {M.N_METRICS - 1}') >= 0; }}", timeout=15000)
        time.sleep(0.5)
        page.click(play)
        page.wait_for_function("() => window.__A2.cur.rs && window.__A2.cur.rs.mode === 'playing'", timeout=8000)
        time.sleep(M.PLAY_SETTLE_S)
        if pattern == "double":
            page.evaluate(M.HOG_JS, [12, M.HOG_SLEEP_S, False])
            lead = M.HOG_LEAD_S
        else:
            page.evaluate(POLL_JS, [N_POLLS])
            lead = rng.uniform(1.0, 2.0)
        time.sleep(lead)
        page.click(play)
        if pattern == "double":
            time.sleep(DOUBLE_GAP_S)
            page.click(play)
            time.sleep(M.WATCH_S - DOUBLE_GAP_S)
        else:
            time.sleep(M.WATCH_S)
        data = page.evaluate(M.COLLECT_JS)
    finally:
        ctx.close()
    py["drain_s"] = M.wait_inflight_zero(port)
    py["end"] = time.time()
    rec = evaluate(arm, rep, data, py, lead)
    rec["logs"] = data
    return rec


def summarize(trials):
    out = {}
    for name, variant, pattern in XARMS:
        ts = [t for t in trials if t["arm"] == name]
        if ts:
            out[name] = {
                "variant": variant,
                "pattern": pattern,
                "n": len(ts),
                "valid": sum(t["verdict"] != "INVALID" for t in ts),
                **{k: sum(t["verdict"] == k for t in ts) for k in ("HELD", "LOST", "UNDONE", "INVALID")},
                "latency_s": sorted(t["latency_s"] for t in ts if t.get("latency_s") is not None),
                "trigger_lost": [t.get("trigger_lost") for t in ts],
                "next_tick_vs_next_poll_s": [(t.get("next_tick_after_click_s"), t.get("next_poll_fetch_after_click_s")) for t in ts],
            }
    return out


def cmd_run(args):
    import dash
    from importlib.metadata import version

    port = args.port
    if port in M.FORBIDDEN_PORTS or port < 18500 or not M.port_free(port):
        sys.exit(f"port {port} refused or busy")
    out = Path(args.out) if args.out else DEFAULT_OUT
    arms = [a for a in XARMS if not args.arms or a[0] in args.arms.split(",")]
    meta = {
        "script": str(HERE),
        "docstring_sha256": hashlib.sha256(__doc__.encode()).hexdigest(),
        "main_script": str(MAIN_PATH),
        "main_docstring_sha256": hashlib.sha256(M.__doc__.encode()).hexdigest(),
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "port": port,
        "dash": dash.__version__,
        "playwright": version("playwright"),
        "renderer_sha256": hashlib.sha256(Path(M.RENDERER).read_bytes()).hexdigest(),
        "params": {"N_POLLS": N_POLLS, "POLL_PERIOD_MS": POLL_PERIOD_MS, "POLL_LATENCY_S": POLL_LATENCY_S, "DOUBLE_GAP_S": DOUBLE_GAP_S, "HOG_SLEEP_S": M.HOG_SLEEP_S, "WATCH_S": M.WATCH_S, "reps": args.reps},
        "arms": arms,
    }
    print(json.dumps({k: meta[k] for k in ("docstring_sha256", "main_docstring_sha256", "started_utc", "port")}), flush=True)
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    srv_log = open(out.with_suffix(".server.log"), "w")
    srv = subprocess.Popen([sys.executable, str(HERE), "serve", "--port", str(port)], stdout=srv_log, stderr=subprocess.STDOUT, env=env)
    trials = []
    try:
        t0 = time.time()
        while True:
            try:
                if all(M.http_get(f"http://127.0.0.1:{port}/{v}/")[0] == 200 for v in ("v1", "v2")):
                    break
            except Exception:
                pass
            if time.time() - t0 > 60 or srv.poll() is not None:
                raise SystemExit("server did not come up")
            time.sleep(0.3)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            meta["chromium"] = browser.version
            for rep in range(args.reps):
                for arm in arms:
                    try:
                        rec = run_trial(browser, port, arm, rep)
                    except Exception as e:
                        rec = {"arm": arm[0], "variant": arm[1], "pattern": arm[2], "rep": rep, "verdict": "INVALID", "invalid": [f"exception: {e!r}"]}
                        M.wait_inflight_zero(port)
                    trials.append(rec)
                    print(json.dumps({k: rec.get(k) for k in ("arm", "rep", "verdict", "latency_s", "lead_s", "ew_at_tp", "trigger_lost", "first_run_after_click_s", "next_tick_after_click_s", "next_poll_fetch_after_click_s", "first_run_trig", "final_state", "invalid")}), flush=True)
                    meta["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    out.write_text(json.dumps({"meta": meta, "summary": summarize(trials), "trials": trials}, indent=1))
            browser.close()
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except subprocess.TimeoutExpired:
            srv.kill()
        srv_log.close()
    for k, v in summarize(trials).items():
        print(k, json.dumps({x: v[x] for x in ("variant", "pattern", "n", "valid", "HELD", "LOST", "UNDONE", "INVALID", "latency_s")}))
    print("results:", out)


def main():
    ap = argparse.ArgumentParser(description="Lane A2 post-hoc arms")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, required=True)
    r = sub.add_parser("run")
    r.add_argument("--port", type=int, default=18574)
    r.add_argument("--reps", type=int, default=5)
    r.add_argument("--arms", default="")
    r.add_argument("--out", default="")
    a = ap.parse_args()
    if a.cmd == "serve":
        if a.port in M.FORBIDDEN_PORTS or a.port < 18500:
            sys.exit(f"refusing port {a.port}")
        serve(a.port)
    else:
        cmd_run(a)


if __name__ == "__main__":
    main()
