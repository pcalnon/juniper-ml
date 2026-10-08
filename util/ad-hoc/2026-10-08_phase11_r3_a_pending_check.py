#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/pending_check.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""At each late release, how many evicted requests were already evicted and still unpaired (any run, and same run)?"""
import json
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
for p in ("reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json", "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json"):
    raw = json.loads((W / p).read_text())["raw"]
    W_, E = {}, {}
    for t, k, rid, _ in raw["req"]:
        if k == "W" and rid not in W_:
            W_[rid] = t
        if k in ("A", "X") and rid not in E:
            E[rid] = (k, t)
    ev = sorted((rid for rid, (k, _t) in E.items() if k == "X"), key=lambda r: W_[r])
    # independent pairing: each evicted request's release = first thunk True->False after its X and before its successor's end
    order = sorted(W_, key=lambda r: W_[r])
    succ = dict(zip(order, order[1:]))
    rels = sorted(t for t, b, a, ty in raw["lane"] if b is True and a is False and ty == "")
    worst = 0
    for rid in ev:
        tx = E[rid][1]
        s = succ[rid]
        s_end = E.get(s, ("?", 10**12))[1]
        mine = [t for t in rels if tx <= t < s_end]
        if not mine:
            print("  no release in successor flight for", rid)
            continue
        t = mine[0]
        others = [o for o in ev if o != rid and E[o][1] <= t and not any(E[o][1] <= u < E.get(succ[o], ("?", 10**12))[1] and u < t for u in rels)]
        worst = max(worst, len(others))
    print(p.split("/")[-2], "evicted", len(ev), "max other evicted-and-unreleased requests at a late release:", worst)
