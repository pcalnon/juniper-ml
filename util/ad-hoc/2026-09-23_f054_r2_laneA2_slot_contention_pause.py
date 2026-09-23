#!/usr/bin/env python
"""
F-CANOPY-054 round 2, Lane A2: does a replay PAUSE click survive dash-renderer slot contention? (canopy#670 v1 vs v2)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (executed by Claude Code, consensus Lane A2)
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: canopy#670 (F-CANOPY-054); juniper-canopy worktree fix/f054-replay-block-clientside;
         v1 = c0530279 (PR as opened), v2 = 85415f3c (local freeze, not pushed)

ENTRY POINT (independent)
-------------------------
Built from the renderer source and the two builds' git objects only. Not read before these numbers existed:
util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py, the laneB/ and laneB2/ scratch dirs, the ledger's Phase 8.
Both builds' REPLAY_CONTROLS_JS, REPLAY_REFILL_POSITION_JS, REPLAY_CONTROL_IDS, the exact Output/Input/State lists
(including list-vs-single shape and keyword args) and the replay-state / replay-interval / replay-slider props are
read from `git show <sha>:src/frontend/components/metrics_panel.py` with `ast` at startup -- never from the working
tree, which a mutation check is rewriting.

RENDERER MECHANICS, VERIFIED IN dash 4.2.0 dash_renderer.dev.js (line numbers of this file)
------------------------------------------------------------------------------------------
M1 Slots. prioritizedCallbacks observer :2846 `available = Math.max(0, 12 - executing.length - watched.length)`;
   it picks `syncCallbacks.slice(0, available)` from ONE `prioritized` list holding server and clientside requests
   alike. A clientside callback is executed through the same `executeCallback` (:1173) whose async `__execute`
   returns a Promise, so it too passes through `watched` (executingCallbacks :2672-2676). A server request holds its
   slot while its fetch is outstanding. => clientside callbacks DO share the 12 slots (claim 1, confirmed in source).
M2 Replacement. requestedCallbacks observer: step 1 (:2985-3016) merges duplicate requests that are BOTH still in
   `requested` (changedPropIds merged with Math.max, :3004-3007); step 2 `pDuplicates` (:3024) groups
   concat(prioritized, requested) by getUniqueIdentifier (:1715, inputs+outputs+state) and removes every member but
   the LAST from `prioritized` (:3151). The removed request's changedPropIds are not carried into the survivor.
   => a request waiting in `prioritized` for a slot is replaced, unmerged, by a newer request of the same callback
   (claim 2's queue mechanics, confirmed in source). The same shape exists for blocked/executing/watched (:3025-3027).
M3 Order. getPriority (:1592) filters its seed callback out on the first pass (`filter` keeps only already-touched
   ids), so every request gets priority "0"; sortPriority (:2798) then returns 1 for every pair, which V8's sort
   treats as already-ordered: `prioritized` is served FIFO. A replaced request re-enters at the tail.
M4 The requested observer awaits wait(0) = setTimeout(0) (:2962, utils/wait.ts :4031) before steps 1-2, so a click
   and a tick that land in the same macrotask batch MERGE (step 1) -- only a request already promoted to
   `prioritized` can be REPLACED (step 2). Promotion is immediate when the callback is ready (getReadyCallbacks
   :1633 checks Inputs only), so under slot saturation a click's request normally sits in `prioritized`.
M5 dash_clientside.set_props (:3860) dispatches updateProps + notifyObservers, i.e. it requests every callback that
   has the prop as an Input -- used here only to start the load (hog callbacks) and, in A7, to stop the replay timer.

HARNESS
-------
One Flask server on 127.0.0.1:<port> (>= 18500) mounting four Dash apps: /v1/ /v2/ /v2m/ /v1u/.
Each app = canopy's replay block for that build (the two clientside callbacks with the build's exact signatures, the
8 buttons as html.Button with canopy's ids, dcc.Slider with the build's props, the replay-position span in the build's
shape, replay-state and replay-interval with the build's props, a STATIC metrics-store of 600 rows, so the refill
callback registers but never fires) + 12 "hog" SERVER callbacks, each Input hog-trigger-<i>.data -> Output
hog-out-<i>.children, sleeping H seconds. Distinct outputs => distinct identifiers => hogs never evict each other, so
K hogs started together hold K slots for ~H s (Chrome sends 6 per host at once; the renderer still counts all K as
`watched`, which is what gates `available`).
Instrument (read-only): a redux store.subscribe() hook logs every change of replay-state.data (mode/index/tick_n/
clicks), replay-play.n_clicks, replay-interval.n_intervals/.disabled/.interval, the play label and the slider value,
plus -- whenever the callbacks slice changes -- per queue list (requested/prioritized/blocked/executing/watched/
executed) the entry count and each replay-controls request's changedPropIds. A capture-phase click listener logs each
click with the executing+watched count at that instant. Variants v1/v2/v2m wrap the build's JS in a logging shim
that records ctx.triggered, the play-count Input, the State it read and the state it returned, then calls the
build's function unchanged; v1u serves v1's JS unwrapped (instrument-invariance arm).

TRIAL (identical for every arm)
  load; wait for the mount run (position text shows "/ 599"); click PLAY; wait for replay-state.mode=="playing";
  wait 2.2 s (>= 2 ticks); t_hog: set_props K hog triggers (sleep H=6 s) [A7: also set_props replay-interval
  disabled=true]; wait 1.5 s; click PAUSE (tp); watch 10 s; collect; close context; wait until the server has no
  hog in flight. Arms are interleaved round-robin, n = 5 each. One Chromium, one context per trial.

ARMS
  A1 v1   K=12  contention
  A2 v2   K=12  contention
  A3 v1   K=0   no-contention control
  A4 v2   K=0   no-contention control
  A5 v1   K=11  dose control: 11 hogs leave one slot free
  A6 v2m  K=12  INSTRUMENT CHECK: v2 with its value-derived recovery removed (`var lost = [];`)
  A7 v1   K=12  mechanism control: replay timer stopped at t_hog, so no tick can replace the click
  A8 v1u  K=12  instrument-invariance: v1 without the logging shim

VERDICT RULE (per trial; fixed before the first run)
  Window = (tp, tp + 10 s], tp = page Date.now() of the pause click.
  INVALID if any: replay-state.mode != "playing" at tp; index did not advance between play and t_hog; play n_clicks
          did not increase after tp (click not delivered); K>=11 arms: executing+watched at tp < K; K=0 arms:
          executing+watched at tp >= 12; mode "stopped" anywhere in the window.
  HELD    replay-state.mode == "paused" appears in the window (first at ta), never returns to "playing" afterwards
          in the window, and replay-state.current_index does not change after ta.
  UNDONE  "paused" appears, then "playing" again in the window.
  LOST    "paused" never appears in the window.
  Arm result = HELD count / valid n. Mechanism fields per trial (reported, not part of the verdict):
  trigger_lost = the first controls run after tp that sees the new play count has no replay-play.n_clicks in
  ctx.triggered; replaced = a replay request carrying replay-play was seen in `prioritized` and no replay request
  carrying replay-play ever reached executing/watched/executed; pause latency = ta - tp; ticks between tp and
  that first run; executing+watched at tp.

PREDICTIONS (fixed before the first run; H = 6 s, tick 1000 ms, click 1.5 s after the hogs start)
  A1 v1  K=12 : LOST 5/5; trigger_lost 5/5; replaced 5/5 (a tick arrives within <= 1 s of the click, while every
                slot is still held for ~4.5 s more).
  A2 v2  K=12 : HELD 5/5; trigger_lost 5/5 (same renderer behaviour) but the pause applies at the first run after
                slots free, latency ~4.5 s (3.5-6.5 s); index frozen after it.
  A3 v1  K=0  : HELD 5/5, latency < 0.3 s, trigger_lost 0/5.
  A4 v2  K=0  : HELD 5/5, latency < 0.3 s, trigger_lost 0/5.
  A5 v1  K=11 : HELD 5/5, latency < 0.3 s, trigger_lost 0/5 (the loss needs ALL 12 slots held).
  A6 v2m K=12 : LOST 5/5 (the harness CAN return LOST for v2's code path; v2's HELD is its recovery's doing).
  A7 v1  K=12, timer stopped : HELD 5/5, latency ~4.5 s, trigger_lost 0/5 (contention delays the click; only a
                replacing tick loses it).
  A8 v1u K=12 : LOST 5/5 (the shim does not change the outcome).
  Headline predicted: v1 0/5 held under contention; v2 5/5 held under contention (late, not lost).

Usage
  LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python <this> freeze
  LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python <this> run --port 18573 [--reps 5] [--arms A1,A2] [--out PATH]
"""

import argparse
import ast
import hashlib
import json
import logging
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANOPY_REPO = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--f054-replay-block-clientside--20260923-0036--2f973ca2"
PANEL_PATH = "src/frontend/components/metrics_panel.py"
BUILD_SHAS = {"v1": "c0530279", "v2": "85415f3c"}
RENDERER = "/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages/dash/dash-renderer/build/dash_renderer.dev.js"
CID = "metrics-panel"
PREFIX = CID + "-"
K_MAX = 12
N_METRICS = 600
HOG_SLEEP_S = 6.0
PLAY_SETTLE_S = 2.2
HOG_LEAD_S = 1.5
WATCH_S = 10.0
FORBIDDEN_PORTS = {8051, 8101, 8202}

HERE = Path(__file__).resolve()
WORKTREE = HERE.parents[2]
DEFAULT_OUT = WORKTREE / "reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_r2_laneA2_slot_contention_pause.json"

# name, variant, K hogs, stop the replay timer at t_hog
ARMS = [
    ("A1", "v1", 12, False),
    ("A2", "v2", 12, False),
    ("A3", "v1", 0, False),
    ("A4", "v2", 0, False),
    ("A5", "v1", 11, False),
    ("A6", "v2m", 12, False),
    ("A7", "v1", 12, True),
    ("A8", "v1u", 12, False),
]
VARIANTS = {"v1": ("v1", None, True), "v2": ("v2", None, True), "v2m": ("v2", "no_recovery", True), "v1u": ("v1", None, False)}

# ----------------------------------------------------------------------------------------------------------------
# Load a build from its git object
# ----------------------------------------------------------------------------------------------------------------


def git_show(sha):
    return subprocess.run(["git", "-C", CANOPY_REPO, "show", f"{sha}:{PANEL_PATH}"], check=True, capture_output=True, text=True).stdout


def git_full_sha(sha):
    return subprocess.run(["git", "-C", CANOPY_REPO, "rev-parse", sha], check=True, capture_output=True, text=True).stdout.strip()


def _eval_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(v.value)
            elif isinstance(v, ast.FormattedValue) and ast.unparse(v.value) == "self.component_id":
                parts.append(CID)
            else:
                raise ValueError("unsupported f-string part: " + ast.unparse(node))
        return "".join(parts)
    raise ValueError("unsupported string node: " + ast.unparse(node))


def _dep(node):
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("Output", "Input", "State")):
        raise ValueError("not a dependency: " + ast.unparse(node))
    d = {"kind": node.func.id, "id": _eval_str(node.args[0]), "prop": _eval_str(node.args[1])}
    for k in node.keywords:
        d[k.arg] = ast.literal_eval(k.value)
    return d


def _root_name(node):
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        node = node.func.value
    return node.id if isinstance(node, ast.Name) else None


def _component_kwargs(cls_node, ctor, comp_id):
    """literal kwargs of the dcc.<ctor>(id=f"{self.component_id}-...") call with that id."""
    for n in ast.walk(cls_node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == ctor:
            kws = {k.arg: k.value for k in n.keywords}
            if "id" in kws:
                try:
                    if _eval_str(kws["id"]) != comp_id:
                        continue
                except ValueError:
                    continue
                return {k: ast.literal_eval(v) for k, v in kws.items() if k != "id"}
    raise KeyError(f"{ctor} {comp_id} not found")


def load_build(tag):
    sha = BUILD_SHAS[tag]
    src = git_show(sha)
    tree = ast.parse(src)
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS"):
            consts[n.targets[0].id] = ast.literal_eval(n.value)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MetricsPanel")
    control_ids = None
    for n in cls.body:
        tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
        if isinstance(tgt, ast.Name) and tgt.id == "REPLAY_CONTROL_IDS":
            control_ids = list(ast.literal_eval(n.value))
    reg = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "register_callbacks")
    sigs = {}
    for call in ast.walk(reg):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "clientside_callback" and call.args:
            root = _root_name(call.args[0])
            if root in ("REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS"):
                args = []
                for a in call.args[1:]:
                    if isinstance(a, ast.List):
                        args.append({"list": True, "deps": [_dep(e) for e in a.elts]})
                    else:
                        args.append({"list": False, "deps": [_dep(a)]})
                sigs[root] = {"args": args, "kwargs": {k.arg: ast.literal_eval(k.value) for k in call.keywords}, "js_expr": ast.unparse(call.args[0])}
    assert set(sigs) == {"REPLAY_CONTROLS_JS", "REPLAY_REFILL_POSITION_JS"}, sigs.keys()
    assert sigs["REPLAY_CONTROLS_JS"]["js_expr"] == (
        "REPLAY_CONTROLS_JS.replace('__PREFIX__', json.dumps(f'{self.component_id}-')).replace('__CONTROLS__', json.dumps(list(self.REPLAY_CONTROL_IDS)))"
    ), sigs["REPLAY_CONTROLS_JS"]["js_expr"]
    assert sigs["REPLAY_REFILL_POSITION_JS"]["js_expr"] == "REPLAY_REFILL_POSITION_JS", sigs["REPLAY_REFILL_POSITION_JS"]["js_expr"]
    return {
        "tag": tag,
        "sha": sha,
        "full_sha": git_full_sha(sha),
        "source_sha256": hashlib.sha256(src.encode()).hexdigest(),
        "controls_js": consts["REPLAY_CONTROLS_JS"],
        "refill_js": consts["REPLAY_REFILL_POSITION_JS"],
        "control_ids": control_ids,
        "sigs": sigs,
        "replay_state": _component_kwargs(cls, "Store", f"{CID}-replay-state")["data"],
        "replay_interval": _component_kwargs(cls, "Interval", f"{CID}-replay-interval"),
        "replay_slider": _component_kwargs(cls, "Slider", f"{CID}-replay-slider"),
    }


MUTANT_RE = re.compile(r"var lost = controls\.filter\(function \(c\) \{.*?\n    \}\);", re.S)


def controls_js_for(build, mutation):
    # exactly what register_callbacks does
    js = build["controls_js"].replace("__PREFIX__", json.dumps(f"{CID}-")).replace("__CONTROLS__", json.dumps(list(build["control_ids"])))
    if mutation == "no_recovery":
        js, n = MUTANT_RE.subn("var lost = []; // LANE-A2 MUTANT: value-derived recovery removed", js)
        assert n == 1, "mutation site not found exactly once"
    return js


def arg_index(build):
    deps = [d for a in build["sigs"]["REPLAY_CONTROLS_JS"]["args"] for d in a["deps"]]
    ins = [d for d in deps if d["kind"] == "Input"]
    sts = [d for d in deps if d["kind"] == "State"]
    ip = [i for i, d in enumerate(ins) if (d["id"], d["prop"]) == (f"{CID}-replay-play", "n_clicks")][0]
    it = [i for i, d in enumerate(ins) if (d["id"], d["prop"]) == (f"{CID}-replay-interval", "n_intervals")][0]
    ist = len(ins) + [i for i, d in enumerate(sts) if (d["id"], d["prop"]) == (f"{CID}-replay-state", "data")][0]
    return ip, it, ist


def wrap_js(js, fn, idx):
    ip, it, ist = idx if idx else (0, 0, 0)
    is_ctl = "true" if fn == "ctl" else "false"
    return (
        "function () {\n"
        "  var args = Array.prototype.slice.call(arguments);\n"
        "  var dc = window.dash_clientside || {};\n"
        "  var ctx = dc.callback_context || {};\n"
        "  var trig = (ctx.triggered || []).map(function (t) { return String(t.prop_id); });\n"
        f"  var rec = {{t: Date.now(), fn: {json.dumps(fn)}, trig: trig}};\n"
        "  var cmp = function (s) { return (s && typeof s === 'object' && s.mode !== undefined) ? {mode: s.mode, i: s.current_index, tn: s.tick_n, cl: (s.clicks || {})['replay-play']} : (s === dc.no_update ? 'no_update' : s); };\n"
        f"  if ({is_ctl}) {{ rec.pc = args[{ip}]; rec.ni = args[{it}]; rec.sin = cmp(args[{ist}]); }}\n"
        "  var out = (" + js.strip() + ").apply(this, args);\n"
        f"  try {{ if ({is_ctl}) {{ rec.sout = cmp(out[0]); rec.dis = (out[1] === dc.no_update) ? 'no_update' : out[1]; }} }} catch (e) {{ rec.werr = String(e); }}\n"
        "  if (window.__A2 && window.__A2.inv) { window.__A2.inv.push(rec); }\n"
        "  return out;\n"
        "}\n"
    )


# ----------------------------------------------------------------------------------------------------------------
# Server
# ----------------------------------------------------------------------------------------------------------------

INFLIGHT = 0
INFLIGHT_LOCK = threading.Lock()


def _make_hog(i):
    def hog(data):
        global INFLIGHT
        with INFLIGHT_LOCK:
            INFLIGHT += 1
        try:
            time.sleep(float((data or {}).get("sleep", 0)))
        finally:
            with INFLIGHT_LOCK:
                INFLIGHT -= 1
        return f"hog {i} done {json.dumps(data)}"

    hog.__name__ = f"hog_{i}"
    return hog


def build_app(server, variant, builds):
    import dash
    from dash import Input, Output, State, dcc, html

    btag, mutation, wrapped = VARIANTS[variant]
    b = builds[btag]
    app = dash.Dash(f"laneA2_{variant}", server=server, url_base_pathname=f"/{variant}/", title=f"laneA2 {variant}")
    ctl_sig = b["sigs"]["REPLAY_CONTROLS_JS"]
    ref_sig = b["sigs"]["REPLAY_REFILL_POSITION_JS"]
    out_ids = {d["id"] for a in ctl_sig["args"] + ref_sig["args"] for d in a["deps"]}
    if f"{CID}-replay-position-index" in out_ids:
        position = html.Span(
            id=f"{CID}-replay-position",
            children=[html.Span("0", id=f"{CID}-replay-position-index"), " / ", html.Span("0", id=f"{CID}-replay-position-max")],
        )
    else:
        position = html.Span(id=f"{CID}-replay-position", children="0 / 0")
    buttons = [("replay-start", "⏮"), ("replay-step-back", "◀"), ("replay-play", "▶"), ("replay-step-forward", "▶"), ("replay-end", "⏭"), ("speed-1x", "1x"), ("speed-2x", "2x"), ("speed-4x", "4x")]
    app.layout = html.Div(
        [
            html.Div(
                id=f"{CID}-replay-controls",
                children=[
                    html.Div([html.Button(label, id=f"{CID}-{suffix}") for suffix, label in buttons]),
                    html.Div([position, dcc.Slider(id=f"{CID}-replay-slider", **b["replay_slider"])], style={"width": "600px"}),
                ],
                style={"display": "block", "padding": "10px"},
            ),
            dcc.Store(id=f"{CID}-metrics-store", data=[{"epoch": i} for i in range(N_METRICS)]),
            dcc.Store(id=f"{CID}-replay-state", data=b["replay_state"]),
            dcc.Interval(id=f"{CID}-replay-interval", **b["replay_interval"]),
            html.Div([dcc.Store(id=f"hog-trigger-{i}") for i in range(K_MAX)]),
            html.Div([html.Div(id=f"hog-out-{i}") for i in range(K_MAX)]),
        ]
    )
    layout_ids = {f"{CID}-{s}" for s, _ in buttons} | {f"{CID}-replay-controls", f"{CID}-replay-position", f"{CID}-replay-slider", f"{CID}-metrics-store", f"{CID}-replay-state", f"{CID}-replay-interval"}
    if f"{CID}-replay-position-index" in out_ids:
        layout_ids |= {f"{CID}-replay-position-index", f"{CID}-replay-position-max"}
    missing = out_ids - layout_ids
    assert not missing, f"{variant}: signature references ids absent from the harness layout: {missing}"

    def mk(d):
        cls = {"Output": Output, "Input": Input, "State": State}[d["kind"]]
        kw = {k: v for k, v in d.items() if k not in ("kind", "id", "prop")}
        return cls(d["id"], d["prop"], **kw)

    def rebuild(sig):
        return [[mk(d) for d in a["deps"]] if a["list"] else mk(a["deps"][0]) for a in sig["args"]]

    ctl_js = controls_js_for(b, mutation)
    ref_js = b["refill_js"]
    if wrapped:
        ctl_js = wrap_js(ctl_js, "ctl", arg_index(b))
        ref_js = wrap_js(ref_js, "refill", None)
    app.clientside_callback(ctl_js, *rebuild(ctl_sig), **ctl_sig["kwargs"])
    app.clientside_callback(ref_js, *rebuild(ref_sig), **ref_sig["kwargs"])
    for i in range(K_MAX):
        app.callback(Output(f"hog-out-{i}", "children"), Input(f"hog-trigger-{i}", "data"), prevent_initial_call=True)(_make_hog(i))
    return app


def serve(port):
    import flask
    from werkzeug.serving import make_server

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    builds = {t: load_build(t) for t in BUILD_SHAS}
    server = flask.Flask("laneA2")
    for v in VARIANTS:
        build_app(server, v, builds)

    @server.route("/__inflight")
    def _inflight():
        return str(INFLIGHT)

    srv = make_server("127.0.0.1", port, server, threaded=True)
    print(f"serving on 127.0.0.1:{port}", flush=True)
    srv.serve_forever()


# ----------------------------------------------------------------------------------------------------------------
# Browser instrument
# ----------------------------------------------------------------------------------------------------------------

INSTR_JS = r"""
(() => {
  if (window.__A2) { return; }
  const A = window.__A2 = {ready: false, clicks: [], store: [], queue: [], inv: [], fetch: [], errs: [], cur: {}, hog: null};
  window.addEventListener('error', (e) => A.errs.push({t: Date.now(), m: String(e.message)}));
  const P = 'metrics-panel-';
  const IDS = {
    rs: [P + 'replay-state', 'data'], pc: [P + 'replay-play', 'n_clicks'], ni: [P + 'replay-interval', 'n_intervals'],
    dis: [P + 'replay-interval', 'disabled'], iv: [P + 'replay-interval', 'interval'], lab: [P + 'replay-play', 'children'],
    sv: [P + 'replay-slider', 'value']
  };
  const pathCache = {};
  const dfs = (node, id, path, depth) => {
    if (!node || typeof node !== 'object' || depth > 80) { return null; }
    if (node.props && node.props.id === id) { return path; }
    const keys = Array.isArray(node) ? node.map((_, i) => i) : Object.keys(node);
    for (const k of keys) {
      const v = node[k];
      if (v && typeof v === 'object') { const r = dfs(v, id, path.concat([k]), depth + 1); if (r) { return r; } }
    }
    return null;
  };
  const getAt = (root, path) => { let n = root; for (const k of path) { if (n == null) { return undefined; } n = n[k]; } return n; };
  const findProps = (layout, id) => {
    let p = pathCache[id];
    let n = p ? getAt(layout, p) : null;
    if (!n || !n.props || n.props.id !== id) { p = dfs(layout, id, [], 0); pathCache[id] = p; n = p ? getAt(layout, p) : null; }
    return n ? n.props : undefined;
  };
  const cmp = (s) => (s && typeof s === 'object') ? {mode: s.mode, i: s.current_index, tn: s.tick_n, cl: (s.clicks || {})['replay-play']} : s;
  const isReplay = (cb) => { const o = cb && cb.callback && cb.callback.output; return typeof o === 'string' && o.indexOf(P + 'replay-state.data') >= 0 && o.indexOf('@') < 0; };
  const shortProp = (p) => p.replace(P + 'replay-interval.n_intervals', 'tick').replace(P, '').replace('.n_clicks', '');
  const tags = new WeakMap(); let tagN = 0;
  const tag = (o) => { if (!tags.has(o)) { tags.set(o, ++tagN); } return tags.get(o); };
  const LISTS = ['requested', 'prioritized', 'blocked', 'executing', 'watched', 'executed'];
  let lastCbs = null, lastSig = null;
  const onState = () => {
    const s = window.store.getState();
    const now = Date.now();
    for (const k in IDS) {
      const [id, prop] = IDS[k];
      const pr = findProps(s.layout, id);
      const v = pr ? pr[prop] : undefined;
      if (A.cur[k] !== v) { A.cur[k] = v; A.store.push({t: now, k: k, v: (k === 'rs') ? cmp(v) : v}); }
    }
    const cbs = s.callbacks;
    if (cbs && cbs !== lastCbs) {
      lastCbs = cbs;
      const q = {};
      for (const L of LISTS) {
        const arr = cbs[L] || [];
        q[L] = {n: arr.length, r: arr.filter(isReplay).map((cb) => tag(cb) + ':' + Object.keys(cb.changedPropIds || {}).map(shortProp).join('+'))};
      }
      const sig = JSON.stringify(q);
      if (sig !== lastSig) { lastSig = sig; A.queue.push({t: now, q: q, done: cbs.completed}); }
    }
  };
  const hook = setInterval(() => {
    if (window.store && window.store.getState && window.store.subscribe) {
      clearInterval(hook);
      window.store.subscribe(onState);
      onState();
      A.ready = true;
    }
  }, 2);
  document.addEventListener('click', (e) => {
    const b = (e.target && e.target.closest) ? e.target.closest('button') : null;
    let ew = null, npr = null;
    try { const c = window.store.getState().callbacks; ew = c.executing.length + c.watched.length; npr = c.prioritized.length; } catch (x) { /* before hydration */ }
    A.clicks.push({t: Date.now(), id: b ? b.id : null, ew: ew, pr: npr, pcBefore: A.cur.pc});
  }, true);
  const of = window.fetch;
  window.fetch = function (input, init) {
    const url = (typeof input === 'string') ? input : (input && input.url) || '';
    const p = of.apply(this, arguments);
    if (url.indexOf('_dash-update-component') >= 0) {
      const rec = {t0: Date.now()};
      try { const b = JSON.parse(init.body); rec.out = String(b.output).slice(0, 40); } catch (x) { rec.out = '?'; }
      A.fetch.push(rec);
      p.then((r) => { rec.t1 = Date.now(); rec.st = r.status; }, (err) => { rec.t1 = Date.now(); rec.err = String(err); });
    }
    return p;
  };
})();
"""

HOG_JS = """([K, H, stopTimer]) => {
  const t = Date.now();
  const dc = window.dash_clientside;
  if (stopTimer) { dc.set_props('metrics-panel-replay-interval', {disabled: true}); }
  for (let i = 0; i < K; i++) { dc.set_props('hog-trigger-' + i, {data: {sleep: H, nonce: t, i: i}}); }
  window.__A2.hog = {t: t, K: K, H: H, stopTimer: stopTimer};
  return t;
}"""

COLLECT_JS = "() => JSON.parse(JSON.stringify({clicks: window.__A2.clicks, store: window.__A2.store, queue: window.__A2.queue, inv: window.__A2.inv, fetch: window.__A2.fetch, errs: window.__A2.errs, hog: window.__A2.hog}))"


# ----------------------------------------------------------------------------------------------------------------
# Verdict
# ----------------------------------------------------------------------------------------------------------------


def evaluate(arm, rep, d, py):
    name, variant, K, stop_timer = arm
    r = {"arm": name, "variant": variant, "K": K, "stop_timer": stop_timer, "rep": rep, "py": py}
    why = []
    plays = [c for c in d["clicks"] if c["id"] == f"{CID}-replay-play"]
    if len(plays) != 2 or not d.get("hog"):
        r.update(verdict="INVALID", invalid=[f"play clicks={len(plays)} hog={bool(d.get('hog'))}"])
        return r
    t_play, tp = plays[0]["t"], plays[1]["t"]
    t_hog = d["hog"]["t"]
    t_end = tp + WATCH_S * 1000
    rs = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "rs" and isinstance(e["v"], dict)]
    pcs = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "pc"]
    nis = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "ni"]
    dis = [(e["t"], e["v"]) for e in d["store"] if e["k"] == "dis"]

    def last_before(series, t):
        xs = [v for tt, v in series if tt <= t]
        return xs[-1] if xs else None

    at_tp = last_before(rs, tp)
    playing_seen = [t for t, v in rs if t_play <= t <= tp and v["mode"] == "playing"]
    i_play = rs[[k for k, (t, v) in enumerate(rs) if t >= playing_seen[0]][0]][1]["i"] if playing_seen else None
    i_hog = (last_before(rs, t_hog) or {}).get("i")
    pc_before, pc_after = last_before(pcs, tp - 1), last_before(pcs, t_end)
    ew = plays[1]["ew"]
    if not at_tp or at_tp["mode"] != "playing":
        why.append(f"mode at tp = {at_tp and at_tp['mode']}")
    if i_play is None or i_hog is None or not i_hog > i_play:
        why.append(f"index did not advance before t_hog ({i_play} -> {i_hog})")
    if not (isinstance(pc_before, int) and isinstance(pc_after, int) and pc_after == pc_before + 1):
        why.append(f"play n_clicks {pc_before} -> {pc_after}")
    if K >= 11 and (ew is None or ew < K):
        why.append(f"executing+watched at tp = {ew} < K={K}")
    if K == 0 and (ew is None or ew >= 12):
        why.append(f"executing+watched at tp = {ew} in a no-contention arm")
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
        idx_after = {v["i"] for t, v in rs if ta <= t <= t_end}
        verdict = "HELD" if len(idx_after) == 1 else "UNDONE"
    final = win[-1][1] if win else at_tp
    # mechanism, from the shim (not in v1u)
    ctl = [x for x in d["inv"] if x.get("fn") == "ctl"]
    first = next((x for x in ctl if x["t"] >= tp and x.get("pc") == pc_after), None)
    trig_play = f"{CID}-replay-play.n_clicks"
    # mechanism, from the queue log
    click_in_prio = False
    click_executed = False
    for e in d["queue"]:
        if e["t"] < tp:
            continue
        q = e["q"]
        if any("replay-play" in x.split(":", 1)[1].split("+") for x in q["prioritized"]["r"]):
            click_in_prio = True
        for L in ("executing", "watched", "executed"):
            if any("replay-play" in x.split(":", 1)[1].split("+") for x in q[L]["r"]):
                click_executed = True
    t_first = first["t"] if first else None
    ticks_between = len([1 for t, v in nis if tp < t <= (t_first if t_first else ta if ta else t_end)])
    r.update(
        verdict="INVALID" if why else verdict,
        raw_verdict=verdict,
        invalid=why,
        tp=tp,
        latency_s=round((ta - tp) / 1000, 3) if ta else None,
        ew_at_tp=ew,
        prioritized_at_tp=plays[1]["pr"],
        index_play_to_hog=[i_play, i_hog],
        mode_at_tp=at_tp and at_tp["mode"],
        final_state=final,
        final_disabled=last_before(dis, t_end),
        first_run_after_click_s=round((t_first - tp) / 1000, 3) if t_first else None,
        trigger_lost=(trig_play not in first["trig"]) if first else None,
        first_run_trig=first["trig"] if first else None,
        first_run_state_out=first.get("sout") if first else None,
        click_request_seen_in_prioritized=click_in_prio,
        click_request_executed=click_executed,
        replaced=click_in_prio and not click_executed,
        ticks_between_click_and_first_run=ticks_between,
        n_hog_fetches=len([f for f in d["fetch"] if f.get("out", "").startswith("hog-out")]),
        errs=d["errs"],
    )
    return r


# ----------------------------------------------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------------------------------------------


def port_free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR like werkzeug's own bind: TIME_WAIT from a previous run is not a listener (a live listener still
    # fails the bind with EADDRINUSE).
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def http_get(url, timeout=2.0):
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310 - loopback only
        return resp.status, resp.read().decode()


def wait_inflight_zero(port, limit=20.0):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if http_get(f"http://127.0.0.1:{port}/__inflight")[1].strip() == "0":
                return round(time.time() - t0, 2)
        except Exception:
            pass
        time.sleep(0.25)
    return None


def run_trial(browser, port, arm, rep):
    name, variant, K, stop_timer = arm
    py = {"start": time.time()}
    ctx = browser.new_context(viewport={"width": 1200, "height": 700})
    ctx.add_init_script(INSTR_JS)
    page = ctx.new_page()
    try:
        page.goto(f"http://127.0.0.1:{port}/{variant}/", wait_until="load")
        page.wait_for_function("() => window.__A2 && window.__A2.ready", timeout=15000)
        page.wait_for_function(f"() => {{ const e = document.getElementById('{CID}-replay-position'); return e && e.textContent.indexOf('/ {N_METRICS - 1}') >= 0; }}", timeout=15000)
        time.sleep(0.5)
        page.click(f"#{CID}-replay-play")
        page.wait_for_function("() => window.__A2.cur.rs && window.__A2.cur.rs.mode === 'playing'", timeout=8000)
        time.sleep(PLAY_SETTLE_S)
        page.evaluate(HOG_JS, [K, HOG_SLEEP_S, stop_timer])
        time.sleep(HOG_LEAD_S)
        page.click(f"#{CID}-replay-play")
        time.sleep(WATCH_S)
        data = page.evaluate(COLLECT_JS)
    finally:
        ctx.close()
    py["drain_s"] = wait_inflight_zero(port)
    py["end"] = time.time()
    rec = evaluate(arm, rep, data, py)
    rec["logs"] = data
    return rec


def summarize(trials):
    out = {}
    for name, variant, K, stop_timer in ARMS:
        ts = [t for t in trials if t["arm"] == name]
        if not ts:
            continue
        valid = [t for t in ts if t["verdict"] != "INVALID"]
        lat = sorted(t["latency_s"] for t in valid if t["latency_s"] is not None)
        out[name] = {
            "variant": variant,
            "K": K,
            "stop_timer": stop_timer,
            "n": len(ts),
            "valid": len(valid),
            "HELD": sum(t["verdict"] == "HELD" for t in ts),
            "LOST": sum(t["verdict"] == "LOST" for t in ts),
            "UNDONE": sum(t["verdict"] == "UNDONE" for t in ts),
            "INVALID": sum(t["verdict"] == "INVALID" for t in ts),
            "latency_s": lat,
            "trigger_lost": [t["trigger_lost"] for t in ts],
            "replaced": [t["replaced"] for t in ts],
            "ew_at_tp": [t["ew_at_tp"] for t in ts],
            "ticks_between": [t["ticks_between_click_and_first_run"] for t in ts],
        }
    return out


def docstring_sha():
    return hashlib.sha256(__doc__.encode()).hexdigest()


def cmd_freeze(_args):
    print(f"utc={datetime.now(timezone.utc).isoformat(timespec='seconds')} docstring_sha256={docstring_sha()} file={HERE}")
    for t in BUILD_SHAS:
        b = load_build(t)
        print(t, b["full_sha"], "source_sha256", b["source_sha256"], "ctl_sig", [(d["kind"], d["id"].replace(PREFIX, ""), d["prop"]) for a in b["sigs"]["REPLAY_CONTROLS_JS"]["args"] for d in a["deps"]])
        print(t, "refill_sig", b["sigs"]["REPLAY_REFILL_POSITION_JS"], "state", b["replay_state"], "interval", b["replay_interval"], "slider", b["replay_slider"])
    b2 = load_build("v2")
    print("v2m mutation applies:", "LANE-A2 MUTANT" in controls_js_for(b2, "no_recovery"))


def cmd_run(args):
    import dash
    from importlib.metadata import version

    port = args.port
    if port in FORBIDDEN_PORTS or port < 18500:
        sys.exit(f"refusing port {port}")
    if not port_free(port):
        sys.exit(f"port {port} busy")
    arms = [a for a in ARMS if not args.arms or a[0] in args.arms.split(",")]
    out = Path(args.out) if args.out else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    builds = {t: load_build(t) for t in BUILD_SHAS}
    meta = {
        "script": str(HERE),
        "docstring_sha256": docstring_sha(),
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "port": port,
        "dash": dash.__version__,
        "playwright": version("playwright"),
        "renderer": RENDERER,
        "renderer_sha256": hashlib.sha256(Path(RENDERER).read_bytes()).hexdigest(),
        "builds": {t: {k: b[k] for k in ("sha", "full_sha", "source_sha256", "control_ids", "replay_state", "replay_interval", "replay_slider")} | {"sigs": b["sigs"]} for t, b in builds.items()},
        "served_js_sha256": {v: hashlib.sha256((wrap_js(controls_js_for(builds[VARIANTS[v][0]], VARIANTS[v][1]), "ctl", arg_index(builds[VARIANTS[v][0]])) if VARIANTS[v][2] else controls_js_for(builds[VARIANTS[v][0]], VARIANTS[v][1])).encode()).hexdigest() for v in VARIANTS},
        "unwrapped_controls_js_sha256": {v: hashlib.sha256(controls_js_for(builds[VARIANTS[v][0]], VARIANTS[v][1]).encode()).hexdigest() for v in VARIANTS},
        "params": {"K_MAX": K_MAX, "HOG_SLEEP_S": HOG_SLEEP_S, "PLAY_SETTLE_S": PLAY_SETTLE_S, "HOG_LEAD_S": HOG_LEAD_S, "WATCH_S": WATCH_S, "N_METRICS": N_METRICS, "reps": args.reps},
        "arms": arms,
        "label": args.label,
    }
    print(json.dumps({k: meta[k] for k in ("docstring_sha256", "started_utc", "port", "dash", "playwright", "renderer_sha256")}), flush=True)
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    srv_log = open(out.with_suffix(".server.log"), "w")
    srv = subprocess.Popen([sys.executable, str(HERE), "serve", "--port", str(port)], stdout=srv_log, stderr=subprocess.STDOUT, env=env)
    trials = []
    try:
        t0 = time.time()
        while True:
            try:
                if all(http_get(f"http://127.0.0.1:{port}/{v}/")[0] == 200 for v in VARIANTS):
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
                    except Exception as e:  # recorded, never silently dropped
                        rec = {"arm": arm[0], "variant": arm[1], "K": arm[2], "stop_timer": arm[3], "rep": rep, "verdict": "INVALID", "invalid": [f"exception: {e!r}"], "latency_s": None, "trigger_lost": None, "replaced": None, "ew_at_tp": None, "ticks_between_click_and_first_run": None}
                        wait_inflight_zero(port)
                    trials.append(rec)
                    print(json.dumps({k: rec.get(k) for k in ("arm", "rep", "verdict", "latency_s", "ew_at_tp", "trigger_lost", "replaced", "ticks_between_click_and_first_run", "first_run_trig", "final_state", "invalid")}), flush=True)
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
    summ = summarize(trials)
    for k, v in summ.items():
        print(k, json.dumps({x: v[x] for x in ("variant", "K", "stop_timer", "n", "valid", "HELD", "LOST", "UNDONE", "INVALID", "latency_s")}))
    print("results:", out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, required=True)
    r = sub.add_parser("run")
    r.add_argument("--port", type=int, default=18573)
    r.add_argument("--reps", type=int, default=5)
    r.add_argument("--arms", default="")
    r.add_argument("--out", default="")
    r.add_argument("--label", default="main")
    a = ap.parse_args()
    if a.cmd == "freeze":
        cmd_freeze(a)
    elif a.cmd == "serve":
        if a.port in FORBIDDEN_PORTS or a.port < 18500:
            sys.exit(f"refusing port {a.port}")
        serve(a.port)
    else:
        cmd_run(a)


if __name__ == "__main__":
    main()
