#!/usr/bin/env python3
"""
Lane A3 causal test: is the candidate training-state store's write landing bound to its trigger PERIOD?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (independent Lane A validator, entry point = source + causal intervention)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 6: F-CANOPY-035 / -052);
         notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md §2 (Lane A)

CLAIM UNDER TEST (a claim, not a fact)
    On canopy main 9bffaba1, ``fetch_training_state`` (candidate_metrics_panel.py:247-268) writes
    ``candidate-metrics-panel-training-state-store`` off ``candidate-metrics-panel-update-interval``.
    Its round trip is ~30 ms and every response carries a new value (a per-call ``timestamp``), yet the
    renderer never applies any write after mount -- F-CANOPY-035's self-eviction mechanism
    (dash_renderer.dev.js :3027 evicts the in-flight ``watched`` entry when the next tick is
    ``requested`` under the same ``getUniqueIdentifier``; :2699 then discards its response).

ONE VARIABLE
    The ``interval`` prop of ``candidate-metrics-panel-update-interval``, changed at runtime through the
    Interval component's OWN ``setProps`` (the DashWrapper path the Interval itself uses for
    ``n_intervals``; falls back to ``dash_clientside.set_props`` only if the fiber walk fails, and the
    JSON records which path was used). Nothing else is touched. dcc.Interval resets its timer on an
    ``interval`` change (``UNSAFE_componentWillReceiveProps`` -> ``resetTimer``), so the new period binds
    from the change onward. Cascor is NOT driven (no start, no PATCH): idle only.

    Fixed phase plan, no early stop (every verdict below is reachable):
        1000 ms (control, 60 s) -> 10000 ms (90 s) -> 1000 ms (60 s) -> 4000 ms (60 s) -> 1000 ms (45 s)

INSTRUMENT
    * a ``window.fetch`` wrapper (installed by an init script, before any page script) records every
      ``_dash-update-component`` POST whose output is this callback's: issue time, changedPropIds, HTTP
      status, and the ``timestamp`` its response carries for the state store (read from a clone, so the
      renderer's own read is untouched);
    * a ``window.store.subscribe`` reader records, on EVERY dispatch, changes of the state store's
      ``data.timestamp``, the Interval's ``n_intervals`` / ``interval`` / ``disabled``, the pool-history
      store length and ``visualization-tabs.active_tab`` -- read from ``getState().layout`` via
      ``paths.strs`` (supplementary: this callback's membership of the renderer's callback lists);
    * positive controls: (1) the tab-switch write -- the reader must see the store go from ``{}`` to a
      timestamped value, or (2) an end-of-run SENTINEL written into the store through the Store
      component's own ``setProps`` must be seen by the same reader.
    * (added after run1, diagnostic only -- the verdict rule below is untouched and its sha256 is
      recorded in every artifact) the browser NETWORK layer's own timing for this callback's requests
      (Playwright ``requestfinished`` -> ``request.timing``), which the page's main thread cannot delay,
      so server/network time can be separated from page-side processing time.

========================================================================================================
VERDICT RULE (BEGIN) -- fixed 2026-09-22 before the first run; not to be edited after it.

Definitions (per phase P; all times on the page's performance.now() clock):
  t_change(P)   : when the setProps that set P's period returned (for the opening 1000 ms control
                  phase, which needs no change: the phase start).
  scored window : [first n_intervals transition after t_change(P), t_end(P) - 8.0 s).  The 8.0 s tail
                  keeps a request issued near the end of P from being scored against the NEXT phase's
                  ticks (8.0 s > the 7.0 s worst wire->apply gap the brief quotes).
  issued(P)     : this callback's HTTP requests whose changedPropIds contain
                  candidate-metrics-panel-update-interval.n_intervals, issued inside the scored window,
                  answered HTTP 200 with a state-store timestamp in the body.
  landed(P)     : the subset of issued(P) whose response timestamp is EVER observed as
                  candidate-metrics-panel-training-state-store.data.timestamp in
                  window.store.getState().layout by the store.subscribe reader, before the run ends.
  L(period)     : sum(landed) / sum(issued), pooled over every phase with that period.
  lands         : L >= 0.5      does-not-land : L <= 0.1      otherwise : partial.
  took(P)       : the layout's `interval` prop reads back the requested value AND the median gap between
                  consecutive n_intervals transitions inside P (from its first tick to t_end) lies in
                  [0.8 x period, 1.5 x period + 1.0 s] for a period >= 4000 ms, or is < 3.0 s for a
                  1000 ms phase.

Ladder, first match wins:
  1. SETPROPS-FAILED         any interval setProps returned not-ok, or took(P) is false for any phase.
  2. POSITIVE-CONTROL-FAILED the reader never observed ANY change of the state store's data.timestamp:
                             neither the tab-switch write nor the end-of-run sentinel. The reader is
                             blind; no verdict.
  3. INDETERMINATE           any period has sum(issued) < 3, or visualization-tabs.active_tab was not
                             "candidates" at any moment inside a scored window.
  4. CONTROL-APPLIES         L(1000) lands -> the claim is not reproduced.
  5. NOT-PERIOD-BOUND        L does-not-land at 1000, 4000 AND 10000.
  6. PERIOD-BOUND            L(1000) does-not-land AND L(10000) lands.
  7. INDETERMINATE           anything else (partial landing somewhere) -- reported with the counts.
Across runs: one verdict per run; if two runs disagree, the combined answer is INDETERMINATE.

VERDICT RULE (END)
========================================================================================================

Usage:
  LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
      util/ad-hoc/2026-09-22_laneA3_candidate_tick_period_test.py --tag run1

Output: reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_laneA3_candidate_tick_period_<tag>.json
Exit codes: 0 the test ran (read the verdict), 2 the dashboard could not be driven at all.
"""

import argparse
import hashlib
import json
import os
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone

CANOPY = os.environ.get("JUNIPER_E2E_CANOPY_URL", "http://127.0.0.1:8051")
DASH = "/dashboard/"
INTERVAL_ID = "candidate-metrics-panel-update-interval"
STORE_ID = "candidate-metrics-panel-training-state-store"
HIST_ID = "candidate-metrics-panel-pool-history-store"
TABS_ID = "visualization-tabs"
OUT_PREFIX = "..candidate-metrics-panel-training-state-store.data"
TICK_PROP = f"{INTERVAL_ID}.n_intervals"
TAB_PROP = f"{TABS_ID}.active_tab"
TAIL_S = 8.0
PLAN = [(1000, 60), (10000, 90), (1000, 60), (4000, 60), (1000, 45)]
SENTINEL_TS = -424242.5

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
OUT_DIR = os.path.join(_REPO, "reports", "e2e-canopy-2026-09-02", "transcripts")


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def verdict_rule_sha256() -> str:
    doc = __doc__ or ""
    start = doc.index("VERDICT RULE (BEGIN)")
    end = doc.index("VERDICT RULE (END)")
    return hashlib.sha256(doc[start:end].encode("utf-8")).hexdigest()


def http_json(path: str, timeout: float = 10.0):
    with urllib.request.urlopen(CANOPY + path, timeout=timeout) as resp:  # noqa: S310 - fixed local URL
        return resp.status, json.loads(resp.read().decode("utf-8"))


# ── source-from-the-BUILT-app: the callback graph the leg actually serves ──────────────────────────────


def _outs(dep: dict) -> list:
    out = dep["output"]
    items = out.strip(".").split("...") if out.startswith("..") else [out]
    return [x.split("@")[0] for x in items]


def _pid(item: dict) -> str:
    iid = item["id"] if isinstance(item["id"], str) else json.dumps(item["id"], sort_keys=True)
    return f"{iid}.{item['property']}"


def built_app_graph() -> dict:
    """Read /_dash-dependencies and answer (a)-(c) off the served graph, not the source text."""
    try:
        _st, deps = http_json(DASH + "_dash-dependencies")
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        return {"ok": False, "why": f"{type(exc).__name__}: {exc}"[:200]}
    by_input: dict = {}
    for k, d in enumerate(deps):
        for i in d["inputs"]:
            by_input.setdefault(_pid(i), []).append(k)

    def downstream(k: int) -> set:
        touched: set = set()
        frontier = [k]
        while frontier:
            nxt = []
            for c in frontier:
                for o in _outs(deps[c]):
                    if o in touched:
                        continue
                    touched.add(o)
                    nxt.extend(by_input.get(o, []))
            frontier = nxt
        return touched

    def summary(d: dict) -> dict:
        return {
            "outputs": _outs(d),
            "inputs": [_pid(i) for i in d["inputs"]],
            "state": [_pid(s) for s in d["state"]],
            "clientside": bool(d.get("clientside_function")),
            "prevent_initial_call": d.get("prevent_initial_call"),
            "running": d.get("running"),
        }

    target = [d for d in deps if d["output"].startswith(OUT_PREFIX)]
    fts = summary(target[0]) if target else None
    writers = {}
    for inp in (fts["inputs"] if fts else []):
        writers[inp] = [summary(d) for d in deps if inp in _outs(d)]
    interval_refs = [summary(d) for d in deps if any(INTERVAL_ID + "." in x for x in _outs(d) + [_pid(i) for i in d["inputs"]] + [_pid(s) for s in d["state"]])]
    claimers = {}
    for inp in (fts["inputs"] if fts else []):
        claimers[inp] = [summary(deps[k]) for k in range(len(deps)) if inp in downstream(k)]
    return {
        "ok": True,
        "n_callbacks": len(deps),
        "fetch_training_state": fts,
        "fetch_training_state_count": len(target),
        "registered_writers_of_each_input": writers,
        "every_callback_referencing_the_interval": interval_refs,
        "callbacks_whose_downstream_closure_reaches_each_input": claimers,
    }


def api_state_pair() -> dict:
    """Two consecutive /api/state GETs: which keys differ (the claim: the value is new every call)."""
    try:
        _s1, a = http_json("/api/state")
        _s2, b = http_json("/api/state")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "why": f"{type(exc).__name__}: {exc}"[:200]}
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    keep = ("status", "phase", "candidate_pool_status", "candidate_pool_phase", "candidate_pool_size", "candidate_epoch", "current_epoch", "timestamp")
    return {"ok": True, "differing_keys": diff, "first": {k: a.get(k) for k in keep}, "second_timestamp": b.get("timestamp")}


# ── in-page instruments ────────────────────────────────────────────────────────────────────────────────

INIT_SCRIPT = r"""
(() => {
  if (window.__A3) return;
  const T0 = performance.now();
  const A3 = window.__A3 = {T0, epochT0: performance.timeOrigin + T0, wire: [], other: {}, otherN: 0, ev: [], lc: [], notes: []};
  const now = () => performance.now() - T0;
  const HEAD = '{"output":"..candidate-metrics-panel-training-state-store.data';
  const origFetch = window.fetch.bind(window);
  let seq = 0;
  window.fetch = function (input, init) {
    const url = (typeof input === 'string') ? input : ((input && input.url) || '');
    if (url.indexOf('_dash-update-component') === -1) return origFetch(input, init);
    const body = (init && typeof init.body === 'string') ? init.body : '';
    if (!body.startsWith(HEAD)) {
      A3.otherN++;
      const k = body.slice(11, 90);
      A3.other[k] = (A3.other[k] || 0) + 1;
      return origFetch(input, init);
    }
    const rec = {seq: ++seq, t_start: now()};
    try {
      const p = JSON.parse(body);
      rec.changed = p.changedPropIds;
      rec.inputs = (p.inputs || []).map(i => [i.id, i.property, i.value]);
    } catch (e) { rec.parse_err = String(e).slice(0, 80); }
    A3.wire.push(rec);
    const pr = origFetch(input, init);
    pr.then(res => {
      rec.t_headers = now();
      rec.http = res.status;
      if (res.status === 200) {
        res.clone().json().then(d => {
          rec.t_body = now();
          try {
            const r = (d && d.response) || {};
            const s = r['candidate-metrics-panel-training-state-store'];
            const sd = s && s.data;
            rec.ts = (sd && sd.timestamp !== undefined) ? sd.timestamp : null;
            if (sd) {
              rec.f = {status: sd.status, phase: sd.phase, cps: sd.candidate_pool_status,
                       cpp: sd.candidate_pool_phase, size: sd.candidate_pool_size, ce: sd.candidate_epoch};
            }
            rec.hist = !!r['candidate-metrics-panel-pool-history-store'];
          } catch (e) { rec.body_err = String(e).slice(0, 80); }
        }, e => { rec.body_err = String(e).slice(0, 80); });
      }
    }, e => { rec.t_fail = now(); rec.fail = String(e).slice(0, 80); });
    return pr;
  };
})();
"""

SUBSCRIBE = r"""
(cfg) => {
  const A3 = window.__A3, s = window.store;
  if (!A3 || !s) return {ok: false, why: !A3 ? 'no recorder' : 'no window.store'};
  if (A3.unsub) return {ok: true, already: true};
  const now = () => performance.now() - A3.T0;
  const propsAt = (layout, p) => {
    if (!p) return undefined;
    let o = layout;
    for (let i = 0; i < p.length; i++) { if (o == null) return undefined; o = o[p[i]]; }
    return o ? o.props : undefined;
  };
  const mine = cb => { const o = cb && cb.callback && cb.callback.output; return typeof o === 'string' && o.startsWith(cfg.outPrefix); };
  const cur = {ts: 'unset', n: 'unset', iv: 'unset', dis: 'unset', tab: 'unset', hl: 'unset', ip: 'unset'};
  let lastLayout = null, lastPaths = null, lastCbs = null, prevW = new Set();
  const cnt = {r: -1, p: -1, b: -1, e: -1};
  const onChange = () => {
    const st = s.getState(), t = now();
    let tsChanged = false;
    if (st.layout !== lastLayout || st.paths !== lastPaths) {
      lastLayout = st.layout; lastPaths = st.paths;
      const P = (st.paths && st.paths.strs) || {};
      const sp = propsAt(st.layout, P[cfg.store]);
      const ip = propsAt(st.layout, P[cfg.interval]);
      const tp = propsAt(st.layout, P[cfg.tabs]);
      const hp = propsAt(st.layout, P[cfg.hist]);
      const ts = sp === undefined ? 'nostore' : ((sp.data && typeof sp.data === 'object' && sp.data.timestamp !== undefined) ? sp.data.timestamp : null);
      const n = ip ? ip.n_intervals : 'nointerval';
      const iv = ip ? ip.interval : 'nointerval';
      const dis = ip ? Boolean(ip.disabled) : 'nointerval';
      const tab = tp ? tp.active_tab : 'notabs';
      const hl = hp ? (Array.isArray(hp.data) ? hp.data.length : null) : 'nohist';
      const ipath = P[cfg.interval] ? P[cfg.interval].join('/') : 'nopath';
      if (ts !== cur.ts) { A3.ev.push({t, k: 'ts', v: ts}); cur.ts = ts; tsChanged = true; }
      if (n !== cur.n) {
        const c = st.callbacks;
        A3.ev.push({t, k: 'n', v: n, pool: [c.requested.length, c.prioritized.length, c.blocked.length, c.executing.length, c.watched.length, c.executed.length]});
        cur.n = n;
      }
      if (iv !== cur.iv) { A3.ev.push({t, k: 'iv', v: iv}); cur.iv = iv; }
      if (dis !== cur.dis) { A3.ev.push({t, k: 'dis', v: dis}); cur.dis = dis; }
      if (tab !== cur.tab) { A3.ev.push({t, k: 'tab', v: tab}); cur.tab = tab; }
      if (hl !== cur.hl) { A3.ev.push({t, k: 'hl', v: hl}); cur.hl = hl; }
      if (ipath !== cur.ip) { A3.ev.push({t, k: 'ipath', v: ipath}); cur.ip = ipath; }
    }
    if (cfg.lifecycle && st.callbacks !== lastCbs) {
      lastCbs = st.callbacks;
      const c = st.callbacks;
      const count = key => { let m = 0; const L = c[key] || []; for (let i = 0; i < L.length; i++) if (mine(L[i])) m++; return m; };
      const r = count('requested'), p = count('prioritized'), b = count('blocked'), e = count('executing');
      const W = new Set(); for (const cb of c.watched) if (mine(cb)) W.add(cb.executionPromise);
      const X = new Set(); for (const cb of c.executed) if (mine(cb)) X.add(cb.executionPromise);
      const S = new Set(); for (const cb of (c.stored || [])) if (mine(cb)) S.add(cb.executionPromise);
      for (const pm of prevW) {
        if (!W.has(pm)) {
          const done = X.has(pm) || S.has(pm) || tsChanged;
          A3.lc.push({t, k: done ? 'w-done' : 'w-drop', r, p, e});
        }
      }
      for (const pm of W) if (!prevW.has(pm)) A3.lc.push({t, k: 'w+', r, p, e});
      prevW = W;
      if (r !== cnt.r || p !== cnt.p || b !== cnt.b || e !== cnt.e) {
        A3.lc.push({t, k: 'cnt', r, p, b, e, w: W.size, x: X.size});
        cnt.r = r; cnt.p = p; cnt.b = b; cnt.e = e;
      }
    }
  };
  A3.unsub = s.subscribe(onChange);
  onChange();
  return {ok: true, t: now()};
}
"""

# The Interval's / Store's OWN setProps (the DashWrapper path), found by a React fiber walk; the idiom is
# the one in util/ad-hoc/e2e_f039_supersession_test.py. Falls back to dash_clientside.set_props.
SETPROPS = r"""
(cfg) => {
  const {id, payload} = cfg;
  const A3 = window.__A3;
  const now = () => performance.now() - A3.T0;
  function fiberOf(el) {
    for (const k in el) {
      if (k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$') || k.startsWith('__reactContainer$')) return el[k];
    }
    return null;
  }
  const root = document.querySelector('#react-entry-point') || document.body;
  const stack = [fiberOf(root)];
  const seen = new Set();
  let hops = 0, found = false;
  while (stack.length && hops < 600000) {
    const n = stack.pop();
    hops++;
    if (!n || seen.has(n)) continue;
    seen.add(n);
    const mp = n.memoizedProps;
    if (mp && mp.id === id) {
      found = true;
      if (typeof mp.setProps === 'function') {
        try { mp.setProps(payload); return {ok: true, via: 'fiber memoizedProps.setProps', hops, t: now()}; }
        catch (e) { return {ok: false, err: String(e).slice(0, 160), hops, t: now()}; }
      }
    }
    if (n.child) stack.push(n.child);
    if (n.sibling) stack.push(n.sibling);
  }
  if (window.dash_clientside && typeof window.dash_clientside.set_props === 'function') {
    try { window.dash_clientside.set_props(id, payload); return {ok: true, via: 'dash_clientside.set_props (fiber walk ' + (found ? 'found no setProps' : 'did not find id') + ')', hops, t: now()}; }
    catch (e) { return {ok: false, err: String(e).slice(0, 160), hops, t: now()}; }
  }
  return {ok: false, err: found ? 'found but no setProps' : 'not found', hops, t: now()};
}
"""

READ_LAYOUT = r"""
(cfg) => {
  const s = window.store; if (!s) return null;
  const st = s.getState(); const P = (st.paths && st.paths.strs) || {};
  const at = p => { if (!p) return undefined; let o = st.layout; for (const k of p) { if (o == null) return undefined; o = o[k]; } return o ? o.props : undefined; };
  const ip = at(P[cfg.interval]) || {}, sp = at(P[cfg.store]) || {}, tp = at(P[cfg.tabs]) || {};
  const txt = id => { const el = document.getElementById(id); return el ? el.textContent : null; };
  return {
    t: performance.now() - window.__A3.T0,
    interval: ip.interval, disabled: ip.disabled, n_intervals: ip.n_intervals,
    store_ts: sp.data && typeof sp.data === 'object' ? (sp.data.timestamp === undefined ? null : sp.data.timestamp) : null,
    active_tab: tp.active_tab,
    lifecycle: st.appLifecycle,
    dom: {badge: txt('candidate-metrics-panel-status-badge'), phase: txt('candidate-metrics-panel-phase'),
          pool_size: txt('candidate-metrics-panel-pool-size'), visibility: document.visibilityState},
  };
}
"""

CFG = {"store": STORE_ID, "interval": INTERVAL_ID, "tabs": TABS_ID, "hist": HIST_ID, "outPrefix": OUT_PREFIX}


def page_now(page) -> float:
    return page.evaluate("() => performance.now() - window.__A3.T0")


def ensure_no_modal(page, tries: int = 10) -> int:
    for i in range(tries):
        n_open = page.evaluate("() => [...document.querySelectorAll('[role=dialog]')].filter(x => (x.className||'').includes('show')).length")
        if not n_open:
            return i
        page.evaluate("() => { const b = document.getElementById('welcome-modal-close'); if (b) b.click(); }")
        page.wait_for_timeout(700)
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)
    return -1


# ── analysis ───────────────────────────────────────────────────────────────────────────────────────────


def _median(xs):
    return round(statistics.median(xs), 3) if xs else None


def analyse(raw: dict, phases: list, sentinel: dict, tab_switch_t: float) -> dict:
    ev = raw["ev"]
    wire = raw["wire"]
    ticks = [(e["t"], e["v"], e.get("pool")) for e in ev if e["k"] == "n" and isinstance(e["v"], (int, float))]
    ts_events = [(e["t"], e["v"]) for e in ev if e["k"] == "ts"]
    tab_events = [(e["t"], e["v"]) for e in ev if e["k"] == "tab"]
    observed_first: dict = {}
    for t, v in ts_events:
        if isinstance(v, (int, float)) and v != SENTINEL_TS and v not in observed_first:
            observed_first[v] = t

    def tab_at(t):
        cur = None
        for te, v in tab_events:
            if te <= t:
                cur = v
            else:
                break
        return cur

    per_phase = []
    for ph in phases:
        t0, t1, period = ph["t_change"], ph["t_end"], ph["period_ms"]
        ph_ticks = [x for x in ticks if t0 < x[0] < t1]
        t_first = ph_ticks[0][0] if ph_ticks else None
        gaps = [(b[0] - a[0]) / 1000.0 for a, b in zip(ph_ticks, ph_ticks[1:])]
        med_gap = _median(gaps)
        if period >= 4000:
            took_cadence = med_gap is not None and 0.8 * period / 1000 <= med_gap <= 1.5 * period / 1000 + 1.0
        else:
            took_cadence = med_gap is not None and med_gap < 3.0
        took = bool(ph["setprops_ok"] and ph["interval_readback"] == period and took_cadence)
        w0 = t_first
        w1 = t1 - TAIL_S * 1000
        tick_reqs = [r for r in wire if TICK_PROP in (r.get("changed") or []) and w0 is not None and w0 <= r["t_start"] < w1]
        issued = [r for r in tick_reqs if r.get("http") == 200 and isinstance(r.get("ts"), (int, float))]
        landed = [r for r in issued if r["ts"] in observed_first]
        apply_lat = [round((observed_first[r["ts"]] - r["t_body"]) / 1000.0, 3) for r in landed if r.get("t_body") is not None]
        rtt = [round((r["t_body"] - r["t_start"]) / 1000.0, 3) for r in issued if r.get("t_body") is not None]
        distinct_ts_in_phase = sorted({v for t, v in ts_events if t0 <= t < t1 and isinstance(v, (int, float)) and v != SENTINEL_TS})
        all_tick_reqs_in_phase = [r for r in wire if TICK_PROP in (r.get("changed") or []) and t0 <= r["t_start"] < t1]
        tab_ok = w0 is not None and all(v == "candidates" for te, v in tab_events if w0 <= te < w1) and tab_at(w0) == "candidates"
        pools = [p for (t, _v, p) in ph_ticks if p]
        per_phase.append({
            "period_ms": period,
            "t_change_s": round(t0 / 1000.0, 3),
            "t_end_s": round(t1 / 1000.0, 3),
            "setprops": ph.get("setprops"),
            "interval_readback": ph["interval_readback"],
            "ticks_delivered_in_phase": len(ph_ticks),
            "n_intervals_span": [ph_ticks[0][1], ph_ticks[-1][1]] if ph_ticks else None,
            "median_tick_gap_s": med_gap,
            "tick_gaps_s": [round(g, 3) for g in gaps],
            "took": took,
            "scored_window_s": [round(w0 / 1000.0, 3) if w0 is not None else None, round(w1 / 1000.0, 3)],
            "tick_requests_in_phase_unscored": len(all_tick_reqs_in_phase),
            "issued_scored": len(issued),
            "landed_scored": len(landed),
            "landed_fraction": round(len(landed) / len(issued), 3) if issued else None,
            "round_trip_s_median": _median(rtt),
            "round_trip_s_max": max(rtt) if rtt else None,
            "wire_to_apply_s_of_landed": apply_lat,
            "distinct_store_timestamps_observed_in_phase": len(distinct_ts_in_phase),
            "active_tab_candidates_throughout_scored_window": tab_ok,
            "pool_lengths_at_ticks_median": [int(statistics.median(col)) for col in zip(*pools)] if pools else None,
            "pool_lengths_at_ticks_max": [max(col) for col in zip(*pools)] if pools else None,
            # diagnostic only (not in the rule): a scored request issued < 1 s after the change may have been
            # triggered by an old-period tick that fired before the new timer bound
            "scored_requests_issued_within_1s_of_change": sum(1 for r in issued if r["t_start"] - t0 < 1000.0),
            "scored_requests": [
                {"seq": r["seq"], "t_start_s": round(r["t_start"] / 1000.0, 3), "rtt_s": round((r["t_body"] - r["t_start"]) / 1000.0, 3) if r.get("t_body") is not None else None,
                 "landed": r["ts"] in observed_first, "apply_s": round((observed_first[r["ts"]] - r["t_body"]) / 1000.0, 3) if (r["ts"] in observed_first and r.get("t_body") is not None) else None}
                for r in issued
            ],
            "dom_at_end": ph.get("dom_at_end"),
        })

    by_period: dict = {}
    for p in per_phase:
        agg = by_period.setdefault(p["period_ms"], {"issued": 0, "landed": 0})
        agg["issued"] += p["issued_scored"]
        agg["landed"] += p["landed_scored"]
    for agg in by_period.values():
        agg["L"] = round(agg["landed"] / agg["issued"], 3) if agg["issued"] else None

    # positive controls
    tab_reqs = [r for r in wire if TAB_PROP in (r.get("changed") or []) and r["t_start"] >= tab_switch_t]
    tab_write_landed = any(isinstance(r.get("ts"), (int, float)) and r["ts"] in observed_first for r in tab_reqs)
    sentinel_seen = any(v == SENTINEL_TS for _t, v in ts_events)
    any_ts_change = len([1 for _t, v in ts_events if isinstance(v, (int, float))]) > 0
    pc = {
        "tab_switch_requests": [{k: r.get(k) for k in ("seq", "t_start", "http", "ts", "changed")} for r in tab_reqs[:3]],
        "tab_switch_write_landed": tab_write_landed,
        "sentinel_setprops": sentinel,
        "sentinel_seen_by_reader": sentinel_seen,
        "reader_ever_saw_a_timestamp": any_ts_change,
    }

    # verdict ladder (as fixed in the docstring)
    def cls(L):
        if L is None:
            return None
        return "lands" if L >= 0.5 else ("does-not-land" if L <= 0.1 else "partial")

    L = {p: by_period[p]["L"] for p in by_period}
    if any(not ph["setprops_ok"] for ph in phases) or any(not p["took"] for p in per_phase):
        verdict = "SETPROPS-FAILED"
    elif not (tab_write_landed or sentinel_seen):
        verdict = "POSITIVE-CONTROL-FAILED"
    elif any(by_period.get(p, {"issued": 0})["issued"] < 3 for p in (1000, 4000, 10000)) or not all(p["active_tab_candidates_throughout_scored_window"] for p in per_phase):
        verdict = "INDETERMINATE"
    elif cls(L.get(1000)) == "lands":
        verdict = "CONTROL-APPLIES"
    elif all(cls(L.get(p)) == "does-not-land" for p in (1000, 4000, 10000)):
        verdict = "NOT-PERIOD-BOUND"
    elif cls(L.get(1000)) == "does-not-land" and cls(L.get(10000)) == "lands":
        verdict = "PERIOD-BOUND"
    else:
        verdict = "INDETERMINATE"

    lc = raw.get("lc") or []
    lc_summary = {
        "w_plus": sum(1 for e in lc if e["k"] == "w+"),
        "w_done": sum(1 for e in lc if e["k"] == "w-done"),
        "w_drop": sum(1 for e in lc if e["k"] == "w-drop"),
        "w_drop_with_new_instance_queued": sum(1 for e in lc if e["k"] == "w-drop" and (e.get("r", 0) + e.get("p", 0) + e.get("e", 0)) > 0),
    }
    lc_by_phase = []
    for ph in phases:
        seg = [e for e in lc if ph["t_change"] <= e["t"] < ph["t_end"]]
        lc_by_phase.append({"period_ms": ph["period_ms"], "w_plus": sum(1 for e in seg if e["k"] == "w+"), "w_done": sum(1 for e in seg if e["k"] == "w-done"), "w_drop": sum(1 for e in seg if e["k"] == "w-drop")})

    return {
        "verdict": verdict,
        "L_by_period": by_period,
        "per_phase": per_phase,
        "positive_controls": pc,
        "lifecycle_supplementary": {"total": lc_summary, "by_phase": lc_by_phase},
        "wire_totals": {
            "this_callback_requests": len(wire),
            "other_dash_requests": raw.get("otherN"),
            "http_non_200": sum(1 for r in wire if r.get("http") not in (200, None)),
            "fetch_failures": sum(1 for r in wire if r.get("fail")),
        },
    }


def network_vs_page(wire: list, net: list, epoch_t0, phases: list) -> dict:
    """Diagnostic only (added after run1): where does the page-observed round trip go?

    The network record is the browser network layer's own timing (Playwright ``request.timing``: ms
    relative to ``startTime``, which is epoch ms) -- it is not delayed by the page's main thread. The
    page record is the in-page fetch wrapper (performance.now() since T0; epoch = epoch_t0 + t).
    Matched on (n_intervals input value, changedPropIds).
    """
    if epoch_t0 is None:
        return {"ok": False, "why": "no epoch alignment"}

    def key_page(r):
        nval = next((i[2] for i in (r.get("inputs") or []) if i[1] == "n_intervals"), None)
        return (nval, tuple(r.get("changed") or []))

    by_key: dict = {}
    for x in net:
        if "err" in x:
            continue
        by_key.setdefault((x["n"], tuple(x["changed"] or [])), []).append(x)

    def phase_of(t):
        for p in phases:
            if p["t_change"] <= t < p["t_end"]:
                return p["period_ms"]
        return "outside-phases"

    rows = []
    for r in wire:
        cands = by_key.get(key_page(r))
        if not cands or r.get("t_body") is None:
            continue
        x = cands.pop(0)
        st_ep = x["start_epoch_ms"]
        rows.append({
            "phase": phase_of(r["t_start"]),
            "net_ttfb_ms": round(x["responseStart"], 1) if x["responseStart"] is not None else None,
            "net_total_ms": round(x["responseEnd"], 1) if x["responseEnd"] is not None else None,
            "page_call_to_net_start_ms": round(st_ep - (epoch_t0 + r["t_start"]), 1),
            "page_headers_after_net_headers_ms": round((epoch_t0 + r["t_headers"]) - (st_ep + x["responseStart"]), 1) if x["responseStart"] is not None else None,
            "page_body_after_net_end_ms": round((epoch_t0 + r["t_body"]) - (st_ep + x["responseEnd"]), 1) if x["responseEnd"] is not None else None,
            "page_total_ms": round(r["t_body"] - r["t_start"], 1),
        })
    summary: dict = {}
    for row in rows:
        summary.setdefault(str(row["phase"]), []).append(row)
    out = {}
    for ph, lst in summary.items():
        def med(k, lst=lst):
            vals = [v[k] for v in lst if v[k] is not None]
            return round(statistics.median(vals), 1) if vals else None

        def mx(k, lst=lst):
            vals = [v[k] for v in lst if v[k] is not None]
            return max(vals) if vals else None
        out[ph] = {"n": len(lst), **{f"{k}_median": med(k) for k in ("net_ttfb_ms", "net_total_ms", "page_call_to_net_start_ms", "page_headers_after_net_headers_ms", "page_body_after_net_end_ms", "page_total_ms")},
                   "net_total_ms_max": mx("net_total_ms"), "page_total_ms_max": mx("page_total_ms")}
    return {"ok": True, "matched": len(rows), "network_records": len(net), "by_phase": out, "rows": rows}


# ── driver ─────────────────────────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="Lane A3: candidate state-store landing vs trigger period")
    ap.add_argument("--tag", default="run1", help="suffix for the JSON artifact")
    ap.add_argument("--no-lifecycle", action="store_true", help="omit the supplementary callback-list reader")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    started = datetime.now(timezone.utc).isoformat()
    out = {
        "probe": os.path.relpath(os.path.abspath(__file__), _REPO),
        "tag": args.tag,
        "started_utc": started,
        "canopy": CANOPY,
        "verdict_rule_sha256": verdict_rule_sha256(),
        "plan": PLAN,
        "tail_s": TAIL_S,
        "lifecycle_reader": not args.no_lifecycle,
    }
    try:
        _s, health = http_json("/v1/health")
        out["serving"] = {k: health.get(k) for k in ("git_sha", "build_date", "version", "training_active", "backend_status")}
    except Exception as exc:  # noqa: BLE001
        out["serving"] = {"ok": False, "why": str(exc)[:200]}
    log(f"serving: {json.dumps(out['serving'])}")
    out["built_app_graph"] = built_app_graph()
    out["api_state_pair_before"] = api_state_pair()
    log(f"/api/state differing keys between two GETs: {out['api_state_pair_before'].get('differing_keys')}")

    phases: list = []
    sentinel: dict = {}
    raw: dict = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        ctx = browser.new_context(viewport={"width": 1600, "height": 1100})  # fresh context: no shared localStorage
        ctx.add_init_script(INIT_SCRIPT)
        page = ctx.new_page()
        console_errors: list = []
        page.on("console", lambda m: console_errors.append(m.text[:240]) if m.type == "error" else None)
        net: list = []

        def on_finished(req) -> None:
            try:
                if "_dash-update-component" not in req.url:
                    return
                body = req.post_data or ""
                if not body.startswith('{"output":"' + OUT_PREFIX):
                    return
                p = json.loads(body)
                tim = req.timing
                nval = next((i.get("value") for i in p.get("inputs", []) if i.get("property") == "n_intervals"), None)
                net.append({"n": nval, "changed": p.get("changedPropIds"), "start_epoch_ms": tim.get("startTime"),
                            "requestStart": tim.get("requestStart"), "responseStart": tim.get("responseStart"), "responseEnd": tim.get("responseEnd")})
            except Exception as exc:  # noqa: BLE001 - recorded, never raised
                net.append({"err": f"{type(exc).__name__}: {exc}"[:160]})

        page.on("requestfinished", on_finished)
        try:
            page.goto(CANOPY + DASH, wait_until="domcontentloaded", timeout=60_000)
            for _ in range(120):
                life = page.evaluate("() => window.store ? window.store.getState().appLifecycle : null")
                if life == "HYDRATED":
                    break
                page.wait_for_timeout(500)
            else:
                log("!! renderer never reached HYDRATED")
                return 2
            out["renderer_bundle"] = page.evaluate("() => [...document.scripts].map(s => s.src).filter(s => s.includes('dash_renderer'))")
            sub = page.evaluate(SUBSCRIBE, {**CFG, "lifecycle": not args.no_lifecycle})
            log(f"subscribe: {sub}")
            if not sub.get("ok"):
                return 2
            page.wait_for_timeout(8000)  # let the mount storm settle
            out["modal_attempts"] = ensure_no_modal(page)
            out["before_tab_switch"] = page.evaluate(READ_LAYOUT, CFG)
            log(f"before tab switch: {json.dumps(out['before_tab_switch'])}")
            tab_switch_t = page_now(page)
            clicked = page.evaluate("""(label) => { const t = [...document.querySelectorAll('[role=tab]')].find(x => x.textContent.trim() === label);
                                          if (!t) return false; t.click(); return true; }""", "Candidate Metrics")
            log(f"clicked Candidate Metrics tab: {clicked}")
            if not clicked:
                return 2
            # positive control 1: the tab-switch write must be seen by the reader (wait up to 30 s)
            pc1_t = None
            for _ in range(60):
                page.wait_for_timeout(500)
                snap = page.evaluate(READ_LAYOUT, CFG)
                if isinstance(snap.get("store_ts"), (int, float)):
                    pc1_t = snap["t"]
                    break
            out["after_tab_switch"] = page.evaluate(READ_LAYOUT, CFG)
            log(f"after tab switch: {json.dumps(out['after_tab_switch'])} (first timestamp seen at page t={pc1_t})")
            if out["after_tab_switch"].get("active_tab") != "candidates":
                log("!! tab did not become 'candidates'")

            for idx, (period, dur) in enumerate(PLAN):
                if idx == 0:
                    res = {"ok": True, "via": "none (opening control: interval already at its declared 1000 ms)", "t": page_now(page)}
                else:
                    res = page.evaluate(SETPROPS, {"id": INTERVAL_ID, "payload": {"interval": period}})
                page.wait_for_timeout(300)
                rb = page.evaluate(READ_LAYOUT, CFG)
                ph = {"period_ms": period, "t_change": res.get("t", page_now(page)), "setprops": res, "setprops_ok": bool(res.get("ok")), "interval_readback": rb.get("interval")}
                log(f"phase {idx + 1}/{len(PLAN)}: period={period} ms for {dur} s; setProps={json.dumps(res)}; readback interval={rb.get('interval')}")
                page.wait_for_timeout(int(dur * 1000) - 300)
                ph["t_end"] = page_now(page)
                ph["dom_at_end"] = page.evaluate(READ_LAYOUT, CFG)
                phases.append(ph)
                log(f"   end: n_intervals={ph['dom_at_end'].get('n_intervals')} store_ts={ph['dom_at_end'].get('store_ts')} tab={ph['dom_at_end'].get('active_tab')} dom={ph['dom_at_end'].get('dom')}")

            # positive control 2: the SENTINEL, written through the Store's own setProps, read by the same reader
            sentinel = page.evaluate(SETPROPS, {"id": STORE_ID, "payload": {"data": {"timestamp": SENTINEL_TS, "laneA3_sentinel": True}}})
            page.wait_for_timeout(1500)
            sentinel["readback"] = page.evaluate(READ_LAYOUT, CFG)
            log(f"sentinel: {json.dumps(sentinel)}")
            raw = page.evaluate("() => { const A = window.__A3; return {wire: A.wire, ev: A.ev, lc: A.lc, other: A.other, otherN: A.otherN, epochT0: A.epochT0}; }")
            out["console_errors_first20"] = console_errors[:20]
            out["console_error_count"] = len(console_errors)
        finally:
            browser.close()

    out["api_state_pair_after"] = api_state_pair()
    out["phases_raw"] = phases
    out["analysis"] = analyse(raw, phases, sentinel, tab_switch_t)
    out["network_vs_page_timing"] = network_vs_page(raw.get("wire") or [], net, raw.get("epochT0"), phases)
    out["raw"] = {"wire": raw.get("wire"), "ev": raw.get("ev"), "lc": raw.get("lc"), "other_top": sorted((raw.get("other") or {}).items(), key=lambda kv: -kv[1])[:40]}
    out["finished_utc"] = datetime.now(timezone.utc).isoformat()

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"2026-09-22_laneA3_candidate_tick_period_{args.tag}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    a = out["analysis"]
    log("")
    log(f"VERDICT: {a['verdict']}")
    log(f"L by period: {json.dumps(a['L_by_period'])}")
    for p in a["per_phase"]:
        log(
            f"  {p['period_ms']:>5} ms: ticks={p['ticks_delivered_in_phase']:>3} med_gap={p['median_tick_gap_s']}s took={p['took']} "
            f"issued={p['issued_scored']:>3} landed={p['landed_scored']:>3} distinct_ts_seen={p['distinct_store_timestamps_observed_in_phase']:>3} "
            f"rtt_med={p['round_trip_s_median']} apply={p['wire_to_apply_s_of_landed'][:6]}"
        )
    log(f"positive controls: {json.dumps(a['positive_controls'], default=str)[:600]}")
    log(f"lifecycle (supplementary): {json.dumps(a['lifecycle_supplementary'])}")
    nv = out["network_vs_page_timing"]
    log(f"network vs page timing (diagnostic): matched={nv.get('matched')} by_phase={json.dumps(nv.get('by_phase'))}")
    log(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
