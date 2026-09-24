# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-B: runs the F-058 census's own JavaScript on that app.
# Source: session ddf7847c's tmpfs scratchpad, r2b.SQyNnR/synth_drive.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scratch driver (lane R2-B): run the f058 census's EXACT INSTALL JS against the synthetic app.

Reads INSTALL out of util/ad-hoc/2026-09-24_f058_trigger_census.py with ast (no import, no side effects),
installs it after a settle, watches for WATCH seconds, and reports how the census would classify each
request (tE set = APPLIED, tGone set with tE null = EVICTED) next to the wire's status codes.
"""
import ast
import json
import sys
import time

from playwright.sync_api import sync_playwright

CENSUS = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda/util/ad-hoc/2026-09-24_f058_trigger_census.py"
url = sys.argv[1]
settle = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
watch = float(sys.argv[3]) if len(sys.argv) > 3 else 40.0

tree = ast.parse(open(CENSUS, encoding="utf-8").read())
INSTALL = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "INSTALL" for t in node.targets):
        INSTALL = ast.literal_eval(node.value)
assert INSTALL, "INSTALL not found"

statuses = []


def on_response(resp):
    if "_dash-update-component" in resp.url:
        try:
            body = resp.request.post_data_json or {}
        except Exception:
            body = {}
        if str(body.get("output") or "") == "feed.data":
            statuses.append(resp.status)


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("response", on_response)
    page.goto(url)
    page.wait_for_timeout(int(settle * 1000))
    n_before = len(statuses)
    inst = page.evaluate(INSTALL, {"feed": "feed.data", "lane": "lane"})
    t0 = time.time()
    page.wait_for_timeout(int(watch * 1000))
    raw = page.evaluate("() => window.__f058")
    browser.close()

reqs = raw["reqs"]
applied = [r for r in reqs if r["tE"] is not None]
evicted = [r for r in reqs if r["tE"] is None and r["tGone"] is not None]
pending = [r for r in reqs if r["tE"] is None and r["tGone"] is None]
after = statuses[n_before:]
print(json.dumps({
    "install": inst,
    "wire_statuses_after_install": {str(s): after.count(s) for s in sorted(set(after))},
    "census_tracked": len(reqs),
    "census_APPLIED": len(applied),
    "census_EVICTED": len(evicted),
    "census_unresolved": len(pending),
    "notifications": raw["notifications"],
    "lane_transitions": len(raw["lane"]),
}, indent=1))
