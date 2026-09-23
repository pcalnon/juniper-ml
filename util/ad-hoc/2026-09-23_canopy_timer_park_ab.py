#!/usr/bin/env python
"""Would parking canopy's two "cheap cut" timers change anything? An in-page A/B, before any code change.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 7 still-owed item 3
         ("cheap cuts to the dispatch rate ... Re-profile idle against the 0.1% baseline");
         util/ad-hoc/2026-09-23_canopy_interval_census.py (the static census that named the two)

THE CANDIDATES (static census of the built app, ``…_interval_census_c0530279.json``):
  * ``metrics-panel-update-interval``: 1 Hz, NO consumer in the built app;
  * ``replay-player-panel-weight-drain``: 2 Hz, one clientside consumer that returns ``no_update`` unless a
    replay session is streaming weights (CAN-015g), and on no tab gate.
Together 3.0 of the page's 6.6 nominal steady-state ticks/s. A tick is a ``setProps`` on the layout -- a
Redux update that re-runs the page's selectors -- and a consumed tick adds a callback lifecycle's worth.

THE QUESTION is whether that is worth a PR: does removing them move the page's saturation?
So nothing is changed in canopy. The timers are PARKED in the page, ``setProps({disabled: true})``;
nothing else writes ``disabled`` on either (neither is in ``_GATED_POLL_INTERVALS``), so the park is sticky.
Windows alternate, each ``--window`` seconds, one variable per B window:

    A0  D  A1  W  A2  DW  A3        (A = baseline, both running; D = dead timer parked;
                                     W = weight-drain parked; DW = both parked)

Each B window is compared with the MEAN of its two neighbouring A windows (drift control).

MEASURED PER WINDOW:
  * store updates/s: a ``store.subscribe`` counter (one notification per base dispatch);
  * main-thread idle %: a CDP sampling profile (1 ms), ``(idle)`` self time over total;
  * page-side response latency L: ``window.fetch`` is wrapped by an init script, and L is from the call to
    the moment the body's ``.json()`` resolves in the page -- the Phase 7 definition (request to page-side
    body parse), which includes main-thread queueing and excludes nothing;
  * the parked timers' ``n_intervals`` at each window's edges, so a park that did not take is visible.

VERDICT RULE, per B window -- FIXED BEFORE THE FIRST RUN:
  WORTH-IT    L p50 down >= 10% against its A-mean, OR idle up >= 2.0 points.
  NEGLIGIBLE  L p50 moved < 5% either way AND idle moved < 1.0 point.
  MIXED       anything else.
  VOID        a parked timer's n_intervals advanced during its B window, or an unparked one did not advance
              during an A window (the park did not take, or the page stopped ticking).

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (:8055 serving canopy#670 head c0530279, idle, Training Metrics,
GPU, one browser, 30 s windows):
  * store updates/s falls in D, W and DW, most in DW and more in W than in D (a consumed tick costs a
    lifecycle; an unconsumed one costs one update).
  * D: NEGLIGIBLE.  W: MIXED or WORTH-IT.  DW: WORTH-IT.
If DW is NEGLIGIBLE, the two cuts are hygiene, not a latency fix, and the ledger says so.

RUN LOG.
  run 1 (``…_timer_park_ab_8055_run1.json``, forward order, settle 25 s, host load 24-34):
    D MIXED (L +28.6%), W WORTH-IT (L -41.9%), DW WORTH-IT (L -31.7%).
    MISSED: "store updates/s falls". It ROSE in W (+9.3/s) and DW, because the page is saturated: freed
    main-thread time goes to applying responses sooner (70 and 73 applied, against 57-60 in A windows).
    Idle % sat at 0.10-0.14% in every window and cannot separate anything at this load.
    CONFOUNDED: A0 was still settling (L p50 15.0 s, falling to 8.5 s by A3), so D is compared against a
    drifting baseline. Run 2 reverses the order (``--order reverse``) and settles 60 s.
  run 2 (``…_timer_park_ab_8055_run2.json``, ``--order reverse --settle 60``, host load 16-24):
    D NEGLIGIBLE (L -1.6%, updates/s -0.2), W WORTH-IT (L -32.3%), DW WORTH-IT (L -32.6%).
  SCORED AGAINST THE PREDICTIONS, both runs:
    * "updates/s falls in D, W and DW": WRONG for W and DW in both runs. It rose, +9.3 and +21.0 in W,
      for the throughput reason above. D was flat in run 2 (-0.2/s).
    * "D NEGLIGIBLE": held in run 2; run 1 was MIXED on the settling baseline.
    * "W MIXED or WORTH-IT": held, WORTH-IT in both runs (-41.9%, -32.3%).
    * "DW WORTH-IT": held in both runs (-31.7%, -32.6%).
  CONCLUSION: the weight drain is the cost. Parking it cuts the idle page's median response-delivery
  latency by about a third, in both orders. The dead timer alone is not measurable: removing it is
  hygiene, not a latency fix.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8055 JUNIPER_E2E_BROWSER_GPU=1 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_canopy_timer_park_ab.py \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_timer_park_ab_8055.json
"""

import argparse
import collections
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")

log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal
SETPROPS = _f039.SETPROPS

DEAD = "metrics-panel-update-interval"
DRAIN = "replay-player-panel-weight-drain"
SEQUENCE = [("A0", ()), ("D", (DEAD,)), ("A1", ()), ("W", (DRAIN,)), ("A2", ()), ("DW", (DEAD, DRAIN)), ("A3", ())]

FETCH_HOOK = """
(() => {
  if (window.__abFetch) return;
  window.__abFetch = [];
  const orig = window.fetch;
  window.fetch = function (input, init) {
    const url = (typeof input === 'string') ? input : (input && input.url) || '';
    const t0 = performance.now();
    const p = orig.apply(this, arguments);
    if (url.indexOf('_dash-update-component') < 0) return p;
    return p.then((res) => {
      const j = res.json.bind(res);
      res.json = function () {
        return j().then((body) => { window.__abFetch.push([t0, performance.now()]); return body; });
      };
      return res;
    });
  };
})();
"""

SUBSCRIBE = """() => {
  const st = window.store;
  if (!st || typeof st.subscribe !== 'function') return false;
  window.__abN = 0;
  st.subscribe(() => { window.__abN += 1; });
  return true;
}"""

N_INTERVALS = """(ids) => { const s = window.store.getState(); const out = {};
  for (const id of ids) { const path = s.paths && s.paths.strs ? s.paths.strs[id] : null; let node = s.layout;
    if (path) { for (const k of path) { if (node == null) break; node = node[k]; } }
    out[id] = node && node.props ? {n: node.props.n_intervals, disabled: node.props.disabled} : null; }
  return out; }"""


def _idle_pct(prof: dict) -> float:
    nodes = {n["id"]: n for n in prof["nodes"]}
    per = collections.Counter()
    for sid, dt in zip(prof.get("samples") or [], prof.get("timeDeltas") or []):
        per[sid] += max(0, dt)
    total = sum(per.values()) or 1
    idle = sum(us for nid, us in per.items() if nodes[nid]["callFrame"].get("functionName") == "(idle)")
    return round(100.0 * idle / total, 2)


def _pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    return round(xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))], 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tab", default="Training Metrics")
    ap.add_argument("--settle", type=float, default=25.0)
    ap.add_argument("--window", type=float, default=30.0)
    ap.add_argument("--order", choices=("forward", "reverse"), default="forward", help="reverse = A0 DW A1 W A2 D A3 (same rule, B windows in the opposite order)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sequence = SEQUENCE if args.order == "forward" else [SEQUENCE[0], SEQUENCE[5], SEQUENCE[2], SEQUENCE[3], SEQUENCE[4], SEQUENCE[1], SEQUENCE[6]]

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": serving_commit(), "tab": args.tab, "window_s": args.window, "order": args.order, "settle_s": args.settle, "windows": []}
    log(f"canopy {CANOPY} serving {json.dumps(res['serving'])}")
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            ensure_no_modal(page)
            page.evaluate(FETCH_HOOK)  # after load: dash-renderer calls window.fetch at call time
            open_tab(page, args.tab)
            page.wait_for_timeout(int(args.settle * 1000))
            if not page.evaluate(SUBSCRIBE):
                log("!! window.store not reachable")
                return 2
            cdp = ctx.new_cdp_session(page)
            cdp.send("Profiler.enable")
            cdp.send("Profiler.setSamplingInterval", {"interval": 1000})
            for label, parked in sequence:
                for tid in (DEAD, DRAIN):
                    page.evaluate(SETPROPS, {"id": tid, "payload": {"disabled": tid in parked}})
                page.wait_for_timeout(1500)  # let the park land before the window opens
                edge0 = page.evaluate(N_INTERVALS, [DEAD, DRAIN])
                n0 = page.evaluate("window.__abN")
                f0 = page.evaluate("window.__abFetch.length")
                t0 = time.time()
                cdp.send("Profiler.start")
                page.wait_for_timeout(int(args.window * 1000))
                prof = cdp.send("Profiler.stop")["profile"]
                dt = time.time() - t0
                n1 = page.evaluate("window.__abN")
                fetches = page.evaluate("(i) => window.__abFetch.slice(i)", f0)
                edge1 = page.evaluate(N_INTERVALS, [DEAD, DRAIN])
                lat = [b - a for a, b in fetches]
                w = {
                    "label": label,
                    "parked": list(parked),
                    "seconds": round(dt, 1),
                    "updates_per_s": round((n1 - n0) / dt, 2),
                    "idle_pct": _idle_pct(prof),
                    "responses": len(lat),
                    "L_p50_ms": _pct(lat, 0.5),
                    "L_p90_ms": _pct(lat, 0.9),
                    "edges": {"start": edge0, "end": edge1},
                }
                adv = {tid: (edge1[tid]["n"] - edge0[tid]["n"]) if (edge0.get(tid) and edge1.get(tid)) else None for tid in (DEAD, DRAIN)}
                w["ticks_in_window"] = adv
                w["void"] = any((tid in parked and (adv[tid] or 0) > 0) or (tid not in parked and not adv[tid]) for tid in (DEAD, DRAIN))
                res["windows"].append(w)
                log(f"  {label:3s} parked={list(parked)!s:58s} upd/s={w['updates_per_s']:7.2f} idle={w['idle_pct']:5.2f}% L50={w['L_p50_ms']} L90={w['L_p90_ms']} n={w['responses']} ticks={adv} void={w['void']}")
            for tid in (DEAD, DRAIN):
                page.evaluate(SETPROPS, {"id": tid, "payload": {"disabled": False}})
        finally:
            browser.close()

    ws = {w["label"]: w for w in res["windows"]}
    order = [w["label"] for w in res["windows"]]
    verdicts = {}
    for label in ("D", "W", "DW"):
        i = order.index(label)  # every B window sits between two A windows, in either order
        b, a0, a1 = ws[label], ws[order[i - 1]], ws[order[i + 1]]
        if b["void"] or a0["void"] or a1["void"]:
            verdicts[label] = {"verdict": "VOID"}
            continue
        a_l = statistics.mean([x for x in (a0["L_p50_ms"], a1["L_p50_ms"]) if x is not None])
        a_i = statistics.mean([a0["idle_pct"], a1["idle_pct"]])
        a_u = statistics.mean([a0["updates_per_s"], a1["updates_per_s"]])
        dl = (b["L_p50_ms"] - a_l) / a_l if (a_l and b["L_p50_ms"] is not None) else None
        di = b["idle_pct"] - a_i
        if (dl is not None and dl <= -0.10) or di >= 2.0:
            v = "WORTH-IT"
        elif (dl is not None and abs(dl) < 0.05) and abs(di) < 1.0:
            v = "NEGLIGIBLE"
        else:
            v = "MIXED"
        verdicts[label] = {"verdict": v, "L_p50_change_pct": None if dl is None else round(100 * dl, 1), "idle_change_pts": round(di, 2), "updates_per_s_change": round(b["updates_per_s"] - a_u, 2)}
    res["verdicts"] = verdicts
    log(f"=> verdicts: {json.dumps(verdicts)}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
