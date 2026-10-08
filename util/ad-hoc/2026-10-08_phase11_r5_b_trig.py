# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r5b.KImIJx/trig.py
# Written by Lane 11-R5B (adversarial, on round 4's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R5B: re-derive the trigger lag from the two transcripts, own reader (no repo code)."""
import json
import sys

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/reports/e2e-canopy-2026-09-02/f058-census-v2/"
PATHS = [W + "2026-10-05_census_live.json", W + "run2/2026-10-05_census_live.json"]


def fold(req):
    recs = {}
    for t, k, rid, p in req:
        r = recs.setdefault(rid, {"tW": None, "end": None, "tEnd": None})
        if k == "W":
            if r["tW"] is None:
                r["tW"] = t
        elif k == "R":
            continue
        elif r["end"] is None:
            r["end"], r["tEnd"] = k, t
    return recs


for path in PATHS:
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    raw = d["raw"]
    recs = fold(raw["req"])
    byW = sorted((r["tW"], rid) for rid, r in recs.items() if r["tW"] is not None)
    print("==", path.split("f058-census-v2/")[1], "served", d["served_sha"][:8])
    for tr in d["triggers"]:
        name = tr["name"]
        if "t_ms" not in tr:
            print(f"  {name}: {tr.get('verdict')} (no t_ms); keys {sorted(tr)}")
            continue
        t, rid = tr["t_ms"], tr["open_request"]
        r = recs[rid]
        age = t - tr["open_since_ms"]
        ans = r["tEnd"] - t if r["tEnd"] is not None else None
        nxt = [(tw, i) for tw, i in byW if tw > t]
        nxtW = nxt[0][0] - t if nxt else None
        gates = [(g[0] - t, g[1], g[2]) for g in raw["gate"] if t < g[0] <= t + 6000]
        fires = [(f[0] - t) for f in raw["fires"] if t - 1000 < f[0] <= t + 6000]
        lane = [(l[0] - t, l[1], l[2], l[3][:40]) for l in raw["lane"] if t - 200 < l[0] <= t + 5000]
        print(f"  {name}: t={t} req={rid} W={r['tW']} age={age} end={r['end']} ans_after={ans} next_W_after={nxtW} took={tr.get('took')} verdict={tr.get('stats', {}).get('verdict')}")
        if "clicks_ms" in tr:
            c = tr["clicks_ms"]
            print(f"     clicks_ms={c} -> after fire {[x - t for x in c]} ; between {c[1] - c[0]}")
        if "mode_before" in tr:
            print(f"     mode_before={tr['mode_before']}")
        print(f"     gate writes (dt, before, value) within 6 s: {gates}")
        print(f"     fires within (-1, 6] s: {fires}")
        # requests in flight at each gate write
        for g in gates:
            tg = t + g[0]
            inflight = [i for i, rr in recs.items() if rr["tW"] is not None and rr["tW"] <= tg and (rr["tEnd"] is None or rr["tEnd"] > tg)]
            for i in inflight:
                rr = recs[i]
                print(f"       at gate +{g[0]}: in flight req {i} W=+{rr['tW'] - t} end={rr['end']} +{(rr['tEnd'] - t) if rr['tEnd'] is not None else None} (into flight {tg - rr['tW']} ms; answered {((rr['tEnd'] - tg) if rr['tEnd'] is not None else None)} ms later)")
    print("  flights (W->end) median:", sorted(r["tEnd"] - r["tW"] for r in recs.values() if r["tW"] is not None and r["tEnd"] is not None)[len([1 for r in recs.values() if r["tW"] is not None and r["tEnd"] is not None]) // 2])
sys.exit(0)
