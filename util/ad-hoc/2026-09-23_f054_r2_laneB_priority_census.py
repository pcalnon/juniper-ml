#!/usr/bin/env python
"""Record the priority strings dash-renderer 4.2.0 actually assigns under the coordinator's load model.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py (its docstring: pollers "score '13'
         against the controls' '11'"); dash_renderer.dev.js:1592-1616 (getPriority)

Reading of getPriority (:1597-1602): each loop starts by FILTERING the callbacks to those already
touched, so the first pass drops the callback itself and the result is "0" for every request. If
that reading is right, arbitration among prioritized requests is not by chain depth at all.

Builds the coordinator's app (its build_app, imported -- nothing of it runs git at import) with K=13,
serves it through route interception with its 2.5 s latency, plays the replay, and records every
distinct priority string seen in callbacks.prioritized for 12 s, split by controls vs pollers.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_r2_laneB_priority_census.py --objects <canopy .git/objects>
"""

import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PROBE = """
() => {
  const st = window.__st;
  window.__prio = {ctl: new Set(), other: new Set(), samples: 0};
  st.subscribe(() => {
    const p = st.getState().callbacks.prioritized || [];
    for (const cb of p) {
      const o = String(cb.callback && cb.callback.output);
      (o.indexOf('metrics-panel-replay-state.data') >= 0 ? window.__prio.ctl : window.__prio.other).add(String(cb.priority));
    }
    if (p.length) window.__prio.samples++;
  });
  return true;
}
"""


async def main_async(a):
    from playwright.async_api import async_playwright

    lb = _load("laneb_cleanroom", "2026-09-23_f054_r2_laneB_cleanroom.py")
    coord = _load("coord_pdup", "2026-09-23_f054_pdup_cleanroom_v1_v2.py")
    js = lb.load_js(lb.gitobj.Store(a.objects), "85415f3c")
    app = coord.build_app(13, "v2", js)
    srv = coord.Server(app, 2.5)
    await lb.wait_browser_slot()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        try:
            page = await (await browser.new_context()).new_page()
            await page.route(coord.BASE + "/**", lambda route: asyncio.ensure_future(srv.handle(route)))
            await page.goto(coord.BASE + "/", wait_until="load", timeout=60000)
            await page.wait_for_function("() => { const e = document.getElementById('metrics-panel-replay-position'); return e && e.textContent.indexOf(' / ') > 0; }", timeout=60000)
            assert (await page.evaluate(coord.INSTRUMENT)).get("found")
            await page.evaluate(PROBE)
            await asyncio.sleep(4.0)
            await page.evaluate("() => document.getElementById('metrics-panel-replay-play').click()")
            await asyncio.sleep(12.0)
            res = await page.evaluate("() => ({ctl: Array.from(window.__prio.ctl), other: Array.from(window.__prio.other), samples: window.__prio.samples})")
        finally:
            await browser.close()
    print(json.dumps(res))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", required=True)
    asyncio.run(main_async(ap.parse_args()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
