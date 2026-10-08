# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/probe2.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-B2 probe 2: late-release attribution alternatives, enabled stretches, gate writes, grid reconstruction."""
import bisect
import importlib.util
import json
import statistics

spec = importlib.util.spec_from_file_location("rt", "util/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

for name, path in [("run1", "ev/2026-10-05_census_live.json"), ("run2", "ev/run2/2026-10-05_census_live.json")]:
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    res = rt.analyze(d)
    req = {}
    for t, kind, rid, props in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    byid = {r["id"]: r for r in reqs}
    Ws = [r["tW"] for r in reqs]
    print(f"=== {name}")
    print(" late releases: evicted -> under; under==evicted+1; release-evW; release-underW; underEnd; next W after release")
    for x in res["late"]:
        ev, un = byid[x["evicted"]], byid[x["under"]]
        i = bisect.bisect_right(Ws, x["release_ms"])
        nextW = Ws[i] - x["release_ms"] if i < len(Ws) else None
        print(f"  {x['evicted']}->{x['under']} succ={x['under'] == x['evicted'] + 1} relEvW={x['release_ms'] - ev['tW']} relUnderW={x['release_ms'] - un['tW']} under={un['end']}@{un['tEnd'] - x['release_ms']} nextW+{nextW}")
    # Enabled stretches: from lane timeline; (t_start_enabled, t_end_enabled, what ended)
    tl = rt.lane_timeline(raw["lane"])
    en = []
    for (t0, s0), (t1, s1) in zip(tl, tl[1:]):
        if s0 is False and s1 is True:
            en.append((t0, t1, t1 - t0))
    durs = sorted(x[2] for x in en)
    print(f" enabled stretches: n {len(en)} min {durs[:8]} median {statistics.median(durs)} p10 {durs[len(durs)//10]} max {durs[-3:]}")
    short = [x for x in en if x[2] < 1000]
    print(f"  enabled < 1000 ms: {len(short)}")
    for a, b, du in short[:20]:
        i = bisect.bisect_left(Ws, b - 50)
        w_near = [w - b for w in Ws[i:i + 2]]
        print(f"   {a}->{b} ({du} ms); W near end (ms from end): {w_near}")
    # Fire -> next W
    fw = []
    for t, _b, _s in raw["fires"]:
        i = bisect.bisect_right(Ws, t)
        fw.append(Ws[i] - t if i < len(Ws) else None)
    print(" fire -> next W (ms):", fw)
    # gate writes with in-flight and answers
    print(" gate writes:")
    for t, before, v in raw["gate"]:
        live = [r for r in reqs if r["tW"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
        i = bisect.bisect_right(Ws, t)
        print(f"   @{t} {before}->{v} in flight {[(r['id'], t - r['tW'], r['end'], (r['tEnd'] - t) if r['tEnd'] else None) for r in live]} next W +{(Ws[i] - t) if i < len(Ws) else None}")
    # grid reconstruction: lane state at fire - 5000k for k=0..7, and distance to nearest boundary
    times = [t for t, _ in tl]

    def state(t):
        i = bisect.bisect_right(times, t) - 1
        return tl[i][1] if i >= 0 else False

    def dist_boundary(t):
        i = bisect.bisect_left(times, t)
        c = [abs(times[j] - t) for j in (i - 1, i) if 0 <= j < len(times)]
        return min(c)

    print(" grid reconstruction (k=1..7: lane disabled at fire-5000k? [dist to nearest lane change ms]):")
    for t, _b, _s in raw["fires"]:
        row = []
        for k in range(1, 8):
            tk = t - 5000 * k
            row.append(f"{'D' if state(tk) else 'e'}{dist_boundary(tk)}")
        print(f"   fire@{t}: {' '.join(row)}")
