#!/usr/bin/env python3
"""
Lane A2 re-creation: does dash-renderer APPLY the responses that carry candidate-metrics-panel-training-state-store.data?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md §2 (Lane A);
         juniper-canopy src/frontend/components/candidate_metrics_panel.py ``fetch_training_state``

Claim under test: with the Candidate Metrics tab active, every response of the writer of
``candidate-metrics-panel-training-state-store.data`` carries a NEW value (``/api/state`` stamps a
per-call ``timestamp``), yet the renderer's copy of the store never changes after mount.

Instruments -- chosen to share nothing with the one that produced the claim:

* WIRE: a raw Chrome DevTools Protocol session on the page (``Network.enable``; request bodies from
  ``requestWillBeSent`` / ``Network.getRequestPostData``; response bodies from
  ``Network.getResponseBody`` after ``loadingFinished``). A request belongs to the writer when a
  WHOLE output token of its ``output`` field (``id.prop``, ``@<sha256>`` suffix stripped) equals the
  subject token.
* RENDERER (primary): a generic walk of ``window.store.getState().layout`` -- every nested object --
  that finds component nodes by ``props.id``. It never consults ``state.paths`` (dash-renderer's own
  id index); that index is read ONCE at the end, as a labelled diagnostic, to compare locations.
* RENDERER (secondary): the committed React fiber tree under ``#react-entry-point``
  (``__reactContainer$<key>.stateNode.current``), reading ``memoizedProps.data`` of the mounted
  ``dcc.Store`` -- what React last rendered, downstream of the layout.
* CONTENT SEARCH: every object anywhere in the layout shaped like an ``/api/state`` payload, with its
  owning component -- a delivered value applied at ANY location is found here.
* APPLY LOG (supplementary): a ``store.subscribe`` listener that re-reads tracked props at the
  location THIS script's walk found and logs every reference/value change.
* POSITIVE CONTROL: the same walk, in the same samples, over (a) every ``dcc.Store`` and (b) every
  ``id.prop`` the wire has carried so far -- a delivered-vs-held table in which the subject is one row.
* FETCH PROBE (supplementary): an init script wraps ``window.fetch`` and ``Response.prototype.json``
  (dash-renderer calls both, ``dash_renderer.dev.js:861`` / ``:939``) to show whether the renderer's
  OWN code received and parsed each body -- "delivered to the network stack" vs "received, then dropped".
* CONTEXT ONLY (not part of the verdict): dash-renderer queue lengths per sample, Interval tick times
  from the apply log, and main-thread long tasks from a ``PerformanceObserver``.

Perturbation check: ``--no-wire --no-apply-log --no-fetch-probe`` drops the CDP session, the subscribe
listener and the wrappers, leaving only the 1 Hz walk and Playwright's own request events.

Pass layout: pass 1 = Candidate Metrics (the claim), pass 2 = Training Metrics (fallback control and the
claim's side statement about ``metrics-panel-training-state-store``), pass 3 = re-entry to Candidate
Metrics. The active tab is read back from the layout at EVERY sample, not assumed from the click.

Read-only toward cascor: it GETs ``/v1/training/status`` for the record and never starts, stops or
PATCHes anything.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-22_laneA2_cdp_store_apply_check.py [--window 60] [--tag run1]
    # perturbation check
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-22_laneA2_cdp_store_apply_check.py --no-wire --no-apply-log --no-fetch-probe \\
        --no-metrics-pass --no-reentry --tag perturbation

Record: reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA2_cdp_store_apply_{run1,
run2_perturbation-nowire-noapplylog,run3_full-with-fetch-probe}.json. The script grew between runs, so
each JSON's ``meta.args`` is the record of what ran: run1 = wire + walk + fiber + content search + apply
log (no long-task observer, no fetch probe); run2 = walk + fiber + content search + long-task observer
only (no CDP session, no apply log, no fetch probe -- it did not exist yet); run3 = everything. cascor
went COMPLETED -> STARTED during run1's pass 1 (another validator's growth window); run2 and run3 were
idle throughout.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from playwright.async_api import async_playwright

CANOPY = "http://127.0.0.1:8051"
CASCOR = "http://127.0.0.1:8202"
DASH_PATH = "/dashboard/"
SUBJECT = "candidate-metrics-panel-training-state-store"
SUBJECT_TOKEN = f"{SUBJECT}.data"
METRICS_STATE = "metrics-panel-training-state-store"
METRICS_STORE = "metrics-panel-metrics-store"
NAMED_CONTROLS = [METRICS_STORE, METRICS_STATE, "training-status-store", "stream-health-store", "candidate-metrics-panel-pool-history-store"]
FIBER_IDS = [METRICS_STATE, METRICS_STORE, "stream-health-store"]
INTERVAL_ID = "candidate-metrics-panel-update-interval"
TABS_ID = "visualization-tabs"
MAX_TRACKED_VALUE_CHARS = 20000
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "reports" / "e2e-canopy-2026-09-02" / "transcripts"

_DUP_SUFFIX = re.compile(r"@[0-9a-f]{64}$")


def output_tokens(output: str) -> list[str]:
    """Split a Dash ``output`` field into whole ``id.prop`` tokens (dash/_utils.py create_callback_id)."""
    if not isinstance(output, str):
        return []
    if output.startswith("..") and output.endswith(".."):
        parts = output[2:-2].split("...")
    else:
        parts = [output]
    return [_DUP_SUFFIX.sub("", p) for p in parts]


def canon(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def http_get_json(url: str, timeout: float = 5.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # nosec B310 - fixed localhost URLs
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 - recorded, not raised
        return {"error": f"{type(e).__name__}: {e}"}


def cascor_summary(obj):
    d = obj.get("data") if isinstance(obj, dict) else None
    if not isinstance(d, dict):
        return obj
    sm = d.get("state_machine") or {}
    mon = d.get("monitor") or {}
    return {
        "state_machine_status": sm.get("status"),
        "phase": sm.get("phase"),
        "training_active": d.get("training_active"),
        "monitor_is_training": mon.get("is_training"),
        "hidden_units": mon.get("current_hidden_units"),
        "snapshot_seq": d.get("snapshot_seq"),
    }


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return {"n": n, "min": round(s[0], 3), "median": round(s[n // 2], 3), "max": round(s[-1], 3), "mean": round(sum(s) / n, 3)}


# --------------------------------------------------------------------------------------------------
# WIRE: raw CDP Network capture
# --------------------------------------------------------------------------------------------------
class Wire:
    def __init__(self):
        self.recs: dict[str, dict] = {}
        self.tasks: set = set()
        self.cdp = None
        self.n_events = Counter()
        self.token_max_chars: dict[str, int] = {}

    def attach(self, cdp):
        self.cdp = cdp
        cdp.on("Network.requestWillBeSent", self._on_req)
        cdp.on("Network.responseReceived", self._on_resp)
        cdp.on("Network.loadingFinished", self._on_done)
        cdp.on("Network.loadingFailed", self._on_fail)

    def trackable_tokens(self):
        return sorted(t for t, n in self.token_max_chars.items() if n <= MAX_TRACKED_VALUE_CHARS and not t.startswith("{"))

    def _spawn(self, coro):
        t = asyncio.get_running_loop().create_task(coro)
        self.tasks.add(t)
        t.add_done_callback(self.tasks.discard)

    def _on_req(self, p):
        req = p.get("request") or {}
        url = (req.get("url") or "").split("?")[0]
        if req.get("method") != "POST" or not url.endswith("/_dash-update-component"):
            return
        self.n_events["dash_request"] += 1
        rid = p["requestId"]
        rec = {"rid": rid, "wall": p.get("wallTime"), "mono": p.get("timestamp"), "status": None, "outcome": "pending"}
        self.recs[rid] = rec
        pd = req.get("postData")
        if pd is None and req.get("postDataEntries"):
            try:
                pd = "".join(base64.b64decode(e.get("bytes", "")).decode("utf-8", "replace") for e in req["postDataEntries"])
            except Exception:  # noqa: BLE001
                pd = None
        if pd is None:
            if req.get("hasPostData"):
                self._spawn(self._fetch_post(rid))
            else:
                rec["req_parse"] = "no_post_data"
        else:
            self._parse_req(rec, pd)

    async def _fetch_post(self, rid):
        rec = self.recs[rid]
        try:
            r = await self.cdp.send("Network.getRequestPostData", {"requestId": rid})
            self._parse_req(rec, r.get("postData", ""))
        except Exception as e:  # noqa: BLE001
            rec["req_parse"] = f"post_unfetched: {e}"[:200]

    @staticmethod
    def _parse_req(rec, pd):
        try:
            body = json.loads(pd)
        except Exception as e:  # noqa: BLE001
            rec["req_parse"] = f"unparsed: {e}"[:200]
            return
        out = body.get("output", "")
        rec["output"] = out
        rec["tokens"] = output_tokens(out)
        # Cross-check the string against the structured ``outputs`` field.
        outs = body.get("outputs")
        outs = outs if isinstance(outs, list) else [outs]
        tok2 = []
        for o in outs:
            if isinstance(o, dict) and isinstance(o.get("id"), str):
                tok2.append(f"{o['id']}.{_DUP_SUFFIX.sub('', str(o.get('property', '')))}")
        rec["tokens_agree"] = sorted(tok2) == sorted(rec["tokens"]) if tok2 else None
        rec["changed"] = body.get("changedPropIds")
        flat = []
        for i in body.get("inputs") or []:
            flat.extend(i if isinstance(i, list) else [i])
        for i in flat:
            if not isinstance(i, dict):
                continue
            if i.get("id") == INTERVAL_ID and i.get("property") == "n_intervals":
                rec["n_intervals"] = i.get("value")
            if i.get("id") == TABS_ID and i.get("property") == "active_tab":
                rec["active_tab_input"] = i.get("value")
        rec["req_parse"] = "ok"

    def _on_resp(self, p):
        rec = self.recs.get(p.get("requestId"))
        if rec is not None:
            rec["status"] = (p.get("response") or {}).get("status")
            rec["mono_resp"] = p.get("timestamp")

    def _on_done(self, p):
        rec = self.recs.get(p.get("requestId"))
        if rec is None:
            return
        rec["mono_done"] = p.get("timestamp")
        if rec.get("status") == 204:
            rec["outcome"] = "prevent_update_204"
            return
        self._spawn(self._fetch_body(p["requestId"]))

    def _on_fail(self, p):
        rec = self.recs.get(p.get("requestId"))
        if rec is not None:
            rec["outcome"] = "failed"
            rec["fail"] = p.get("errorText")
            rec["canceled"] = p.get("canceled")
            rec["mono_done"] = p.get("timestamp")

    async def _fetch_body(self, rid):
        rec = self.recs[rid]
        try:
            r = await self.cdp.send("Network.getResponseBody", {"requestId": rid})
        except Exception as e:  # noqa: BLE001
            rec["outcome"] = "unfetched"
            rec["fetch_err"] = str(e)[:200]
            return
        body = r.get("body", "")
        if r.get("base64Encoded"):
            body = base64.b64decode(body).decode("utf-8", "replace")
        rec["body_bytes"] = len(body)
        try:
            obj = json.loads(body)
        except Exception:  # noqa: BLE001
            rec["outcome"] = "unparsed"
            rec["body_head"] = body[:200]
            return
        resp = obj.get("response") if isinstance(obj, dict) else None
        if not isinstance(resp, dict):
            rec["outcome"] = "unparsed"
            rec["body_head"] = body[:200]
            return
        rec["outcome"] = "ok"
        carried = {}
        for cid, props in resp.items():
            if not isinstance(props, dict):
                continue
            for prop, val in props.items():
                c = canon(val)
                tok = f"{cid}.{prop}"
                ent = {"h": hashlib.sha1(c.encode()).hexdigest()[:12]}
                if isinstance(val, dict) and "timestamp" in val:
                    ent["ts"] = val["timestamp"]
                carried[tok] = ent
                self.token_max_chars[tok] = max(self.token_max_chars.get(tok, 0), len(c))
        rec["carried"] = carried


class PWRequests:
    """--no-wire mode: a request census from Playwright's OWN request events (no bodies, no extra CDP session).

    Used only to test whether this script's CDP capture perturbs what it measures.
    """

    def __init__(self):
        self.recs: dict[str, dict] = {}
        self.tasks: set = set()
        self.n_events = Counter()

    def attach(self, page):
        page.on("request", self._on_req)

    def trackable_tokens(self):
        return []

    def _on_req(self, req):
        if req.method != "POST" or not req.url.split("?")[0].endswith("/_dash-update-component"):
            return
        self.n_events["dash_request"] += 1
        rec = {"rid": f"pw{self.n_events['dash_request']}", "wall": time.time(), "mono": None, "status": None, "outcome": "not_captured"}
        try:
            Wire._parse_req(rec, req.post_data or "")
        except Exception as e:  # noqa: BLE001
            rec["req_parse"] = f"error {e}"[:200]
        self.recs[rec["rid"]] = rec


# --------------------------------------------------------------------------------------------------
# RENDERER: in-page reads (layout walk, fiber walk, content search, apply log)
# --------------------------------------------------------------------------------------------------
JS_LONGTASK_INIT = """(() => {
  try {
    window.__laneA2_longtasks = [];
    new PerformanceObserver((list) => { for (const e of list.getEntries()) { if (window.__laneA2_longtasks.length < 200000) window.__laneA2_longtasks.push([e.startTime, e.duration]); } })
      .observe({type: 'longtask', buffered: true});
  } catch (e) { window.__laneA2_longtasks_error = String(e); }
})();"""

# Supplementary: did the RENDERER'S OWN JS receive and parse each body? dash-renderer calls the global fetch()
# (dash_renderer.dev.js:861) and res.json() on a 200 (:939); wrapping both, before any page script runs,
# separates "delivered to the network stack" from "received and parsed by the renderer".
JS_FETCH_PROBE_INIT = r"""(() => {
  try {
    const SUBJECT = 'candidate-metrics-panel-training-state-store';
    const REC = window.__laneA2_fetch = [];
    const of = window.fetch;
    window.fetch = function (input, init) {
      const url = (typeof input === 'string') ? input : ((input && input.url) || '');
      const p = of.apply(this, arguments);
      if (url.indexOf('_dash-update-component') >= 0) {
        let out = null;
        try { out = JSON.parse((init && init.body) || '{}').output; } catch (e) { out = null; }
        const r = {t_call: Date.now(), out};
        if (REC.length < 50000) REC.push(r);
        p.then((res) => { r.t_resp = Date.now(); r.status = res.status; try { Object.defineProperty(res, '__laneA2', {value: r}); } catch (e) { r.tag_err = String(e); } },
               (err) => { r.err = String(err); r.t_err = Date.now(); });
      }
      return p;
    };
    const oj = Response.prototype.json;
    Response.prototype.json = function () {
      const r = this.__laneA2;
      const p = oj.apply(this, arguments);
      if (r) {
        r.t_json_call = Date.now();
        p.then((d) => {
          r.t_json_done = Date.now();
          try {
            const resp = d && d.response;
            if (resp && typeof resp === 'object' && resp[SUBJECT]) { r.subj = true; r.subj_ts = (resp[SUBJECT].data || {}).timestamp; }
          } catch (e) { r.parse_note = String(e); }
        }, (e) => { r.json_err = String(e); });
      }
      return p;
    };
  } catch (e) { window.__laneA2_fetch_error = String(e); }
})();"""

JS_READY = """() => {
  try {
    const st = window.store && window.store.getState && window.store.getState();
    if (!st || !st.layout) return false;
    return JSON.stringify(st.layout).length > 10000;
  } catch (e) { return false; }
}"""

JS_INSTALL = r"""(args) => {
  if (window.__laneA2) return {installed: false, reason: 'already installed'};
  const SUBJECT = args.subject;
  const SUBJECT_TOKEN = SUBJECT + '.data';
  const hasOwn = Object.prototype.hasOwnProperty;
  const A = {subject: SUBJECT};
  A.h32 = (s) => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); } return (h >>> 0).toString(16).padStart(8, '0'); };
  A.hv = (v) => { let s; try { s = JSON.stringify(v); } catch (e) { return 'unserialisable'; } return s === undefined ? 'undefined' : A.h32(s) + ':' + s.length; };
  A.tsOf = (v) => (v !== null && typeof v === 'object' && !Array.isArray(v) && hasOwn.call(v, 'timestamp')) ? v.timestamp : null;
  A.isComp = (v) => v !== null && typeof v === 'object' && !Array.isArray(v) && typeof v.type === 'string' && typeof v.namespace === 'string' && v.props !== null && typeof v.props === 'object';
  // Generic walk of the WHOLE layout object graph (every nested object/array), indexing component nodes by
  // props.id and recording every /api/state-shaped object wherever it sits. Never consults state.paths.
  A.walk = (root) => {
    // V: objects, P: parent frame, K: key in parent, C: nearest enclosing component frame (-1 = none).
    const V = [root], P = [-1], K = [null], C = [-1];
    const byId = {}; const apiState = []; let nComp = 0;
    for (let i = 0; i < V.length; i++) {
      const v = V[i];
      if (Array.isArray(v)) {
        for (let j = 0; j < v.length; j++) { const c = v[j]; if (c !== null && typeof c === 'object') { V.push(c); P.push(i); K.push(j); C.push(C[i]); } }
        continue;
      }
      const comp = A.isComp(v);
      if (comp) { nComp++; const id = v.props.id; if (typeof id === 'string') (byId[id] = byId[id] || []).push(i); }
      else if (hasOwn.call(v, 'candidate_pool_status') && typeof v.timestamp === 'number') apiState.push(i);
      const owner = comp ? i : C[i];
      for (const k in v) { if (!hasOwn.call(v, k)) continue; const c = v[k]; if (c !== null && typeof c === 'object') { V.push(c); P.push(i); K.push(k); C.push(owner); } }
    }
    const pathOf = (i) => { const out = []; while (i > 0) { out.push(K[i]); i = P[i]; } return out.reverse(); };
    const ownerOf = (i) => { const o = C[i]; if (o < 0) return null; const id = V[o].props.id; return typeof id === 'string' ? id : JSON.stringify(id); };
    return {V, byId, apiState, nComp, nObj: V.length, pathOf, ownerOf};
  };
  // Committed React fiber tree (FiberRoot.current, not the container's creation-time fiber).
  A.fiberRoot = () => {
    const c = document.getElementById('react-entry-point');
    if (!c) return null;
    const key = Object.keys(c).find((k) => k.startsWith('__reactContainer$'));
    if (!key) return null;
    const host = c[key];
    return (host && host.stateNode && host.stateNode.current) || null;
  };
  A.fiberFind = (ids) => {
    const want = new Set(ids); const out = {}; ids.forEach((i) => { out[i] = []; });
    const root = A.fiberRoot(); if (!root) return {error: 'no fiber root', out};
    const stack = [root]; let n = 0;
    while (stack.length) {
      const f = stack.pop(); n++;
      const p = f.memoizedProps;
      if (p !== null && typeof p === 'object' && !Array.isArray(p) && typeof p.id === 'string' && want.has(p.id) && hasOwn.call(p, 'data')) {
        const t = f.type;
        const name = t ? (typeof t === 'string' ? t : (t.displayName || t.name || '?')) : '?';
        out[p.id].push({name, ts: A.tsOf(p.data), h: A.hv(p.data)});
      }
      if (f.sibling) stack.push(f.sibling);
      if (f.child) stack.push(f.child);
    }
    return {n, out};
  };
  A.splitTok = (tok) => { const j = tok.lastIndexOf('.'); return j > 0 ? [tok.slice(0, j), tok.slice(j + 1)] : [tok, '']; };
  A.hasSubject = (c) => {
    try {
      const o = c && c.callback && c.callback.output;
      if (typeof o !== 'string') return false;
      const parts = (o.startsWith('..') && o.endsWith('..')) ? o.slice(2, -2).split('...') : [o];
      return parts.some((p) => p.replace(/@[0-9a-f]{64}$/, '') === SUBJECT_TOKEN);
    } catch (e) { return false; }
  };
  // Supplementary apply log: re-read tracked props at the location THIS walk found; log reference/value changes.
  A.rec = {events: [], nNotify: 0, nLayoutChange: 0, nReindex: 0, errors: 0, lastErr: null, installedAt: Date.now(), capped: false};
  A.paths = {}; A.storeIds = {}; A.trackProps = {}; A.refs = {}; A.lastLayout = null;
  A.getAt = (root, path) => { let v = root; for (const k of path) { if (v === null || typeof v !== 'object') return undefined; v = v[k]; } return v; };
  A.index = (lay) => {
    const W = A.walk(lay); const paths = {}; const storeIds = {};
    for (const id in W.byId) { const i = W.byId[id][0]; paths[id] = W.pathOf(i); if (W.V[i].type === 'Store') storeIds[id] = true; }
    A.paths = paths; A.storeIds = storeIds; A.rec.nReindex++;
  };
  A.setTokens = (tokens) => {
    const tp = {};
    for (const id in A.storeIds) tp[id] = ['data'];
    tp[SUBJECT] = ['data'];
    for (const tok of tokens || []) { const [id, prop] = A.splitTok(tok); if (!prop) continue; tp[id] = tp[id] || []; if (!tp[id].includes(prop)) tp[id].push(prop); }
    A.trackProps = tp;
  };
  A.push = (e) => { if (A.rec.events.length < 60000) A.rec.events.push(e); else A.rec.capped = true; };
  A.onNotify = () => {
    A.rec.nNotify++;
    try {
      const lay = window.store.getState().layout;
      if (lay === A.lastLayout) return;
      A.lastLayout = lay; A.rec.nLayoutChange++;
      const now = Date.now();
      let stale = false;
      for (const id in A.trackProps) { const pth = A.paths[id]; if (!pth) continue; const n = A.getAt(lay, pth); if (!A.isComp(n) || n.props.id !== id) { stale = true; break; } }
      if (stale) { A.index(lay); A.push({t: now, kind: 'reindex'}); }
      for (const id in A.trackProps) {
        const pth = A.paths[id]; if (!pth) continue;
        const n = A.getAt(lay, pth); if (!A.isComp(n)) continue;
        for (const prop of A.trackProps[id]) {
          const key = id + '.' + prop; const d = n.props[prop];
          if (!hasOwn.call(A.refs, key)) { A.refs[key] = d; if (prop === 'data') A.push({t: now, kind: 'init', id, prop, ts: A.tsOf(d), h: id === SUBJECT ? A.hv(d) : undefined}); continue; }
          if (d !== A.refs[key]) { A.refs[key] = d; A.push({t: now, kind: 'change', id, prop, ts: prop === 'data' ? A.tsOf(d) : undefined, h: id === SUBJECT ? A.hv(d) : undefined}); }
        }
      }
    } catch (e) { A.rec.errors++; A.rec.lastErr = String((e && e.stack) || e); }
  };
  A.sample = (fiberIds, tokens) => {
    if (tokens) A.setTokens(tokens);
    const t0 = performance.now();
    const st = window.store.getState();
    const W = A.walk(st.layout);
    const walkMs = performance.now() - t0;
    const nodesFor = (id) => (W.byId[id] || []).map((i) => W.V[i]);
    const subject = (W.byId[SUBJECT] || []).map((i) => { const n = W.V[i]; return {path: W.pathOf(i).join('/'), type: n.type, has_data: hasOwn.call(n.props, 'data'), ts: A.tsOf(n.props.data), h: A.hv(n.props.data)}; });
    const tabs = nodesFor('visualization-tabs').map((n) => n.props.active_tab);
    const iv = nodesFor('candidate-metrics-panel-update-interval').map((n) => ({n: n.props.n_intervals, disabled: n.props.disabled === true, interval: n.props.interval}));
    const stores = {};
    for (const id in W.byId) { for (const i of W.byId[id]) { const n = W.V[i]; if (n.type === 'Store') (stores[id] = stores[id] || []).push({ts: A.tsOf(n.props.data), h: A.hv(n.props.data)}); } }
    const tok = {};
    for (const t of tokens || []) { const [id, prop] = A.splitTok(t); const idx = W.byId[id]; tok[t] = idx ? idx.map((i) => A.hv(W.V[i].props[prop])) : null; }
    const api = W.apiState.map((i) => ({path: W.pathOf(i).join('/'), owner: W.ownerOf(i), ts: W.V[i].timestamp}));
    const q = {}; const cbs = st.callbacks || {};
    for (const k in cbs) { if (Array.isArray(cbs[k])) { q[k] = cbs[k].length; if (cbs[k].some(A.hasSubject)) (q.subject_in = q.subject_in || []).push(k); } }
    const t1 = performance.now();
    const fiber = A.fiberFind([SUBJECT].concat(fiberIds || []));
    const fiberMs = performance.now() - t1;
    return {t: Date.now(), walk_ms: walkMs, fiber_ms: fiberMs, n_comp: W.nComp, n_obj: W.nObj, subject, active_tab: tabs, interval: iv, stores, tokens: tok, api_state: api, queues: q, fiber, title: document.title};
  };
  A.index(window.store.getState().layout);
  A.setTokens([]);
  if (args.apply_log) {
    A.onNotify();
    A.unsubscribe = window.store.subscribe(A.onNotify);
  }
  window.__laneA2 = A;
  return {installed: true, apply_log: !!args.apply_log, tracked_ids: Object.keys(A.trackProps).length, indexed_ids: Object.keys(A.paths).length, subject_path: A.paths[SUBJECT] || null};
}"""

JS_SAMPLE = "(a) => window.__laneA2.sample(a.fiber, a.tokens)"
JS_TAB = "() => { const s = window.__laneA2.walk(window.store.getState().layout); return (s.byId['visualization-tabs'] || []).map((i) => s.V[i].props.active_tab); }"
JS_HARVEST = """(subject) => {
  const A = window.__laneA2;
  const st = window.store.getState();
  let dashIndex;
  try { dashIndex = (st.paths && st.paths.strs) ? (st.paths.strs[subject] || null) : 'no paths.strs'; } catch (e) { dashIndex = 'error: ' + e; }
  const F = window.__laneA2_fetch || null;
  const fsum = F ? {n: F.length, resolved: F.filter((r) => r.t_resp).length, json_called: F.filter((r) => r.t_json_call).length, json_done: F.filter((r) => r.t_json_done).length, errors: F.filter((r) => r.err || r.json_err).length} : null;
  const fsubj = F ? F.filter((r) => typeof r.out === 'string' && r.out.indexOf(subject + '.data') >= 0) : null;
  return {rec: A.rec, own_index_path: A.paths[subject] || null, diagnostic_only_dash_paths_strs: dashIndex,
          time_origin: performance.timeOrigin, longtasks: window.__laneA2_longtasks || null, longtasks_error: window.__laneA2_longtasks_error || null,
          fetch_probe_summary: fsum, fetch_probe_subject: fsubj, fetch_probe_error: window.__laneA2_fetch_error || null};
}"""


async def dismiss_welcome(page, log):
    loc = page.locator("#welcome-modal-close")
    try:
        if await loc.count() and await loc.first.is_visible():
            await loc.first.click(force=True, timeout=15000)
            log.append("welcome modal: dismissed")
            await asyncio.sleep(1.0)
        else:
            log.append("welcome modal: not visible")
    except Exception as e:  # noqa: BLE001
        log.append(f"welcome modal: click error {str(e).splitlines()[0]}")


async def select_tab(page, label, tab_id, log, deadline_s=24.0):
    link = page.locator(".nav-link", has_text=re.compile(rf"^\s*{re.escape(label)}\s*$"))
    tabs = None
    for attempt in range(3):
        n = await link.count()
        target = link.first if n else page.get_by_role("tab", name=label, exact=True).first
        log.append(f"tab {tab_id}: attempt {attempt + 1}, .nav-link matches={n}")
        try:
            # Trusted CDP input first. The page never settles (a callback is always in flight), so the
            # renderer main thread can hold the input event for many seconds.
            await target.click(force=True, timeout=30000)
            log.append(f"tab {tab_id}: trusted force-click returned")
        except Exception as e:  # noqa: BLE001
            log.append(f"tab {tab_id}: trusted click error {str(e).splitlines()[0]}")
            try:
                # Fallback: a DOM click event. react-bootstrap's Nav.Link onClick -> dbc Tabs setProps({active_tab})
                # handles it identically; the layout read below is what confirms the view either way.
                await target.dispatch_event("click", timeout=15000)
                log.append(f"tab {tab_id}: fallback dispatch_event('click') returned")
            except Exception as e2:  # noqa: BLE001
                log.append(f"tab {tab_id}: fallback click error {str(e2).splitlines()[0]}")
        t_end = time.time() + deadline_s / 3
        while time.time() < t_end:
            tabs = await page.evaluate(JS_TAB)
            if tabs == [tab_id]:
                log.append(f"tab {tab_id}: confirmed from layout after attempt {attempt + 1}")
                return True
            await asyncio.sleep(0.5)
    log.append(f"tab {tab_id}: NOT confirmed (layout says {tabs})")
    return False


async def sample_window(page, wire, seconds, period=1.0):
    samples = []
    t0 = time.time()
    i = 0
    while True:
        target = t0 + i * period
        if target > t0 + seconds:
            break
        delay = target - time.time()
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            s = await page.evaluate(JS_SAMPLE, {"fiber": FIBER_IDS, "tokens": wire.trackable_tokens() + [f"{INTERVAL_ID}.n_intervals"]})
        except Exception as e:  # noqa: BLE001
            s = {"t": int(time.time() * 1000), "error": str(e)[:300]}
        s["py_t"] = time.time()
        samples.append(s)
        i += 1
        # Keep ~1 Hz without drifting into a backlog when an evaluate is held by a busy main thread.
        if time.time() > t0 + i * period:
            i = int((time.time() - t0) / period) + 1
    return samples


# --------------------------------------------------------------------------------------------------
# ANALYSIS
# --------------------------------------------------------------------------------------------------
def rec_wall(r, mono_key):
    if r.get("wall") is None or r.get("mono") is None or r.get(mono_key) is None:
        return None
    return r["wall"] + (r[mono_key] - r["mono"])


def distinct_series(vals):
    vals = [v for v in vals if v is not None]
    return len(set(vals)), sum(1 for a, b in zip(vals, vals[1:]) if a != b)


def analyse_pass(name, expect_tab, samples, wire_recs, events, grace_s, longtasks=None, time_origin=None, fetch_subject=None):
    good = [s for s in samples if "error" not in s]
    ws = good[0]["t"] / 1000.0 if good else None
    we = good[-1]["t"] / 1000.0 if good else None
    out = {"pass": name, "expect_tab": expect_tab, "window_wall": [ws, we], "samples": len(samples), "sample_errors": len(samples) - len(good)}
    if not good:
        return out
    out["window_s"] = round(we - ws, 2)
    out["sample_gap_s"] = stats([(b["t"] - a["t"]) / 1000.0 for a, b in zip(good, good[1:])])

    # --- view-state assertion, every sample ---
    tab_bad = [s["active_tab"] for s in good if s.get("active_tab") != [expect_tab]]
    out["active_tab_ok_all_samples"] = not tab_bad
    out["active_tab_bad_samples"] = tab_bad[:5]

    # --- WIRE: the writer's requests in the window ---
    subj = sorted((r for r in wire_recs if SUBJECT_TOKEN in (r.get("tokens") or []) and r.get("wall") and ws <= r["wall"] <= we), key=lambda r: r["wall"])
    tally = Counter()
    delivered = []
    for r in subj:
        oc = r.get("outcome")
        if oc == "ok":
            c = (r.get("carried") or {}).get(SUBJECT_TOKEN)
            if c is not None:
                tally["carried"] += 1
                if c.get("ts") is None:
                    tally["carried_without_timestamp"] += 1
                delivered.append({"ts": c.get("ts"), "h": c["h"], "req_wall": r["wall"], "done_wall": rec_wall(r, "mono_done")})
            else:
                tally["no_update_omitted"] += 1
        else:
            tally[oc] += 1
    gaps = [b["wall"] - a["wall"] for a, b in zip(subj, subj[1:])]
    rtt = [(r["mono_done"] - r["mono"]) for r in subj if r.get("mono_done") is not None and r.get("mono") is not None]
    all_dash = [r for r in wire_recs if r.get("wall") and ws <= r["wall"] <= we]
    out["wire"] = {
        "writer_requests": len(subj),
        "outcomes": dict(tally),
        "distinct_delivered_timestamps": len({d["ts"] for d in delivered if d["ts"] is not None}),
        "distinct_delivered_values": len({d["h"] for d in delivered}),
        "request_gap_s": stats(gaps),
        "round_trip_s": stats(rtt),
        "active_tab_inputs": dict(Counter(str(r.get("active_tab_input")) for r in subj)),
        "changed_prop_ids": dict(Counter(json.dumps(r.get("changed")) for r in subj)),
        "tokens_agree_with_outputs_field": dict(Counter(str(r.get("tokens_agree")) for r in subj)),
        "n_intervals_requested": [r.get("n_intervals") for r in subj],
        "all_dash_requests_in_window": len(all_dash),
        "all_dash_outcomes": dict(Counter(r.get("outcome") for r in all_dash)),
    }

    # --- RENDERER (primary): layout walk ---
    walk_ts_flat = [x["ts"] for s in good for x in s["subject"]]
    walk_h = [s["subject"][0]["h"] if s["subject"] else None for s in good]
    out["renderer_walk"] = {
        "matches_per_sample": dict(Counter(len(s["subject"]) for s in good)),
        "paths_seen": sorted({x["path"] for s in good for x in s["subject"]}),
        "distinct_timestamps": len(set(map(repr, walk_ts_flat))),
        "distinct_values": len({x["h"] for s in good for x in s["subject"]}),
        "timestamps_seen": sorted(set(walk_ts_flat), key=lambda v: (v is None, v or 0)),
        "values_seen": sorted({x["h"] for s in good for x in s["subject"]}),
        "sample_to_sample_changes": distinct_series(walk_h)[1],
        "walk_ms": stats([s["walk_ms"] for s in good]),
        "n_comp": stats([s["n_comp"] for s in good]),
        "n_obj": stats([s["n_obj"] for s in good]),
    }
    # --- RENDERER (secondary): React fiber ---
    def fib(sample, sid):
        return ((sample.get("fiber") or {}).get("out") or {}).get(sid, [])

    fib_entries = [e for s in good for e in fib(s, SUBJECT)]
    out["renderer_fiber"] = {
        "fibers_per_sample": dict(Counter(len(fib(s, SUBJECT)) for s in good)),
        "component_names": sorted({e["name"] for e in fib_entries}),
        "distinct_timestamps": len({repr(e["ts"]) for e in fib_entries}),
        "distinct_values": len({e["h"] for e in fib_entries}),
        "timestamps_seen": sorted({e["ts"] for e in fib_entries}, key=lambda v: (v is None, v or 0)),
        "errors": sorted({(s.get("fiber") or {}).get("error") for s in good if (s.get("fiber") or {}).get("error")}),
        "fiber_ms": stats([s["fiber_ms"] for s in good]),
        "control_fibers": {sid: dict(zip(("distinct_values", "sample_to_sample_changes"), distinct_series([fib(s, sid)[0]["h"] if fib(s, sid) else None for s in good]))) for sid in FIBER_IDS},
    }
    # --- CONTENT SEARCH: /api/state-shaped objects anywhere in the layout ---
    by_loc = defaultdict(set)
    for s in good:
        for a in s.get("api_state") or []:
            by_loc[f"{a.get('owner')} @ {a['path']}"].add(a["ts"])
    delivered_ts = {d["ts"] for d in delivered if d["ts"] is not None}
    all_layout_ts = set().union(*by_loc.values()) if by_loc else set()
    out["content_search"] = {
        "api_state_payload_locations_distinct_ts": {p: len(v) for p, v in sorted(by_loc.items())},
        "delivered_writer_ts_found_anywhere_in_layout": len(delivered_ts & all_layout_ts),
    }
    # --- APPLY LOG (supplementary) ---
    ev_win = [e for e in events if ws <= e["t"] / 1000.0 <= we + grace_s]
    subj_changes = [e for e in ev_win if e.get("id") == SUBJECT and e.get("kind") == "change"]
    out["apply_log"] = {
        "subject_changes": len(subj_changes),
        "subject_change_timestamps": [e.get("ts") for e in subj_changes][:50],
        "reindex_events": sum(1 for e in ev_win if e.get("kind") == "reindex"),
        "delivered_ts_seen_in_apply_log": len(delivered_ts & {e.get("ts") for e in subj_changes}),
    }
    # --- per delivered response: was it ever seen by ANY renderer read? ---
    seen_any = set(walk_ts_flat) | {e["ts"] for e in fib_entries} | all_layout_ts | {e.get("ts") for e in ev_win if e.get("id") == SUBJECT}
    out["delivered_seen_by_any_read"] = sum(1 for d in delivered if d["ts"] in seen_any)
    out["delivered_not_seen_by_any_read"] = sum(1 for d in delivered if d["ts"] not in seen_any)
    out["renderer_ts_provenance"] = []
    for t in sorted(t for t in set(walk_ts_flat) if t is not None):
        src = [r for r in wire_recs if ((r.get("carried") or {}).get(SUBJECT_TOKEN) or {}).get("ts") == t]
        out["renderer_ts_provenance"].append({
            "ts": t,
            "delivered_by": [{"req_wall": r["wall"], "done_wall": rec_wall(r, "mono_done"), "active_tab_input": r.get("active_tab_input"), "changed": r.get("changed"), "n_intervals": r.get("n_intervals"), "in_window": bool(ws <= r["wall"] <= we)} for r in src],
        })

    # --- POSITIVE CONTROL (a): every dcc.Store, same walk, same samples ---
    series = defaultdict(list)
    for s in good:
        for sid, lst in (s.get("stores") or {}).items():
            series[sid].append(lst[0]["h"] if lst else None)
    changed = {}
    for sid, v in series.items():
        d, ch = distinct_series(v)
        if d > 1:
            changed[sid] = {"distinct_values": d, "sample_to_sample_changes": ch}
    out["control_stores"] = {
        "stores_in_layout": len(series),
        "stores_changed_content_in_window": dict(sorted(changed.items(), key=lambda kv: -kv[1]["sample_to_sample_changes"])),
        "named": {sid: dict(zip(("distinct_values", "sample_to_sample_changes"), distinct_series(series.get(sid, [])))) for sid in NAMED_CONTROLS},
    }
    # --- POSITIVE CONTROL (b): delivered-vs-held for EVERY response-written id.prop in the window ---
    wire_vals = defaultdict(list)
    for r in sorted(all_dash, key=lambda r: r["wall"]):
        for t, ent in (r.get("carried") or {}).items():
            wire_vals[t].append(ent["h"])
    held = defaultdict(list)
    for s in good:
        for t, hs in (s.get("tokens") or {}).items():
            held[t].append(hs[0] if hs else None)
    held[SUBJECT_TOKEN] = walk_h
    ev_changes = Counter(f"{e['id']}.{e.get('prop', 'data')}" for e in ev_win if e.get("kind") == "change")
    table = {}
    for t in sorted(set(wire_vals) | {SUBJECT_TOKEN}):
        hd, hch = distinct_series(held.get(t, []))
        table[t] = {
            "wire_carried": len(wire_vals.get(t, [])),
            "wire_distinct": len(set(wire_vals.get(t, []))),
            "held_samples": len([x for x in held.get(t, []) if x is not None]),
            "held_distinct": hd,
            "held_changes": hch,
            "apply_log_changes": ev_changes.get(t, 0),
        }
    out["delivered_vs_held"] = dict(sorted(table.items(), key=lambda kv: (-kv[1]["wire_distinct"], kv[0])))
    out["positive_controls_response_written"] = sorted(t for t, v in table.items() if t != SUBJECT_TOKEN and v["wire_distinct"] >= 2 and v["held_distinct"] >= 2)
    out["apply_log_changes_by_prop"] = dict(ev_changes.most_common(20))
    # --- interval cadence as the renderer saw it ---
    ns = [s["interval"][0]["n"] for s in good if s.get("interval")]
    out["interval"] = {
        "n_first_last": [ns[0], ns[-1]] if ns else None,
        "ticks_per_s": round((ns[-1] - ns[0]) / (we - ws), 3) if ns and we > ws else None,
        "sample_to_sample_changes": distinct_series(ns)[1],
        "disabled_values": sorted({str(s["interval"][0]["disabled"]) for s in good if s.get("interval")}),
        "period_ms": sorted({s["interval"][0]["interval"] for s in good if s.get("interval")}),
    }
    # --- renderer queues (context only) ---
    qkeys = sorted({k for s in good for k in (s.get("queues") or {}) if k != "subject_in"})
    out["renderer_queues_context"] = {
        "len_stats": {k: stats([(s.get("queues") or {}).get(k) for s in good]) for k in qkeys},
        "subject_seen_in": dict(Counter(k for s in good for k in (s.get("queues") or {}).get("subject_in", []))),
    }
    out["titles"] = dict(Counter(s.get("title") for s in good))

    # --- per-writer apply breakdown, for store values that carry a ``timestamp`` ---
    per_writer = {}
    for sid in (SUBJECT, METRICS_STATE, "stream-health-store"):
        tok = f"{sid}.data"
        held_ts = {x["ts"] for s in good for x in (s.get("stores") or {}).get(sid, []) if x.get("ts") is not None}
        held_ts |= {e.get("ts") for e in ev_win if e.get("id") == sid and e.get("ts") is not None}
        if sid == SUBJECT:
            held_ts |= {t for t in seen_any if t is not None}
        rows = defaultdict(lambda: {"carried": 0, "with_ts": 0, "applied": 0})
        for r in all_dash:
            ent = (r.get("carried") or {}).get(tok)
            if ent is None:
                continue
            row = rows[r.get("output", "?")]
            row["carried"] += 1
            if ent.get("ts") is not None:
                row["with_ts"] += 1
                row["applied"] += int(ent["ts"] in held_ts)
        per_writer[tok] = dict(rows)
    out["per_writer_apply_by_timestamp"] = per_writer

    # --- fetch probe: did the renderer's own JS receive and parse each subject body? ---
    if fetch_subject is not None:
        fr = [r for r in fetch_subject if SUBJECT_TOKEN in output_tokens(r.get("out")) and ws <= r.get("t_call", 0) / 1000.0 <= we]
        ticks = sorted(e["t"] for e in events if e.get("id") == INTERVAL_ID and e.get("prop") == "n_intervals" and e.get("kind") == "change")
        rows = []
        for r in fr:
            end = r.get("t_json_done")
            rows.append({
                "call_to_resp_ms": (r["t_resp"] - r["t_call"]) if r.get("t_resp") else None,
                "call_to_json_done_ms": (end - r["t_call"]) if end else None,
                "ticks_between_call_and_json_done": sum(1 for t in ticks if r["t_call"] <= t <= end) if end else None,
                "ms_from_json_done_to_next_tick": (min((t for t in ticks if t >= end), default=None) - end) if end and any(t >= end for t in ticks) else None,
                "subj_ts": r.get("subj_ts"),
                "applied": r.get("subj_ts") in seen_any if r.get("subj_ts") is not None else None,
            })
        out["fetch_probe_subject"] = {
            "requests": len(fr),
            "fetch_resolved_in_js": sum(1 for r in fr if r.get("t_resp")),
            "json_parsed_by_renderer": sum(1 for r in fr if r.get("t_json_done")),
            "parsed_body_carried_subject": sum(1 for r in fr if r.get("subj")),
            "parsed_and_applied": sum(1 for x in rows if x["applied"]),
            "call_to_json_done_ms": stats([x["call_to_json_done_ms"] for x in rows]),
            "ticks_between_call_and_json_done": dict(Counter(str(x["ticks_between_call_and_json_done"]) for x in rows)),
            "ms_from_json_done_to_next_tick": stats([x["ms_from_json_done_to_next_tick"] for x in rows]),
            "interval_ticks_logged_in_window": sum(1 for t in ticks if ws * 1000 <= t <= we * 1000),
            "rows": rows,
        }

    # --- main-thread congestion (context): long tasks overlapping the window ---
    if longtasks is not None and time_origin:
        busy = 0.0
        n_lt = 0
        mx = 0.0
        for start, dur in longtasks:
            a = (time_origin + start) / 1000.0
            b = a + dur / 1000.0
            ov = min(b, we) - max(a, ws)
            if ov > 0:
                busy += ov
                n_lt += 1
                mx = max(mx, dur)
        out["main_thread_longtasks"] = {"count": n_lt, "busy_s": round(busy, 2), "busy_fraction": round(busy / (we - ws), 3) if we > ws else None, "max_ms": round(mx, 1)}
    return out


def verdict(p1):
    w = p1.get("wire") or {}
    rw = p1.get("renderer_walk") or {}
    rf = p1.get("renderer_fiber") or {}
    ctrl = p1.get("positive_controls_response_written") or []
    if not p1.get("active_tab_ok_all_samples"):
        return "INDETERMINATE", ["Candidate Metrics tab not held for every sample"]
    if rw.get("matches_per_sample") != {1: p1["samples"] - p1["sample_errors"]}:
        return "INDETERMINATE", [f"layout walk did not find exactly one subject node per sample: {rw.get('matches_per_sample')}"]
    delivered = w.get("distinct_delivered_timestamps", 0)
    seen_vals = rw.get("distinct_values", 0)
    if delivered >= 5 and seen_vals <= 1 and rf.get("distinct_values", 0) <= 1 and ctrl:
        return "REPRODUCED", [f"{delivered} distinct timestamps delivered; renderer walk held {seen_vals} value(s), fiber {rf.get('distinct_values')}; {len(ctrl)} response-written control prop(s) changed on the same read path"]
    if seen_vals > 1 and p1.get("delivered_seen_by_any_read", 0) > 1:
        return "NOT REPRODUCED", [f"renderer walk held {seen_vals} distinct values; {p1['delivered_seen_by_any_read']} delivered values were seen by a renderer read"]
    return "INDETERMINATE", [f"delivered={delivered} held_values={seen_vals} controls={len(ctrl)}"]


# --------------------------------------------------------------------------------------------------
async def main_async(args):
    log = []
    meta = {
        "script": str(Path(__file__).resolve().relative_to(REPO)),
        "started_wall": time.time(),
        "canopy_health_before": http_get_json(CANOPY + "/v1/health"),
        "cascor_status_before": cascor_summary(http_get_json(CASCOR + "/v1/training/status")),
        "loadavg_before": Path("/proc/loadavg").read_text().strip(),
        "args": vars(args),
    }
    wire = PWRequests() if args.no_wire else Wire()
    passes = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not args.headed)
        meta["browser_version"] = browser.version
        context = await browser.new_context(viewport={"width": 1680, "height": 1050})
        await context.add_init_script(JS_LONGTASK_INIT)
        if not args.no_fetch_probe:
            await context.add_init_script(JS_FETCH_PROBE_INIT)
        page = await context.new_page()
        if args.no_wire:
            wire.attach(page)
        else:
            cdp = await context.new_cdp_session(page)
            wire.attach(cdp)
            await cdp.send("Network.enable", {"maxTotalBufferSize": 256 * 1024 * 1024, "maxResourceBufferSize": 64 * 1024 * 1024, "maxPostDataSize": 4 * 1024 * 1024})
        await page.goto(CANOPY + DASH_PATH, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_function(JS_READY, timeout=90000, polling=500)
        meta["install"] = await page.evaluate(JS_INSTALL, {"subject": SUBJECT, "apply_log": not args.no_apply_log})
        log.append(f"installed: {meta['install']}")
        await asyncio.sleep(args.post_load)
        await dismiss_welcome(page, log)

        # PASS 1 -- the claim: Candidate Metrics tab, idle.
        ok = await select_tab(page, "Candidate Metrics", "candidates", log)
        await asyncio.sleep(args.settle)
        meta["cascor_status_pass1_start"] = cascor_summary(http_get_json(CASCOR + "/v1/training/status"))
        s1 = await sample_window(page, wire, args.window)
        meta["cascor_status_pass1_end"] = cascor_summary(http_get_json(CASCOR + "/v1/training/status"))
        passes["pass1_candidates"] = {"tab_confirmed": ok, "samples": s1}

        # PASS 2 -- Training Metrics tab (fallback control + the claim's side statement).
        if not args.no_metrics_pass:
            ok = await select_tab(page, "Training Metrics", "metrics", log)
            await asyncio.sleep(args.settle)
            s2 = await sample_window(page, wire, args.metrics_window)
            passes["pass2_metrics"] = {"tab_confirmed": ok, "samples": s2}

        # PASS 3 -- supplementary: re-enter Candidate Metrics; is the tab-switch-triggered write applied?
        if not args.no_reentry:
            ok = await select_tab(page, "Candidate Metrics", "candidates", log)
            s3 = await sample_window(page, wire, args.reentry_window)
            passes["pass3_reentry"] = {"tab_confirmed": ok, "samples": s3}

        await asyncio.sleep(args.grace)
        harvest = await page.evaluate(JS_HARVEST, SUBJECT)
        pending = list(wire.tasks)
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        await browser.close()
    meta["cascor_status_after"] = cascor_summary(http_get_json(CASCOR + "/v1/training/status"))
    meta["canopy_health_after"] = http_get_json(CANOPY + "/v1/health")
    meta["loadavg_after"] = Path("/proc/loadavg").read_text().strip()
    meta["finished_wall"] = time.time()

    recs = list(wire.recs.values())
    events = harvest["rec"]["events"]
    result = {"meta": meta, "log": log, "wire_event_counts": dict(wire.n_events), "wire_outcomes_all": dict(Counter(r.get("outcome") for r in recs)), "apply_log_meta": {k: v for k, v in harvest["rec"].items() if k != "events"}}
    result["index_paths"] = {"own_walk": harvest["own_index_path"], "diagnostic_only_dash_paths_strs": harvest["diagnostic_only_dash_paths_strs"]}
    expect = {"pass1_candidates": "candidates", "pass2_metrics": "metrics", "pass3_reentry": "candidates"}
    result["longtask_observer_error"] = harvest.get("longtasks_error")
    result["fetch_probe"] = {"summary_whole_session": harvest.get("fetch_probe_summary"), "error": harvest.get("fetch_probe_error")}
    result["analysis"] = {
        k: dict(analyse_pass(k, expect[k], p["samples"], recs, events, args.grace, harvest.get("longtasks"), harvest.get("time_origin"), harvest.get("fetch_probe_subject")), tab_confirmed=p["tab_confirmed"])
        for k, p in passes.items()
    }
    verdict_label, why = verdict(result["analysis"]["pass1_candidates"])
    result["verdict_pass1_mechanical"] = {"verdict": verdict_label, "reasons": why}

    # Compact raw series for the record (subject + named controls only).
    result["raw"] = {}
    for k, p in passes.items():
        result["raw"][k] = [
            {
                "t": s.get("t"),
                "tab": s.get("active_tab"),
                "iv_n": (s.get("interval") or [{}])[0].get("n"),
                "subj_walk": [(x["ts"], x["h"]) for x in s.get("subject", [])],
                "subj_fiber": [(x["ts"], x["h"]) for x in ((s.get("fiber") or {}).get("out") or {}).get(SUBJECT, [])],
                "controls": {c: [x["h"] for x in (s.get("stores") or {}).get(c, [])] for c in NAMED_CONTROLS},
                "queues": s.get("queues"),
                "title": s.get("title"),
                "error": s.get("error"),
            }
            for s in p["samples"]
        ]
    result["raw"]["writer_requests"] = [
        {k2: r.get(k2) for k2 in ("wall", "mono", "mono_resp", "mono_done", "status", "outcome", "n_intervals", "active_tab_input", "changed", "body_bytes", "fetch_err", "fail")}
        | {"carried_ts": ((r.get("carried") or {}).get(SUBJECT_TOKEN) or {}).get("ts"), "carried_h": ((r.get("carried") or {}).get(SUBJECT_TOKEN) or {}).get("h"), "carried_tokens": sorted((r.get("carried") or {}).keys())}
        for r in sorted((r for r in recs if SUBJECT_TOKEN in (r.get("tokens") or [])), key=lambda r: r.get("wall") or 0)
    ]
    result["raw"]["apply_log_subject_and_named"] = [e for e in events if e.get("id") in ([SUBJECT] + NAMED_CONTROLS) or e.get("kind") == "reindex"]
    named_tokens = {f"{METRICS_STATE}.data", "stream-health-store.data", "latency-display.children"}
    result["raw"]["named_token_deliveries"] = [
        {"wall": r.get("wall"), "writer": r.get("output"), "token": t, "ts": ent.get("ts"), "h": ent["h"]}
        for r in sorted(recs, key=lambda r: r.get("wall") or 0)
        for t, ent in (r.get("carried") or {}).items()
        if t in named_tokens
    ]

    out_path = Path(args.out) if args.out else OUT_DIR / f"2026-09-22_laneA2_cdp_store_apply_{args.tag}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1, default=str))
    print(f"wrote {out_path}")
    for k, a in result["analysis"].items():
        print(f"\n=== {k} (tab confirmed: {a.get('tab_confirmed')}, held all samples: {a.get('active_tab_ok_all_samples')}) window {a.get('window_s')} s, {a.get('samples')} samples, gap {a.get('sample_gap_s')}")
        print("  wire:", json.dumps({x: a["wire"][x] for x in ("writer_requests", "outcomes", "distinct_delivered_timestamps", "request_gap_s", "round_trip_s", "active_tab_inputs", "changed_prop_ids")}))
        print("  walk:", json.dumps({x: a["renderer_walk"][x] for x in ("matches_per_sample", "distinct_timestamps", "distinct_values", "values_seen", "timestamps_seen", "sample_to_sample_changes", "walk_ms")}))
        print("  fiber:", json.dumps({x: a["renderer_fiber"][x] for x in ("fibers_per_sample", "component_names", "distinct_values", "timestamps_seen", "errors", "control_fibers")}))
        print("  content:", json.dumps(a["content_search"]))
        print("  apply_log:", json.dumps({x: a["apply_log"][x] for x in ("subject_changes", "reindex_events", "delivered_ts_seen_in_apply_log")}))
        print("  delivered seen/not-seen by any read:", a.get("delivered_seen_by_any_read"), a.get("delivered_not_seen_by_any_read"))
        print("  renderer ts provenance:", json.dumps(a.get("renderer_ts_provenance"))[:600])
        print("  control stores changed:", json.dumps(a["control_stores"]["stores_changed_content_in_window"]))
        print("  response-written controls (wire>=2 & held>=2):", a["positive_controls_response_written"])
        top = list(a["delivered_vs_held"].items())[:14]
        for t, v in top:
            print(f"     {t:70s} {v}")
        print("  interval:", json.dumps(a["interval"]))
        print("  queues:", json.dumps(a["renderer_queues_context"]))
        print("  per-writer apply:", json.dumps(a.get("per_writer_apply_by_timestamp")))
        print("  main-thread long tasks:", json.dumps(a.get("main_thread_longtasks")))
        fp = a.get("fetch_probe_subject")
        if fp:
            print("  fetch probe (subject):", json.dumps({x: fp[x] for x in fp if x != "rows"}))
    print("\nindex paths:", json.dumps(result["index_paths"]))
    print("apply log meta:", json.dumps(result["apply_log_meta"])[:400])
    print("wire outcomes (whole session):", result["wire_outcomes_all"])
    print("verdict (pass 1, mechanical):", verdict_label, why)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--window", type=float, default=60.0)
    ap.add_argument("--metrics-window", type=float, default=60.0)
    ap.add_argument("--reentry-window", type=float, default=20.0)
    ap.add_argument("--settle", type=float, default=6.0)
    ap.add_argument("--post-load", type=float, default=10.0)
    ap.add_argument("--grace", type=float, default=4.0)
    ap.add_argument("--no-metrics-pass", action="store_true")
    ap.add_argument("--no-reentry", action="store_true")
    ap.add_argument("--no-wire", action="store_true", help="perturbation check: no CDP session; count requests from Playwright's own events")
    ap.add_argument("--no-apply-log", action="store_true", help="perturbation check: no store.subscribe listener")
    ap.add_argument("--no-fetch-probe", action="store_true", help="do not wrap window.fetch / Response.prototype.json")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--tag", default="run1")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
