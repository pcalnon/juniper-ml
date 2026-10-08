#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r4b.5mnsCd/myreader.py
# Written by Lane 11-R4B (adversarial, on round 3's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone; py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R4B's own reader, no repo code. Lane changes by a PUSH-ORDER walk (first record of each run of identical
(before, after) pairs is the innermost), compared against the type selection; evictions from raw.req; for every eviction,
the last re-enable (lane True->False) after the evicted request entered W and before its X, classified by the raw fire /
gate logs, else a release; for releases, whether the predecessor (previous W) was evicted before it (a late release)."""
import json

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/reports/e2e-canopy-2026-09-02/f058-census-v2/"
T = [W + "2026-10-05_census_live.json", W + "run2/2026-10-05_census_live.json"]


def push_walk(lane):
    out, prev = [], None
    for t, b, a, ty in lane:
        if prev is not None and (b, a) == prev:
            continue  # an enclosing record of the change just logged
        out.append((t, b, a, ty))
        prev = (b, a)
    return out


def type_sel(lane):
    return sorted([(t, b, a, ty) for (t, b, a, ty) in lane if ty in ("", "SET_LAYOUT")], key=lambda r: r[0])


allrows = []
for ti, p in enumerate(T, 1):
    with open(p) as fh:
        d = json.load(fh)
    raw = d["raw"]
    pw = push_walk(raw["lane"])
    ts = type_sel(raw["lane"])
    alt_pw = sum(1 for x, y in zip(pw, pw[1:]) if y[1] != x[2])
    same = [(r[0], r[2]) for r in sorted(pw, key=lambda r: r[0])] == [(r[0], r[2]) for r in ts]
    nonthunk_only = [r for r in pw if r[3] not in ("", "SET_LAYOUT")]
    print(f"T{ti}: push-walk changes {len(pw)} (alternation breaks {alt_pw}); type-selection {len(ts)}; identical (t, after): {same}; push-walk changes carried by a non-thunk innermost record: {len(nonthunk_only)}")
    req = {}
    for t, k, rid, props in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "W": None, "end": None, "tEnd": None})
        if k == "W" and r["W"] is None:
            r["W"] = t
        elif k in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = k, t
    order = sorted((r for r in req.values() if r["W"] is not None), key=lambda r: r["W"])
    prev_of = {b["id"]: a for a, b in zip(order, order[1:])}
    enables = sorted(t for t, b, a, ty in pw if b is True and a is False)
    fires = [f[0] for f in raw["fires"]]
    gates = [g[0] for g in raw["gate"] if g[2] is False]
    for r in order:
        if r["end"] != "X":
            continue
        cand = [t for t in enables if r["W"] <= t < r["tEnd"]]
        if not cand:
            allrows.append((ti, r["id"], None, None, "none"))
            continue
        t = cand[-1]
        f = [x for x in fires if abs(x - t) <= 5]
        g = [x for x in gates if abs(x - t) <= 5]
        if f:
            kind, src = "fire", f[0]
        elif g:
            kind, src = "gate", g[0]
        else:
            pv = prev_of.get(r["id"])
            kind = "late-release-of-pred" if (pv and pv["end"] == "X" and pv["tEnd"] <= t) else "release-other"
            src = t
        allrows.append((ti, r["id"], r["tEnd"] - t, r["tEnd"] - src, kind))
for row in allrows:
    print("  T%d req %s: X - last enable %s ms; X - source record %s ms; %s" % row)
trig = [r for r in allrows if r[4] in ("fire", "gate")]
late = [r for r in allrows if r[4] == "late-release-of-pred"]
other = [r for r in allrows if r[4] not in ("fire", "gate", "late-release-of-pred")]
print(f"trigger-started n={len(trig)}: lane-time {min(r[2] for r in trig)}-{max(r[2] for r in trig)}; source-record time {min(r[3] for r in trig)}-{max(r[3] for r in trig)}")
fr = [r for r in trig if r[4] == "fire"]
print(f"  fires n={len(fr)}: source-record {min(r[3] for r in fr)}-{max(r[3] for r in fr)}")
print(f"late-release-started n={len(late)}: {min(r[2] for r in late)}-{max(r[2] for r in late)}; >2400: {sorted(r[2] for r in late if r[2] > 2400)}")
print(f"other: {other}")
