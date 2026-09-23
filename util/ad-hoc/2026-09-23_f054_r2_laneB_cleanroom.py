#!/usr/bin/env python
"""canopy#670 round 2 (Lane B): does v2 fix the round-1 findings, and what did its corrections break?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 (F-CANOPY-054); util/ad-hoc/2026-09-23_f054_r2_laneB_gitobj.py

SERVING. Playwright route interception through the Dash app's Flask test client (NO PORT is bound),
the serving model of Lane B2's round-1 clean room. One browser at a time.

BUILDS. The replay JavaScript is read from git OBJECTS: v1 = c0530279 (the PR as opened), v2 =
85415f3c (the local freeze). Each build is wired exactly as its metrics_panel.py registers it (v2:
position split into -index / -max spans; the refill writes the max alone, no State).

SLOT CONTROL. Twelve CLIENTSIDE callbacks, fired by one button, each return a Promise the harness
resolves on demand (``window.__holders``). They sit in ``watched`` and fill the renderer's 12 slots
(dash_renderer.dev.js:2846) with no network timing at all, so a slot can be freed in the SAME task
as a click. That is the only way to make the double-application race below deterministic.

ARMS, VERDICTS AND PREDICTIONS -- FIXED BEFORE THE FIRST RUN.
  lost_pause    play; saturate; a tick request queued in ``prioritized``; click pause (own task);
                2.5 s (>= 2 ticks replace the queued request); release all.
                PAUSE-LOST: no 'paused' after the click. PAUSE-HELD: 'paused' applied and still
                'paused' at the end. PAUSE-UNDONE: 'paused' then 'playing'.
                Predicted: v1 PAUSE-LOST (round-1 finding); v2 PAUSE-HELD, latency >= 2.5 s (the
                release), index at the pause == index at the click.
  double_pause  play; saturate; a tick request queued; in ONE task: click pause, free ONE slot. The
                queued tick request runs first and applies the pause by COUNT; the click's own
                request runs after and carries the play trigger.
                Predicted: v1 PAUSE-HELD; v2 PAUSE-UNDONE (``times = max(pending, triggered ? 1 : 0)``
                and the one-toggle branch ignores ``times``).
  double_step   stopped; saturate; a speed-1x click queued; in ONE task: click step-forward, free ONE
                slot. Predicted: v1 index +1; v2 index +2 for one click.
  nan_box       step x5; clear the slider's number box. Predicted: v1 index NaN (round-1 finding);
                v2 index 5 kept, slider written back finite.
  same_pass     step x5; in ONE task: click step-forward, set_props the metrics store (240 rows).
                Predicted: v1 text '5 / 239' with state 6 (round-1 finding); v2 '6 / 239'.
  shrink        4x play from 0 until index >= 60 (120 rows), then set_props the store to 50 rows (a
                display-mode switch). Ticks continue past the new max, so the slider is written
                values above 100. FALSE-SEEK if the mode leaves 'playing' without a click, or the
                index jumps back. Predicted: no FALSE-SEEK in either build (the slider does not
                echo a programmatic value).

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_r2_laneB_cleanroom.py --objects <canopy .git/objects> \\
        --arms lost_pause,double_pause,double_step,nan_box,same_pass,shrink --builds v1,v2 --runs 3 --out <json>
"""

import argparse
import ast
import asyncio
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gitobj", HERE / "2026-09-23_f054_r2_laneB_gitobj.py")
gitobj = importlib.util.module_from_spec(_spec)
sys.modules["gitobj"] = gitobj
_spec.loader.exec_module(gitobj)

MP_PATH = "src/frontend/components/metrics_panel.py"
# "v3" was added by the orchestrator after round 2, to run this lane's arms on the committed correction
# (the local canopy commit a967a5bd: this review's idempotent-count fix, Lane B2's slider skip, and a no-op
# run that writes nothing). Every other line of this script is Lane B's.
REFS = {"v1": "c0530279", "v2": "85415f3c", "v3": "a967a5bd"}
P = "metrics-panel-"
BASE = "http://cleanroom.test"
N_HOLD = 12


def load_js(store, ref):
    sha, body = store.blob_at(store.resolve(ref), MP_PATH)
    src = body.decode("utf-8")
    tree = ast.parse(src)
    out = {"ref": ref, "blob": sha, "sha256": hashlib.sha256(body).hexdigest()}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS"):
            out[node.targets[0].id] = ast.literal_eval(node.value)
        if isinstance(node, ast.ClassDef) and node.name == "MetricsPanel":
            for b in node.body:
                if isinstance(b, ast.AnnAssign) and getattr(b.target, "id", None) == "REPLAY_CONTROL_IDS":
                    out["REPLAY_CONTROL_IDS"] = ast.literal_eval(b.value)
    assert {"REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS", "REPLAY_CONTROL_IDS"} <= set(out)
    return out


def build_app(version, js, rows):
    import dash
    from dash import Input, Output, State, dcc, html

    app = dash.Dash(__name__)
    buttons = [c for c in js["REPLAY_CONTROL_IDS"] if c != "replay-slider"]
    kids = [html.Button("hold", id="hold-btn", n_clicks=0), html.Div([html.Div(id=f"hold-out-{i}") for i in range(N_HOLD)])]
    kids += [html.Button(c, id=P + c) for c in buttons]  # no n_clicks: canopy's dbc.Buttons start unset
    if version == "v1":
        kids.append(html.Span(id=P + "replay-position", children="0 / 0"))
        pos_out = [Output(P + "replay-position", "children")]
    else:
        kids.append(html.Span(id=P + "replay-position", children=[html.Span("0", id=P + "replay-position-index"), " / ", html.Span("0", id=P + "replay-position-max")]))
        pos_out = [Output(P + "replay-position-index", "children"), Output(P + "replay-position-max", "children")]
    kids += [
        dcc.Slider(id=P + "replay-slider", min=0, max=100, value=0, marks=None, updatemode="drag"),
        dcc.Store(id=P + "metrics-store", data=[{"epoch": i} for i in range(rows)]),
        dcc.Store(id=P + "replay-state", data={"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None}),
        dcc.Interval(id=P + "replay-interval", interval=1000, disabled=True, n_intervals=0),
    ]
    app.layout = html.Div(kids)
    controls_js = js["REPLAY_CONTROLS_JS"].replace("__PREFIX__", json.dumps(P)).replace("__CONTROLS__", json.dumps(list(js["REPLAY_CONTROL_IDS"])))
    app.clientside_callback(
        controls_js,
        [Output(P + "replay-state", "data"), Output(P + "replay-interval", "disabled"), Output(P + "replay-interval", "interval"), Output(P + "replay-slider", "value"), Output(P + "replay-slider", "max"), *pos_out, Output(P + "replay-play", "children")],
        [Input(P + c, "n_clicks") for c in buttons] + [Input(P + "replay-slider", "value"), Input(P + "replay-interval", "n_intervals")],
        [State(P + "replay-state", "data"), State(P + "metrics-store", "data")],
        prevent_initial_call=False,
    )
    if version == "v1":
        app.clientside_callback(js["REPLAY_REFILL_POSITION_JS"], Output(P + "replay-position", "children", allow_duplicate=True), Input(P + "metrics-store", "data"), State(P + "replay-state", "data"), prevent_initial_call=True)
    else:
        app.clientside_callback(js["REPLAY_REFILL_POSITION_JS"], Output(P + "replay-position-max", "children", allow_duplicate=True), Input(P + "metrics-store", "data"), prevent_initial_call=True)
    for i in range(N_HOLD):
        # distinct source per holder, so each is its own clientside function
        app.clientside_callback(
            "function(n) { /* holder %d */ return new Promise(function (res) { (window.__holders = window.__holders || []).push(function () { res('released ' + n); }); }); }" % i,
            Output(f"hold-out-{i}", "children"),
            Input("hold-btn", "n_clicks"),
            prevent_initial_call=True,
        )
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
  const CTL = 'metrics-panel-replay-state.data';
  const isCtl = cb => { const o = cb && cb.callback && cb.callback.output; return typeof o === 'string' && o.indexOf(CTL) >= 0 && o.indexOf('@') < 0; };
  window.__prop = (id, prop) => { const s = st.getState(); const p = s.paths && s.paths.strs && s.paths.strs[id]; if (!p) return undefined; let n = s.layout; for (const k of p) { n = n ? n[k] : undefined; } return n && n.props ? n.props[prop] : undefined; };
  window.__rec = {state: [], q: [], runs: []};
  let lastS = null, lastQ = null, lastExec = new Set();
  const sample = () => {
    const s = st.getState();
    const d = window.__prop('metrics-panel-replay-state', 'data');
    const sv = window.__prop('metrics-panel-replay-slider', 'value');
    const ks = d ? JSON.stringify([d.mode, d.current_index, d.clicks ? d.clicks['replay-play'] : null, d.clicks ? d.clicks['replay-step-forward'] : null]) : 'none';
    const now = performance.now();
    if (ks !== lastS) { lastS = ks; window.__rec.state.push([now, d ? d.mode : null, d ? d.current_index : null, d && d.clicks ? d.clicks['replay-play'] : null, d && d.clicks ? d.clicks['replay-step-forward'] : null, sv]); }
    const cbs = s.callbacks || {};
    const pool = (cbs.executing || []).length + (cbs.watched || []).length;
    const snap = {};
    for (const q of ['requested', 'prioritized', 'blocked', 'executing', 'watched']) {
      const arr = (cbs[q] || []).filter(isCtl).map(cb => Object.keys(cb.changedPropIds || {}).map(x => x.replace('metrics-panel-', '')).join('+') + ((cb.predecessors && cb.predecessors.length) ? ' <pred>' : ''));
      if (arr.length) snap[q] = arr;
    }
    // every controls run, with its trigger list. A clientside run leaves ``executing`` inside a
    // nested dispatch before this subscriber sees it, so the run is caught in ``watched`` (where it
    // stays until its promise resolves) as well as in ``executing``.
    const running = (cbs.executing || []).concat(cbs.watched || []).filter(isCtl);
    for (const cb of running) { const key = cb.executionPromise || cb; if (!lastExec.has(key)) { window.__rec.runs.push([now, Object.keys(cb.changedPropIds || {}).map(x => x.replace('metrics-panel-', '')).join('+')]); } }
    lastExec = new Set(running.map(cb => cb.executionPromise || cb));
    const prios = Array.from(new Set((cbs.prioritized || []).map(cb => String(cb.priority))));
    const kq = JSON.stringify(snap) + '|' + pool + '|' + prios.join(',');
    if (kq !== lastQ) { lastQ = kq; window.__rec.q.push([now, pool, snap, prios]); }
  };
  sample();
  st.subscribe(sample);
  return {found: true};
}
"""


class Server:
    def __init__(self, app):
        self.client = app.server.test_client()

    async def handle(self, route):
        req = route.request
        url = req.url[len(BASE):] or "/"
        try:
            if req.method == "POST":
                resp = self.client.post(url, data=req.post_data_buffer, headers={"Content-Type": req.headers.get("content-type", "application/json")})
            else:
                resp = self.client.get(url)
            headers = {k: v for k, v in resp.headers.items() if k.lower() not in ("content-length", "transfer-encoding")}
            await route.fulfill(status=resp.status_code, headers=headers, body=resp.data)
        except Exception as exc:  # noqa: BLE001
            print(f"route error {url}: {exc!r}", flush=True)
            try:
                await route.abort()
            except Exception:  # noqa: BLE001
                pass


async def now(page):
    return await page.evaluate("performance.now()")


async def wait_for(page, js_pred, timeout_s, poll=0.02):
    t_end = time.time() + timeout_s
    while time.time() < t_end:
        if await page.evaluate(js_pred):
            return True
        await asyncio.sleep(poll)
    return False


def pos_text(version):
    return f"() => document.getElementById('{P}replay-position').textContent"


async def click(page, cid):
    await page.evaluate(f"() => document.getElementById('{P}{cid}').click()")


async def saturate(page):
    await page.evaluate("() => document.getElementById('hold-btn').click()")
    ok = await wait_for(page, "() => { const c = window.__st.getState().callbacks; return (c.executing.length + c.watched.length) >= 12; }", 5)
    assert ok, "could not fill the 12 slots"


async def release_all(page):
    await page.evaluate("() => { while (window.__holders && window.__holders.length) { window.__holders.shift()(); } }")


QUEUED_CTL = "() => (window.__st.getState().callbacks.prioritized || []).some(cb => { const o = cb.callback && cb.callback.output; return typeof o === 'string' && o.indexOf('metrics-panel-replay-state.data') >= 0 && o.indexOf('@') < 0; })"


def other_browsers() -> int:
    """Headless browsers running on this host (the review allows ONE browser at a time)."""
    n = 0
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            try:
                if b"chrome-headless-shell" in (p / "cmdline").read_bytes():
                    n += 1
            except OSError:
                pass
    return n


async def wait_browser_slot(limit_s=3600):
    t0 = time.time()
    while other_browsers() and time.time() - t0 < limit_s:
        await asyncio.sleep(3)
    if other_browsers():
        raise RuntimeError("another browser still running after the wait limit")
    waited = time.time() - t0
    if waited > 1:
        print(f"  (waited {waited:.0f}s for another lane's browser)", flush=True)


async def run_arm(pw, arm, version, js, rows):
    app = build_app(version, js, rows)
    srv = Server(app)
    await wait_browser_slot()
    browser = await pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
    try:
        return await _run_arm(browser, srv, arm, version, rows)
    finally:
        # ALWAYS close: a leaked browser would be counted by wait_browser_slot() and deadlock the
        # retry on this harness's own process (it did, once).
        try:
            await browser.close()
        except Exception:  # noqa: BLE001
            pass


async def _run_arm(browser, srv, arm, version, rows):
    page = await (await browser.new_context()).new_page()
    page.on("crash", lambda: print(f"  [{arm} {version}] PAGE CRASH", flush=True))
    page.on("console", lambda m: print(f"  [{arm} {version}] console.{m.type}: {m.text[:200]}", flush=True) if m.type in ("error",) else None)
    page.on("pageerror", lambda e: print(f"  [{arm} {version}] pageerror: {str(e)[:200]}", flush=True))
    await page.route(BASE + "/**", lambda route: asyncio.ensure_future(srv.handle(route)))
    await page.goto(BASE + "/", wait_until="load", timeout=60000)
    await page.wait_for_function(f"() => {{ const e = document.getElementById('{P}replay-position'); return e && e.textContent === '0 / {rows - 1}'; }}", timeout=60000)
    assert (await page.evaluate(INSTRUMENT)).get("found")
    await asyncio.sleep(1.0)
    res = {"arm": arm, "version": version}
    playing = "() => { const d = window.__prop('metrics-panel-replay-state', 'data'); return d && d.mode === 'playing'; }"

    if arm in ("lost_pause", "double_pause"):
        await click(page, "replay-play")
        assert await wait_for(page, playing, 5), "play never applied"
        await asyncio.sleep(1.5)
        await saturate(page)
        res["tick_queued"] = await wait_for(page, QUEUED_CTL, 4)
        idx_click = await page.evaluate("() => window.__prop('metrics-panel-replay-state', 'data').current_index")
        if arm == "lost_pause":
            t_click = await now(page)
            await click(page, "replay-play")
            await asyncio.sleep(2.5)
            t_rel = await now(page)
            await release_all(page)
        else:
            t_click = await page.evaluate(f"() => {{ const t = performance.now(); document.getElementById('{P}replay-play').click(); window.__holders.shift()(); return t; }}")
            await asyncio.sleep(2.0)
            t_rel = await now(page)
            await release_all(page)
        await asyncio.sleep(3.0)
        rec = await page.evaluate("() => window.__rec")
        after = [r for r in rec["state"] if r[0] >= t_click]
        paused = next((r for r in after if r[1] == "paused"), None)
        replayed = [r for r in after if paused and r[0] > paused[0] and r[1] == "playing"]
        final = rec["state"][-1]
        verdict = "PAUSE-LOST" if paused is None else ("PAUSE-UNDONE" if replayed else ("PAUSE-HELD" if final[1] == "paused" else "OTHER"))
        res.update(verdict=verdict, idx_at_click=idx_click, pause_latency_ms=round(paused[0] - t_click) if paused else None, idx_at_pause=paused[2] if paused else None, release_ms_after_click=round(t_rel - t_click), final=final[1:3], undone_ms_after_pause=round(replayed[0][0] - paused[0]) if replayed else None)
        res["runs_after_click"] = [[round(t - t_click), trig] for t, trig in rec["runs"] if t >= t_click][:6]
        res["q_after_click"] = [[round(t - t_click), pool, snap] for t, pool, snap, _ in rec["q"] if 0 <= t - t_click <= 3500 and snap][:14]

    elif arm == "double_step":
        await saturate(page)
        await click(page, "speed-1x")
        res["speed_queued"] = await wait_for(page, QUEUED_CTL, 4)
        idx0 = await page.evaluate("() => window.__prop('metrics-panel-replay-state', 'data').current_index")
        t_click = await page.evaluate(f"() => {{ const t = performance.now(); document.getElementById('{P}replay-step-forward').click(); window.__holders.shift()(); return t; }}")
        await asyncio.sleep(1.0)
        await release_all(page)
        await asyncio.sleep(2.0)
        rec = await page.evaluate("() => window.__rec")
        final = rec["state"][-1]
        res.update(idx_before=idx0, idx_after=final[2], step_clicks=1, verdict=f"INDEX+{final[2] - idx0}", mode=final[1])
        res["runs_after_click"] = [[round(t - t_click), trig] for t, trig in rec["runs"] if t >= t_click][:6]

    elif arm == "nan_box":
        for _ in range(5):
            await click(page, "replay-step-forward")
            await asyncio.sleep(0.2)
        box = page.locator(f"#{P}replay-slider input[type=number]")
        await box.fill("")
        await box.press("Enter")
        await asyncio.sleep(0.6)
        d = await page.evaluate("() => window.__prop('metrics-panel-replay-state', 'data')")
        sv = await page.evaluate("() => window.__prop('metrics-panel-replay-slider', 'value')")
        res.update(after_clear={"mode": d["mode"], "index": d["current_index"], "index_is_nan": d["current_index"] != d["current_index"], "slider": sv, "slider_is_nan": sv != sv, "pos": await page.evaluate(pos_text(version))})
        await click(page, "replay-play")
        await asyncio.sleep(2.5)
        d2 = await page.evaluate("() => window.__prop('metrics-panel-replay-state', 'data')")
        res.update(after_play={"mode": d2["mode"], "index": d2["current_index"], "pos": await page.evaluate(pos_text(version))})
        res["verdict"] = "NAN-STATE" if res["after_clear"]["index_is_nan"] else ("CLEAN" if res["after_clear"]["index"] == 5 else "OTHER")

    elif arm == "same_pass":
        for _ in range(5):
            await click(page, "replay-step-forward")
            await asyncio.sleep(0.2)
        big = json.dumps([{"epoch": i} for i in range(2 * rows)])
        await page.evaluate("() => {" + f"document.getElementById('{P}replay-step-forward').click(); window.dash_clientside.set_props('{P}metrics-store', {{data: {big}}});" + "}")
        await asyncio.sleep(1.2)
        d = await page.evaluate("() => window.__prop('metrics-panel-replay-state', 'data')")
        text = await page.evaluate(pos_text(version))
        res.update(state_index=d["current_index"], pos=text, verdict="STALE-INDEX" if not text.startswith(f"{d['current_index']} /") else "CONSISTENT")

    elif arm == "shrink":
        await click(page, "speed-4x")
        await asyncio.sleep(0.4)
        await click(page, "replay-play")
        assert await wait_for(page, playing, 5)
        assert await wait_for(page, "() => window.__prop('metrics-panel-replay-state', 'data').current_index >= 60", 30)
        t_shrink = await now(page)
        small = json.dumps([{"epoch": i} for i in range(50)])
        await page.evaluate("() => {" + f"window.dash_clientside.set_props('{P}metrics-store', {{data: {small}}});" + "}")
        await asyncio.sleep(3.0)
        rec = await page.evaluate("() => window.__rec")
        after = [r for r in rec["state"] if r[0] >= t_shrink]
        left_playing = [r for r in after if r[1] != "playing"]
        idx = [r[2] for r in after]
        jumped_back = any(b < a for a, b in zip(idx, idx[1:]))
        res.update(after=[[round(r[0] - t_shrink), r[1], r[2], r[5]] for r in after][:16], verdict="FALSE-SEEK" if (left_playing and left_playing[0][1] == "paused") or jumped_back else ("STOPPED-AT-END" if left_playing else "NO-FALSE-SEEK"))
        res["slider_triggers_after_shrink"] = [[round(t - t_shrink), pool, snap] for t, pool, snap, _ in rec["q"] if t >= t_shrink and any("replay-slider" in x for v in snap.values() for x in v)][:8]
    return res


async def main_async(a):
    from playwright.async_api import async_playwright

    store = gitobj.Store(a.objects)
    js = {}
    for v in a.builds.split(","):
        if v == "v2fix":
            # v2 plus the minimal fix proposed by this review: a triggered button applies only when its
            # count shows it pending, so a click applied by count is never applied again.
            j = load_js(store, REFS["v2"])
            old = 'var times = (ev === "replay-slider") ? 1 : Math.max(pending[ev], inTriggers[ev] ? 1 : 0);'
            new = 'var times = (ev === "replay-slider") ? 1 : pending[ev];\n        if (times <= 0) { continue; }'
            assert j["REPLAY_CONTROLS_JS"].count(old) == 1
            j["REPLAY_CONTROLS_JS"] = j["REPLAY_CONTROLS_JS"].replace(old, new)
            j["ref"] = "85415f3c+fix_idempotent"
            js[v] = j
        else:
            js[v] = load_js(store, REFS[v])
    if "v2" in js:
        assert "state.clicks = seen;" in js["v2"]["REPLAY_CONTROLS_JS"]
    if "v1" in js:
        assert "state.clicks" not in js["v1"]["REPLAY_CONTROLS_JS"]
    out = {"probe": Path(__file__).name, "sources": {v: {k: js[v][k] for k in ("ref", "blob", "sha256")} for v in js}, "runs": []}
    async with async_playwright() as pw:
        for run in range(a.runs):
            for arm in a.arms.split(","):
                for v in a.builds.split(","):
                    r = None
                    for attempt in range(3):
                        try:
                            r = await run_arm(pw, arm, v, js[v], a.rows)
                            break
                        except Exception as exc:  # noqa: BLE001  (a browser killed by another lane's cleanup)
                            print(f"  {arm} {v}: attempt {attempt} failed: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
                            await asyncio.sleep(5)
                    if r is None:
                        r = {"arm": arm, "version": v, "verdict": "HARNESS-FAILED"}
                    r["run"] = run
                    out["runs"].append(r)
                    brief = {k: r.get(k) for k in ("verdict", "pause_latency_ms", "idx_at_click", "idx_at_pause", "release_ms_after_click", "undone_ms_after_pause", "final", "idx_before", "idx_after", "state_index", "pos", "after_clear", "after_play")}
                    print(f"run {run} {arm:12s} {v}: {json.dumps({k: x for k, x in brief.items() if x is not None})}", flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("->", a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--objects", required=True)
    ap.add_argument("--arms", default="lost_pause,double_pause,double_step,nan_box,same_pass,shrink")
    ap.add_argument("--builds", default="v1,v2")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--rows", type=int, default=120)
    ap.add_argument("--out", required=True)
    asyncio.run(main_async(ap.parse_args()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
