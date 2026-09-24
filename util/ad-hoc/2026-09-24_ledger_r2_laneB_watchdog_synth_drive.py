# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-B: the fire-detector check (2 real fires, 0 counted).
# Source: session ddf7847c's tmpfs scratchpad, r2b.SQyNnR/synth_drive2.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scratch driver 2 (lane R2-B): does the f058 census's watchdog_fires() count a real fire?

Installs the census's EXACT INSTALL JS (ast-extracted) and scores its since-log with the census's OWN
watchdog_fires() (ast-extracted and exec'd alone), against window.__groundTruthFires.
"""
import ast
import json
import sys

from playwright.sync_api import sync_playwright

CENSUS = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/graceful-sprouting-panda/util/ad-hoc/2026-09-24_f058_trigger_census.py"
url = sys.argv[1]
watch = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0

src = open(CENSUS, encoding="utf-8").read()
tree = ast.parse(src)
INSTALL = None
ns = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "INSTALL" for t in node.targets):
        INSTALL = ast.literal_eval(node.value)
    if isinstance(node, ast.FunctionDef) and node.name == "watchdog_fires":
        exec(compile(ast.Module(body=[node], type_ignores=[]), "watchdog_fires", "exec"), ns)
watchdog_fires = ns["watchdog_fires"]

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(2000)
    page.evaluate(INSTALL, {"feed": "feed.data", "lane": "lane"})
    page.wait_for_timeout(int(watch * 1000))
    raw = page.evaluate("() => window.__f058")
    truth = page.evaluate("() => window.__groundTruthFires || 0")
    browser.close()

since = raw["since"]
long_resets = [e for e in since if e[2] is None and e[1] is not None and (e[0] - e[1]) >= 29500]
print(json.dumps({
    "ground_truth_fires": truth,
    "census_watchdog_fires": len(watchdog_fires(since)),
    "since_resets_after_29_5s": len(long_resets),
    "their_lane_disabled_flags": [e[3] for e in long_resets],
    "since_log": since,
}, indent=1))
