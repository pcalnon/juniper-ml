#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R5A.LBVRcz/triglag.py
# Written by Lane 11-R5A (measurement re-creation, artifact-first, on round 4's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R5A's own reader of the trigger lag, written from the shim's JavaScript and the live driver only.

raw.req  = [t, kind, id, props], kind W (entered watched), A (answer taken), X (evicted), R (pruned+re-added)
raw.gate = [t, before, value]   a gate write to the lane's disabled
raw.lane = [t, before, after, action types]
trigger  = {name, t_ms (page time at the poll that found the open request), open_request, open_since_ms, clicks_ms}
Prints numbers only.
"""
import json
import statistics
import sys

PATHS = sys.argv[1:]


def fold(req):
    recs = {}
    for t, kind, rid, props in req:
        r = recs.setdefault(rid, {"tW": None, "end": None, "tEnd": None})
        if kind == "W":
            if r["tW"] is None:
                r["tW"] = t
        elif kind == "R":
            continue
        elif r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    return recs


for p in PATHS:
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    raw = d["raw"]
    recs = fold(raw["req"])
    flights = [r["tEnd"] - r["tW"] for r in recs.values() if r["tW"] is not None and r["end"] is not None]
    print(f"== {p.split('/')[-2]}: {len(recs)} requests, flight median {statistics.median(flights)} ms (n={len(flights)})")
    gate = raw["gate"]
    print("   gate records:", [(g[0], g[1], g[2]) for g in gate])
    for trg in d["triggers"]:
        name = trg["name"]
        if "t_ms" not in trg:
            print(f"   {name}: no t_ms ({trg.get('verdict')})")
            continue
        t = trg["t_ms"]
        rid = trg["open_request"]
        r = recs[rid]
        age = t - trg["open_since_ms"]
        print(f"   {name}: fired t={t}; open_request {rid} tW={r['tW']} (open_since {trg['open_since_ms']}), age at fire {age} ms; "
              f"targeted request {r['end']} at +{r['tEnd'] - t} ms")
        # next request to enter watched after the fire
        nxt = sorted((v["tW"], k) for k, v in recs.items() if v["tW"] is not None and v["tW"] > t)
        if nxt:
            ntw, nid = nxt[0]
            nr = recs[nid]
            print(f"      next request {nid} entered +{ntw - t} ms; ended {nr['end']} at +{nr['tEnd'] - t if nr['tEnd'] is not None else None} ms")
        after = [g for g in gate if g[0] > t and g[0] <= t + 10000]
        print(f"      gate writes within 10 s: {[(g[0] - t, g[1], g[2]) for g in after]}")
        if name == "T-tab":
            c = trg["clicks_ms"]
            print(f"      clicks returned at +{c[0] - t}, +{c[1] - t} ms; between clicks {c[1] - c[0]} ms")
            for i, ci in enumerate(c):
                nxt_c = c[i + 1] if i + 1 < len(c) else ci + 10000
                gw = [g for g in gate if ci <= g[0] < nxt_c]
                gw2 = [g for g in gate if g[0] >= ci]
                print(f"      click {i + 1}: first gate write after its return +{(gw2[0][0] - ci) if gw2 else None} ms (abs +{(gw2[0][0] - t) if gw2 else None} ms)")
            # where is each gate write relative to requests in flight
            for g in after:
                inflight = [(k, v["tW"], v["tEnd"], v["end"]) for k, v in recs.items() if v["tW"] is not None and v["tW"] <= g[0] and (v["tEnd"] is None or v["tEnd"] > g[0])]
                print(f"      gate write at +{g[0] - t}: in flight {[(k, g[0] - tw, (te - g[0]) if te else None, e) for k, tw, te, e in inflight]}")
