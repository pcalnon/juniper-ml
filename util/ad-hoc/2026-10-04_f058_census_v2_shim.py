#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — instrument; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""The F-CANOPY-058 census v2 in-page shim: dash-renderer's callback lifecycle, read at the DISPATCH.

A library for ``2026-10-04_f058_census_v2_live.py``, ``…_synth_check.py`` and ``…_debug_probe.py``, which load
it by path (a dated file name cannot be imported).

Installed with Playwright's ``add_init_script``, so it runs before the page's own scripts. It traps the
assignment ``window.store = this.__store`` (``dash_renderer.dev.js:3798`` in dash 4.2.0) and wraps that
store's ``dispatch`` before any callback runs. The renderer's observers receive the store object itself
(``StoreObserver.notify`` calls ``o.observer(store)``) and read ``store.dispatch`` at each call, and the
watched observer's resolution uses the ``dispatch`` it read when the request entered ``watched``
(``:2667-2709``), so every lifecycle action after page load goes through the wrapper.

Why not a store SUBSCRIBER, as v1 did: an answer that carries no props enters and leaves ``executed`` inside
one synchronous dispatch, so a subscriber never sees it there and v1 scored it EVICTED (13 of 13 on a
synthetic app). The wrapper sees the action itself.

Per request of the FEED callback (``callback.output`` exactly ``FEED``), keyed by ``executionPromise``:

  W   ``Callbacks.AddWatched``: the request is in flight.
  A   ``Callbacks.RemoveWatched`` and ``Callbacks.AddExecuted`` for the same promise in ONE dispatched action
      tree: the response was taken (``:2707``). ``props`` records whether its ``executionResult.data`` carried
      any output, so a ``no_update`` answer (HTTP 200, empty data) is A with ``props=0``, never an eviction.
  X   ``Callbacks.RemoveWatched`` WITHOUT a matching ``AddExecuted``: the request was pruned from ``watched``
      before it resolved, so its response, when it lands, is discarded (``:2699-2704``). An EVICTION.

Writes to the lane's ``disabled``, every one, with the lane's value before and after the dispatch and the
action types that carried it: the ``running=`` guard (``ON_PROP_CHANGE``), the gate and the watchdog.

Watchdog fires, at the write: an ``AddExecuted`` of the callback whose output is ``LANE.disabled@…`` (the
duplicate output) whose ``executionResult.data[LANE].disabled === false``, with the lane's value before that
dispatch and ``window.__metricsStoreDisabledSince`` as it stood before the watchdog reset it. v1 read the lane
AFTER the fire's own write, and counted 0 of 2 real fires.

Gate writes: an ``AddExecuted`` of the callback whose outputs include ``LANE.disabled`` without ``@``, with the
value it wrote for this lane.
"""

SHIM = r"""
(() => {
  const cfg = window.__f058cfg || {};
  const FEED = cfg.feed || 'metrics-panel-metrics-store.data';
  const LANE = cfg.lane || 'metrics-store-interval';
  const T0 = Date.now();
  const R = window.__f058v2 = {t0: T0, installed: false, dispatches: 0, req: [], lane: [], fires: [], gate: [], errors: []};
  const outOf = (cb) => String(((cb && cb.callback) || {}).output || '');
  const isFeed = (cb) => outOf(cb) === FEED;
  const isWatchdog = (cb) => outOf(cb).indexOf(LANE + '.disabled@') !== -1;
  const isGate = (cb) => { const o = outOf(cb); return !isWatchdog(cb) && (o === LANE + '.disabled' || o.indexOf('..' + LANE + '.disabled..') !== -1 || o.indexOf('...' + LANE + '.disabled') !== -1); };
  const ids = new Map(); let seq = 0;
  const idOf = (cb) => { const k = cb && cb.executionPromise; if (!k) return 0; if (!ids.has(k)) ids.set(k, ++seq); return ids.get(k); };
  const laneProps = (s) => {
    const p = s && s.paths && s.paths.strs ? s.paths.strs[LANE] : null; let node = s ? s.layout : null;
    if (!p) return null; for (const k of p) { if (node == null) return null; node = node[k]; } return node && node.props ? node.props : null;
  };
  const laneDisabled = (s) => { const p = laneProps(s); return p ? p.disabled === true : null; };
  const flatten = (a, out) => { if (!a || typeof a !== 'object') return; if (a.type === 'Callbacks.Aggregate' && Array.isArray(a.payload)) { a.payload.forEach((x) => flatten(x, out)); } else { out.push(a); } };
  const hasProps = (res) => { const d = res && res.data; return d && typeof d === 'object' ? Object.keys(d).length : 0; };
  const laneValueIn = (res) => { const d = res && res.data; const v = d && d[LANE]; return v && Object.prototype.hasOwnProperty.call(v, 'disabled') ? v.disabled : undefined; };
  function wrap(store) {
    if (!store || store.__f058v2) return;
    const orig = store.dispatch;
    store.dispatch = function (action) {
      R.dispatches += 1;
      let now, before, sinceBefore, flat;
      try {
        now = Date.now() - T0; before = laneDisabled(store.getState());
        sinceBefore = window.__metricsStoreDisabledSince || null; flat = []; flatten(action, flat);
      } catch (e) { R.errors.push(String(e)); flat = []; }
      const out = orig.apply(this, arguments);
      try {
        const removedW = new Map(), addedE = new Map(), addedW = new Set();
        for (const a of flat) {
          const p = Array.isArray(a.payload) ? a.payload : [];
          if (a.type === 'Callbacks.AddWatched') { for (const cb of p) if (isFeed(cb)) { const id = idOf(cb); addedW.add(id); R.req.push([now, 'W', id, 0]); } }
          else if (a.type === 'Callbacks.RemoveWatched') { for (const cb of p) if (isFeed(cb)) removedW.set(idOf(cb), cb); }
          else if (a.type === 'Callbacks.AddExecuted') {
            for (const cb of p) {
              if (isFeed(cb)) addedE.set(idOf(cb), cb);
              else if (isWatchdog(cb)) { const v = laneValueIn(cb.executionResult); if (v === false) R.fires.push([now, before, sinceBefore ? sinceBefore - T0 : null]); }
              else if (isGate(cb)) { const v = laneValueIn(cb.executionResult); if (v !== undefined) R.gate.push([now, before, v]); }
            }
          }
        }
        // A: taken (moved to executed). R: pruned and re-added in the same dispatch (pruneCallbacks' modified
        // copy), still in flight. X: removed with neither: its response will be discarded, an EVICTION.
        for (const [id] of removedW) { const e = addedE.get(id); R.req.push([now, e ? 'A' : (addedW.has(id) ? 'R' : 'X'), id, e ? hasProps(e.executionResult) : 0]); }
        const after = laneDisabled(store.getState());
        if (after !== before) R.lane.push([now, before, after, flat.map((a) => a.type).join('+')]);
      } catch (e) { R.errors.push(String(e)); }
      return out;
    };
    store.__f058v2 = true; R.installed = true;
  }
  let st;
  Object.defineProperty(window, 'store', {configurable: true, enumerable: true, get() { return st; }, set(v) { st = v; wrap(v); }});
})();
"""


def classify(req_log):
    """Fold the per-dispatch request log into one record per request: {id: {tW, tEnd, end, props}}."""
    recs = {}
    for t, kind, rid, props in req_log:
        r = recs.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None, "props": None})
        if kind == "W":
            if r["tW"] is None:
                r["tW"] = t
        elif kind == "R":
            continue
        elif r["end"] is None:
            r["end"], r["tEnd"], r["props"] = kind, t, props
    return recs


def window_stats(recs, lo_ms, hi_ms):
    """Requests that ENTERED watched in [lo, hi) and ended by hi: answered (A) or evicted (X)."""
    rows = sorted((r for r in recs.values() if r["tW"] is not None and lo_ms <= r["tW"] < hi_ms and r["end"] is not None and r["tEnd"] <= hi_ms), key=lambda r: r["tW"])
    answered = [r for r in rows if r["end"] == "A"]
    evicted = [r for r in rows if r["end"] == "X"]
    run = best = 0
    for r in rows:
        run = run + 1 if r["end"] == "X" else 0
        best = max(best, run)
    t_ans = sorted(r["tEnd"] for r in answered)
    gaps = sorted(b - a for a, b in zip(t_ans, t_ans[1:]))
    return {
        "resolved": len(rows),
        "answered": len(answered),
        "answered_with_props": sum(1 for r in answered if r["props"]),
        "evicted": len(evicted),
        "evicted_fraction": round(len(evicted) / len(rows), 3) if rows else None,
        "longest_evicted_run": best,
        "cadence_ms_median": gaps[len(gaps) // 2] if gaps else None,
    }
