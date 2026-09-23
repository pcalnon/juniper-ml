#!/usr/bin/env python
"""F-CANOPY-054 round 2: under renderer slot contention, does a pause click survive? canopy#670 v1 vs v2.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy fix/f054-replay-block-clientside (canopy#670); ledger Phase 8 (F-CANOPY-054)

CREDIT. Adapted from Lane B2's clean room in the round-1 independent review of canopy#670
(2026-09-23), which measured the defect this re-checks with the PR as opened: 28 dropped pauses in all,
26 of 56 trials across the K >= 13 arms, and 0 of 15 with its click-counting variant at K = 16. (This line
first said "19 of 36"; that was a miscount, corrected from B2's own table.) The serving (Playwright route interception through the Dash
app's Flask test client, so NO PORT IS BOUND), the load model (K guarded 250 ms pollers with a
3-callback fan-out) and the queue instrument are B2's. What changed: both builds run here, paired,
and their JavaScript is read from git objects rather than from a working tree. v1 is the PR as opened
(``c0530279``), and v2 is the staged index by default, so a concurrent mutation check cannot leak
into it.

THE MECHANISM UNDER TEST (dash-renderer 4.2.0, dash_renderer.dev.js). Clientside callbacks share the
12 execution slots (:2846). A request waiting in ``prioritized`` is replaced by the next request of
the same callback (``pDuplicates``, :3024, removed at :3151), and only requests still in
``requested`` merge their changed-prop ids (:3004-3007). v1 dispatches on ``ctx.triggered``, so a
pause click replaced by a tick is lost. v2 derives events from values: it keeps each button's count
as of its last applied click (``state.clicks``) and applies anything above it at the next run.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN. Per trial, after play has applied and 2-4 s of playback:
  HELD      a ``paused`` state is applied within 8 s of the pause click.
  DROPPED   no ``paused`` within 8 s, the index advanced after the click (the callback ran and applied
            ticks without the pause), and the replay did not reach ``stopped``.
  STARVED   no ``paused`` within 8 s and the index did not advance (the callback did not run at all).
  VOID      play never applied within 20 s, or the replay reached its end.
  A HELD trial is RECOVERED when the click was seen in ``prioritized`` and no run of the controls
  callback naming ``replay-play`` among its changed props was ever seen executing: the pause arrived
  through the count, not the trigger. That is the only v2 path the round-1 defect exercises.
  INSTRUMENT CHECK: in the K=0 arms, at least 80% of HELD trials must show the click executing. If not,
  the sampler cannot see execution and RECOVERED is not trusted (the overall verdict is then VOID).
Overall:
  V2-HOLDS  v1 DROPPED >= 1 across the K >= 13 arms (the contention reproduced the defect) AND v2
            DROPPED == 0 in every arm AND v2 RECOVERED >= 1 (the recovery path actually ran).
  V2-FAILS  v2 DROPPED >= 1 in any arm.
  VACUOUS   v1 DROPPED == 0, or v2 RECOVERED == 0: the run did not exercise what it claims to test.

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (L = 2.5 s, n = 6 a arm, K in 0/12/13/16, 1x and 4x):
  v1: HELD everywhere at K = 0; DROPPED in some K >= 13 arms, more at 4x than at 1x (B2 measured
      3/10 and 5/10 at K=13, 5/8 and 6/8 at K=16).
  v2: DROPPED 0 in every arm; RECOVERED in most K >= 13 trials where v1's equivalent would drop;
      pause latency higher than v1's HELD latency at the same K (one tick late: about one tick
      period plus a slot wait).
  Overall: V2-HOLDS.

RUN LOG (2026-09-23, ``…_f054_pdup_cleanroom_v1_v2.json``, v1 ``c0530279`` against v2 ``85415f3c``, 639 s;
host load ~6-10, and for part of the run the status-bar census drove a second browser):
  OVERALL V2-HOLDS. The instrument check passed: 24 of 24 K=0 pauses were seen executing.
  * v1: HELD 37, DROPPED 5, VOID 2. Every DROPPED trial has the same trace: the click seen in
    ``prioritized``, never executed, and replaced there by a request of ``replay-interval.n_intervals``.
    Both VOIDs are "could not settle": v1 could not be paused within 40 s of clicking (K=13 and K=16, both
    at 4x), so those arms ended early. ``v1_k16_4x`` therefore has n = 2.
  * v2: HELD 48 of 48, DROPPED 0. 16 were RECOVERED: the same replacement trace, and the pause applied
    from the count, within 54-1023 ms (median 322.5 ms).
  SCORED AGAINST THE PREDICTIONS:
  * v1 all HELD at K=0: held.
  * v1 DROPPED in some K >= 13 arms: held (1/6 at 13-4x, 3/6 at 16-1x, 1 plus the abort at 16-4x; 0/6
    at 13-1x). "More at 4x than at 1x" cannot be scored, because the 4x arm at K=16 aborted.
  * v2 DROPPED 0 in every arm: held.
  * v2 RECOVERED in most K >= 13 trials: held narrowly, 13 of 24.
  * v2 pause latency above v1's HELD latency at the same K: MIXED. It was higher in 3 of 5 comparable
    arms. "About one tick period plus a slot wait" is an upper bound, not the latency: the replacing request
    can arrive at any point in the period.

Usage (JuniperCanopy1 carries dash 4.2.0 and playwright):
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py --canopy <fix worktree> \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_pdup_cleanroom_v1_v2.json
"""

import argparse
import ast
import asyncio
import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

MP_PATH = "src/frontend/components/metrics_panel.py"
P = "metrics-panel-"
ROWS = 5000  # large enough that no trial reaches the end
BASE = "http://cleanroom.test"
PAUSE_WINDOW_S = 8.0
PLAY_WINDOW_S = 20.0
UNDO_WATCH_S = 3.0


def load_js(canopy: str, spec: str) -> dict:
    """Read the replay JavaScript from a git OBJECT (``<ref>:path``, or ``:path`` for the index)."""
    src = subprocess.run(["git", "-C", canopy, "show", spec], capture_output=True, text=True, check=True).stdout
    tree = ast.parse(src)
    out = {"spec": spec, "sha256": hashlib.sha256(src.encode("utf-8")).hexdigest()}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS"):
                out[node.targets[0].id] = ast.literal_eval(node.value)
        if isinstance(node, ast.ClassDef) and node.name == "MetricsPanel":
            for b in node.body:
                if isinstance(b, ast.AnnAssign) and getattr(b.target, "id", None) == "REPLAY_CONTROL_IDS":
                    out["REPLAY_CONTROL_IDS"] = ast.literal_eval(b.value)
    missing = {"REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS", "REPLAY_CONTROL_IDS"} - set(out)
    assert not missing, f"{spec}: missing {missing}"
    return out


def build_app(k: int, version: str, js: dict):
    import dash
    from dash import Input, Output, State, dcc, html, no_update

    app = dash.Dash(__name__)
    controls_js = js["REPLAY_CONTROLS_JS"].replace("__PREFIX__", json.dumps(P)).replace("__CONTROLS__", json.dumps(list(js["REPLAY_CONTROL_IDS"])))
    buttons = [c for c in js["REPLAY_CONTROL_IDS"] if c != "replay-slider"]

    kids = [
        dcc.Store(id=P + "replay-state", data={"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None}),
        dcc.Store(id=P + "metrics-store", data=[{"epoch": i} for i in range(ROWS)]),
        dcc.Interval(id=P + "replay-interval", interval=1000, disabled=True, n_intervals=0),
    ]
    kids += [html.Button(c, id=P + c, n_clicks=0) for c in buttons]
    if version == "v1":
        kids.append(html.Span(id=P + "replay-position", children="0 / 0"))
        position_outputs = [Output(P + "replay-position", "children")]
    else:
        # v2 splits the position so a refill writes the max alone; the wrapper keeps one text to read.
        kids.append(html.Span(id=P + "replay-position", children=[html.Span("0", id=P + "replay-position-index"), " / ", html.Span("0", id=P + "replay-position-max")]))
        position_outputs = [Output(P + "replay-position-index", "children"), Output(P + "replay-position-max", "children")]
    kids.append(dcc.Slider(id=P + "replay-slider", min=0, max=100, value=0, marks=None, updatemode="drag"))
    for i in range(k):
        kids += [dcc.Interval(id=f"load{i}-int", interval=250, n_intervals=0), dcc.Store(id=f"load{i}-store")]
        kids += [html.Div(id=f"load{i}-r{j}") for j in range(3)]
    app.layout = html.Div(kids)

    app.clientside_callback(
        controls_js,
        [
            Output(P + "replay-state", "data"),
            Output(P + "replay-interval", "disabled"),
            Output(P + "replay-interval", "interval"),
            Output(P + "replay-slider", "value"),
            Output(P + "replay-slider", "max"),
            *position_outputs,
            Output(P + "replay-play", "children"),
        ],
        [Input(P + c, "n_clicks") for c in buttons] + [Input(P + "replay-slider", "value"), Input(P + "replay-interval", "n_intervals")],
        [State(P + "replay-state", "data"), State(P + "metrics-store", "data")],
        prevent_initial_call=False,
    )
    if version == "v1":
        app.clientside_callback(js["REPLAY_REFILL_POSITION_JS"], Output(P + "replay-position", "children", allow_duplicate=True), Input(P + "metrics-store", "data"), State(P + "replay-state", "data"), prevent_initial_call=True)
    else:
        app.clientside_callback(js["REPLAY_REFILL_POSITION_JS"], Output(P + "replay-position-max", "children", allow_duplicate=True), Input(P + "metrics-store", "data"), prevent_initial_call=True)

    # K guarded pollers, canopy's idle shape: running= on a DEDICATED interval, no_update at idle, and a
    # downstream fan-out of 3. (This comment first said the fan-out makes each score '13' against the controls'
    # '11', from B2's priority census. Lane A2, round 2, refuted that: in dash 4.2.0 getPriority returns "0" for
    # every callback, because its first pass is a ramda FILTER that drops its own start callback (:1598), so
    # ``prioritized`` is FIFO. The fan-out models canopy's poll shape, not a priority; the drop counts stand.)
    for i in range(k):

        def _mk(i=i):
            @app.callback(Output(f"load{i}-store", "data"), Input(f"load{i}-int", "n_intervals"), running=[(Output(f"load{i}-int", "disabled"), True, False)], prevent_initial_call=True)
            def poll(n):  # noqa: ARG001
                return no_update

            for j in range(3):

                @app.callback(Output(f"load{i}-r{j}", "children"), Input(f"load{i}-store", "data"), prevent_initial_call=True)
                def render(d, j=j):  # noqa: ARG001
                    return str(d)

        _mk()
    return app


INSTRUMENT = """
() => {
  function fiberOf(el) { for (const k in el) { if (k.startsWith('__reactFiber$') || k.startsWith('__reactContainer$') || k.startsWith('__reactInternalInstance$')) return el[k]; } return null; }
  let st = (window.store && typeof window.store.getState === 'function') ? window.store : null;
  if (!st) {
    for (const sel of ['#react-entry-point', '#_dash-app-content', 'body']) {
      const el = document.querySelector(sel); if (!el) continue;
      let f = fiberOf(el), hops = 0;
      while (f && hops < 8000 && !st) { const mp = f.memoizedProps; if (mp && mp.store && typeof mp.store.getState === 'function') st = mp.store; f = f.child || f.sibling || (f.return ? f.return.sibling : null); hops++; }
      if (st) break;
    }
  }
  if (!st) return {found: false};
  window.__st = st;
  const SID = 'metrics-panel-replay-state';
  const CTL = 'metrics-panel-replay-state.data';
  const isCtl = cb => { const o = cb && cb.callback && cb.callback.output; return typeof o === 'string' && o.indexOf(CTL) >= 0; };
  function getData(s) {
    const p = s.paths && s.paths.strs && s.paths.strs[SID];
    if (!p) return undefined;
    let n = s.layout; for (const k of p) { n = n ? n[k] : undefined; }
    return n && n.props ? n.props.data : undefined;
  }
  window.__rec = {state: [], q: [], poolFullNotifies: 0, notifies: 0};
  let lastS = null, lastQ = null;
  const sample = () => {
    const s = st.getState();
    const d = getData(s);
    const ks = d ? (d.mode + '|' + d.current_index + '|' + d.speed) : 'none';
    const now = Date.now();
    if (ks !== lastS) { lastS = ks; window.__rec.state.push([now, d ? d.mode : null, d ? d.current_index : null, d ? d.speed : null]); }
    const cbs = s.callbacks || {};
    const pool = (cbs.executing || []).length + (cbs.watched || []).length;
    window.__rec.notifies++; if (pool >= 12) window.__rec.poolFullNotifies++;
    const snap = {};
    for (const q of ['requested', 'prioritized', 'blocked', 'executing', 'watched']) {
      const arr = (cbs[q] || []).filter(isCtl).map(cb => Object.keys(cb.changedPropIds || {}).map(x => x.replace('metrics-panel-', '')).join('+'));
      if (arr.length) snap[q] = arr;
    }
    const kq = JSON.stringify(snap) + '|' + pool + '|' + (cbs.prioritized || []).length;
    if (kq !== lastQ) { lastQ = kq; window.__rec.q.push([now, pool, (cbs.prioritized || []).length, snap]); }
  };
  sample();
  st.subscribe(sample);
  return {found: true};
}
"""


class Server:
    def __init__(self, app, latency):
        self.client = app.server.test_client()
        self.latency = latency
        self.posts = 0

    async def handle(self, route):
        req = route.request
        url = req.url[len(BASE) :] or "/"
        try:
            if req.method == "POST":
                self.posts += 1
                await asyncio.sleep(self.latency * random.uniform(0.8, 1.2))
                resp = self.client.post(url, data=req.post_data_buffer, headers={"Content-Type": req.headers.get("content-type", "application/json")})
            else:
                resp = self.client.get(url)
            headers = {k: v for k, v in resp.headers.items() if k.lower() not in ("content-length", "transfer-encoding")}
            await route.fulfill(status=resp.status_code, headers=headers, body=resp.data)
        except Exception as exc:  # the page must never hang on a harness error
            print(f"route error {url}: {exc!r}", flush=True)
            try:
                await route.abort()
            except Exception as abort_exc:  # the route was already handled or closed
                print(f"route abort failed {url}: {abort_exc!r}", flush=True)


async def last_state(page):
    return await page.evaluate("() => { const r = window.__rec.state; return r[r.length - 1]; }")


async def wait_mode(page, mode, since, timeout_s):
    t_end = time.time() + timeout_s
    while time.time() < t_end:
        hit = await page.evaluate(f"() => window.__rec.state.find(r => r[0] >= {since} && r[1] === '{mode}') || null")
        if hit:
            return hit
        await asyncio.sleep(0.05)
    return None


async def settle_not_playing(page, budget_s=40.0):
    """Unscored: bring the replay to a non-playing mode before the next trial (a starved play click can
    apply late and would otherwise invert the next trial). Returns (settled, repaused): ``repaused`` means
    the replay was PLAYING when a trial ended, which is how an undone pause would otherwise vanish."""
    t_end = time.time() + budget_s
    first = True
    while time.time() < t_end:
        cur = await last_state(page)
        if cur and cur[1] != "playing":
            return True, not first
        first = False
        t_r = await page.evaluate("Date.now()")
        await page.click(f"#{P}replay-play")
        if await wait_mode(page, "paused", t_r, 8):
            return True, True
        await asyncio.sleep(0.5)
    return False, True


async def run_arm(pw, arm, version, k, speed_ctl, trials, latency, js, seed):
    random.seed(seed)
    app = build_app(k, version, js)
    srv = Server(app, latency)
    browser = await pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    page = await (await browser.new_context()).new_page()
    await page.route(BASE + "/**", lambda route: asyncio.ensure_future(srv.handle(route)))
    await page.goto(BASE + "/", wait_until="load", timeout=60000)
    await page.wait_for_function(f"() => {{ const e = document.getElementById('{P}replay-position'); return e && e.textContent === '0 / {ROWS - 1}'; }}", timeout=60000)
    found = await page.evaluate(INSTRUMENT)
    assert found.get("found"), found
    await asyncio.sleep(6.0)  # let the pollers reach steady state
    results = []
    await page.click(f"#{P}{speed_ctl}")  # speed once, while stopped: no ticks, so nothing contends with it
    await asyncio.sleep(1.0)
    for t in range(trials):
        settled, repaused = await settle_not_playing(page)
        if repaused and results:
            results[-1]["repaused_before_next_trial"] = True  # the previous trial ended PLAYING
        if not settled:
            results.append({"trial": t, "verdict": "VOID", "why": "could not settle to a non-playing mode"})
            break
        t_play = await page.evaluate("Date.now()")
        await page.click(f"#{P}replay-play")
        if not await wait_mode(page, "playing", t_play, PLAY_WINDOW_S):
            results.append({"trial": t, "verdict": "VOID", "why": "play never applied"})
            print(f"  [{arm}] trial {t}: VOID (play never applied)", flush=True)
            continue
        await asyncio.sleep(random.uniform(2.0, 4.0))
        t_click = await page.evaluate("Date.now()")
        await page.click(f"#{P}replay-play")
        hit = await wait_mode(page, "paused", t_click, PAUSE_WINDOW_S)
        rec = {"trial": t, "t_click": t_click}
        win_ms = int(PAUSE_WINDOW_S * 1000)
        after = await page.evaluate(f"() => window.__rec.state.filter(r => r[0] >= {t_click} && r[0] <= {t_click} + {win_ms})")
        before = await page.evaluate(f"() => {{ const r = window.__rec.state.filter(x => x[0] < {t_click}); return r[r.length - 1]; }}")
        stopped = any(r[1] == "stopped" for r in after)
        if hit:
            upto = [r for r in after if r[0] <= hit[0]]
            rec.update(verdict="HELD", latency_ms=hit[0] - t_click, index_advance_before_pause=(max((r[2] for r in upto if r[2] is not None), default=before[2]) - before[2]) if before else None)
            # UNDONE (added after round 2, Lane B2): watch UNDO_WATCH_S more, with no click, for a `playing`
            # write after the pause -- one click applied twice undoes the pause. The first run scored HELD
            # on the first `paused` record and could not see this.
            await asyncio.sleep(UNDO_WATCH_S)
            undo = await page.evaluate(f"() => window.__rec.state.find(r => r[0] > {hit[0]} && r[1] === 'playing') || null")
            if undo:
                rec.update(verdict="UNDONE", undone_ms=undo[0] - t_click)
        elif stopped:
            rec.update(verdict="VOID", why="reached the end")
        else:
            advanced = bool(after) and before is not None and any(r[2] is not None and r[2] > before[2] for r in after)
            rec.update(verdict="DROPPED" if advanced else "STARVED", index_before=before[2] if before else None, index_at_window_end=after[-1][2] if after else None)
        q = await page.evaluate(f"() => window.__rec.q.filter(r => r[0] >= {t_click} && r[0] <= {t_click} + {win_ms})")
        in_prio = [r for r in q if any("replay-play" in x for x in r[3].get("prioritized", []))]
        ran = [r for r in q if any("replay-play" in x for x in r[3].get("executing", []) + r[3].get("watched", []))]
        rec["click_seen_in_prioritized"] = bool(in_prio)
        rec["click_executed"] = bool(ran)
        rec["recovered"] = rec["verdict"] == "HELD" and bool(in_prio) and not ran
        if in_prio:
            last_in = in_prio[-1][0]
            nxt = [r for r in q if r[0] > last_in]
            rec["replaced_by"] = nxt[0][3] if nxt else None
        rec["pool_at_click"] = q[0][1] if q else None
        results.append(rec)
        print(f"  [{arm}] trial {t}: {rec['verdict']} lat={rec.get('latency_ms')} in_prio={rec['click_seen_in_prioritized']} executed={rec['click_executed']} recovered={rec['recovered']} pool_at_click={rec['pool_at_click']} replaced_by={rec.get('replaced_by')}", flush=True)
        await asyncio.sleep(1.0)
    stats = await page.evaluate("() => ({notifies: window.__rec.notifies, poolFull: window.__rec.poolFullNotifies})")
    qlog = await page.evaluate("() => window.__rec.q")
    slog = await page.evaluate("() => window.__rec.state")
    await browser.close()
    held = [r for r in results if r["verdict"] == "HELD"]
    lat = [r["latency_ms"] for r in held]
    summ = {
        "arm": arm,
        "version": version,
        "K": k,
        "speed": speed_ctl,
        "latency_s": latency,
        "trials": trials,
        "verdicts": {v: sum(1 for r in results if r["verdict"] == v) for v in sorted({r["verdict"] for r in results})},
        "recovered": sum(1 for r in results if r.get("recovered")),
        "held_with_click_executed": sum(1 for r in held if r.get("click_executed")),
        "pause_latency_ms_median": statistics.median(lat) if lat else None,
        "pause_latency_ms_max": max(lat) if lat else None,
        "pool_full_fraction_of_notifies": round(stats["poolFull"] / max(1, stats["notifies"]), 3),
        "posts": srv.posts,
    }
    print(f"  [{arm}] SUMMARY {json.dumps(summ)}", flush=True)
    return {"summary": summ, "trials": results, "qlog": qlog, "state_log": slog}


def overall(arms: dict) -> dict:
    s = [a["summary"] for a in arms.values()]

    def n(version, verdict, kmin=0):
        return sum(x["verdicts"].get(verdict, 0) for x in s if x["version"] == version and x["K"] >= kmin)

    k0_held = sum(x["verdicts"].get("HELD", 0) for x in s if x["K"] == 0)
    k0_exec = sum(x["held_with_click_executed"] for x in s if x["K"] == 0)
    instrument_ok = k0_held > 0 and k0_exec >= 0.8 * k0_held
    v1_dropped_k13 = n("v1", "DROPPED", 13)
    v2_dropped = n("v2", "DROPPED")
    v2_recovered = sum(x["recovered"] for x in s if x["version"] == "v2")
    if not instrument_ok:
        verdict = "VOID (instrument cannot see execution at K=0)"
    elif v2_dropped >= 1:
        verdict = "V2-FAILS"
    elif v1_dropped_k13 == 0 or v2_recovered == 0:
        verdict = "VACUOUS"
    else:
        verdict = "V2-HOLDS"
    return {
        "instrument_ok": instrument_ok,
        "k0_held": k0_held,
        "k0_held_with_click_executed": k0_exec,
        "v1": {v: n("v1", v) for v in ("HELD", "DROPPED", "STARVED", "VOID")},
        "v2": {v: n("v2", v) for v in ("HELD", "DROPPED", "STARVED", "VOID")},
        "v1_dropped_at_K_ge_13": v1_dropped_k13,
        "v2_recovered": v2_recovered,
        "verdict": verdict,
    }


async def main_async(args):
    from playwright.async_api import async_playwright

    js = {"v1": load_js(args.canopy, f"{args.v1_ref}:{MP_PATH}"), "v2": load_js(args.canopy, (f"{args.v2_ref}:{MP_PATH}" if args.v2_ref != "INDEX" else f":{MP_PATH}"))}
    assert "state.clicks = seen;" not in js["v1"]["REPLAY_CONTROLS_JS"], "v1 source already counts clicks: wrong ref"
    assert "state.clicks = seen;" in js["v2"]["REPLAY_CONTROLS_JS"], "v2 source does not count clicks: wrong ref"
    plan = []
    pair = 0
    for k in [int(x) for x in args.ks.split(",")]:
        for speed in args.speeds.split(","):
            order = ("v1", "v2") if pair % 2 == 0 else ("v2", "v1")  # alternate, so neither build always runs first
            plan += [(f"{v}_k{k}_{speed.replace('speed-', '')}", v, k, speed) for v in order]
            pair += 1
    out = {"probe": Path(__file__).name, "credit": "adapted from Lane B2's round-1 clean room (canopy#670 review, 2026-09-23)", "sources": {v: {"spec": js[v]["spec"], "sha256": js[v]["sha256"]} for v in js}, "latency_s": args.latency, "trials": args.trials, "seed": args.seed, "arms": {}}
    t0 = time.time()
    async with async_playwright() as pw:
        for name, version, k, speed in plan:
            print(f"arm {name}: version={version} K={k} speed={speed} L={args.latency}s", flush=True)
            out["arms"][name] = await run_arm(pw, name, version, k, speed, args.trials, args.latency, js[version], seed=args.seed)
    out["elapsed_s"] = round(time.time() - t0, 1)
    out["overall"] = overall(out["arms"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("SUMMARY TABLE")
    for r in out["arms"].values():
        print(json.dumps(r["summary"]))
    print(f"OVERALL {json.dumps(out['overall'])}")
    print(f"-> {args.out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canopy", required=True, help="canopy checkout whose git objects hold both builds")
    ap.add_argument("--v1-ref", default="c0530279", help="canopy#670 as opened")
    ap.add_argument("--v2-ref", required=True, help="the build to test against v1: a commit, or INDEX for the staged metrics_panel.py (fragile: the index can move under a run)")
    ap.add_argument("--ks", default="0,12,13,16")
    ap.add_argument("--speeds", default="speed-1x,speed-4x")
    ap.add_argument("--trials", type=int, default=6)
    ap.add_argument("--latency", type=float, default=2.5)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    asyncio.run(main_async(ap.parse_args()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
