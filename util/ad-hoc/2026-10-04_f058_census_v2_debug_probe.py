#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Debug: does the feed store ever change (APPLIED, independent of the shim), and what action types carry the feed?

Written when the first synthetic controls scored every request evicted. Three observables independent of the
shim's A/X classification decided it: no ``AddExecuted`` ever carried the feed, the store never held a non-null
value, and the wire showed every feed request answered HTTP 200. So the shim was right, and the synthetic app
was cascading from the gate's mount write; ``…_synth_check.py`` now holds that as its ``mount-cascade`` case and
starts the controls' gate after load.

Usage (canopy env): ``… <this file> [data|noupdate]`` against ``2026-10-04_f058_census_v2_synth_app.py`` on 9491.
"""

import importlib.util
import json
import os
import socket
import subprocess  # nosec B404
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_sibling(name: str):
    """Load this census's ``2026-10-04_f058_census_v2_<name>.py`` beside this file (a dated name cannot be imported)."""
    spec = importlib.util.spec_from_file_location(f"f058_census_v2_{name}", HERE / f"2026-10-04_f058_census_v2_{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


SHIM = _load_sibling("shim").SHIM
APP = HERE / "2026-10-04_f058_census_v2_synth_app.py"

PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
PORT = 9491
EXTRA = r"""
(() => {
  const D = window.__dbg = {types: {}, feedTypes: {}, storeVals: [], resp: 0};
  let st;
  const desc = Object.getOwnPropertyDescriptor(window, 'store');
  Object.defineProperty(window, 'store', {configurable: true, enumerable: true,
    get() { return desc.get(); },
    set(v) { desc.set(v); const o = v.dispatch; v.dispatch = function (a) {
        const walk = (x) => { if (!x || typeof x !== 'object') return; D.types[x.type] = (D.types[x.type] || 0) + 1;
          if (x.type === 'Callbacks.Aggregate' && Array.isArray(x.payload)) x.payload.forEach(walk);
          else if (Array.isArray(x.payload)) for (const cb of x.payload) { const out = String(((cb && cb.callback) || {}).output || ''); if (out === 'metrics-panel-metrics-store.data') D.feedTypes[x.type] = (D.feedTypes[x.type] || 0) + 1; } };
        walk(a); return o.apply(this, arguments); };
      v.subscribe(() => { const s = v.getState(); const p = s.paths && s.paths.strs ? s.paths.strs['metrics-panel-metrics-store'] : null; let n = s.layout; if (p) for (const k of p) { if (n == null) break; n = n[k]; }
        const val = n && n.props ? JSON.stringify(n.props.data) : null; if (D.storeVals[D.storeVals.length - 1] !== val) D.storeVals.push(val); });
    }});
})();
"""


def main():
    from playwright.sync_api import sync_playwright

    env = dict(os.environ, PORT=str(PORT), FEED_MODE=sys.argv[1] if len(sys.argv) > 1 else "data", LAT="3")
    for k in ("LD_LIBRARY_PATH", "LIBTORCH", "LIBTORCH_LIB"):
        env.pop(k, None)
    proc = subprocess.Popen([PY, str(APP)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603
    statuses = []
    try:
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", PORT)) == 0:
                    break
            time.sleep(0.2)
        with sync_playwright() as pw:
            b = pw.chromium.launch(headless=True)
            ctx = b.new_context()
            ctx.add_init_script(script=SHIM)
            ctx.add_init_script(script=EXTRA)
            page = ctx.new_page()

            def on_resp(r):
                if "_dash-update-component" in r.url:
                    try:
                        body = r.request.post_data_json or {}
                    except Exception:
                        body = {}
                    if str(body.get("output") or "") == "metrics-panel-metrics-store.data":
                        statuses.append(r.status)

            page.on("response", on_resp)
            page.goto(f"http://127.0.0.1:{PORT}/")
            page.wait_for_timeout(30000)
            d = page.evaluate("() => window.__dbg")
            r = page.evaluate("() => window.__f058v2")
            b.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    print(json.dumps({"wire": {str(s): statuses.count(s) for s in set(statuses)}, "feedTypes": d["feedTypes"], "storeVals_n": len(d["storeVals"]), "storeVals_tail": d["storeVals"][-3:], "req_head": r["req"][:12], "lane_head": r["lane"][:10]}, indent=1))


if __name__ == "__main__":
    main()
