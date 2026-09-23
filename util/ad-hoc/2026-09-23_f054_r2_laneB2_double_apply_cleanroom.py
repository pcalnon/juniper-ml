#!/usr/bin/env python
"""F-CANOPY-054 round 2, Lane B2: does canopy#670 v2 apply ONE pause click TWICE (pause, then undone)?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation (independent-agent consensus, round 2, Lane B2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 v2 = local commit 85415f3c (REPLAY_CONTROLS_JS);
         util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py (the orchestrator's adaptation of B2's
         round-1 clean room); util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py (logic level)

THE SEQUENCE UNDER TEST (dash-renderer 4.2.0, dash_renderer.dev.js in JuniperCanopy1):
  1. A tick request T of the controls callback waits in ``prioritized`` (pool full, :2846).
  2. The user clicks pause. setProps writes n_clicks into the layout at once, and the click's
     request C enters ``requested``. The requested observer's pass is deferred by ``await wait(0)``
     (:2961-2962; wait = setTimeout, :4030-4031).
  3. If a completion lands first, the prioritized observer (inputs ``callbacks.prioritized`` and
     ``callbacks.completed``, :2902) picks T and executes it against the CURRENT layout (:2853,
     fillVals :1183), which already holds the new n_clicks. v2 applies the pause by count.
  4. The requested pass then finds C with no duplicate left in prioritized/executing/watched
     (:3024-3027) and runs it: triggered = [play], pending 0, times = max(0, 1) = 1 -> a SECOND
     toggle. The pause is undone and the interval re-enabled.

SERVING: Playwright route interception through the Dash app's Flask test client. NO PORT IS BOUND.
The page's function is wrapped in place so every run's triggers and counts are logged.

VERDICT RULE (fixed before the first run), per pause trial:
  HELD      a ``paused`` state applied within 8 s, and no ``playing`` state after it in the window.
  UNDONE    a ``paused`` state applied, then a ``playing`` state after it with no new user click.
  DROPPED   no ``paused`` within 8 s and the index advanced.   STARVED   no ``paused``, no advance.
Per arm: DOUBLE = runs whose trigger names the play button while its count is already consumed
(pending 0) -- the double application itself, read from the wrapper, independent of the verdict.

PREDICTIONS (fixed before the first run): K=0 -> UNDONE 0, DOUBLE 0 (no slot waits). Under K >= 13
a small but non-zero DOUBLE and UNDONE count; more with the main-thread load arm (``sat``), which
widens the click -> wait(0) window the way canopy's 0.1%-idle main thread does.

Arm spec: name:K:speed[:sat_ms_per_50ms[:fan[:delay0_ms]]]. delay0 > 0 is a REACHABILITY lever, not a rate model. fan is each poller's downstream fan-out (default 3,
scoring '13' > the controls' '11'); fan 0 makes the pollers terminal ('0'), so the controls callback is
the FIRST pick at every completion -- the regime in which step 3 above needs only one completion.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_r2_laneB2_double_apply_cleanroom.py --arms k0:0:4x,k13:13:4x --trials 10 --out <json>
"""

import argparse
import ast
import asyncio
import json
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

CANOPY = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--f054-replay-block-clientside--20260923-0036--2f973ca2"
MP_PATH = "src/frontend/components/metrics_panel.py"
P = "metrics-panel-"
ROWS = 5000
BASE = "http://cleanroom.test"
WINDOW_S = 8.0


def load_js(ref):
    src = subprocess.run(["git", "-C", CANOPY, "show", f"{ref}:{MP_PATH}"], capture_output=True, text=True, check=True).stdout
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in ("REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS"):
            out[node.targets[0].id] = ast.literal_eval(node.value)
        if isinstance(node, ast.ClassDef) and node.name == "MetricsPanel":
            for b in node.body:
                if isinstance(b, ast.AnnAssign) and getattr(b.target, "id", None) == "REPLAY_CONTROL_IDS":
                    out["REPLAY_CONTROL_IDS"] = ast.literal_eval(b.value)
    assert "state.clicks = seen;" in out["REPLAY_CONTROLS_JS"], f"{ref} is not v2"
    return out


def build_app(k, js, fan=3):
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
    kids += [html.Button(c, id=P + c) for c in buttons]  # n_clicks left unset, as canopy's dbc.Buttons are
    kids.append(html.Span(id=P + "replay-position", children=[html.Span("0", id=P + "replay-position-index"), " / ", html.Span("0", id=P + "replay-position-max")]))
    kids.append(dcc.Slider(id=P + "replay-slider", min=0, max=100, value=0, marks=None, updatemode="drag"))
    for i in range(k):
        kids += [dcc.Interval(id=f"load{i}-int", interval=250, n_intervals=0), dcc.Store(id=f"load{i}-store")]
        kids += [html.Div(id=f"load{i}-r{j}") for j in range(fan)]
    app.layout = html.Div(kids)
    app.clientside_callback(
        controls_js,
        [
            Output(P + "replay-state", "data"),
            Output(P + "replay-interval", "disabled"),
            Output(P + "replay-interval", "interval"),
            Output(P + "replay-slider", "value"),
            Output(P + "replay-slider", "max"),
            Output(P + "replay-position-index", "children"),
            Output(P + "replay-position-max", "children"),
            Output(P + "replay-play", "children"),
        ],
        [Input(P + c, "n_clicks") for c in buttons] + [Input(P + "replay-slider", "value"), Input(P + "replay-interval", "n_intervals")],
        [State(P + "replay-state", "data"), State(P + "metrics-store", "data")],
        prevent_initial_call=False,
    )
    app.clientside_callback(js["REPLAY_REFILL_POSITION_JS"], Output(P + "replay-position-max", "children", allow_duplicate=True), Input(P + "metrics-store", "data"), prevent_initial_call=True)
    for i in range(k):

        def _mk(i=i):
            @app.callback(Output(f"load{i}-store", "data"), Input(f"load{i}-int", "n_intervals"), running=[(Output(f"load{i}-int", "disabled"), True, False)], prevent_initial_call=True)
            def poll(n):  # noqa: ARG001
                return no_update

            for j in range(fan):

                @app.callback(Output(f"load{i}-r{j}", "children"), Input(f"load{i}-store", "data"), prevent_initial_call=True)
                def render(d, j=j):  # noqa: ARG001
                    return str(d)

        _mk()
    return app


INSTRUMENT = """
([sat, delay0]) => {
  // RECHABILITY LEVER (off unless delay0 > 0): zero-delay timers run delay0 ms late. dash-renderer defers
  // every requested pass with ``await wait(0)`` = setTimeout(resolve, 0) (:2961-2962, :4030-4031), so this
  // models the requested pass running late behind other work, as on canopy's 0.1%-idle main thread.
  // dcc.Interval uses setInterval and React schedules through MessageChannel, so neither is touched.
  if (delay0 > 0 && !window.__delay0) {
    const origST = window.setTimeout;
    window.setTimeout = function (fn, ms, ...rest) { return origST(fn, (ms === undefined || ms === 0) ? delay0 : ms, ...rest); };
    window.__delay0 = delay0;
  }
  function fiberOf(el) { for (const k in el) { if (k.startsWith('__reactFiber$') || k.startsWith('__reactContainer$') || k.startsWith('__reactInternalInstance$')) return el[k]; } return null; }
  let st = null;
  for (const sel of ['#react-entry-point', '#_dash-app-content', 'body']) {
    const el = document.querySelector(sel); if (!el) continue;
    let f = fiberOf(el), hops = 0;
    while (f && hops < 8000 && !st) { const mp = f.memoizedProps; if (mp && mp.store && typeof mp.store.getState === 'function') st = mp.store; f = f.child || f.sibling || (f.return ? f.return.sibling : null); hops++; }
    if (st) break;
  }
  if (!st) return {found: false};
  const SID = 'metrics-panel-replay-state';
  function getData(s) { const p = s.paths && s.paths.strs && s.paths.strs[SID]; if (!p) return undefined; let n = s.layout; for (const k of p) { n = n ? n[k] : undefined; } return n && n.props ? n.props.data : undefined; }
  window.__rec = {state: [], runs: [], poolFull: 0, notifies: 0};
  let lastS = null;
  st.subscribe(() => {
    const s = st.getState(); const d = getData(s);
    const ks = d ? (d.mode + '|' + d.current_index) : 'none';
    if (ks !== lastS) { lastS = ks; window.__rec.state.push([Date.now(), d ? d.mode : null, d ? d.current_index : null]); }
    const cbs = s.callbacks || {}; window.__rec.notifies++;
    if ((cbs.executing || []).length + (cbs.watched || []).length >= 12) window.__rec.poolFull++;
  });
  // wrap the registered controls function IN PLACE: the renderer looks it up by name at every call
  const ns = window.dash_clientside._dashprivate_clientside_funcs;
  const key = Object.keys(ns).find(k => String(ns[k]).indexOf('state.clicks = seen;') >= 0);
  if (!key) return {found: false, why: 'controls function not found'};
  const orig = ns[key];
  ns[key] = function () {
    const a = Array.from(arguments);
    const ctx = window.dash_clientside.callback_context || {};
    const trig = (ctx.triggered || []).map(t => String(t.prop_id).replace('metrics-panel-', ''));
    const inS = a[10] || {};
    const res = orig.apply(this, a);
    const o = res && res[0] && typeof res[0] === 'object' && res[0].mode ? res[0] : null;
    window.__rec.runs.push({t: Date.now(), trig: trig, play: a[0], seenPlay: (inS.clicks || {})['replay-play'], modeIn: inS.mode, modeOut: o ? o.mode : 'NU'});
    return res;
  };
  // optional main-thread load, modelling canopy's measured 0.1%-idle main thread: busy `sat` ms of every 50 ms
  if (sat > 0) { setInterval(() => { const t0 = performance.now(); while (performance.now() - t0 < sat) {} }, 50); }
  return {found: true, key: key};
}
"""


class Server:
    def __init__(self, app, latency):
        self.client = app.server.test_client()
        self.latency = latency

    async def handle(self, route):
        req = route.request
        url = req.url[len(BASE):] or "/"
        try:
            if req.method == "POST":
                await asyncio.sleep(self.latency * random.uniform(0.8, 1.2))
                resp = self.client.post(url, data=req.post_data_buffer, headers={"Content-Type": req.headers.get("content-type", "application/json")})
            else:
                resp = self.client.get(url)
            headers = {k: v for k, v in resp.headers.items() if k.lower() not in ("content-length", "transfer-encoding")}
            await route.fulfill(status=resp.status_code, headers=headers, body=resp.data)
        except Exception as exc:
            print(f"route error {url}: {exc!r}", flush=True)
            try:
                await route.abort()
            except Exception:
                # the route was already handled or closed; the error is printed above
                pass


async def wait_mode(page, mode, since, timeout_s):
    t_end = time.time() + timeout_s
    while time.time() < t_end:
        hit = await page.evaluate(f"() => window.__rec.state.find(r => r[0] >= {since} && r[1] === '{mode}') || null")
        if hit:
            return hit
        await asyncio.sleep(0.05)
    return None


async def settle_paused(page, budget_s=60.0):
    t_end = time.time() + budget_s
    while time.time() < t_end:
        cur = await page.evaluate("() => { const r = window.__rec.state; return r[r.length - 1]; }")
        if cur and cur[1] != "playing":
            await asyncio.sleep(1.5)  # a late second application would show here; re-check
            cur2 = await page.evaluate("() => { const r = window.__rec.state; return r[r.length - 1]; }")
            if cur2 and cur2[1] != "playing":
                return True
        t_r = await page.evaluate("Date.now()")
        await page.click(f"#{P}replay-play")
        await wait_mode(page, "paused", t_r, 8)
    return False


async def run_arm(pw, name, k, speed, sat, trials, latency, js, seed, fan=3, delay0=0):
    random.seed(seed)
    app = build_app(k, js, fan)
    srv = Server(app, latency)
    browser = await pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    page = await (await browser.new_context()).new_page()
    await page.route(BASE + "/**", lambda route: asyncio.ensure_future(srv.handle(route)))
    await page.goto(BASE + "/", wait_until="load", timeout=60000)
    await page.wait_for_function(f"() => {{ const e = document.getElementById('{P}replay-position'); return e && e.textContent === '0 / {ROWS - 1}'; }}", timeout=60000)
    found = await page.evaluate(INSTRUMENT, [sat, delay0])
    assert found.get("found"), found
    await asyncio.sleep(6.0)
    await page.click(f"#{P}speed-{speed}")
    await asyncio.sleep(1.5)
    results = []
    for t in range(trials):
        if not await settle_paused(page):
            results.append({"trial": t, "verdict": "VOID", "why": "could not settle"})
            break
        t_play = await page.evaluate("Date.now()")
        await page.click(f"#{P}replay-play")
        if not await wait_mode(page, "playing", t_play, 20):
            results.append({"trial": t, "verdict": "VOID", "why": "play never applied"})
            continue
        await asyncio.sleep(random.uniform(2.0, 4.0))
        t_click = await page.evaluate("Date.now()")
        await page.click(f"#{P}replay-play")
        await asyncio.sleep(WINDOW_S)
        win = await page.evaluate(f"() => window.__rec.state.filter(r => r[0] >= {t_click} && r[0] <= {t_click} + {int(WINDOW_S * 1000)})")
        before = await page.evaluate(f"() => {{ const r = window.__rec.state.filter(x => x[0] < {t_click}); return r[r.length - 1]; }}")
        runs = await page.evaluate(f"() => window.__rec.runs.filter(r => r.t >= {t_click} && r.t <= {t_click} + {int(WINDOW_S * 1000)})")
        paused_at = next((r for r in win if r[1] == "paused"), None)
        replayed = [r for r in win if paused_at and r[0] > paused_at[0] and r[1] == "playing"]
        if paused_at and replayed:
            verdict = "UNDONE"
        elif paused_at:
            verdict = "HELD"
        else:
            adv = before is not None and any(r[2] is not None and r[2] > before[2] for r in win)
            verdict = "DROPPED" if adv else "STARVED"
        doubles = [r for r in runs if "replay-play.n_clicks" in r["trig"] and r["play"] is not None and r["play"] == r["seenPlay"]]
        by_count = [r for r in runs if "replay-play.n_clicks" not in r["trig"] and (r["play"] or 0) > (r["seenPlay"] or 0) and r["modeOut"] != "NU"]
        rec = {"trial": t, "verdict": verdict, "pause_ms": (paused_at[0] - t_click) if paused_at else None, "undone_ms": (replayed[0][0] - t_click) if replayed else None, "double_runs": doubles, "pause_by_count_runs": by_count, "runs": runs}
        results.append(rec)
        print(f"  [{name}] trial {t}: {verdict} pause_ms={rec['pause_ms']} undone_ms={rec['undone_ms']} by_count={len(by_count)} double={len(doubles)} runs={[ (r['trig'], r['play'], r['seenPlay'], r['modeIn'], r['modeOut']) for r in runs[:4]]}", flush=True)
    stats = await page.evaluate("() => ({n: window.__rec.notifies, full: window.__rec.poolFull})")
    await browser.close()
    held = [r for r in results if r["verdict"] == "HELD"]
    summ = {
        "arm": name, "K": k, "speed": speed, "sat_ms_per_50": sat, "fan": fan, "delay0_ms": delay0, "trials": trials, "latency_s": latency,
        "verdicts": {v: sum(1 for r in results if r["verdict"] == v) for v in sorted({r["verdict"] for r in results})},
        "trials_with_double_application": sum(1 for r in results if r.get("double_runs")),
        "trials_with_pause_applied_by_count": sum(1 for r in results if r.get("pause_by_count_runs")),
        "pause_ms_median": statistics.median([r["pause_ms"] for r in held]) if held else None,
        "pool_full_fraction": round(stats["full"] / max(1, stats["n"]), 3),
    }
    print(f"  [{name}] SUMMARY {json.dumps(summ)}", flush=True)
    return {"summary": summ, "trials": results}


async def main_async(a):
    from playwright.async_api import async_playwright

    js = load_js(a.ref)
    out = {"probe": Path(__file__).name, "source": f"{a.ref}:{MP_PATH}", "latency_s": a.latency, "trials": a.trials, "arms": {}}
    async with async_playwright() as pw:  # ONE browser at a time: arms run sequentially
        for spec in a.arms.split(","):
            name, k, speed, *rest = spec.split(":")
            sat = int(rest[0]) if rest else 0
            fan = int(rest[1]) if len(rest) > 1 else 3  # 0 = terminal pollers, which the controls ('11') OUTRANK
            delay0 = int(rest[2]) if len(rest) > 2 else 0  # the reachability lever; 0 = off
            print(f"arm {name}: K={k} speed={speed} sat={sat}ms/50ms fan={fan} delay0={delay0}ms L={a.latency}s", flush=True)
            out["arms"][name] = await run_arm(pw, name, int(k), speed, sat, a.trials, a.latency, js, a.seed, fan, delay0)
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    for r in out["arms"].values():
        print(json.dumps(r["summary"]))
    print(f"-> {a.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="85415f3c")
    ap.add_argument("--arms", default="k0:0:4x,k13:13:4x,k16:16:4x")
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--latency", type=float, default=2.5)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--out", required=True)
    asyncio.run(main_async(ap.parse_args()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
