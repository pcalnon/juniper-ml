#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc -- Lane A independent re-derivation
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Lane A re-derivation of F-CANOPY-038 (metrics-store no-op suppression) and M-METRICS-18 (replay slider).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (F-CANOPY-038, F-CANOPY-048);
         notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md (M-METRICS-18);
         notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md s.2 (Lane A)

INDEPENDENCE. Written from the canopy source and the Dash 4.2.0 wire format only. It does not import,
copy or read 2026-09-22_state_store_consumer_roundtrip.py or 2026-09-08_replay_block_redrive.py.

INSTRUMENTS
  wire   passive Playwright listeners on every POST /_dash-update-component. The request body carries
         the callback's Inputs and State -- and State is exactly the operand the server-side handler
         compares against -- and the response map says what was written. Nothing is intercepted.
  redux  optional (--redux): read-only reads of window.store.getState(): the renderer's own copy of a
         component's props (layout via paths.strs) and its callback queues. Nothing is dispatched.
  ref    the script's own GET of canopy's /api/metrics/history?limit=<window_size> -- the same URL the
         handler fetches, normalised the same way -- used as the reference operand when attributing a
         no_update to a handler branch.
  server (server-eval step) synthetic POSTs of handle_replay_controls / update_replay_ui with explicit
         Inputs and State. Both callbacks are pure; nothing server-side changes.

STEPS
  deps         served /_dash-dependencies + _dash-config: every writer of the metrics store and of
               replay-state, their exact output strings, and the callback transport.
  claim1       idle census of every response to a request whose output includes
               metrics-panel-metrics-store.data, split by writer (plain = REST poll, @hash = WS append),
               classified carried / no_update / unparseable, each no_update attributed to a branch.
               --control appends a positive control: window size -> 10 must produce a second carried
               write and then suppression on the new value.
  claim2       M-METRICS-18 (slider: keyboard ArrowRight x10, then a mouse drag) and the play button,
               driven only once the client-side store is non-empty (read from request State, not from
               the position text, which is itself an output of the callback under test). Positive
               control: the display-mode radio (M-METRICS-19) round trip on the same page.
  server-eval  what the server returns for the same gestures given the live store contents.

Nothing here starts, stops or PATCHes cascor, and nothing modifies canopy.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "reports" / "e2e-canopy-2026-09-02" / "transcripts"
PREFIX = "2026-09-22_laneA_f038_m18_"

CANOPY = os.environ.get("JUNIPER_E2E_CANOPY_URL", "http://127.0.0.1:8051").rstrip("/")
CASCOR = os.environ.get("JUNIPER_E2E_CASCOR_URL", "http://127.0.0.1:8202").rstrip("/")
DASH = CANOPY + "/dashboard/"
UPDATE_PATH = "_dash-update-component"

STORE_ID = "metrics-panel-metrics-store"
STORE_TOKEN = STORE_ID + ".data"
REPLAY_STATE_ID = "metrics-panel-replay-state"
REPLAY_STATE_TOKEN = REPLAY_STATE_ID + ".data"

LAUNCH_ARGS = ["--disable-dev-shm-usage", "--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=vulkan", "--enable-features=Vulkan"]


# ----------------------------------------------------------------------------- helpers
def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha(v):
    return hashlib.sha256(canon(v).encode("utf-8")).hexdigest()[:16]


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def http_json(url, data=None, timeout=20):
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode("utf-8"), headers=headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return r.status, (json.loads(raw.decode("utf-8")) if raw else None), len(raw)


def provenance():
    out = {"captured_utc": utc_now()}
    for name, url in (("canopy", CANOPY + "/v1/health"), ("cascor", CASCOR + "/v1/health")):
        try:
            st, body, _ = http_json(url, timeout=10)
            keep = ("git_sha", "build_date", "version", "training_active", "active_connections", "status")
            out[name] = {"http": st, **{k: body.get(k) for k in keep if isinstance(body, dict) and k in body}}
        except Exception as e:  # noqa: BLE001 -- provenance must never abort a run
            out[name] = {"error": repr(e)}
    return out


def split_output(output):
    """Dash output string -> tokens. Multi-output is '..a.p...b.q..'; single is 'a.p' (an allow_duplicate output carries '@<hash>')."""
    if output.startswith("..") and output.endswith(".."):
        return output[2:-2].split("...")
    return [output]


def token_base(tok):
    return tok.split("@", 1)[0]


def flat_props(items):
    """[{id, property, value}] (wildcard entries nest as lists) -> {'id.prop': value}."""
    out = {}
    for it in items or []:
        if isinstance(it, list):
            out.update(flat_props(it))
            continue
        if isinstance(it, dict) and "id" in it and "property" in it:
            cid = it["id"] if isinstance(it["id"], str) else canon(it["id"])
            out[f"{cid}.{it['property']}"] = it.get("value")
    return out


def summ(v, limit=600):
    if isinstance(v, list) and (len(v) > 8 or len(canon(v)) > limit):
        return {"_list_len": len(v), "_sha": sha(v)}
    if len(canon(v)) > limit:
        return {"_type": type(v).__name__, "_json_len": len(canon(v)), "_sha": sha(v)}
    return v


def history_rows(payload):
    """Mirror _update_metrics_store_handler's envelope normalisation exactly (history -> data -> list -> [])."""
    if isinstance(payload, dict):
        if isinstance(payload.get("history"), list):
            return payload["history"]
        if isinstance(payload.get("data"), list):
            return payload["data"]
        return []
    if isinstance(payload, list):
        return payload
    return []


def row_marks(rows):
    """A human-checkable fingerprint of a history list: length and first/last row identity."""
    if not isinstance(rows, list) or not rows:
        return {"len": len(rows) if isinstance(rows, list) else None}
    first, last = rows[0], rows[-1]
    pick = lambda r: {k: r.get(k) for k in ("epoch", "phase", "timestamp")} if isinstance(r, dict) else r  # noqa: E731
    return {"len": len(rows), "first": pick(first), "last": pick(last)}


def classify(rec, comp_id, prop):
    """-> (class, value, why). class is carried | no_update | unparseable | pending."""
    if rec.get("pending"):
        return "pending", None, "no_response_before_capture_end"
    if rec.get("failure"):
        return "unparseable", None, "request_failed:" + str(rec["failure"])
    st = rec.get("status")
    if st == 204:
        return "no_update", None, "http_204_prevent_update"
    if st != 200:
        return "unparseable", None, f"http_{st}"
    resp = rec.get("resp")
    if not isinstance(resp, dict) or not isinstance(resp.get("response"), dict):
        return "unparseable", None, "no_response_map"
    comp = resp["response"].get(comp_id)
    if not isinstance(comp, dict) or prop not in comp:
        return "no_update", None, "id_absent_from_response_map"
    return "carried", comp[prop], "id_in_response_map"


# ----------------------------------------------------------------------------- wire capture
class Wire:
    """Passive capture of every POST /_dash-update-component (request body + response)."""

    def __init__(self, t0):
        self.t0 = t0
        self.seq = 0
        self.inflight = {}
        self.rows = []

    def _t(self):
        return round(time.time() - self.t0, 3)

    def on_request(self, req):
        if UPDATE_PATH not in req.url or req.method != "POST":
            return
        self.seq += 1
        raw = req.post_data or ""
        try:
            body = json.loads(raw)
        except Exception:  # noqa: BLE001
            body = None
        self.inflight[id(req)] = (req, {"seq": self.seq, "t_req_seen": self._t(), "body": body, "req_bytes": len(raw)})

    def _timing(self, req, rec):
        try:
            tm = req.timing
            if tm and tm.get("startTime", -1) > 0:
                rec["t_req"] = round(tm["startTime"] / 1000.0 - self.t0, 3)
                if tm.get("responseEnd", -1) >= 0:
                    rec["t_done"] = round((tm["startTime"] + tm["responseEnd"]) / 1000.0 - self.t0, 3)
        except Exception:  # noqa: BLE001
            pass
        rec.setdefault("t_req", rec["t_req_seen"])

    def on_finished(self, req):
        # NOT popped until the body is in hand: resp.body() yields to the dispatcher, and a record popped
        # before it would be invisible to the main greenlet (in neither inflight nor rows) meanwhile.
        ent = self.inflight.get(id(req))
        if not ent:
            return
        rec = ent[1]
        rec["t_done_seen"] = self._t()
        try:
            resp = req.response()
            rec["status"] = resp.status if resp else None
            raw = resp.body() if resp else b""
            rec["resp_bytes"] = len(raw)
            if rec["status"] == 200 and raw:
                try:
                    rec["resp"] = json.loads(raw)
                except Exception as e:  # noqa: BLE001
                    rec["resp_parse_error"] = repr(e)
        except BaseException as e:  # noqa: BLE001 -- CancelledError at teardown is a BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            rec["resp_error"] = repr(e)
        self._timing(req, rec)
        rec.setdefault("t_done", rec["t_done_seen"])
        self.inflight.pop(id(req), None)  # pop + append with no yield between them: atomic to the main greenlet
        self.rows.append(rec)

    def on_failed(self, req):
        ent = self.inflight.get(id(req))
        if not ent:
            return
        rec = ent[1]
        rec["t_done_seen"] = self._t()
        rec["failure"] = req.failure
        self._timing(req, rec)
        rec.setdefault("t_done", rec["t_done_seen"])
        self.inflight.pop(id(req), None)
        self.rows.append(rec)

    def all_rows(self):
        pend = [dict(v[1], pending=True) for v in self.inflight.values()]
        return sorted(self.rows + pend, key=lambda r: r["seq"])

    def latest_store_state_len(self):
        """Length of the client's store copy as sent in the newest REST-poll request's State."""
        best = None
        for rec in list(self.rows) + [v[1] for v in self.inflight.values()]:
            body = rec.get("body") or {}
            if STORE_TOKEN in split_output(body.get("output", "")):
                if best is None or rec["seq"] > best["seq"]:
                    best = rec
        if best is None:
            return None, None
        st = flat_props((best.get("body") or {}).get("state")).get(STORE_TOKEN)
        return (len(st) if isinstance(st, list) else None), best["seq"]


# ----------------------------------------------------------------------------- page helpers
GL_JS = """() => {
  const c = document.createElement('canvas');
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  if (!gl) return {webgl: null};
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  return {webgl: (typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext) ? 'webgl2' : 'webgl',
          vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
          renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)};
}"""

DOM_JS = """() => {
  const q = s => document.querySelector(s);
  const thumbs = document.querySelectorAll('#metrics-panel-replay-slider [role="slider"]');
  const thumb = thumbs[0];
  const pos = q('#metrics-panel-replay-position');
  const play = q('#metrics-panel-replay-play');
  const ctr = q('#metrics-panel-replay-controls');
  const wsc = q('#metrics-panel-window-size-container');
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const tm = tabs.find(e => (e.textContent || '').trim() === 'Training Metrics');
  const n = id => document.querySelectorAll('[id="' + id + '"]').length;
  return {
    t_page_ms: Math.round(performance.now()),
    slider_aria_valuenow: thumb ? thumb.getAttribute('aria-valuenow') : null,
    slider_thumbs: thumbs.length,
    position_text: pos ? pos.textContent : null,
    play_text: play ? play.textContent : null,
    replay_controls_display: ctr ? getComputedStyle(ctr).display : null,
    window_size_container_display: wsc ? getComputedStyle(wsc).display : null,
    training_metrics_tab_selected: tm ? tm.getAttribute('aria-selected') : null,
    dom_id_counts: {slider: n('metrics-panel-replay-slider'), position: n('metrics-panel-replay-position'), play: n('metrics-panel-replay-play')},
  };
}"""

REDUX_JS = """() => {
  const st = window.store && window.store.getState && window.store.getState();
  if (!st) return {available: false};
  const get = (id) => {
    const p = st.paths && st.paths.strs ? st.paths.strs[id] : undefined;
    if (!p) return null;
    let n = st.layout;
    for (const k of p) { if (n == null) break; n = n[k]; }
    return (n && n.props) ? n.props : null;
  };
  const ms = get('metrics-panel-metrics-store');
  const sl = get('metrics-panel-replay-slider');
  const ri = get('metrics-panel-replay-interval');
  const rs = get('metrics-panel-replay-state');
  const pos = get('metrics-panel-replay-position');
  const pb = get('metrics-panel-replay-play');
  const cb = st.callbacks || {};
  const queues = {};
  for (const L of ['requested', 'prioritized', 'blocked', 'executing', 'watched', 'executed', 'stored']) {
    const arr = cb[L] || [];
    queues[L] = {n: arr.length,
                 relevant: arr.map(c => c && c.callback && c.callback.output)
                              .filter(o => typeof o === 'string' && (o.indexOf('replay') >= 0 || o.indexOf('metrics-panel-metrics-store') >= 0))};
  }
  queues.completed = cb.completed;
  // duplicate-instance census over the renderer layout (skip heavy data props)
  const want = new Set(['metrics-panel-metrics-store', 'metrics-panel-replay-state', 'metrics-panel-replay-slider', 'metrics-panel-replay-position']);
  const counts = {};
  const stack = [st.layout];
  let visited = 0;
  while (stack.length && visited < 200000) {
    const n = stack.pop(); visited++;
    if (n == null || typeof n !== 'object') continue;
    if (Array.isArray(n)) { for (const c of n) stack.push(c); continue; }
    const id = n.props && n.props.id;
    if (typeof id === 'string' && want.has(id)) counts[id] = (counts[id] || 0) + 1;
    const src = n.props ? n.props : n;
    for (const k of Object.keys(src)) {
      if (k === 'data' || k === 'figure' || k === 'options') continue;
      const v = src[k];
      if (v && typeof v === 'object') stack.push(v);
    }
  }
  return {available: true,
          metrics_store_data: ms ? ms.data : undefined,
          replay_state: rs ? rs.data : undefined,
          slider: sl ? {value: sl.value, max: sl.max, drag_value: sl.drag_value} : null,
          replay_interval: ri ? {disabled: ri.disabled, interval: ri.interval, n_intervals: ri.n_intervals} : null,
          position_children: pos ? pos.children : null,
          play_children: pb ? pb.children : null,
          callbacks: queues,
          layout_id_counts: counts};
}"""


def redux_snapshot(page):
    try:
        snap = page.evaluate(REDUX_JS)
    except Exception as e:  # noqa: BLE001
        return {"error": repr(e)}
    data = snap.pop("metrics_store_data", None) if isinstance(snap, dict) else None
    if isinstance(snap, dict) and snap.get("available"):
        snap["metrics_store"] = {"sha": sha(data), **row_marks(data)} if isinstance(data, list) else {"value": summ(data)}
        snap["_metrics_store_value"] = data
    return snap


def dom_snapshot(page, label, t0, wire, redux=False):
    out = {"label": label, "t": round(time.time() - t0, 3), "wire_seq": wire.seq}
    try:
        out["dom"] = page.evaluate(DOM_JS)
    except Exception as e:  # noqa: BLE001
        out["dom_error"] = repr(e)
    if redux:
        out["redux"] = redux_snapshot(page)
    n, seq = wire.latest_store_state_len()
    out["client_store_len_from_latest_poll_state"] = {"len": n, "poll_seq": seq}
    return out


def launch(p, headed):
    return p.chromium.launch(headless=not headed, args=LAUNCH_ARGS)


WELCOMED_INIT = "try { localStorage.setItem('juniper_canopy_welcomed', '1'); } catch (e) {}"


def open_page(browser, t0, suppress_welcome=True):
    ctx = browser.new_context(viewport={"width": 1600, "height": 1100})
    if suppress_welcome:
        # The first-visit "Welcome to Juniper Canopy" modal (welcome-modal) opens whenever this flag is
        # absent and intercepts every pointer event. Its own "Get Started" button does nothing but set
        # this flag (clientside callback, dashboard_manager.py ~:3713), so seeding it = a returning user.
        ctx.add_init_script(WELCOMED_INIT)
    page = ctx.new_page()
    gpu = page.evaluate(GL_JS)
    wire = Wire(t0)
    console = []
    page.on("request", wire.on_request)
    page.on("requestfinished", wire.on_finished)
    page.on("requestfailed", wire.on_failed)
    page.on("console", lambda m: console.append({"t": round(time.time() - t0, 3), "type": m.type, "text": m.text[:400]}) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console.append({"t": round(time.time() - t0, 3), "type": "pageerror", "text": str(e)[:400]}))
    return ctx, page, wire, console, gpu


def activate_training_metrics(page, t0):
    page.goto(DASH, wait_until="domcontentloaded", timeout=180000)
    tab = page.get_by_role("tab", name="Training Metrics", exact=True)
    tab.first.wait_for(state="visible", timeout=180000)
    before = {"aria_selected": tab.first.get_attribute("aria-selected"), "class": tab.first.get_attribute("class")}
    t_click = round(time.time() - t0, 3)
    tab.first.click(timeout=60000)
    after = {"aria_selected": tab.first.get_attribute("aria-selected"), "class": tab.first.get_attribute("class")}
    dialogs = page.evaluate(MODAL_JS)
    return {"t_tab_click": t_click, "before": before, "after": after, "tab_matches": tab.count(),
            "open_dialogs_after_click": [d for d in dialogs if d.get("visible")]}


MODAL_JS = """() => [...document.querySelectorAll('[role="dialog"], .modal.show')].map(d => ({
  cls: d.className, id: d.id || null, visible: !!(d.offsetWidth || d.offsetHeight),
  title: (d.querySelector('.modal-title') || {}).textContent || null,
  text: (d.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 600),
  buttons: [...d.querySelectorAll('button')].map(b => ({id: b.id || null, text: (b.textContent || '').trim().slice(0, 60), cls: b.className}))
}))"""


def step_modal(args):
    """Read-only: what dialog is open on a fresh load? Nothing is clicked."""
    from playwright.sync_api import sync_playwright

    t0 = time.time()
    with sync_playwright() as p:
        browser = launch(p, args.headed)
        ctx, page, wire, console, gpu = open_page(browser, t0, suppress_welcome=False)
        page.goto(DASH, wait_until="domcontentloaded", timeout=180000)
        seen = []
        for i in range(12):
            page.wait_for_timeout(2500)
            seen.append({"t": round(time.time() - t0, 1), "dialogs": page.evaluate(MODAL_JS)})
        ctx.close()
        browser.close()
    write_json("modal_probe", {"script": script_block(args), "provenance": provenance(), "samples": seen, "webgl_about_blank": gpu})
    print(json.dumps(seen[-1], indent=1)[:3000])


def pump(page, seconds, step_ms=1000, on_tick=None):
    end = time.time() + seconds
    while time.time() < end:
        page.wait_for_timeout(min(step_ms, max(1, int((end - time.time()) * 1000))))
        if on_tick:
            on_tick()


def served_deps():
    st, deps, _ = http_json(DASH + "_dash-dependencies", timeout=30)
    return deps


def writers_of(deps, token_base_name):
    out = []
    for cb in deps:
        toks = split_output(cb.get("output", ""))
        if any(token_base(t) == token_base_name for t in toks):
            out.append({
                "output": cb.get("output"),
                "inputs": [f"{i['id']}.{i['property']}" for i in cb.get("inputs", [])],
                "state": [f"{s['id']}.{s['property']}" for s in cb.get("state", [])],
                "prevent_initial_call": cb.get("prevent_initial_call"),
                "clientside": bool(cb.get("clientside_function")),
                "websocket": cb.get("websocket"),
            })
    return out


def write_json(name, payload):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{PREFIX}{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO)}")
    return path


def script_block(args):
    return {"path": str(Path(__file__).resolve().relative_to(REPO)), "sha256_16": file_sha(__file__), "argv": sys.argv[1:], "step": args.step}


# ----------------------------------------------------------------------------- step: deps
def step_deps(args):
    deps = served_deps()
    with urllib.request.urlopen(DASH, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    cfg = {}
    marker = '<script id="_dash-config" type="application/json">'
    if marker in html:
        raw = html.split(marker, 1)[1].split("</script>", 1)[0]
        try:
            cfg = json.loads(raw)
        except Exception as e:  # noqa: BLE001
            cfg = {"parse_error": repr(e)}
    payload = {
        "script": script_block(args),
        "provenance": provenance(),
        "callbacks_total": len(deps),
        "any_callback_websocket_flag": sorted({str(cb.get("websocket")) for cb in deps}),
        "dash_config": {k: cfg.get(k) for k in ("dash_version", "validate_callbacks", "websocket", "serve_locally", "requests_pathname_prefix", "ui")},
        "dash_config_has_websocket_key": "websocket" in cfg,
        "writers_of_metrics_store": writers_of(deps, STORE_TOKEN),
        "writers_of_replay_state": writers_of(deps, REPLAY_STATE_TOKEN),
        "readers_of_replay_state_as_input": [cb.get("output") for cb in deps if any(f"{i['id']}.{i['property']}" == REPLAY_STATE_TOKEN for i in cb.get("inputs", []))],
        "callbacks_with_replay_slider_value_as_input": [cb.get("output") for cb in deps if any(f"{i['id']}.{i['property']}" == "metrics-panel-replay-slider.value" for i in cb.get("inputs", []))],
    }
    write_json("deps", payload)


# ----------------------------------------------------------------------------- step: claim1
class RefFetcher(threading.Thread):
    """Background GETs of the handler's own URL, so the main greenlet keeps pumping Playwright events."""

    def __init__(self, t0, period=5.0):
        super().__init__(daemon=True)
        self.t0, self.period = t0, period
        self.limits = {500}
        self.refs = []
        self.stop_evt = threading.Event()

    def fetch(self, limit):
        t = round(time.time() - self.t0, 3)
        try:
            st, body, nbytes = http_json(f"{CANOPY}/api/metrics/history?limit={limit}", timeout=20)
            rows = history_rows(body)
            self.refs.append({"t": t, "limit": limit, "http": st, "bytes": nbytes, "sha": sha(rows), **row_marks(rows), "_val": rows})
        except Exception as e:  # noqa: BLE001
            self.refs.append({"t": t, "limit": limit, "error": repr(e)})

    def run(self):
        while not self.stop_evt.is_set():
            for lim in sorted(self.limits):
                self.fetch(lim)
            self.stop_evt.wait(self.period)

    def nearest(self, limit, t):
        cands = [r for r in self.refs if r.get("limit") == limit and "_val" in r]
        if not cands:
            return None
        return min(cands, key=lambda r: abs(r["t"] - t))


def attribute_poll(rec, refs, modulus=None):
    body = rec.get("body") or {}
    inputs, states = flat_props(body.get("inputs")), flat_props(body.get("state"))
    state_val = states.get(STORE_TOKEN)
    mode_state = inputs.get("metrics-panel-display-mode-store.data")
    mode_state = mode_state if isinstance(mode_state, dict) else {}
    mode = mode_state.get("mode", "window")
    wsz = mode_state.get("window_size", 100)  # mirrors the handler exactly (no `or` default)
    full = mode in ("full", "hidden_units")
    limit = 0 if full else wsz
    ws_live = bool(isinstance(states.get("ws-liveness-store.data"), dict) and states["ws-liveness-store.data"].get("metrics_live"))
    cls, val, why = classify(rec, STORE_ID, "data")
    ref = refs.nearest(limit, rec.get("t_req", 0))
    ref_val = ref["_val"] if ref else None
    row = {
        "seq": rec["seq"], "t_req": rec.get("t_req"), "t_done": rec.get("t_done"),
        "latency_s": round(rec["t_done"] - rec["t_req"], 3) if rec.get("t_done") is not None and rec.get("t_req") is not None else None,
        "trigger": body.get("changedPropIds"), "n_intervals": inputs.get("metrics-store-interval.n_intervals"),
        "mode": mode, "window_size": wsz, "ws_live": ws_live,
        "state": {"sha": sha(state_val), **row_marks(state_val)} if isinstance(state_val, list) else {"value": summ(state_val)},
        "class": cls, "why": why, "http": rec.get("status"), "resp_bytes": rec.get("resp_bytes"),
    }
    if cls == "carried":
        row["carried"] = {"sha": sha(val), **row_marks(val)} if isinstance(val, list) else {"value": summ(val)}
        row["carried_equals_state_py_eq"] = (isinstance(state_val, list) and val == state_val)
        row["carried_equals_ref_py_eq"] = (ref_val is not None and val == ref_val)
    row["state_equals_ref_py_eq"] = (ref_val is not None and isinstance(state_val, list) and state_val == ref_val)
    row["ref"] = {"t": ref["t"], "limit": limit, "sha": ref["sha"], "len": ref.get("len")} if ref else None
    # Branch attribution, in the handler's own order (_update_metrics_store_handler, canopy 9bffaba1).
    if cls == "carried":
        row["branch"] = "ANOMALY carried value == State" if row["carried_equals_state_py_eq"] else "write (fetched list != State)"
    elif cls == "no_update":
        if ws_live and not full:
            row["branch"] = "ws_live demotion (REST fetch skipped) -- NOT Stage 2"
        elif full and modulus and isinstance(row["n_intervals"], int) and row["n_intervals"] % modulus != 0:
            row["branch"] = "full-history modulus gate -- NOT Stage 2"
        elif ref_val is None:
            row["branch"] = "unattributable (no reference fetch)"
        elif isinstance(state_val, list) and state_val == ref_val and ref_val:
            row["branch"] = "Stage 2 identity suppression (State == fetched, fetched non-empty)"
        elif not ref_val and state_val:
            row["branch"] = "empty-guard -- NOT Stage 2"
        else:
            row["branch"] = "UNEXPLAINED no_update (error branch, or reference drift)"
    else:
        row["branch"] = "unparseable"
    return row


def ws_append_row(rec, tok):
    body = rec.get("body") or {}
    inputs, states = flat_props(body.get("inputs")), flat_props(body.get("state"))
    cls, val, why = classify(rec, STORE_ID, "data")
    buf = inputs.get("ws-metrics-buffer.data")
    events = (buf or {}).get("events") if isinstance(buf, dict) else None
    return {"seq": rec["seq"], "t_req": rec.get("t_req"), "token": tok, "class": cls, "why": why,
            "buffer_events": len(events) if isinstance(events, list) else None,
            "carried": ({"sha": sha(val), **row_marks(val)} if isinstance(val, list) else summ(val)) if cls == "carried" else None,
            "state_len": len(states.get(STORE_TOKEN)) if isinstance(states.get(STORE_TOKEN), list) else None}


def summarise_polls(polls, lo=None, hi=None):
    sel = [r for r in polls if (lo is None or (r["t_req"] or 0) >= lo) and (hi is None or (r["t_req"] or 0) < hi)]
    c = Counter(r["class"] for r in sel)
    b = Counter(r["branch"] for r in sel)
    carried_payloads = Counter(r["carried"]["sha"] for r in sel if r["class"] == "carried" and "sha" in (r.get("carried") or {}))
    state_shas = Counter(r["state"].get("sha") for r in sel)
    return {"window_s": [lo, hi], "responses": len(sel), "by_class": dict(c), "by_branch": dict(b),
            "distinct_carried_payload_shas": dict(carried_payloads), "distinct_state_shas_sent": dict(state_shas)}


def step_claim1(args):
    from playwright.sync_api import sync_playwright

    prov_before = provenance()
    deps = served_deps()
    store_writers = writers_of(deps, STORE_TOKEN)
    t0 = time.time()
    refs = RefFetcher(t0)
    snaps, phases = [], {}
    with sync_playwright() as p:
        browser = launch(p, args.headed)
        ctx, page, wire, console, gpu = open_page(browser, t0)
        refs.start()
        tab = activate_training_metrics(page, t0)
        t_tab = tab["t_tab_click"]
        phases["idle"] = [t_tab, t_tab + args.seconds]
        snaps.append(dom_snapshot(page, "idle_start", t0, wire, args.redux))

        def track_limits():
            for rec in wire.rows[-5:]:
                body = rec.get("body") or {}
                if STORE_TOKEN in split_output(body.get("output", "")):
                    ms = flat_props(body.get("inputs")).get("metrics-panel-display-mode-store.data")
                    if isinstance(ms, dict):
                        refs.limits.add(0 if ms.get("mode") in ("full", "hidden_units") else ms.get("window_size", 100))

        third = args.seconds / 3.0
        for k in (1, 2, 3):
            pump(page, third, on_tick=track_limits)
            snaps.append(dom_snapshot(page, f"idle_{int(k * third)}s", t0, wire, args.redux))

        if args.control:
            # POSITIVE CONTROL: a genuinely different fetch must be CARRIED, and then suppressed on the new value.
            refs.limits.add(10)
            t_ctl = round(time.time() - t0, 3)
            box = page.locator("#metrics-panel-window-size")
            box.fill("10", timeout=60000)
            box.press("Tab", timeout=60000)
            phases["control_window_10"] = [t_ctl, t_ctl + args.control_seconds]
            pump(page, args.control_seconds, on_tick=track_limits)
            snaps.append(dom_snapshot(page, "control_end", t0, wire, args.redux))

        page.wait_for_timeout(1500)
        rows = wire.all_rows()
        refs.stop_evt.set()
        ctx.close()
        browser.close()
    refs.join(timeout=30)

    polls, appends, other_outputs = [], [], Counter()
    for rec in rows:
        body = rec.get("body") or {}
        toks = split_output(body.get("output", ""))
        hits = [t for t in toks if token_base(t) == STORE_TOKEN]
        if not hits:
            other_outputs[body.get("output", "?")] += 1
            continue
        for tok in hits:
            if tok == STORE_TOKEN:
                polls.append(attribute_poll(rec, refs))
            else:
                appends.append(ws_append_row(rec, tok))

    # redux instrument vs request-State instrument: do they agree on the client copy?
    agreement = []
    for s in snaps:
        rx = s.get("redux") or {}
        mv = rx.pop("_metrics_store_value", None)
        if rx.get("available") and isinstance(mv, list):
            later = [r for r in polls if (r["t_req"] or 0) >= s["t"]]
            nxt = later[0] if later else None
            agreement.append({"snapshot": s["label"], "redux_store_sha": sha(mv), "redux_len": len(mv),
                              "next_poll_seq": nxt["seq"] if nxt else None, "next_poll_state_sha": nxt["state"].get("sha") if nxt else None})

    ref_summary = Counter((r.get("limit"), r.get("sha"), r.get("len")) for r in refs.refs if "sha" in r)
    first_carried_t = next((r["t_req"] for r in polls if r["class"] == "carried"), None)
    idle_lo, idle_hi = phases["idle"]
    payload = {
        "script": script_block(args),
        "provenance_before": prov_before,
        "provenance_after": provenance(),
        "browser": {"launch_args": LAUNCH_ARGS, "headless": not args.headed, "webgl_about_blank": gpu},
        "served_writers_of_metrics_store": store_writers,
        "tab_activation": tab,
        "phases_s": phases,
        "summary": {
            "rest_poll_all_capture": summarise_polls(polls),
            "rest_poll_idle_window": summarise_polls(polls, idle_lo, idle_hi),
            "rest_poll_first_60s_after_tab": summarise_polls(polls, idle_lo, idle_lo + 60),
            "rest_poll_idle_after_first_fill": summarise_polls(polls, first_carried_t + 0.001, idle_hi) if first_carried_t is not None else None,
            "rest_poll_control_window": summarise_polls(polls, *phases["control_window_10"]) if "control_window_10" in phases else None,
            "ws_append_writer": {"responses": len(appends), "by_class": dict(Counter(r["class"] for r in appends))},
            "reference_fetches_distinct": [{"limit": k[0], "sha": k[1], "len": k[2], "n": v} for k, v in ref_summary.items()],
            "reference_fetch_errors": [r for r in refs.refs if "error" in r],
            "all_update_component_requests": len(rows),
            "requests_by_output_top": other_outputs.most_common(25),
        },
        "rest_poll_rows": polls,
        "ws_append_rows": appends,
        "redux_vs_state_agreement": agreement,
        "snapshots": snaps,
        "console_errors_warnings": console[:200],
    }
    write_json("claim1_idle" + (f"_{args.tag}" if args.tag else ""), payload)
    print(json.dumps(payload["summary"], indent=1, default=str)[:6000])


# ----------------------------------------------------------------------------- step: claim2
def replay_rows(rows):
    out = []
    for rec in rows:
        body = rec.get("body") or {}
        raw_out = body.get("output", "")
        toks = split_output(raw_out)
        inputs, states = flat_props(body.get("inputs")), flat_props(body.get("state"))
        role = []
        if any(token_base(t) == REPLAY_STATE_TOKEN for t in toks):
            role.append("output")
        if REPLAY_STATE_TOKEN in inputs:
            role.append("input")
        if REPLAY_STATE_TOKEN in states:
            role.append("state")
        if not role:
            continue
        cls, val, why = classify(rec, REPLAY_STATE_ID, "data")
        resp_map = (rec.get("resp") or {}).get("response") if isinstance(rec.get("resp"), dict) else None
        ms_state = states.get(STORE_TOKEN)
        ms_input = inputs.get(STORE_TOKEN)
        out.append({
            "seq": rec["seq"], "t_req": rec.get("t_req"), "t_done": rec.get("t_done"), "http": rec.get("status"),
            "output": raw_out, "role_of_replay_state": role, "trigger": body.get("changedPropIds"),
            "inputs": {k: summ(v) for k, v in inputs.items()},
            "state": {k: summ(v) for k, v in states.items()},
            "metrics_store_len_seen_by_callback": (len(ms_state) if isinstance(ms_state, list) else (len(ms_input) if isinstance(ms_input, list) else None)),
            "replay_state_write": {"class": cls, "why": why, "value": val} if "output" in role else None,
            "response_map": {cid: {p: summ(v) for p, v in props.items()} for cid, props in resp_map.items()} if isinstance(resp_map, dict) else None,
            "failure": rec.get("failure"),
        })
    return out


def phase_counts(rows, phases):
    out = {}
    for name, (lo, hi) in phases.items():
        sel = [r for r in rows if lo <= (r.get("t_req") or 0) < hi]
        c = Counter((r.get("body") or {}).get("output", "?") for r in sel)
        out[name] = {"requests": len(sel), "by_output": c.most_common(40)}
    return out


def step_claim2(args):
    from playwright.sync_api import sync_playwright

    prov_before = provenance()
    deps = served_deps()
    t0 = time.time()
    snaps, phases, notes = [], {}, []
    with sync_playwright() as p:
        browser = launch(p, args.headed)
        ctx, page, wire, console, gpu = open_page(browser, t0)
        tab = activate_training_metrics(page, t0)
        snaps.append(dom_snapshot(page, "after_tab", t0, wire, args.redux))

        # Readiness: the CLIENT's store copy, read from the State of the newest REST-poll request.
        t_wait = round(time.time() - t0, 3)
        ready = None
        deadline = time.time() + args.ready_timeout
        while time.time() < deadline:
            page.wait_for_timeout(1000)
            n, seq = wire.latest_store_state_len()
            if n:
                ready = {"t": round(time.time() - t0, 3), "client_store_len": n, "poll_seq": seq}
                break
        phases["wait_store"] = [t_wait, round(time.time() - t0, 3)]
        snaps.append(dom_snapshot(page, "store_ready" if ready else "store_NEVER_ready", t0, wire, args.redux))
        if not ready:
            notes.append("client store never non-empty within ready_timeout: the row cannot be exercised -> BLOCKED")

        if ready:
            thumb = page.locator('#metrics-panel-replay-slider [role="slider"]').first
            # Phase A: keyboard ArrowRight x10 on the focused thumb.
            t_a = round(time.time() - t0, 3)
            try:
                thumb.scroll_into_view_if_needed(timeout=60000)
                thumb.focus(timeout=60000)
                for _ in range(10):
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(250)
            except Exception as e:  # noqa: BLE001
                notes.append(f"slider keyboard phase error: {e!r}")
            for lab, wait in (("keys+0.5s", 0.5), ("keys+3s", 2.5), ("keys+8s", 5), ("keys+15s", 7)):
                pump(page, wait)
                snaps.append(dom_snapshot(page, lab, t0, wire, args.redux))
            phases["slider_keys"] = [t_a, round(time.time() - t0, 3)]

            # Phase B: a real mouse drag of the thumb (the row's literal interaction).
            t_b = round(time.time() - t0, 3)
            try:
                tb = thumb.bounding_box(timeout=60000)
                track = page.locator("#metrics-panel-replay-slider .dash-slider-root").first.bounding_box(timeout=60000)
                cx, cy = tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] / 2
                page.mouse.move(cx, cy)
                page.mouse.down()
                page.mouse.move(cx + 0.3 * track["width"], cy, steps=12)
                page.mouse.up()
                notes.append(f"drag from x={cx:.0f} by {0.3 * track['width']:.0f}px (track width {track['width']:.0f})")
            except Exception as e:  # noqa: BLE001
                notes.append(f"slider drag phase error: {e!r}")
            for lab, wait in (("drag+0.5s", 0.5), ("drag+5s", 4.5), ("drag+12s", 7)):
                pump(page, wait)
                snaps.append(dom_snapshot(page, lab, t0, wire, args.redux))
            phases["slider_drag"] = [t_b, round(time.time() - t0, 3)]

            # Phase C: the play button (data-independent toggle, M-METRICS-13's control).
            t_c = round(time.time() - t0, 3)
            try:
                page.locator("#metrics-panel-replay-play").click(timeout=60000)
            except Exception as e:  # noqa: BLE001
                notes.append(f"play click error: {e!r}")
            for lab, wait in (("play+0.5s", 0.5), ("play+3s", 2.5), ("play+8s", 5), ("play+20s", 12)):
                pump(page, wait)
                snaps.append(dom_snapshot(page, lab, t0, wire, args.redux))
            phases["play_click"] = [t_c, round(time.time() - t0, 3)]

        # Phase D: POSITIVE CONTROL -- M-METRICS-19 (PASS row): a server callback whose output must land in the DOM.
        t_d = round(time.time() - t0, 3)
        ctl = {"t": t_d}
        try:
            page.locator("#metrics-panel-display-mode label", has_text="Full History").first.click(timeout=60000)
            ctl["hidden_after_s"] = None
            for i in range(30):
                page.wait_for_timeout(1000)
                d = page.evaluate("() => { const e = document.querySelector('#metrics-panel-window-size-container'); return e ? getComputedStyle(e).display : null; }")
                if d == "none":
                    ctl["hidden_after_s"] = i + 1
                    break
            page.locator("#metrics-panel-display-mode label", has_text="Sliding Window").first.click(timeout=60000)
            ctl["shown_again_after_s"] = None
            for i in range(30):
                page.wait_for_timeout(1000)
                d = page.evaluate("() => { const e = document.querySelector('#metrics-panel-window-size-container'); return e ? getComputedStyle(e).display : null; }")
                if d and d != "none":
                    ctl["shown_again_after_s"] = i + 1
                    break
        except Exception as e:  # noqa: BLE001
            ctl["error"] = repr(e)
        phases["positive_control_display_mode"] = [t_d, round(time.time() - t0, 3)]
        snaps.append(dom_snapshot(page, "final", t0, wire, args.redux))
        page.wait_for_timeout(1500)
        rows = wire.all_rows()
        ctx.close()
        browser.close()

    for s in snaps:
        rx = s.get("redux") or {}
        rx.pop("_metrics_store_value", None)
    rrows = replay_rows(rows)
    ctl_rows = []
    for rec in rows:
        body = rec.get("body") or {}
        if "metrics-panel-display-mode-store.data" in [token_base(t) for t in split_output(body.get("output", ""))]:
            cls, val, why = classify(rec, "metrics-panel-window-size-container", "style")
            ctl_rows.append({"seq": rec["seq"], "t_req": rec.get("t_req"), "http": rec.get("status"), "trigger": body.get("changedPropIds"), "container_style_write": cls, "value": val})
    writes = [r for r in rrows if "output" in r["role_of_replay_state"]]
    payload = {
        "script": script_block(args),
        "provenance_before": prov_before,
        "provenance_after": provenance(),
        "browser": {"launch_args": LAUNCH_ARGS, "headless": not args.headed, "webgl_about_blank": gpu},
        "served_writers_of_replay_state": writers_of(deps, REPLAY_STATE_TOKEN),
        "tab_activation": tab,
        "store_ready": ready,
        "phases_s": phases,
        "notes": notes,
        "summary": {
            "requests_naming_replay_state": len(rrows),
            "requests_WRITING_replay_state": len(writes),
            "replay_state_writes_by_class": dict(Counter((r["replay_state_write"] or {}).get("class") for r in writes)),
            "requests_naming_replay_state_by_output": dict(Counter(r["output"] for r in rrows)),
            "positive_control_display_mode": ctl,
            "positive_control_wire_rows": ctl_rows,
            "all_update_component_requests": len(rows),
        },
        "phase_request_counts": phase_counts(rows, phases),
        "replay_rows": rrows,
        "snapshots": snaps,
        "console_errors_warnings": console[:200],
    }
    write_json("claim2_replay" + (f"_{args.tag}" if args.tag else ""), payload)
    print(json.dumps({k: payload[k] for k in ("store_ready", "phases_s", "notes", "summary")}, indent=1, default=str)[:6000])
    for s in snaps:
        d = s.get("dom") or {}
        print(f"{s['label']:>16} t={s['t']:7.1f} slider={d.get('slider_aria_valuenow')!s:>5} pos={d.get('position_text')!r:>10} play={d.get('play_text')!r} ctrl={d.get('replay_controls_display')} store_len(State)={s['client_store_len_from_latest_poll_state']['len']}")


# ----------------------------------------------------------------------------- step: server-eval
def step_server_eval(args):
    deps = served_deps()
    hrc = next(cb for cb in deps if split_output(cb["output"])[0] == REPLAY_STATE_TOKEN and any(i["id"] == "metrics-panel-replay-play" for i in cb.get("inputs", [])))
    uru = next(cb for cb in deps if "metrics-panel-replay-position.children" in split_output(cb["output"]))
    st, body, _ = http_json(f"{CANOPY}/api/metrics/history?limit=500")
    hist = history_rows(body)
    default_state = {"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None}

    def outputs_of(cb):
        return [{"id": token_base(t).rsplit(".", 1)[0], "property": token_base(t).rsplit(".", 1)[1]} for t in split_output(cb["output"])]

    def call(cb, input_values, changed, state_values):
        req = {
            "output": cb["output"],
            "outputs": outputs_of(cb),
            "inputs": [{"id": i["id"], "property": i["property"], "value": input_values.get(f"{i['id']}.{i['property']}")} for i in cb["inputs"]],
            "changedPropIds": changed,
            "state": [{"id": s["id"], "property": s["property"], "value": state_values.get(f"{s['id']}.{s['property']}")} for s in cb.get("state", [])],
        }
        try:
            code, resp, nbytes = http_json(DASH + UPDATE_PATH, data=req, timeout=30)
            return {"http": code, "response": resp}
        except urllib.error.HTTPError as e:
            return {"http": e.code, "error": e.read().decode("utf-8", "replace")[:400]}

    n = len(hist)
    cases = {}
    cases["slider_value_10"] = call(hrc, {"metrics-panel-replay-slider.value": 10}, ["metrics-panel-replay-slider.value"],
                                    {REPLAY_STATE_TOKEN: default_state, STORE_TOKEN: hist})
    cases["play_click_1"] = call(hrc, {"metrics-panel-replay-play.n_clicks": 1, "metrics-panel-replay-slider.value": 0}, ["metrics-panel-replay-play.n_clicks"],
                                 {REPLAY_STATE_TOKEN: default_state, STORE_TOKEN: hist})
    rs_after_slider = (((cases["slider_value_10"].get("response") or {}).get("response") or {}).get(REPLAY_STATE_ID) or {}).get("data")
    cases["update_replay_ui_after_slider"] = call(uru, {REPLAY_STATE_TOKEN: rs_after_slider, STORE_TOKEN: hist}, [REPLAY_STATE_TOKEN], {})
    cases["update_replay_ui_on_fill_default_state"] = call(uru, {REPLAY_STATE_TOKEN: default_state, STORE_TOKEN: hist}, [STORE_TOKEN], {})
    expected = {
        "slider_value_10": {"current_index": int((10 / 100) * (n - 1)) if n - 1 > 0 else 0, "mode": "paused", "interval_disabled": True},
        "play_click_1": {"mode": "playing", "interval_disabled": False, "interval_ms": 1000},
        "update_replay_ui_on_fill_default_state": {"position": f"0 / {n - 1}"},
    }
    payload = {"script": script_block(args), "provenance": provenance(), "history_rows": n, "history_sha": sha(hist),
               "handle_replay_controls_output": hrc["output"], "update_replay_ui_output": uru["output"],
               "code_derived_expectation": expected, "cases": cases}
    write_json("server_eval", payload)
    print(json.dumps({"history_rows": n, "expected": expected, "cases": cases}, indent=1, default=str)[:4000])


# ----------------------------------------------------------------------------- step: report
def step_report(args):
    """Compact human summary of an artifact this script wrote (--file)."""
    d = json.loads(Path(args.file).read_text(encoding="utf-8"))
    pb, pa = d.get("provenance_before") or d.get("provenance") or {}, d.get("provenance_after") or {}
    print("canopy sha", (pb.get("canopy") or {}).get("git_sha"), "conns before/after", (pb.get("canopy") or {}).get("active_connections"), (pa.get("canopy") or {}).get("active_connections"))
    if "rest_poll_rows" in d:
        for k in ("rest_poll_idle_window", "rest_poll_first_60s_after_tab", "rest_poll_idle_after_first_fill", "rest_poll_control_window"):
            s = d["summary"].get(k)
            if s:
                print(k, s["window_s"], "n", s["responses"], s["by_class"], s["by_branch"], "carried", s["distinct_carried_payload_shas"], "state", s["distinct_state_shas_sent"])
        print("ws_append", d["summary"]["ws_append_writer"], "refs", d["summary"]["reference_fetches_distinct"], "ref errors", len(d["summary"]["reference_fetch_errors"]))
        for r in d["rest_poll_rows"]:
            print(" ", r["seq"], r["t_req"], r["class"], "state_len", r["state"].get("len"), "carried_len", (r.get("carried") or {}).get("len"), r["branch"][:48])
        print("redux_vs_state", json.dumps(d.get("redux_vs_state_agreement")))
    if "replay_rows" in d:
        print("store_ready", d.get("store_ready"), "phases", d.get("phases_s"))
        print("notes", d.get("notes"))
        print("summary", json.dumps(d["summary"], default=str)[:3000])
        for r in d["replay_rows"]:
            print(" ", r["seq"], r["t_req"], r["http"], r["output"][:70], r["role_of_replay_state"], r["trigger"], "store_len", r["metrics_store_len_seen_by_callback"], "write", r["replay_state_write"], "resp", json.dumps(r["response_map"])[:300])
    for s in d.get("snapshots", []):
        dom = s.get("dom") or {}
        rx = s.get("redux") or {}
        print(f"{s['label']:>18} t={s['t']:7.1f} slider={dom.get('slider_aria_valuenow')!s:>5} pos={dom.get('position_text')!r} play={dom.get('play_text')!r} ctrl={dom.get('replay_controls_display')} State_len={s['client_store_len_from_latest_poll_state']['len']}")
        if rx:
            print(f"{'':>18} redux store={rx.get('metrics_store')} replay_state={rx.get('replay_state')} slider={rx.get('slider')} pos={rx.get('position_children')!r} ids={rx.get('layout_id_counts')}")
            print(f"{'':>18} queues={json.dumps(rx.get('callbacks'))}")
    print("console", d.get("console_errors_warnings", [])[:8])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("step", choices=["deps", "modal", "claim1", "claim2", "server-eval", "report"])
    ap.add_argument("--file", help="report: artifact path")
    ap.add_argument("--seconds", type=float, default=90.0, help="claim1: idle census length after tab activation")
    ap.add_argument("--control", action="store_true", help="claim1: append the window-size positive control")
    ap.add_argument("--control-seconds", type=float, default=45.0)
    ap.add_argument("--ready-timeout", type=float, default=180.0, help="claim2: max wait for a non-empty client store")
    ap.add_argument("--redux", action="store_true", help="also read the renderer redux store (read-only)")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    {"deps": step_deps, "modal": step_modal, "claim1": step_claim1, "claim2": step_claim2, "server-eval": step_server_eval, "report": step_report}[args.step](args)


if __name__ == "__main__":
    main()
