#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (Lane B adversary scratch -- NOT archived)
# Application : canopy E2E validation arc, F-CANOPY-048 mechanism review
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Lane B discriminating variants of util/ad-hoc/2026-09-22_f048_replay_cycle_cleanroom.py.

WHY. The clean room's feeder writes ``data.data`` with ``allow_duplicate=True``. Dash appends
``@<sha256>`` to that output's PROPERTY (dash/_utils.py:159-163) and dash-renderer keeps the suffix
(splitIdAndProp dev.js:5895, combineIdAndProp :1539, inputMap[id][prop] :1552), so the feeder's
readiness closure is {data.data@<hash>} and reaches nothing. The clean room therefore did NOT model
"a feeder upstream of the block"; it modelled "an always-pending callback unrelated to the block".
These variants separate the readings.

FEEDER VARIANTS (one Interval, 1000 ms, always present):
  dup-always        the original: allow_duplicate writer of data.data, sleeps 1.5 s (always pending)
  unrelated-always  PRIMARY writer of an unrelated store ``other.data`` (no consumer), sleeps 1.5 s
  primary-always    PRIMARY writer of data.data (the one-shot fill becomes the allow_duplicate one), 1.5 s
  dup-gapped        as dup-always but sleeps 0.2 s: pending only part of each second
  primary-gapped    as primary-always but sleeps 0.2 s

ARMS:
  cycle    canopy's shape: B takes slider.value as INPUT (A: state+data -> slider+pos)
  acyclic  B takes slider.value as STATE
  merged   ONE callback C = A+B: Inputs play, slider.value, state, data; Outputs state, slider.value, pos

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (R = controls respond: a control request after the clicks
AND the label sequence changes; F = the fill shows in pos, "0 / 79" or "0 / 80"):
  dup-always        cycle: not R, not F   acyclic: R, F       merged: R, F
  unrelated-always  cycle: not R, not F   acyclic: R, F       merged: R, F
  primary-always    cycle: not R, not F   acyclic: R, not F   merged: not R, not F
  dup-gapped        cycle: R              acyclic: R, F       merged: R, F
  primary-gapped    cycle: R              acyclic: R          merged: R
Reading if these hold: (1) the lock needs the cycle PLUS any always-pending callback, related or not;
(2) the feeder's allow_duplicate output is why the acyclic A applied the fill; (3) a merged callback
escapes the self-closure but is still held by an always-pending PRIMARY writer upstream of its Input;
(4) a feeder with gaps lets the breaker fire, so "perpetual pollers" is not enough -- something must
be pending at EVERY observer pass.
"""

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

ROWS = 80
VARIANTS = ("dup-always", "unrelated-always", "primary-always", "dup-gapped", "primary-gapped")
ARMS = ("cycle", "acyclic", "merged")


def _serve(variant: str, arm: str, port: int) -> None:
    import dash
    from dash import Input, Output, State, dcc, html

    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            dcc.Store(id="state", data={"mode": "stopped", "i": 0}),
            dcc.Store(id="data", data=[]),
            dcc.Store(id="other", data=0),
            dcc.Interval(id="fill", interval=2000, n_intervals=0, max_intervals=1),
            dcc.Interval(id="feed-tick", interval=1000, n_intervals=0),
            dcc.Slider(id="slider", min=0, max=100, value=0),
            html.Div(id="pos", children="0 / 0"),
            html.Button("▶", id="play", n_clicks=0),
        ]
    )
    sleep_s = 1.5 if variant.endswith("always") else 0.2

    if variant.startswith("primary"):
        @app.callback(Output("data", "data"), Input("feed-tick", "n_intervals"), prevent_initial_call=True)
        def feed(n):
            time.sleep(sleep_s)
            return list(range(ROWS + (n % 2)))

        @app.callback(Output("data", "data", allow_duplicate=True), Input("fill", "n_intervals"), prevent_initial_call=True)
        def fill(n):  # noqa: ARG001
            return list(range(ROWS))
    else:
        @app.callback(Output("data", "data"), Input("fill", "n_intervals"), prevent_initial_call=True)
        def fill(n):  # noqa: ARG001
            return list(range(ROWS))

        if variant.startswith("dup"):
            @app.callback(Output("data", "data", allow_duplicate=True), Input("feed-tick", "n_intervals"), prevent_initial_call=True)
            def feed(n):
                time.sleep(sleep_s)
                return list(range(ROWS + (n % 2)))
        else:  # unrelated
            @app.callback(Output("other", "data"), Input("feed-tick", "n_intervals"), prevent_initial_call=True)
            def feed(n):
                time.sleep(sleep_s)
                return n

    if arm in ("cycle", "acyclic"):
        @app.callback([Output("slider", "value"), Output("pos", "children")], [Input("state", "data"), Input("data", "data")], prevent_initial_call=False)
        def ui(state, data):
            mx = len(data) - 1 if data else 0
            i = (state or {}).get("i", 0)
            return ((i / mx * 100) if mx > 0 else 0), f"{i} / {mx}"

        slider_dep = Input("slider", "value") if arm == "cycle" else State("slider", "value")

        @app.callback(Output("state", "data"), [Input("play", "n_clicks"), slider_dep], [State("state", "data"), State("data", "data")], prevent_initial_call=True)
        def controls(n, slider_value, state, data):  # noqa: ARG001
            st = dict(state or {"mode": "stopped", "i": 0})
            st["mode"] = "paused" if st.get("mode") == "playing" else "playing"
            return st
    else:
        @app.callback(
            [Output("state", "data"), Output("slider", "value"), Output("pos", "children")],
            [Input("play", "n_clicks"), Input("slider", "value"), Input("state", "data"), Input("data", "data")],
            prevent_initial_call=False,
        )
        def merged(n, slider_value, state, data):  # noqa: ARG001
            trig = [t.get("prop_id", "") for t in (dash.callback_context.triggered or [])]
            st = dict(state or {"mode": "stopped", "i": 0})
            mx = len(data) - 1 if data else 0
            if any(t.startswith("play.") for t in trig):
                st["mode"] = "paused" if st.get("mode") == "playing" else "playing"
            elif any(t.startswith("slider.") for t in trig):
                st["i"] = int((slider_value or 0) / 100 * mx) if mx > 0 else 0
            i = st.get("i", 0)
            return st, ((i / mx * 100) if mx > 0 else 0), f"{i} / {mx}"

    @app.callback(Output("play", "children"), Input("state", "data"), prevent_initial_call=False)
    def label(state):
        return "⏸" if (state or {}).get("mode") == "playing" else "▶"

    app.run(host="127.0.0.1", port=port, debug=False)


FIND_STORE = """
() => {
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$')) return el[k];
      if (k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  for (const sel of ['#react-entry-point', '#_dash-app-content', 'body']) {
    const el = document.querySelector(sel);
    if (!el) continue;
    let f = fiberOf(el), hops = 0;
    while (f && hops < 8000) {
      const mp = f.memoizedProps;
      if (mp && mp.store && typeof mp.store.getState === 'function') { window.__dashStore = mp.store; return true; }
      f = f.child || f.sibling || (f.return ? f.return.sibling : null);
      hops++;
    }
  }
  return false;
}
"""

INSTALL_CENSUS = """
() => {
  const st = window.__dashStore;
  const name = c => { const d = (c && c.callback) || c || {}; return d.output || '<?>'; };
  window.__cen = {n: 0, quiescent: 0, quiescent_with_requested: 0, requested: {}, nonreq_pending_min: 1e9, q_samples: [], t_install: performance.now()};
  st.subscribe(() => {
    const s = st.getState().callbacks || {};
    const rec = window.__cen;
    rec.n += 1;
    const nonreq = ['prioritized','blocked','executing','watched','executed'].reduce((a, k) => a + ((s[k] || []).length), 0);
    const req = (s.requested || []).length;
    if (nonreq < rec.nonreq_pending_min) rec.nonreq_pending_min = nonreq;
    if (nonreq === 0) {
      rec.quiescent += 1;
      if (req > 0) rec.quiescent_with_requested += 1;
      if (rec.q_samples.length < 40) rec.q_samples.push([Math.round(performance.now()), (s.requested || []).map(name), s.completed || 0]);
    }
    for (const c of (s.requested || [])) { const k = name(c); rec.requested[k] = (rec.requested[k] || 0) + 1; }
    if (rec.t_first_feeder_pending === undefined) {
      const all = ['requested','prioritized','blocked','executing','watched','executed'].flatMap(k => s[k] || []);
      if (all.some(c => ((c.callback || {}).inputs || []).some(i => i.id === 'feed-tick'))) rec.t_first_feeder_pending = Math.round(performance.now());
    }
  });
  return true;
}
"""


def _drive(port: int) -> dict:
    from playwright.sync_api import sync_playwright

    wire = {"ctl_requests": 0, "ctl_responses": 0, "pos_requests": 0, "feed_requests": 0}
    t0 = [None]
    ctl_times: list = []
    obs: dict = {}

    def is_ctl(out: str) -> bool:
        # B's output is "state.data"; the merged C's multi-output string names "state.data" too.
        # No feeder, A or label output contains that token.
        return "state.data" in out

    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        page = b.new_context().new_page()

        def on_request(req):
            if "_dash-update-component" not in req.url:
                return
            out = str((req.post_data_json or {}).get("output") or "")
            now = time.monotonic() - (t0[0] or time.monotonic())
            if is_ctl(out):
                wire["ctl_requests"] += 1
                ctl_times.append(round(now, 2))
            if "pos.children" in out:
                wire["pos_requests"] += 1
            if "feed-tick" in json.dumps((req.post_data_json or {}).get("inputs") or []):
                wire["feed_requests"] += 1

        def on_response(resp):
            if "_dash-update-component" in resp.url and is_ctl(str((resp.request.post_data_json or {}).get("output") or "")):
                wire["ctl_responses"] += 1

        page.on("request", on_request)
        page.on("response", on_response)
        t0[0] = time.monotonic()
        page.goto(f"http://127.0.0.1:{port}/", wait_until="load", timeout=30000)
        page.wait_for_selector("#pos", timeout=15000)
        obs["store_found"] = page.evaluate(FIND_STORE)
        if obs["store_found"]:
            page.evaluate(INSTALL_CENSUS)
        page.wait_for_timeout(6000)
        obs["pos_after_fill"] = page.text_content("#pos")
        obs["label_before"] = page.text_content("#play")
        c_before = wire["ctl_requests"]
        labels = []
        obs["t_clicks_ms"] = []
        for _ in range(3):
            obs["t_clicks_ms"].append(round(page.evaluate("() => performance.now()")))
            page.click("#play")
            page.wait_for_timeout(3000)
            labels.append(page.text_content("#play"))
        obs["labels_after_clicks"] = labels
        obs["pos_end"] = page.text_content("#pos")
        obs["ctl_requests_after_clicks"] = wire["ctl_requests"] - c_before
        if obs["store_found"]:
            cen = page.evaluate("() => window.__cen")
            obs["census"] = {k: cen.get(k) for k in ("n", "quiescent", "quiescent_with_requested", "nonreq_pending_min", "q_samples", "t_install", "t_first_feeder_pending")}
            qs = cen.get("q_samples") or []
            tf = cen.get("t_first_feeder_pending")
            obs["census"]["quiescent_after_feeder_start"] = sum(1 for q in qs if tf is not None and q[0] > tf)
            obs["census"]["t_clicks_ms"] = obs.get("t_clicks_ms")
            obs["census"]["requested_residency"] = dict(sorted(cen["requested"].items(), key=lambda kv: -kv[1])[:8])
        b.close()
    obs.update(wire)
    obs["ctl_request_times_s"] = ctl_times
    return obs


def _run(variant: str, arm: str, port: int) -> dict:
    proc = mp.Process(target=_serve, args=(variant, arm, port), daemon=True)
    proc.start()
    time.sleep(4.0)
    try:
        res = _drive(port)
    finally:
        proc.terminate()
        proc.join(timeout=5)
    seq = [res["label_before"]] + list(res["labels_after_clicks"])
    res["R"] = res["ctl_requests_after_clicks"] > 0 and any(a != b for a, b in zip(seq, seq[1:]))
    res["F"] = res["pos_after_fill"] in (f"0 / {ROWS - 1}", f"0 / {ROWS}")
    res.update({"variant": variant, "arm": arm, "port": port})
    cen = res.get("census", {})
    print(f"  [{variant:16s} {arm:7s}] R={res['R']!s:5s} F={res['F']!s:5s} pos_fill={res['pos_after_fill']!r} labels={[res['label_before']] + res['labels_after_clicks']} "
          f"ctl_after={res['ctl_requests_after_clicks']} ctl_req/resp={res['ctl_requests']}/{res['ctl_responses']} pos_req={res['pos_requests']} feed_req={res['feed_requests']} "
          f"census n={cen.get('n')} quiescent={cen.get('quiescent')} q_with_req={cen.get('quiescent_with_requested')} q_after_feeder={cen.get('quiescent_after_feeder_start')} "
          f"t_install={cen.get('t_install')} t_feeder={cen.get('t_first_feeder_pending')} t_clicks={res.get('t_clicks_ms')}", flush=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8111)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--variants", default=",".join(VARIANTS))
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import dash

    out = {"probe": Path(__file__).name, "dash": dash.__version__, "runs": args.runs, "results": []}
    port = args.port
    for _ in range(args.runs):
        for variant in args.variants.split(","):
            for arm in args.arms.split(","):
                out["results"].append(_run(variant, arm, port))
                port += 1
                Path(args.out).write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"results -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
