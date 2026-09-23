#!/usr/bin/env python
"""Phase 7 still-owed item 4: does the top status bar ever APPLY a periodic response? One browser.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 7 item 4, "a candidate
         fourth writer of the F-053 class"; Phase 8)

THE SUSPECT. ``update_unified_status_bar`` (dashboard_manager.py) is a SERVER callback on the shared 1 Hz
``fast-update-interval``, with 11 Outputs and no ``running=`` guard. dash-renderer drops an in-flight
(``watched``) callback when a new request of the same callback enters ``requested`` (the requestedCallbacks
observer's ``wDuplicates`` step), and the late response is then discarded (executingCallbacks observer).
With the page's response-delivery latency at 5-15 s against a ~1 s tick, every in-flight status-bar
request should be evicted before its response is processed: F-CANOPY-053's class (E), eviction.

THE DISCRIMINATOR. The bar's ``latency-display.children`` is recomputed on every response (it prints the
server-side /api/status round trip), so at idle EVERY applied response changes the store, while an
evicted one changes nothing. Over ``--seconds`` after the settle, one browser, this records:
  * wire: requests sent for the callback whose outputs include ``status-indicator.style``, and responses
    delivered for them (playwright request / response events);
  * renderer: unique callback objects of that callback entering ``watched`` (in flight) and ``executed``
    (reached the apply stage), from a Redux subscription holding a WeakSet per queue;
  * store: every change of ``latency-display``, ``top-status-display`` and ``top-epoch-display``
    ``children``, stamped;
  * server truth at the end: GET ``/api/status`` on the leg, against the bar's status text.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN.
  NEVER-APPLIES      0 ``executed`` entries AND 0 ``latency-display`` changes, with >= 10 responses
                     delivered.
  RARELY-APPLIES     executed / delivered below 0.25.
  APPLIES            executed / delivered at or above 0.25.
  VOID               fewer than 10 responses delivered (the lane was not polling; nothing to judge).

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (idle trio, Training Metrics tab, GPU, 60 s after a 45 s settle):
  the parent build (:8055, 723ee812): NEVER-APPLIES or RARELY-APPLIES.
  the cuts build (:8056, 668380ec): the same. The cuts cut L by about a third, which still leaves it
  well above the 1 s tick.

RUN LOG (2026-09-23). Both predictions held: :8055 NEVER-APPLIES (36 requests, 36 responses, 38 watched,
0 executed) and :8056 NEVER-APPLIES (42 / 43 / 44 / 0). The bar showed its LAYOUT DEFAULTS throughout
("Stopped", "0", "") against a server at epoch 76 with 68 hidden units.

THE PERIOD ARM (``--period-ms``), added after those two runs to discriminate the mechanism on the same page.
After the baseline window, ``fast-update-interval``'s period is set in the page (``setProps``) and a second
window is recorded. The wire probe also stamps each request, so the bar's own delivery latency L is
measured in each window. If the responses are lost to EVICTION (a new request of the same callback
arriving before the previous response is processed), a period well above L must let them apply. If they
are lost for another reason, such as an error or a readiness hold, the period does not matter.
VERDICT RULE for the slowed window -- FIXED BEFORE ITS FIRST RUN:
  APPLIES            executed >= 2 AND latency-display changes >= 1.
  NEVER-APPLIES      executed == 0 AND latency-display changes == 0, with >= 3 responses delivered.
  VOID               anything else, or fewer than 3 responses delivered.
PREDICTION (:8055, baseline 60 s at 1000 ms, then 150 s at 20000 ms): baseline NEVER-APPLIES; slowed
window APPLIES, with the bar showing the server's epoch (76) by the end; baseline median L above 1 s,
slowed-window median L below 20 s.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8055 JUNIPER_E2E_BROWSER_GPU=1 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_status_bar_apply_census.py \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_status_bar_apply_census_8055.json
"""

import argparse
import importlib.util
import json
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


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")
SETPROPS = _f039.SETPROPS

log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal

MARK = "status-indicator.style"
WATCHED_IDS = ("latency-display", "top-status-display", "top-epoch-display")

INSTALL = """(cfg) => {
  const st = window.store;
  if (!st || typeof st.subscribe !== 'function') return {found: false};
  const mark = cfg.mark, ids = cfg.ids;
  const outOf = (c) => { const d = (c && c.callback) || {}; return String(d.output || ''); };
  const seenW = new WeakSet(), seenE = new WeakSet();
  const R = window.__sb = {watched: 0, executed: 0, changes: [], n: 0};
  const last = {};
  const at = (s, id) => { const path = s.paths && s.paths.strs ? s.paths.strs[id] : null; let node = s.layout;
    if (!path) return undefined; for (const k of path) { if (node == null) return undefined; node = node[k]; }
    return node && node.props ? node.props.children : undefined; };
  const sample = () => {
    const s = st.getState(); R.n += 1;
    const cb = s.callbacks || {};
    for (const c of (cb.watched || [])) { if (outOf(c).indexOf(mark) >= 0 && !seenW.has(c)) { seenW.add(c); R.watched += 1; } }
    for (const c of (cb.executed || [])) { if (outOf(c).indexOf(mark) >= 0 && !seenE.has(c)) { seenE.add(c); R.executed += 1; } }
    for (const id of ids) { const v = JSON.stringify(at(s, id)); if (last[id] !== v) { if (id in last) R.changes.push([Date.now(), id, v && v.slice(0, 120)]); last[id] = v; } }
  };
  sample();
  st.subscribe(sample);
  return {found: true, initial: Object.fromEntries(ids.map((id) => [id, last[id] && last[id].slice(0, 120)]))};
}"""


def _api_status(base: str) -> dict:
    try:
        with urllib.request.urlopen(f"{base}/api/status", timeout=5) as r:  # nosec B310 - loopback test leg
            p = json.loads(r.read().decode("utf-8"))
        return {k: p.get(k) for k in ("status", "is_running", "phase", "current_epoch", "hidden_units") if k in p}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:160]}


def _baseline_verdict(delivered: int, executed: int, lat_changes: int) -> str:
    if delivered < 10:
        return "VOID"
    if executed == 0 and lat_changes == 0:
        return "NEVER-APPLIES"
    return "RARELY-APPLIES" if executed / delivered < 0.25 else "APPLIES"


def _slowed_verdict(delivered: int, executed: int, lat_changes: int) -> str:
    if delivered < 3:
        return "VOID"
    if executed >= 2 and lat_changes >= 1:
        return "APPLIES"
    if executed == 0 and lat_changes == 0:
        return "NEVER-APPLIES"
    return "VOID"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tab", default="Training Metrics")
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--period-ms", type=int, default=None, help="after the baseline window, set fast-update-interval's period and record a second window")
    ap.add_argument("--period-seconds", type=float, default=150.0, help="length of the slowed window")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": serving_commit(), "tab": args.tab, "settle_s": args.settle, "seconds": args.seconds, "period_ms": args.period_ms}
    log(f"canopy {CANOPY} serving {json.dumps(res['serving'])}")
    wire = {"requests": 0, "responses": 0, "latency_s": []}
    sent = {}
    armed = {"on": False}

    def _is_bar(req) -> bool:
        return "_dash-update-component" in req.url and MARK in str((req.post_data_json or {}).get("output") or "")

    def on_request(req):
        if armed["on"] and _is_bar(req):
            wire["requests"] += 1
            sent[req] = time.time()

    def on_response(resp):
        if armed["on"] and _is_bar(resp.request):
            wire["responses"] += 1
            t = sent.pop(resp.request, None)
            if t is not None:
                wire["latency_s"].append(round(time.time() - t, 3))

    def window(page, seconds: float) -> dict:
        wire.update(requests=0, responses=0, latency_s=[])
        sent.clear()
        install = page.evaluate(INSTALL, {"mark": MARK, "ids": list(WATCHED_IDS)})
        if not install.get("found"):
            raise RuntimeError("window.store not reachable")
        armed["on"] = True
        t0 = time.time()
        page.wait_for_timeout(int(seconds * 1000))
        armed["on"] = False
        rec = page.evaluate("window.__sb")
        lat = sorted(wire["latency_s"])
        return {
            "install": install,
            "elapsed_s": round(time.time() - t0, 1),
            "wire": {"requests": wire["requests"], "responses": wire["responses"], "latency_s_median": lat[len(lat) // 2] if lat else None, "latency_s_min": lat[0] if lat else None, "latency_s_max": lat[-1] if lat else None, "latency_samples": len(lat)},
            "renderer": {"watched_entries": rec["watched"], "executed_entries": rec["executed"], "store_notifications": rec["n"]},
            "store_changes": rec["changes"],
            "latency_display_changes": sum(1 for c in rec["changes"] if c[1] == "latency-display"),
            "dom_bar": page.evaluate("() => Object.fromEntries(['top-status-display', 'top-epoch-display', 'latency-display'].map((id) => { const e = document.getElementById(id); return [id, e ? e.textContent : null]; }))"),
        }

    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, [])
        try:
            page.on("request", on_request)
            page.on("response", on_response)
            ensure_no_modal(page)
            open_tab(page, args.tab)
            page.wait_for_timeout(int(args.settle * 1000))
            try:
                res["baseline"] = window(page, args.seconds)
            except RuntimeError as e:
                log(f"!! {e}")
                return 2
            if args.period_ms:
                res["set_period"] = page.evaluate(SETPROPS, {"id": "fast-update-interval", "payload": {"interval": args.period_ms}})
                log(f"  fast-update-interval period -> {args.period_ms} ms: {json.dumps(res['set_period'])[:200]}")
                res["slowed"] = window(page, args.period_seconds)
        finally:
            browser.close()
    res["server_status"] = _api_status(CANOPY)
    b = res["baseline"]
    b["verdict"] = _baseline_verdict(b["wire"]["responses"], b["renderer"]["executed_entries"], b["latency_display_changes"])
    # the single-window keys the first two runs wrote, kept so their transcripts compare directly
    res.update(wire={k: b["wire"][k] for k in ("requests", "responses")}, renderer=b["renderer"], store_changes=b["store_changes"], latency_display_changes=b["latency_display_changes"], verdict=b["verdict"], install=b["install"])
    log(f"  initial bar: {json.dumps(b['install'].get('initial'))}")
    log(f"  BASELINE wire: {b['wire']}  renderer: {b['renderer']}  latency-display changes: {b['latency_display_changes']}  DOM: {b['dom_bar']}")
    log(f"=> BASELINE VERDICT: {b['verdict']}")
    if "slowed" in res:
        s = res["slowed"]
        s["verdict"] = _slowed_verdict(s["wire"]["responses"], s["renderer"]["executed_entries"], s["latency_display_changes"])
        log(f"  SLOWED ({args.period_ms} ms) wire: {s['wire']}  renderer: {s['renderer']}  latency-display changes: {s['latency_display_changes']}  DOM: {s['dom_bar']}")
        log(f"=> SLOWED VERDICT: {s['verdict']}")
    log(f"  server /api/status: {json.dumps(res['server_status'])}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
