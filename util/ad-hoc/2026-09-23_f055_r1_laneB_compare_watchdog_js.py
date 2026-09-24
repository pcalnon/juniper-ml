# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: compares the refactored strand watchdogs' JavaScript.
# Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/compare_watchdog_js.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Compare the registered strand-watchdog JS between the parent and fix builds.

Reads the JSON dumps written by dump_callbacks.py; extracts each watchdog's inline script
by its Dash function name; compares whitespace-normalised token streams.
"""

import json
import re
import sys

parent = json.load(open(sys.argv[1], encoding="utf-8"))
fix = json.load(open(sys.argv[2], encoding="utf-8"))


def watchdog_js(dump, lane):
    recs = [r for r in dump["records"] if r["output"].startswith(f"{lane}.disabled@")]
    assert len(recs) == 1, (lane, len(recs))
    fn = recs[0]["clientside"]["function_name"]
    hits = [s for s in dump["inline_scripts"] if fn in s]
    assert len(hits) == 1, (lane, fn, len(hits))
    return fn, hits[0]


def norm(js):
    return re.sub(r"\s+", " ", js).strip()


p_fn, p_js = watchdog_js(parent, "metrics-store-interval")
f_fn, f_js = watchdog_js(fix, "metrics-store-interval")
s_fn, s_js = watchdog_js(fix, "status-bar-interval")

print("parent metrics fn:", p_fn)
print("fix    metrics fn:", f_fn)
print("fix    status  fn:", s_fn)
print("metrics JS identical after whitespace normalisation:", norm(p_js).replace(p_fn, "FN") == norm(f_js).replace(f_fn, "FN"))
sub = norm(s_js).replace(s_fn, "FN").replace("__statusBarDisabledSince", "__metricsStoreDisabledSince")
print("status JS == metrics JS modulo clock name:", sub == norm(f_js).replace(f_fn, "FN"))
print("---- parent metrics watchdog (normalised) ----")
print(norm(p_js))
print("---- fix status-bar watchdog (normalised) ----")
print(norm(s_js))
