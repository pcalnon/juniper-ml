#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/myreader.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R4A's own reader of the census v2 transcripts, written from the shim's JavaScript only.

Lane timeline: a PUSH-ORDER walk of raw.lane. The shim pushes a dispatch's record after orig.apply returns, so a
nested (inner) dispatch's record precedes its enclosing one; the enclosing one re-logs the same change with an
earlier entry time and a `before` that no longer equals the current state. So: a record whose `before` equals the
current state is a new change (the innermost record); any other is a re-log.

Requests: raw.req folded per id: tW = first W; end = first A or X (R = pruned and re-added, still in flight).
Re-enables: every lane change to enabled (after == False). Classified by cause:
  fire  -- within 2 ms of a raw.fires record;  gate -- within 2 ms of a raw.gate record writing False;
  own   -- an answered request's A follows within 100 ms (its own guard release);
  late  -- otherwise; for an eviction, it must lie after the evicted predecessor's X (the predecessor's response
           landing while its successor is in flight).
For each eviction X of request S: the last re-enable in [tW(S), X(S)).
"""
import json
import sys
from collections import Counter


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def timeline(lane):
    st = None
    tl, relog, breaks = [], 0, 0
    for t, before, after, types in lane:
        if before == st or (st is None and not tl):
            if tl and tl[-1][1] == after:
                breaks += 1
            tl.append((t, after, types))
            st = after
        else:
            relog += 1
    return tl, relog, breaks


def requests(req):
    recs = {}
    for t, kind, rid, props in req:
        r = recs.setdefault(rid, {"id": rid, "tW": None, "end": None, "tEnd": None, "props": None})
        if kind == "W":
            if r["tW"] is None:
                r["tW"] = t
        elif kind == "R":
            continue
        elif r["end"] is None:
            r["end"], r["tEnd"], r["props"] = kind, t, props
    return recs


def main(paths):
    allrows = []
    for p in paths:
        d = load(p)
        raw = d["raw"]
        tl, relog, breaks = timeline(raw["lane"])
        recs = requests(raw["req"])
        order = sorted((r for r in recs.values() if r["tW"] is not None), key=lambda r: r["tW"])
        fires = [f[0] for f in raw["fires"]]
        gate_false = [g[0] for g in raw["gate"] if g[2] is False]
        answers = sorted(r["tEnd"] for r in recs.values() if r["end"] == "A")
        enables = [t for t, after, _ty in tl if after is False]
        ev = [r for r in order if r["end"] == "X"]
        ans = [r for r in order if r["end"] == "A"]
        print(f"== {p.split('/')[-2] if 'run2' in p else 'run1'}: changes={len(tl)} relogs={relog} breaks={breaks} requests={len(order)} answered={len(ans)} evicted={len(ev)} open={sum(1 for r in order if r['end'] is None)} fires={len(fires)} gate_false={len(gate_false)}")

        def cause(t):
            if any(abs(t - f) <= 2 for f in fires):
                return "fire"
            if any(abs(t - g) <= 2 for g in gate_false):
                return "gate"
            if any(0 <= a - t <= 100 for a in answers):
                return "own"
            return "late"

        idx = {r["id"]: i for i, r in enumerate(order)}
        for r in ev:
            ens = [t for t in enables if r["tW"] <= t < r["tEnd"]]
            if not ens:
                allrows.append((p, r["id"], None, None, None, None))
                continue
            t = ens[-1]
            c = cause(t)
            ref = t
            note = ""
            if c == "fire":
                ref = min(fires, key=lambda f: abs(f - t))
            elif c == "gate":
                ref = min(gate_false, key=lambda g: abs(g - t))
            elif c == "late":
                pred = order[idx[r["id"]] - 1]
                note = f"pred {pred['id']} end={pred['end']} X@{pred['tEnd']} ok={pred['end'] == 'X' and pred['tEnd'] < t}"
            allrows.append((p, r["id"], c, r["tEnd"] - t, r["tEnd"] - ref, note))
    trig = [x for x in allrows if x[2] in ("fire", "gate")]
    late = [x for x in allrows if x[2] == "late"]
    other = [x for x in allrows if x[2] not in ("fire", "gate", "late")]
    print(f"evictions: {len(allrows)}; trigger-started {len(trig)} ({Counter(x[2] for x in trig)}); within-run (late) {len(late)}; other {len(other)}")
    print("  trigger-started, from the lane change:", sorted(x[3] for x in trig))
    print("  trigger-started, from the fire/gate record:", sorted(x[4] for x in trig), "range", min(x[4] for x in trig), max(x[4] for x in trig))
    fr = [x[4] for x in trig if x[2] == "fire"]
    print("  fire-started only, from the fire record:", sorted(fr), "range", min(fr), max(fr), "n", len(fr))
    ls = sorted(x[3] for x in late)
    print("  within-run, from the late release:", ls, "range", min(ls), max(ls), "above 2400:", [g for g in ls if g > 2400])
    print("  within-run predecessor checks all ok:", all(x[5].endswith("ok=True") for x in late))
    for x in other:
        print("  OTHER:", x)
    alln = [x[3] for x in allrows if x[3] is not None]
    print("  all 29 from the lane change:", min(alln), max(alln))


if __name__ == "__main__":
    main(sys.argv[1:])
