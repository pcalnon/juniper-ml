# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 1, Lane B1: the driver for F-CANOPY-058's second-Input trigger.
# Source: session ddf7847c's tmpfs scratchpad, f058repro.6JTgea/drive.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Drive app.py in headless Chromium and count applies vs requests (Lane B1 scratch).

Prediction fixed before the first run:
  control window (no trigger): applies ~= window / (R + 1) and every request applies;
  after one mid-request change of the 'mode' Store: if the second-Input trigger starts
  F-CANOPY-058's cascade, applies drop to ~0 while requests continue at >= 1 per R+1 s.
"""
import json
import sys
import time

from playwright.sync_api import sync_playwright

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9471
CONTROL_S = float(sys.argv[2]) if len(sys.argv) > 2 else 30
AFTER_S = float(sys.argv[3]) if len(sys.argv) > 3 else 90

OBS = """
() => {
  window.__applies = [];
  const el = document.getElementById('out');
  new MutationObserver(() => window.__applies.push([performance.now(), el.textContent])).observe(el, {childList: true, characterData: true, subtree: true});
  window.__reqs = [];
  return true;
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    reqs, resps = [], []
    t_start = time.time()

    def on_req(r):
        if "_dash-update-component" in r.url and "out.children" in (r.post_data or ""):
            reqs.append(time.time() - t_start)

    def on_resp(r):
        if "_dash-update-component" in r.url and "out.children" in (r.request.post_data or ""):
            resps.append(time.time() - t_start)

    pg.on("request", on_req)
    pg.on("response", on_resp)
    pg.goto(f"http://127.0.0.1:{PORT}/")
    pg.wait_for_selector("#out")
    pg.evaluate(OBS)
    t_obs = time.time() - t_start
    pg.wait_for_timeout(int(CONTROL_S*1000))
    ctrl_applies = pg.evaluate("() => window.__applies.length")
    ctrl_reqs = len([t for t in reqs if t >= t_obs])
    ctrl_resps = len([t for t in resps if t >= t_obs])
    # Wait until a request is in flight (a request started with no response after it), 0.8 s in.
    deadline = time.time() + 15
    fired_at = None
    while time.time() < deadline:
        last_req = reqs[-1] if reqs else -1
        last_resp = resps[-1] if resps else -1
        now = time.time() - t_start
        if last_req > last_resp and now - last_req > 0.8:
            if not (len(sys.argv) > 4 and sys.argv[4] == "notrigger"):
                pg.evaluate("() => window.dash_clientside.set_props('mode', {data: {mode: 'window', window_size: Math.random()}})")
            fired_at = now
            break
        pg.wait_for_timeout(50)
    n_app_before = pg.evaluate("() => window.__applies.length")
    t_fire = time.time() - t_start
    pg.wait_for_timeout(int(AFTER_S*1000))
    applies = pg.evaluate("() => window.__applies")
    after_applies = len(applies) - n_app_before
    after_reqs = len([t for t in reqs if t > t_fire])
    after_resps = len([t for t in resps if t > t_fire])
    print(json.dumps({
        "control_window_s": CONTROL_S, "control_requests": ctrl_reqs, "control_responses": ctrl_resps, "control_applies": ctrl_applies,
        "trigger_fired_at_s": fired_at, "after_window_s": AFTER_S, "after_requests": after_reqs, "after_responses": after_resps, "after_applies": after_applies,
    }, indent=1))
    b.close()
