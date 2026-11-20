#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-035 -- does an UNOPPOSED response land? The discriminator for supersession.

THE QUESTION, AND WHY THE EXISTING INSTRUMENTS CANNOT ANSWER IT.

``util/ad-hoc/2026-09-08_f035_supersession_test.py`` disables ``fast-update-interval``
and the store fills (``APPLIED-UNCONTENDED``, two replicates). That intervention
removes **all ten** callbacks on that Interval at once, so it cannot separate:

  H1  SUPERSESSION -- dash-renderer retires an in-flight call when the SAME callback
      is re-requested (``eDuplicates`` at dash_renderer.dev.js:3026 concatenates
      ``requested`` last, so the newcomer survives and the in-flight one is dropped;
      its response is discarded on arrival). Driven only by this callback's own
      re-request rate.
  H2  FAILED / ABORTED RESPONSE -- ``Callback failed: the server did not respond``
      appeared in 2 of 4 failing probe runs and none of the successful one
      (ledger, F-CANOPY-035). Produces the same signature and needs a different fix.
  H3  PROMOTION STARVATION -- the fast lane's other nine callbacks saturate the
      renderer so this one's output is never applied.

``2026-09-05_f035_store_write_latency_probe.py`` measures duration/gap/overlap but
brackets the store only at window START and END, so it can say "69% of writes were
overlapped" and cannot say whether the **31% that were not** landed. That 31% is the
load-bearing number: the ledger records nine unopposed responses in a window that
ended with ``len=0``, and supersession cannot explain a response nothing superseded.

WHAT THIS PROBE ADDS: a PER-RESPONSE bracket. Every invocation of the store's writer
is timed from its own request body, classified opposed / unopposed against the other
invocations' start times, and matched against a continuous in-page trace of the
store's length. That turns "the store was empty at the end" into "response #7 arrived
at t=12.4 s with 71 rows, nothing was in flight against it, and the store did not
move" -- which refutes H1 as a sufficient cause, or fails to.

THE OPPOSITION BOUNDARY -- corrected 2026-09-10 after run 1, from the shipped bundle.

Run 1 classified opposition by the next **HTTP request start** and returned
``SUPERSESSION-INSUFFICIENT`` on 25 of 25 unopposed responses failing to land. **That
verdict is an artifact of the wrong boundary and is superseded by this module.** Read
from ``dash_renderer.dev.js`` (the unminified bundle ships in JuniperCanopy1):

  :2676  a deferred callback enters ``watched`` when its fetch is initiated.
  :2698  on resolution it must STILL be in ``watched``:
         ``currentCb = find(cb => ..., watched); if (currentCb) {...}`` -- else the
         observer RETURNS and the result is discarded, never applied.
  :3027  ``wDuplicates = map(g => g.slice(0,-1), groupBy(getUniqueIdentifier,
         concat(watched, requested)))`` -- ``requested`` is concatenated LAST, so a
         newly REQUESTED invocation evicts the in-flight one from ``watched``.

So the displacing event is **a new entry in ``requested``**, created by the Interval
TICK -- which happens on the 1000 ms cadence whether or not the previous request has
even been sent. A response is vulnerable for its whole in-flight span, and the correct
question is "did a TICK fall inside this call's flight?", not "did another request
start inside it?". This probe therefore records ``fast-update-interval.n_intervals``
transitions and classifies on those.

It also explains a number the ledger read the other way: ``everSeen {watched: 1}`` --
two concurrent entries never observed -- was taken as evidence AGAINST supersession.
The eviction is synchronous with the insertion (one reducer pass), so two concurrent
entries can NEVER be observed. That observation is what this mechanism predicts.

Because ``getUniqueIdentifier`` hashes ONE callback's own inputs/outputs/state, the
other nine fast-lane callbacks are different identities and cannot appear in its
group -- so they cannot evict it. H3 is excluded at the source, not by an A/B.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN UNDER THIS BOUNDARY, and deliberately not
a free parameter. (This arc has twice archived contradictory verdicts for one
phenomenon because the rule was edited after the data came in.)

  NO-WRITES               zero store-writing invocations observed -> the instrument
                          found nothing; its own control failed; no verdict.
  NO-TICK-TRACE           the tick counter was not observable -> the boundary cannot
                          be applied; no verdict.
  ALL-LANDED              every response landed -> the defect did not reproduce in
                          this window; no verdict on mechanism.
  NO-TICK-FREE            every response had a tick inside its flight -> consistent
                          with supersession but not discriminating on its own; the
                          quantitative prediction (duration vs 1000 ms) is reported.
  SUPERSESSION-INSUFFICIENT   >=1 TICK-FREE response did NOT land. Nothing could have
                          evicted it, so H1 does not account for the outcome.
  SUPERSESSION-CONSISTENT every tick-free response landed AND >=1 tick-crossed
                          response did not. The outcome tracks eviction exactly.

H2 is scored on a SEPARATE axis and never folded into the verdict above: console
errors are counted and correlated with non-landing responses by timestamp. A probe
that merges two hypotheses into one string cannot report that both fired.

PERTURBATION. Sampling the renderer changes the race it measures (ledger trap: an
``evaluate`` on a saturated topology page costs ~22 s, and the lifecycle probe's
per-notify ``JSON.stringify`` perturbed its own subject). So the store trace is taken
by an in-page Redux ``subscribe`` that reads ONE length and appends only on CHANGE,
plus a 1 Hz heartbeat to prove liveness -- harvested with a single ``evaluate`` after
the window closes. Network timing is taken on the Python side and touches the page
not at all.

POSITIVE CONTROL. The window ends by disabling ``fast-update-interval`` via
``setProps`` -- the 2026-09-08 intervention -- and expects the store to fill. If it
does not, the observer could not have seen a fill that occurred, and every zero above
is uninterpretable. Reported as ``control_fill``; a run whose control fails scores
CONTROL-FAILED regardless of anything else.

IDENTITY. Records the commit each leg SERVES (canopy and cascor ``/v1/health``) and
the page's own ``active_tab``, per the ledger's traps: a ``git_sha`` stamp lies when
the tree is dirty, and a browser artifact that names no tab cannot be read later
(F-CANOPY-051: the persisted tab is browser-global).

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-10_f035_unopposed_response_test.py --window 90
"""

import argparse
import importlib.util
import json
import os
import statistics
import sys
import time
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")

log = _seg17.log
CANOPY = _seg17.CANOPY
open_dashboard = _seg17.open_dashboard
open_tab = _seg17.open_tab
SETPROPS = _f039.SETPROPS  # the same fiber walk F-039 and the 09-08 test used; one idiom, not three

METRICS_STORE = "metrics-panel-metrics-store"
TOPO_STORE = "network-visualizer-topology-store"
INTERVAL = "fast-update-interval"
WRITER_OUTPUT = f"{METRICS_STORE}.data"
TICK_MS = 1000  # DashboardConstants.FAST_UPDATE_INTERVAL_MS, canopy_constants.py:370

# A response "landed" if the store's length changed to a POSITIVE value within this
# many seconds of the response arriving. 2.0 s is two fast-lane ticks -- generous
# against the 1.827 s median round trip, so a late apply is still counted as landed.
LAND_WINDOW_S = 2.0

CASCOR = os.environ.get("JUNIPER_E2E_CASCOR_URL", "http://127.0.0.1:8202")
OUT = os.environ.get("F035_UNOPPOSED_RESULTS", "/tmp/juniper-e2e/f035_unopposed.json")


# ---------------------------------------------------------------------------
# In-page observer: one length read per Redux notify, appended only on change.
# ---------------------------------------------------------------------------
_JS_INSTALL = """
(specs) => {
  if (window.__f035obs) return {ok: false, why: 'already installed'};
  // specs: [{id, prop, mode}] -- mode 'len' records a list's length, 'value' the
  // raw scalar (used for fast-update-interval.n_intervals, the eviction clock).
  const read = (spec) => {
    const s = (window.store && window.store.getState) ? window.store.getState() : null;
    if (!s || !s.layout) return null;
    try {
      const strs = (s.paths && s.paths.strs) ? s.paths.strs : null;
      if (strs && strs[spec.id]) {
        let node = s.layout;
        for (const key of strs[spec.id]) { if (node == null) break; node = node[key]; }
        if (node && node.props && (spec.prop in node.props)) {
          const v = node.props[spec.prop];
          if (spec.mode === 'value') return (v === undefined) ? null : v;
          if (Array.isArray(v)) return v.length;
          if (v === null || v === undefined) return -1;   // explicit null value
          return -2;                                       // a non-list value
        }
      }
    } catch (e) { return -3; }                             // read threw
    return null;                                           // id not in paths.strs
  };
  const obs = {t0: Date.now(), samples: [], last: {}, notifies: 0, heartbeats: 0};
  const tick = (reason) => {
    for (const spec of specs) {
      const key = spec.id + '.' + spec.prop;
      const L = read(spec);
      const prev = (obs.last[key] === undefined) ? null : obs.last[key];
      if (prev !== L) {
        obs.samples.push({t: Date.now() - obs.t0, id: spec.id, prop: spec.prop,
                          len: L, prev: prev, reason: reason});
        obs.last[key] = L;
      }
    }
  };
  tick('install');
  obs.unsub = window.store.subscribe(() => { obs.notifies++; tick('notify'); });
  obs.hb = setInterval(() => { obs.heartbeats++; tick('heartbeat'); }, 1000);
  window.__f035obs = obs;
  return {ok: true, specs: specs, initial: obs.last};
}
"""

_JS_HARVEST = """
() => {
  const o = window.__f035obs;
  if (!o) return null;
  return {samples: o.samples, notifies: o.notifies, heartbeats: o.heartbeats,
          last: o.last, dur_ms: Date.now() - o.t0};
}
"""

_JS_ACTIVE_TAB = """
() => {
  const t = document.querySelector('[role=tab].active');
  return t ? t.textContent.trim() : null;
}
"""


def _health(base: str) -> dict:
    """``/v1/health`` off a leg -- the commit it SERVES, never a checkout."""
    try:
        with urllib.request.urlopen(f"{base}/v1/health", timeout=5) as r:  # noqa: S310
            payload = json.loads(r.read().decode("utf-8"))
        return {
            "ok": True,
            "url": base,
            "version": payload.get("version"),
            "git_sha": payload.get("git_sha"),
            "build_date": payload.get("build_date"),
        }
    except Exception as exc:  # noqa: BLE001 - reported, never raised from a probe
        return {"ok": False, "url": base, "why": f"{type(exc).__name__}: {exc}"[:160]}


def _classify(invocations: list, trace: list) -> None:
    """Annotate each invocation with ``opposed`` and ``landed``, in place.

    opposed -- another invocation of the SAME callback started while this one was in
    flight. That is dash-renderer's retirement precondition, read off request start
    times so it holds whether or not either response carried a value. Opposition is
    computed WITHIN a writer: ``getUniqueIdentifier`` hashes one callback's own
    inputs/outputs/state, so the co-owning WS-append callback is a different identity
    and cannot supersede the poll.

    landed  -- the store's length moved to a POSITIVE value within LAND_WINDOW_S of
    this response arriving.
    """
    fills = [s for s in trace if s["id"] == METRICS_STORE and isinstance(s["len"], int) and s["len"] > 0]
    ticks = [s["t"] for s in trace if s["id"] == INTERVAL and s["prop"] == "n_intervals"]
    by_writer: dict = {}
    for iv in invocations:
        if iv.get("t_start") is not None:
            by_writer.setdefault(iv.get("writer"), []).append(iv["t_start"])
    for iv in invocations:
        ts, te = iv.get("t_start"), iv.get("t_end")
        if ts is None or te is None:
            iv["opposed"] = None
            iv["tick_crossed"] = None
            iv["landed"] = None
            continue
        # HTTP boundary -- kept for continuity with the 09-05 latency probe, and
        # NOT the one the verdict uses. See the module docstring.
        iv["opposed"] = any(ts < s < te for s in by_writer.get(iv.get("writer"), []))
        # The boundary the renderer actually uses: did a tick create a `requested`
        # entry while this call was in flight (and therefore in `watched`)?
        crossing = [t for t in ticks if ts < t < te]
        iv["tick_crossed"] = bool(crossing) if ticks else None
        iv["ticks_inside"] = len(crossing)
        match = [f for f in fills if te <= f["t"] <= te + LAND_WINDOW_S]
        iv["landed"] = bool(match)
        iv["landed_at"] = round(match[0]["t"], 3) if match else None


def main() -> int:
    ap = argparse.ArgumentParser(description="F-035: does an unopposed response land?")
    ap.add_argument("--window", type=float, default=90.0, help="observation seconds")
    ap.add_argument("--tab", default="Candidate Metrics", help="tab to drive")
    ap.add_argument("--control-settle", type=float, default=25.0, help="seconds to watch after disabling the tick")
    ap.add_argument("--no-control", action="store_true", help="skip the positive control")
    ap.add_argument("--metrics-period", type=int, default=None,
                    help="setProps the FIXED leg's metrics-store-interval period (ms) before the window, "
                         "to test whether the post-fix poll cadence is period-bound or overhead-bound")
    ap.add_argument("--early-observer", action="store_true",
                    help="install the observer BEFORE opening the tab, so the store's first fill is "
                         "timestamped. On a FIXED leg the store fills during page load, so an observer "
                         "installed after the tab settle reads it already full and records no transition.")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {
        "probe": Path(__file__).name,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "canopy": CANOPY,
        "tick_ms": TICK_MS,
        "land_window_s": LAND_WINDOW_S,
        "window_s": args.window,
        "tab_requested": args.tab,
        "serving": {"canopy": _health(CANOPY), "cascor": _health(CASCOR)},
        "invocations": [],
        "console": [],
    }
    log(f"canopy  serving: {res['serving']['canopy']}")
    log(f"cascor  serving: {res['serving']['cascor']}")

    invocations: list = []
    pending: dict = {}
    console: list = []
    t0 = time.time()

    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            def _install():
                return page.evaluate(
                    _JS_INSTALL,
                    [
                        {"id": METRICS_STORE, "prop": "data", "mode": "len"},
                        {"id": TOPO_STORE, "prop": "data", "mode": "len"},
                        # the eviction clock: every increment creates a `requested` entry
                        {"id": INTERVAL, "prop": "n_intervals", "mode": "value"},
                    ],
                )

            early = None
            if args.early_observer:
                early = _install()
                res["observer_install"] = early
                res["observer_install_at"] = round(time.time() - t0, 3)
                log(f"observer (EARLY, pre-tab): {early} at t={res['observer_install_at']:.2f}s")

            open_tab(page, args.tab)
            page.wait_for_timeout(4000)
            res["tab_active"] = page.evaluate(_JS_ACTIVE_TAB)
            log(f"active tab: {res['tab_active']!r} (requested {args.tab!r})")

            install = early or page.evaluate(
                _JS_INSTALL,
                [
                    {"id": METRICS_STORE, "prop": "data", "mode": "len"},
                    {"id": TOPO_STORE, "prop": "data", "mode": "len"},
                    # the eviction clock: every increment creates a `requested` entry
                    {"id": INTERVAL, "prop": "n_intervals", "mode": "value"},
                ],
            )
            if early is None:
                # The observer's own clock starts at install, which is ~10-20 s after
                # the Python clock (navigation + tab + settle). Record the offset NOW:
                # without it every `landed` classification compares two different time
                # origins. (In --early-observer mode this was already recorded, and
                # re-recording it here would overwrite the true origin with a later one.)
                t_install = time.time() - t0
                res["observer_install"] = install
                res["observer_install_at"] = round(t_install, 3)
                log(f"observer: {install} (installed at t={t_install:.3f}s)")
            if not install or not install.get("ok"):
                res["verdict"] = "CONTROL-FAILED"
                res["verdict_why"] = f"observer refused to install: {install}"
                Path(OUT).parent.mkdir(parents=True, exist_ok=True)
                Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
                return 2

            def on_console(msg):
                console.append({"t": round(time.time() - t0, 3), "type": msg.type, "text": msg.text[:400]})

            def on_request(req):
                if "_dash-update-component" not in req.url:
                    return
                try:
                    body = req.post_data or ""
                except Exception:  # noqa: BLE001
                    return
                try:
                    out = (json.loads(body) or {}).get("output")
                except ValueError:
                    return
                # The poll writer's output is exactly ``<store>.data``. The WS-append
                # co-Overtoad declares ``allow_duplicate``, which Dash suffixes -- so an
                # exact match selects the poll writer and records the other separately.
                if not isinstance(out, str) or not out.startswith(METRICS_STORE):
                    return
                pending[req] = (time.time(), out)

            def on_response(resp):
                rec = pending.pop(resp.request, None)
                if rec is None:
                    return
                t_start, out = rec
                t_end = time.time()
                rows, kind = None, "unknown"
                try:
                    payload = json.loads(resp.text())
                except Exception:  # noqa: BLE001
                    payload = None
                if isinstance(payload, dict):
                    rmap = payload.get("response")
                    if isinstance(rmap, dict) and METRICS_STORE in rmap:
                        val = (rmap.get(METRICS_STORE) or {}).get("data")
                        if isinstance(val, list):
                            rows, kind = len(val), "write"
                        else:
                            kind = "non-list"
                    else:
                        kind = "no_update"
                invocations.append(
                    {
                        "t_start": round(t_start - t0, 3),
                        "t_end": round(t_end - t0, 3),
                        "duration_s": round(t_end - t_start, 3),
                        "status": resp.status,
                        "kind": kind,
                        "rows": rows,
                        "output": out,
                        "writer": "poll" if out == WRITER_OUTPUT else "ws-append",
                    }
                )

            page.on("console", on_console)
            page.on("request", on_request)
            page.on("response", on_response)

            if args.metrics_period is not None:
                sp = page.evaluate(SETPROPS, {"id": "metrics-store-interval",
                                              "payload": {"interval": args.metrics_period}})
                res["metrics_period_setprops"] = {"ms": args.metrics_period, "result": sp}
                log(f"metrics-store-interval period -> {args.metrics_period}ms: {sp}")

            log(f"observing {args.window:.0f} s ...")
            page.wait_for_timeout(int(args.window * 1000))

            res["control"] = {"ran": False}
            if not args.no_control:
                log("positive control: disabling fast-update-interval")
                sp = page.evaluate(SETPROPS, {"id": "fast-update-interval", "payload": {"disabled": True}})
                res["control"] = {"ran": True, "setprops": sp, "t_disabled": round(time.time() - t0, 3)}
                page.wait_for_timeout(int(args.control_settle * 1000))
                # leave the page as we found it, in case the leg is reused
                page.evaluate(SETPROPS, {"id": "fast-update-interval", "payload": {"disabled": False}})

            page.remove_listener("request", on_request)
            page.remove_listener("response", on_response)
            page.remove_listener("console", on_console)

            harvest = page.evaluate(_JS_HARVEST) or {}
            res["observer"] = {k: harvest.get(k) for k in ("notifies", "heartbeats", "last", "dur_ms")}
            res["trace"] = harvest.get("samples", [])
        finally:
            browser.close()

    # The observer's samples are milliseconds since ITS install; the invocations are
    # seconds since the Python t0. Shift the trace onto the Python timeline.
    obs_offset = res.get("observer_install_at", 0.0)
    trace = [{"t": round(s["t"] / 1000.0 + obs_offset, 3), "id": s["id"], "prop": s.get("prop"),
              "len": s["len"], "prev": s["prev"], "reason": s["reason"]} for s in res.get("trace", [])]
    res["trace"] = trace
    res["console"] = console
    res["invocations"] = invocations
    _classify(invocations, trace)

    # Scored on the POLL writer only -- the F-035 subject. The WS-append co-Overtoad is
    # counted in `kinds` and excluded here; it is a different callback identity.
    writes = [iv for iv in invocations if iv["kind"] == "write" and iv["writer"] == "poll"]
    pre_control = [iv for iv in writes if not res.get("control", {}).get("ran")
                   or iv["t_end"] < res["control"].get("t_disabled", 1e9)]
    unopposed = [iv for iv in pre_control if iv["opposed"] is False]
    opposed = [iv for iv in pre_control if iv["opposed"] is True]
    unopposed_failed = [iv for iv in unopposed if iv["landed"] is False]
    opposed_failed = [iv for iv in opposed if iv["landed"] is False]
    # the boundary the verdict uses
    tickfree = [iv for iv in pre_control if iv["tick_crossed"] is False]
    tickcross = [iv for iv in pre_control if iv["tick_crossed"] is True]
    tickfree_failed = [iv for iv in tickfree if iv["landed"] is False]
    tickcross_failed = [iv for iv in tickcross if iv["landed"] is False]
    have_ticks = any(iv["tick_crossed"] is not None for iv in pre_control)

    metrics_fills = [s for s in trace if s["id"] == METRICS_STORE and isinstance(s["len"], int) and s["len"] > 0]
    ctl = res.get("control", {})
    control_fill = None
    if ctl.get("ran"):
        t_dis = ctl.get("t_disabled", 0.0)
        control_fill = next((s for s in metrics_fills if s["t"] >= t_dis), None)
        ctl["fill"] = control_fill

    durs = [iv["duration_s"] for iv in pre_control]
    starts = [iv["t_start"] for iv in pre_control]
    gaps = [round(b - a, 3) for a, b in zip(sorted(starts), sorted(starts)[1:])]

    res["summary"] = {
        "invocations": len(invocations),
        "writes": len(writes),
        "writes_pre_control": len(pre_control),
        "rows_each": sorted({iv["rows"] for iv in writes if iv["rows"] is not None}),
        "kinds": {k: sum(1 for iv in invocations if iv["kind"] == k)
                  for k in sorted({iv["kind"] for iv in invocations})},
        "http_opposed": len(opposed),
        "http_unopposed": len(unopposed),
        "http_unopposed_failed_to_land": len(unopposed_failed),
        "http_opposed_failed_to_land": len(opposed_failed),
        "tick_crossed": len(tickcross),
        "tick_free": len(tickfree),
        "tick_free_failed_to_land": len(tickfree_failed),
        "tick_crossed_failed_to_land": len(tickcross_failed),
        "ticks_observed": sum(1 for s in trace if s["id"] == INTERVAL),
        "durations_under_tick": sum(1 for iv in pre_control if iv["duration_s"] < TICK_MS / 1000.0),
        "landed_any": sum(1 for iv in pre_control if iv["landed"]),
        "duration_s": {"n": len(durs), "min": min(durs) if durs else None,
                       "median": round(statistics.median(durs), 3) if durs else None,
                       "max": max(durs) if durs else None},
        "request_gap_s": {"n": len(gaps), "min": min(gaps) if gaps else None,
                          "median": round(statistics.median(gaps), 3) if gaps else None,
                          "max": max(gaps) if gaps else None},
        "metrics_store_fills": len(metrics_fills),
        "console_errors": sum(1 for c in console if c["type"] == "error"),
        "callback_failed_msgs": sum(1 for c in console if "did not respond" in c["text"] or "Callback failed" in c["text"]),
    }

    # --- verdict, by the rule fixed in this module's docstring -----------------
    if ctl.get("ran") and not control_fill:
        verdict = "CONTROL-FAILED"
        why = ("disabling the tick did not fill the store, so the observer could not have "
               "seen a fill that occurred; every zero above is uninterpretable")
    elif not pre_control:
        verdict = "NO-WRITES"
        why = "no store-writing invocation was observed; the instrument's own control failed"
    elif not unopposed_failed and not opposed_failed:
        verdict = "ALL-LANDED"
        why = "every response landed; the defect did not reproduce in this window"
    elif not have_ticks:
        verdict = "NO-TICK-TRACE"
        why = "the tick counter was not observable, so the eviction boundary cannot be applied"
    elif not tickfree:
        verdict = "NO-TICK-FREE"
        why = (f"a tick fell inside all {len(pre_control)} in-flight windows -- consistent with "
               f"eviction, and predicted by a median {res['summary']['duration_s']['median']}s "
               f"round trip against a {TICK_MS}ms tick, but not discriminating on its own")
    elif tickfree_failed:
        verdict = "SUPERSESSION-INSUFFICIENT"
        why = (f"{len(tickfree_failed)} of {len(tickfree)} TICK-FREE responses did not land; "
               "no `requested` entry could have evicted them, so supersession does not account "
               "for the outcome")
    else:
        verdict = "SUPERSESSION-CONSISTENT"
        why = (f"all {len(tickfree)} tick-free responses landed and {len(tickcross_failed)} of "
               f"{len(tickcross)} tick-crossed ones did not; the outcome tracks eviction")
    res["verdict"] = verdict
    res["verdict_why"] = why

    # H2 scored on its own axis, never folded into the verdict.
    failed_msgs = [c for c in console if "did not respond" in c["text"] or "Callback failed" in c["text"]]
    correlated = 0
    for iv in unopposed_failed + opposed_failed:
        if any(abs(c["t"] - iv["t_end"]) <= 3.0 for c in failed_msgs):
            correlated += 1
    res["h2_failed_response"] = {
        "console_failed_msgs": len(failed_msgs),
        "non_landing_responses": len(unopposed_failed) + len(opposed_failed),
        "correlated_within_3s": correlated,
        "messages": failed_msgs[:20],
    }

    s = res["summary"]
    log("")
    log(f"  serving canopy   : {res['serving']['canopy'].get('git_sha')} v{res['serving']['canopy'].get('version')}")
    log(f"  active tab       : {res.get('tab_active')!r}")
    log(f"  invocations      : {s['invocations']} ({s['kinds']})")
    log(f"  writes           : {s['writes']} rows={s['rows_each']}")
    log(f"  duration_s       : {s['duration_s']}")
    log(f"  request gap_s    : {s['request_gap_s']}")
    log(f"  ticks observed   : {s['ticks_observed']}  (durations under one tick: {s['durations_under_tick']}/{len(pre_control)})")
    log(f"  TICK boundary    : crossed {s['tick_crossed']} / free {s['tick_free']}")
    log(f"  FAILED TO LAND   : tick-free {s['tick_free_failed_to_land']}/{s['tick_free']}  "
        f"tick-crossed {s['tick_crossed_failed_to_land']}/{s['tick_crossed']}")
    log(f"  (HTTP boundary, superseded: unopposed {s['http_unopposed_failed_to_land']}/{s['http_unopposed']})")
    log(f"  store fills      : {s['metrics_store_fills']}  observer notifies={res['observer'].get('notifies')} "
        f"heartbeats={res['observer'].get('heartbeats')}")
    log(f"  control fill     : {control_fill}")
    log(f"  H2 console       : {res['h2_failed_response']['console_failed_msgs']} failed-response msgs, "
        f"{correlated} correlated with a non-landing response")
    log(f"  VERDICT          : {verdict} -- {why}")

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
