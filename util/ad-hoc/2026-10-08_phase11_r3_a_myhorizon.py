#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R3A.THYyw0/myhorizon.py
# Written by Lane 11-R3A (measurement re-creation, artifact-first, on round 2's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R3A's own reader: every mid-request re-enable, its in-flight request's fate, and the next W.

Written from the shim's JavaScript (``2026-10-04_f058_census_v2_shim.py``), not from the repo readers:
  req  [t, 'W'|'A'|'X'|'R', id, props]  -- t = entry time of the dispatch that carried the action
  fires [t, laneBefore, since]          -- watchdog AddExecuted writing disabled=false
  gate  [t, laneBefore, value]          -- gate AddExecuted with its written value
A re-enable is a fire, or a gate write of False, whose laneBefore is True.  It is "mid-request" if a feeder
request has entered watched (W) and not yet ended (A/X) at that time.
"""
import json
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
RUNS = {
    "run1": W / "reports/e2e-canopy-2026-09-02/f058-census-v2/2026-10-05_census_live.json",
    "run2": W / "reports/e2e-canopy-2026-09-02/f058-census-v2/run2/2026-10-05_census_live.json",
}


def requests(raw):
    out = {}
    for t, k, rid, props in raw["req"]:
        r = out.setdefault(rid, {"id": rid, "W": None, "end": None, "tEnd": None})
        if k == "W" and r["W"] is None:
            r["W"] = t
        elif k in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = k, t
    return sorted((r for r in out.values() if r["W"] is not None), key=lambda r: r["W"])


allrows = []
for run, path in RUNS.items():
    d = json.loads(path.read_text())
    raw = d["raw"]
    reqs = requests(raw)
    trig = {x["name"]: x for x in d["triggers"]}
    events = [(t, "fire") for t, b, _s in raw["fires"] if b is True] + [(t, "gate") for t, b, v in raw["gate"] if b is True and v is False]
    nonmid = []
    for t, kind in sorted(events):
        live = [r for r in reqs if r["W"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
        if not live:
            nonmid.append((t, kind))
            continue
        assert len(live) == 1, (run, t, live)
        q = live[0]
        nxt = next(r for r in reqs if r["W"] > t)
        row = {
            "run": run, "t": t, "kind": kind, "q": q["id"], "q_end": q["end"],
            "q_end_minus_t": q["tEnd"] - t,
            "nextW_minus_t": nxt["W"] - t, "next_id": nxt["id"],
            "q_W_age": t - q["W"],
        }
        allrows.append(row)
    print(run, "re-enables with nothing in flight:", nonmid)
    print(run, "triggers:", {k: (v.get("t_ms"), v.get("clicks_ms"), v.get("open_request"), v.get("open_since_ms")) for k, v in trig.items()})

print("\nmid-request re-enables:", len(allrows), "fires", sum(r["kind"] == "fire" for r in allrows), "gate", sum(r["kind"] == "gate" for r in allrows))
ev = [r for r in allrows if r["q_end"] == "X"]
nev = [r for r in allrows if r["q_end"] == "A"]
print("evicting:", len(ev), "of which fires", sum(r["kind"] == "fire" for r in ev))
print("  evict (X) - t, all 8:", sorted(r["q_end_minus_t"] for r in ev), "-> range", min(r["q_end_minus_t"] for r in ev), max(r["q_end_minus_t"] for r in ev))
evf = [r for r in ev if r["kind"] == "fire"]
print("  evict (X) - t, fires:", min(r["q_end_minus_t"] for r in evf), max(r["q_end_minus_t"] for r in evf))
print("non-evicting:", len(nev), "of which fires", sum(r["kind"] == "fire" for r in nev))
print("  answer (A) - t, all:", min(r["q_end_minus_t"] for r in nev), max(r["q_end_minus_t"] for r in nev))
nevf = [r for r in nev if r["kind"] == "fire"]
print("  answer (A) - t, fires:", min(r["q_end_minus_t"] for r in nevf), max(r["q_end_minus_t"] for r in nevf))
print("  gate non-evicting:", [(r["run"], r["t"], r["q_end_minus_t"]) for r in nev if r["kind"] == "gate"])
print("other end kinds:", [r for r in allrows if r["q_end"] not in ("A", "X")])
nw = sorted(allrows, key=lambda r: r["nextW_minus_t"])
print("\nnext W - t, all 32:", [r["nextW_minus_t"] for r in nw])
print("  range", nw[0]["nextW_minus_t"], nw[-1]["nextW_minus_t"])
print("  top 4:", [(r["run"], r["t"], r["kind"], r["nextW_minus_t"], r["q_end"]) for r in nw[-4:]])
print("  without top 3:", nw[0]["nextW_minus_t"], nw[-4]["nextW_minus_t"])
print("  evicting only next W - t:", sorted(r["nextW_minus_t"] for r in ev))
print("  fires only next W - t range:", min(r["nextW_minus_t"] for r in allrows if r["kind"] == "fire"), max(r["nextW_minus_t"] for r in allrows if r["kind"] == "fire"))
print("  X to next W (evicting):", sorted(r["nextW_minus_t"] - r["q_end_minus_t"] for r in ev))
print("  q age at re-enable (ms into flight):", min(r["q_W_age"] for r in allrows), max(r["q_W_age"] for r in allrows))
