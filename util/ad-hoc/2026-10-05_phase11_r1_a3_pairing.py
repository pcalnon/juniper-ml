# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/pairing.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-A3: is the release trace's late-release pairing forced by the timeline, or chosen by its oldest-first rule?

Independent of the trace's assignment rule: for each eviction run, list every non-own, non-write release
(the trace's own definitions of release/write, recomputed here) in order with the run's X and A events, and
check strict alternation X_k < r_k < (X_{k+1} or A_{k+1}) with exactly one release per interval. If that holds,
any one-response-per-request pairing must be the diagonal one, so the oldest-first rule is not what makes it.
Also derives the numbers no named instrument prints (cycle medians, the 34.8 s stall).
"""
import bisect
import json
import statistics
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"


def main(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = d["raw"]
    req = {}
    for t, kind, rid, _p in raw["req"]:
        r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
        if kind == "W" and r["tW"] is None:
            r["tW"] = t
        elif kind in ("A", "X") and r["end"] is None:
            r["end"], r["tEnd"] = kind, t
    reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
    writes = sorted({t for t, _b, _s in raw["fires"]} | {t for t, _b, v in raw["gate"] if v is False})
    rel = sorted(t for t, b, a, ty in raw["lane"] if b is True and a is False and ty == "" and not any(abs(t - w) <= 2 for w in writes))
    a_times = sorted(r["tEnd"] for r in reqs if r["end"] == "A")
    # own: a release followed by SOME A within 100 ms (looser than the trace: any request, not the newest in flight)
    own = [t for t in rel if (lambda i: i < len(a_times) and a_times[i] - t <= 100)(bisect.bisect_left(a_times, t))]
    other = [t for t in rel if t not in set(own)]
    print(f"{path.name if hasattr(path, 'name') else path}: releases {len(rel)}, followed by an A within 100 ms {len(own)}, other {len(other)}, evicted {sum(r['end'] == 'X' for r in reqs)}")
    # alternation per run
    runs, cur = [], []
    for r in reqs:
        if r["end"] == "X":
            cur.append(r)
        elif cur:
            runs.append((cur, r))
            cur = []
    ok_all = True
    for run, nxt in runs:
        evs = run + [nxt]
        bounds = []
        for k, r in enumerate(run):
            lo = r["tEnd"]
            hi = evs[k + 1]["tEnd"]
            inside = [t for t in other if lo <= t < hi]
            bounds.append(len(inside))
        # releases between the run's first W - 10 s and its first X (should be none from this run)
        before = [t for t in other if run[0]["tW"] - 10000 <= t < run[0]["tEnd"]]
        ok = all(c == 1 for c in bounds) and not before
        ok_all &= ok
        print(f"  run of {len(run)} (ids {run[0]['id']}..{run[-1]['id']}, then {nxt['id']} {nxt['end']}): non-own releases per [X_k, end_k+1) {bounds}; any in the 10 s before the first X: {before} -> alternation {'HOLDS' if ok else 'FAILS'}")
    print(f"  every run strictly alternates: {ok_all}; non-own releases outside every run interval: {[t for t in other if not any(r[0]['tEnd'] <= t < nx['tEnd'] for r, nx in [(rr, n) for rr, n in runs])]}")
    # derived numbers
    gaps = [b - a for a, b in zip(a_times, a_times[1:])]
    print(f"  median gap between consecutive A over the whole run: {statistics.median(gaps)} ms; max {max(gaps)} ms")
    longest = max(gaps)
    i = gaps.index(longest)
    print(f"  longest A-to-A gap {longest} ms, from {a_times[i]} to {a_times[i + 1]}")
    # in-flight durations of A-only requests
    afl = sorted(r["tEnd"] - r["tW"] for r in reqs if r["end"] == "A")
    print(f"  A-only in-flight: min {afl[0]} max {afl[-1]}; all ended in-flight min {min(r['tEnd'] - r['tW'] for r in reqs if r['end'])}")
    # next-W gap after own releases vs after late releases (does a late release re-enable like an own one?)
    w_times = sorted(r["tW"] for r in reqs)
    def next_w(t):
        j = bisect.bisect_right(w_times, t)
        return w_times[j] - t if j < len(w_times) else None
    own_nw = sorted(x for x in (next_w(t) for t in own) if x is not None)
    oth_nw = sorted(x for x in (next_w(t) for t in other) if x is not None)
    q = lambda xs: (xs[0], statistics.median(xs), xs[-1]) if xs else None
    print(f"  release -> next W (ms): after own releases (min, median, max) {q(own_nw)}; after the other releases {q(oth_nw)}")


if __name__ == "__main__":
    for p in (EV / "2026-10-05_census_live.json", EV / "run2/2026-10-05_census_live.json"):
        main(p)
