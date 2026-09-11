#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-035 aftermath -- the store is FULL and the loss plot is still empty. Why?

With canopy#613 the shared metrics store fills (0 -> 66 rows at ~7 s after load, live,
with the fast lane still ticking). ``2026-09-04_f035_candidate_loss_redrive.py`` then
scores M-CANDIDATES-07 **FAIL** on a NEW branch of its own rule -- "store populated but
no candidate trace rendered" -- and the figure carries zero traces AND zero
annotations, so it is not even the ``create_empty_plot`` placeholder.

The old blocker is gone, so this is either a defect that the permanently-empty store
was MASKING, or an interaction with the fix. Two candidates, which need different
answers, so this probe separates them instead of assuming:

  D1  THE DATA. The client's copy of the store does not carry what the server serves
      -- e.g. the candidate-phase rows are absent from the 66 the client holds, or
      their shape does not match ``_candidate_series_from_history``'s reader. Test:
      dump the client's own entries, count candidate-phase ones, and run the real
      adapter over the real client value.
  D2  THE RENDER. The data is fine, and the consumer simply never re-rendered after
      the store filled. ``update_loss_plot`` is triggered by the store's ``data``;
      the store now changes exactly ONCE and then holds (identity suppression,
      F-CANOPY-038's guard). If that single render is lost or ran before the fill,
      the plot stays empty forever with no further trigger to rescue it. Test: force
      a SECOND store change and see whether the figure gains a trace.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN.

  DATA-DEFECT        the client's store carries no usable candidate-phase entry, so
                     the adapter is right to plot nothing. The defect is upstream of
                     the figure and D2 is not reached.
  RENDER-LOST        the client's store DOES yield a series, and the figure is empty
                     until a forced store change makes it render. The consumer's
                     single render was lost; the store filling once is not enough.
  RENDER-STILL-DEAD  the store yields a series, and the figure stays empty even after
                     a forced change. Neither candidate; the consumer is broken in a
                     third way.
  ALREADY-RENDERED   the figure already carries a candidate trace. M-CANDIDATES-07
                     passes and the redrive's FAIL was a timing artifact.

CORRECTION 2026-09-10, round-1 consensus validation -- THE STATED REASON FOR
``--no-force`` WAS FALSE, AND THE RESULT IT EXPLAINED AWAY STANDS UNEXPLAINED.

This module, the ledger's Phase 6 and the session handoff all claimed the forced arm
(``window_size: 40``) "drops the very rows the figure needs, because the candidate
entries sit EARLY in the history". Checked against the live fixture:

    candidate rows are at indices 53-64 of 66 -- LATE.
    a last-40 window keeps ALL TWELVE.

So the force did **not** remove the candidate data, and ``RENDER-STILL-DEAD`` is not
self-contamination. It is an unexplained observation, and the only one in the set where
forcing a store change failed to produce a render. Keep ``--no-force`` for rate
observations anyway -- a forced arm is still a different treatment and should not be
pooled with unforced ones -- but do not repeat the old rationale, and do not treat that
run as discounted.

(The artifact records ``store_after_force: {len: 40}`` and never its phase census, so
which 40 rows survived is unknowable from it. A re-run should record the census.)

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8053 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-10_f035_downstream_consumer_probe.py --no-force
"""

import importlib.util
import json
import os
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


_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")

log = _seg17.log
CANOPY = _seg17.CANOPY
open_dashboard = _seg17.open_dashboard
open_tab = _seg17.open_tab
_store = _seg17._store
fig_info = _seg17.settle_figure  # not used for scoring; see _traces
SETPROPS = _f039.SETPROPS

STORE = "metrics-panel-metrics-store"
MODE_STORE = "metrics-panel-display-mode-store"
LOSS_FIG = "candidate-metrics-panel-loss-plot"
OUT = os.environ.get("F035_DOWNSTREAM_RESULTS", "/tmp/juniper-e2e/f035_downstream.json")

_JS_FIG = """
(id) => {
  const el = document.getElementById(id);
  if (!el) return {present: false};
  const gd = el.querySelector('.js-plotly-plot') || el;
  const data = (gd && gd.data) ? gd.data : null;
  const layout = (gd && gd.layout) ? gd.layout : null;
  return {
    present: true,
    traces: data ? data.map(t => ({name: t.name || null, n: (t.x && t.x.length) || 0})) : null,
    annotations: (layout && layout.annotations) ? layout.annotations.map(a => a.text) : [],
  };
}
"""


def _traces(page):
    return page.evaluate(_JS_FIG, LOSS_FIG)


def _adapter(history):
    """The REAL ``_candidate_series_from_history``, run over the client's own value."""
    if not isinstance(history, list):
        return {}
    epochs, losses, phases = [], [], []
    for entry in history:
        if not isinstance(entry, dict):
            continue
        phase = str(entry.get("phase") or entry.get("cascade_phase") or "")
        if "candidate" not in phase.lower():
            continue
        nested = entry.get("metrics") if isinstance(entry.get("metrics"), dict) else {}
        loss = nested.get("loss")
        if loss is None:
            loss = entry.get("loss", entry.get("train_loss"))
        epoch = entry.get("epoch")
        if epoch is None or isinstance(loss, bool) or not isinstance(loss, (int, float)):
            continue
        epochs.append(epoch)
        losses.append(float(loss))
        phases.append(phase)
    return {"epochs": epochs, "losses": losses, "phases": phases} if epochs else {}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-force", action="store_true",
                    help="do not force a second store change; use this for any render-rate "
                         "observation, so the forced arm cannot perturb the rate. NOTE the "
                         "original rationale for this flag was WRONG -- see the module docstring.")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY,
           "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, [])
        try:
            # Census the consumer ON THE WIRE before anything else. "The figure is
            # empty" is satisfied by two mechanisms that need opposite fixes -- the
            # callback never RUNS, or it runs and its output is never APPLIED -- and
            # this arc has twice returned a confident verdict that could not tell them
            # apart. Every dash POST body names its output, so counting responses that
            # name the loss plot separates them directly.
            wire = {"loss_plot_responses": 0, "carried_figure": 0, "other_responses": 0, "samples": []}

            def on_response(resp):
                if "_dash-update-component" not in resp.url:
                    return
                try:
                    payload = json.loads(resp.text())
                except Exception:  # noqa: BLE001
                    return
                rmap = payload.get("response") if isinstance(payload, dict) else None
                if not isinstance(rmap, dict):
                    return
                if LOSS_FIG in rmap:
                    wire["loss_plot_responses"] += 1
                    fig = (rmap.get(LOSS_FIG) or {}).get("figure")
                    if fig is not None:
                        wire["carried_figure"] += 1
                        if len(wire["samples"]) < 3:
                            data = fig.get("data") if isinstance(fig, dict) else None
                            wire["samples"].append({
                                "n_traces": len(data) if isinstance(data, list) else None,
                                "trace_names": [t.get("name") for t in data][:5] if isinstance(data, list) else None,
                            })
                else:
                    wire["other_responses"] += 1

            page.on("response", on_response)
            res["wire"] = wire

            open_tab(page, "Candidate Metrics")
            page.wait_for_timeout(20000)  # let the store fill (measured ~7 s post-load)

            rd = _store(page, STORE) or {}
            val = rd.get("value")
            res["store"] = {"ok": rd.get("ok"), "via": rd.get("via"),
                            "len": len(val) if isinstance(val, list) else None}
            log(f"  store: {res['store']}")

            phases = {}
            samples = []
            if isinstance(val, list):
                for e in val:
                    if isinstance(e, dict):
                        p = str(e.get("phase") or e.get("cascade_phase") or "<none>")
                        phases[p] = phases.get(p, 0) + 1
                samples = [e for e in val if isinstance(e, dict)][:2]
                cand = [e for e in val if isinstance(e, dict) and "candidate" in str(e.get("phase") or e.get("cascade_phase") or "").lower()]
                samples += cand[:2]
            res["client_phase_census"] = phases
            res["client_samples"] = samples
            log(f"  client phase census: {phases}")

            series = _adapter(val)
            res["adapter_series_len"] = len(series.get("epochs", [])) if series else 0
            log(f"  adapter over the CLIENT value -> {res['adapter_series_len']} points")

            before = _traces(page)
            res["figure_before"] = before
            log(f"  figure BEFORE: {before}")

            if before.get("traces"):
                populated = [t for t in before["traces"] if (t.get("n") or 0) > 0]
                if populated:
                    res["verdict"] = "ALREADY-RENDERED"
                    res["verdict_why"] = f"the figure already carries {populated}"
                    _write(res)
                    return 0

            if not series:
                res["verdict"] = "DATA-DEFECT"
                res["verdict_why"] = (
                    f"the client's store holds {res['store']['len']} entries with phase census "
                    f"{phases} and the real adapter derives NO candidate series from it, so the "
                    "figure is right to plot nothing; the defect is upstream of the figure")
                _write(res)
                return 0

            if args.no_force:
                res["verdict"] = "NOT-RENDERED-NO-FORCE"
                res["verdict_why"] = (
                    f"the client's store yields a {res['adapter_series_len']}-point candidate series and "
                    "the figure is empty; --no-force means the second-chance arm was deliberately not run")
                _write(res)
                return 0

            # D2: force a SECOND store change and see whether the consumer renders.
            log("  forcing a second store change via the display-mode store ...")
            sp = page.evaluate(SETPROPS, {"id": MODE_STORE, "payload": {"data": {"mode": "window", "window_size": 40}}})
            res["forced_change"] = {"setprops": sp}
            page.wait_for_timeout(25000)
            rd2 = _store(page, STORE) or {}
            v2 = rd2.get("value")
            res["store_after_force"] = {"ok": rd2.get("ok"), "len": len(v2) if isinstance(v2, list) else None}
            after = _traces(page)
            res["figure_after"] = after
            log(f"  store AFTER force: {res['store_after_force']}")
            log(f"  figure AFTER: {after}")
            log(f"  WIRE: loss-plot responses={wire['loss_plot_responses']} "
                f"carrying a figure={wire['carried_figure']} samples={wire['samples']}")

            pop_after = [t for t in (after.get("traces") or []) if (t.get("n") or 0) > 0]
            if pop_after:
                res["verdict"] = "RENDER-LOST"
                res["verdict_why"] = (
                    f"the client's store yields a {res['adapter_series_len']}-point candidate series and the "
                    f"figure was EMPTY until a forced store change, after which it rendered {pop_after}. The "
                    "consumer's single render after the fill did not survive; one fill is not enough while "
                    "identity suppression stops any further trigger.")
            else:
                res["verdict"] = "RENDER-STILL-DEAD"
                res["verdict_why"] = (
                    f"the client's store yields a {res['adapter_series_len']}-point candidate series and the "
                    "figure stayed empty even after a forced store change; the consumer is broken in a way "
                    "neither candidate covers")
        finally:
            browser.close()

    _write(res)
    return 0


def _write(res):
    log(f"  VERDICT: {res.get('verdict')} -- {res.get('verdict_why')}")
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
