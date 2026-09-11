#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""F-CANOPY-052 — is it F-CANOPY-035's mechanism recurring on the CONSUMER?

THE HYPOTHESIS, arrived at by round-2 (Lane B) review rather than by this arc's own
instruments, and verified at source before this probe was written:

  * ``update_loss_plot`` takes ``candidate-metrics-panel-training-state-store.data`` as
    an Input (candidate_metrics_panel.py:342).
  * ``fetch_training_state`` writes that store off ``candidate-metrics-panel-update-interval``
    -- period **1000 ms** (:93, :223-224) -- and returns ``self._fetch_training_state()``
    UNCONDITIONALLY on both branches (:259-268) while the candidates tab is active.
  * ``/api/state`` carries a per-call ``timestamp``, so the written value is genuinely
    DIFFERENT every tick (verified live: two consecutive GETs differ only in
    ``timestamp``).

So ``update_loss_plot`` is re-``requested`` about once a second under ONE
``getUniqueIdentifier`` -- and dash_renderer.dev.js:3027 evicts the in-flight entry
from ``watched`` while :2698 discards its response. That is F-CANOPY-035's mechanism
exactly, on the callback one step downstream of the store F-035 repaired.

It also explains the signature this arc recorded and could not place: the
``dcc.Graph`` at candidate_metrics_panel.py:189-193 is declared with **no ``figure=``
prop**, so "zero traces AND zero annotations" is reachable ONLY as the mount default --
neither of ``update_loss_plot``'s two return paths can produce it (both return a
figure; one carries a trace, the other a ``create_empty_plot`` annotation). The panel
is not rendering an empty figure. It is rendering nothing, ever.

WHAT THIS PROBE DOES. One runtime intervention, no product change: disable
``candidate-metrics-panel-update-interval`` via ``setProps`` immediately after the tab
opens, BEFORE the metrics store fills. That removes the 1 Hz re-request while leaving
everything else -- the fast lane, the metrics poll, the fill itself -- untouched.

  control    (default)            the tick runs. Prediction: renders sometimes (2 of 6
                                  in the runs to date).
  treatment  --disable-panel-tick the tick is stopped. Prediction: renders EVERY time.

This is the unconfounded A/B the sweep was not: one variable, and it is the variable
the hypothesis names. It is also a dry run of the fix -- demoting that Input to State
is the F-CANOPY-039 precedent, which took the topology rebuild 0/11 -> 11/11.

VERDICT RULE — FIXED BEFORE THE FIRST RUN.

  TRIGGER-EVICTION-CONFIRMED  every treatment run rendered AND at least one control run
                              did not. The consumer's own 1 Hz re-trigger is what stops
                              it; F-052 is F-035's mechanism and the fix is the trigger.
  NOT-THE-TRIGGER             at least one treatment run failed to render. Stopping the
                              re-trigger is not sufficient; the hypothesis is wrong or
                              incomplete.
  CONTROL-DID-NOT-REPRODUCE   every control run rendered too. The defect did not appear
                              in this session; no comparison is possible.
  SETPROPS-FAILED             the interval could not be stopped (n_intervals kept
                              advancing). Says nothing.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8053 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-11_f052_trigger_eviction_test.py --runs 3
"""

import argparse
import importlib.util
import json
import os
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
_store = _seg17._store
SETPROPS = _f039.SETPROPS

STORE = "metrics-panel-metrics-store"
STATE_STORE = "candidate-metrics-panel-training-state-store"
PANEL_TICK = "candidate-metrics-panel-update-interval"
LOSS_FIG = "candidate-metrics-panel-loss-plot"
OUT = os.environ.get("F052_TRIGGER_RESULTS", "/tmp/juniper-e2e/f052_trigger_eviction.json")

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

_JS_PROP = """
(a) => { const [id, prop] = a;
  const st = window.store && window.store.getState ? window.store.getState() : null;
  if (!st || !st.layout) return null;
  const strs = st.paths && st.paths.strs ? st.paths.strs : null;
  if (!strs || !strs[id]) return null;
  let node = st.layout;
  for (const k of strs[id]) { if (node == null) break; node = node[k]; }
  return (node && node.props && prop in node.props) ? node.props[prop] : null;
}
"""


def _health(base: str) -> dict:
    try:
        with urllib.request.urlopen(f"{base}/v1/health", timeout=5) as r:  # noqa: S310
            p = json.loads(r.read().decode("utf-8"))
        return {"ok": True, "url": base, "version": p.get("version"), "git_sha": p.get("git_sha")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "url": base, "why": f"{type(exc).__name__}: {exc}"[:160]}


def _one(pw, disable_tick: bool, settle_s: float, serving: dict) -> dict:
    from playwright.sync_api import sync_playwright  # noqa: F401  (type only)

    rec = {"arm": "treatment" if disable_tick else "control", "serving": serving}
    wire = {"loss_plot_responses": 0, "carried_figure": 0, "other": 0}
    browser, ctx, page = open_dashboard(pw, [])
    try:
        def on_response(resp):
            if "_dash-update-component" not in resp.url:
                return
            try:
                payload = json.loads(resp.text())
            except Exception:  # noqa: BLE001
                wire["other"] += 1
                return
            rmap = payload.get("response") if isinstance(payload, dict) else None
            if not isinstance(rmap, dict):
                wire["other"] += 1
                return
            if LOSS_FIG in rmap:
                wire["loss_plot_responses"] += 1
                if (rmap.get(LOSS_FIG) or {}).get("figure") is not None:
                    wire["carried_figure"] += 1
            else:
                wire["other"] += 1

        page.on("response", on_response)
        open_tab(page, "Candidate Metrics")

        # Stop the consumer's own re-trigger BEFORE the metrics store fills (measured
        # at 7.3-11.9 s after observer install in the runs that timestamp it).
        if disable_tick:
            sp = page.evaluate(SETPROPS, {"id": PANEL_TICK, "payload": {"disabled": True}})
            rec["setprops"] = sp
            n0 = page.evaluate(_JS_PROP, [PANEL_TICK, "n_intervals"])
            rec["tick_n_at_disable"] = n0

        page.wait_for_timeout(int(settle_s * 1000))

        rec["tick_n_end"] = page.evaluate(_JS_PROP, [PANEL_TICK, "n_intervals"])
        rec["tick_disabled_end"] = page.evaluate(_JS_PROP, [PANEL_TICK, "disabled"])
        rd = _store(page, STORE) or {}
        val = rd.get("value")
        rec["store_len"] = len(val) if isinstance(val, list) else None
        rec["figure"] = page.evaluate(_JS_FIG, LOSS_FIG)
        rec["wire"] = dict(wire)
        traces = (rec["figure"] or {}).get("traces") or []
        rec["rendered"] = any((t.get("n") or 0) > 0 for t in traces)
    finally:
        browser.close()
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="F-052: is the consumer evicted by its own 1 Hz re-trigger?")
    ap.add_argument("--runs", type=int, default=3, help="runs PER ARM")
    ap.add_argument("--settle", type=float, default=30.0, help="seconds to wait before reading the figure")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    serving = _health(CANOPY)
    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": serving,
           "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "settle_s": args.settle, "runs_per_arm": args.runs, "observations": []}
    log(f"serving: {serving}")

    with sync_playwright() as pw:
        for i in range(args.runs):
            for disable in (False, True):
                rec = _one(pw, disable, args.settle, serving)
                rec["i"] = i
                res["observations"].append(rec)
                log(f"  [{rec['arm']:9s} {i + 1}/{args.runs}] rendered={rec['rendered']} "
                    f"store_len={rec['store_len']} tick_n={rec.get('tick_n_at_disable')}->{rec['tick_n_end']} "
                    f"disabled={rec['tick_disabled_end']} loss_resp={rec['wire']['loss_plot_responses']}")

    ctrl = [o for o in res["observations"] if o["arm"] == "control"]
    trt = [o for o in res["observations"] if o["arm"] == "treatment"]
    c_ok = sum(1 for o in ctrl if o["rendered"])
    t_ok = sum(1 for o in trt if o["rendered"])
    # Did the intervention actually stop the clock? n_intervals must not advance.
    stopped = all(o.get("tick_n_end") == o.get("tick_n_at_disable") for o in trt
                  if o.get("tick_n_at_disable") is not None)

    if not stopped:
        verdict = "SETPROPS-FAILED"
        why = "the panel interval kept advancing after disabled=true; the treatment was never applied"
    elif c_ok == len(ctrl):
        verdict = "CONTROL-DID-NOT-REPRODUCE"
        why = f"every control run rendered ({c_ok}/{len(ctrl)}); no comparison is possible"
    elif t_ok == len(trt):
        verdict = "TRIGGER-EVICTION-CONFIRMED"
        why = (f"treatment rendered {t_ok}/{len(trt)} with the consumer's 1 Hz re-trigger stopped, while "
               f"control rendered {c_ok}/{len(ctrl)} with it running. The consumer is evicted by its own "
               "re-request: F-CANOPY-052 is F-CANOPY-035's mechanism, and the fix is at the trigger.")
    else:
        verdict = "NOT-THE-TRIGGER"
        why = (f"treatment rendered only {t_ok}/{len(trt)}; stopping the re-trigger is not sufficient, so "
               "the hypothesis is wrong or incomplete")

    res["summary"] = {"control_rendered": f"{c_ok}/{len(ctrl)}", "treatment_rendered": f"{t_ok}/{len(trt)}",
                      "tick_actually_stopped": stopped}
    res["verdict"], res["verdict_why"] = verdict, why
    log("")
    log(f"  control  rendered: {c_ok}/{len(ctrl)}")
    log(f"  treatment rendered: {t_ok}/{len(trt)}   (tick stopped: {stopped})")
    log(f"  VERDICT: {verdict} -- {why}")
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
