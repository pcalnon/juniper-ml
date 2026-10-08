#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/extra_checks.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R3A extra checks: T-mode/T-gate lags; R2B's exact mutation through the 7af6a381 trace; push-order walk."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
RUNS = {
    "run1": W / "reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json",
    "run2": W / "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json",
}
spec = importlib.util.spec_from_file_location("rt", W / "util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)

for run, p in RUNS.items():
    d = json.loads(p.read_text())
    raw = d["raw"]
    reqW = {}
    reqEnd = {}
    for t, k, rid, _ in raw["req"]:
        if k == "W" and rid not in reqW:
            reqW[rid] = t
        if k in ("A", "X") and rid not in reqEnd:
            reqEnd[rid] = (k, t)
    for trg in d["triggers"]:
        if not trg.get("t_ms"):
            continue
        t, rid = trg["t_ms"], trg["open_request"]
        nxtW = min(w for r, w in reqW.items() if w > t)
        end = reqEnd.get(rid)
        gate_after = [(g[0] - t, g[1], g[2]) for g in raw["gate"] if t < g[0] <= t + 6000]
        print(f"{run} {trg['name']}: t={t} target={rid} into-flight={t - trg['open_since_ms']} target-end={end[0]}+{end[1]-t} nextW=+{nxtW - t} gate-writes-after={gate_after} clicks={[c - t for c in trg.get('clicks_ms') or []]}")
    # Push-order walk (R2A's method re-implemented independently): a record whose before == current state is a NEW change.
    state = None
    walk = []
    nonthunk_new = []
    for rec in raw["lane"]:
        t, b, a, ty = rec
        if b == state or (state is None and b is None):
            walk.append((t, a, ty))
            if ty not in ("", "SET_LAYOUT"):
                nonthunk_new.append(rec)
            state = a
    inner = rt.lane_timeline(raw["lane"])
    print(f"{run}: push-order changes {len(walk)}; innermost-type changes {len(inner)}; new changes carried only by non-thunk types: {len(nonthunk_new)}; dispatches {raw['dispatches']}")

# R2B's exact mutation on run 1: move req 177's release (902896) to 905500 and drop req 178's (905789).
d = json.loads(RUNS["run1"].read_text())
m = copy.deepcopy(d)
kept = []
for rec in m["raw"]["lane"]:
    rel = rec[1] is True and rec[2] is False and rec[3] == ""
    if rel and rec[0] == 905789:
        continue
    if rel and rec[0] == 902896:
        rec[0] = 905500
    kept.append(rec)
m["raw"]["lane"] = kept
res = rt.analyze(m)
for x in res["late"]:
    if x["evicted"] in (176, 177, 178, 179):
        print("R2B mutation: late", x["evicted"], "release", x["release_ms"], "under", x["under"], "ambiguous_with", x["ambiguous_with"])
print("R2B mutation: evictions 177/178 ->", [(e["id"], (e["late"] or {}).get("release_ms")) for e in res["evictions"] if e["id"] in (177, 178)], "unassigned", res["unassigned"], "breaks", res["alternation_breaks"])
# Same mutation WITHOUT dropping 178's release: is the moved one still flagged?
m2 = copy.deepcopy(d)
for rec in m2["raw"]["lane"]:
    if rec[1] is True and rec[2] is False and rec[3] == "" and rec[0] == 902896:
        rec[0] = 905500
res2 = rt.analyze(m2)
print("variant (178 kept):", [(x["evicted"], x["release_ms"], x["ambiguous_with"]) for x in res2["late"] if x["evicted"] in (177, 178)], "unassigned", [u["t"] for u in res2["unassigned"]])
