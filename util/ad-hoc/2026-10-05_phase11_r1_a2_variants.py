# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/variants.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Reproduce the ledger's divergent figures under alternative lane timelines / percentile rules, to locate the cause."""
import importlib.util, sys, io, contextlib, statistics
spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec); sys.modules["myreader"] = mr; spec.loader.exec_module(mr)


def timeline_outermost(L):
    """Changes at the OUTERMOST record of each nesting chain (the enclosing dispatch's entry time)."""
    out = []
    for j, r in enumerate(L):
        nxt = L[j + 1] if j + 1 < len(L) else None
        if nxt is not None and nxt[3] not in ("", "SET_LAYOUT") and (nxt[1], nxt[2]) == (r[1], r[2]) and nxt[0] <= r[0]:
            continue
        out.append((r[0], r[1], r[2], j))
    out.sort(key=lambda x: (x[0], x[3]))
    return out


def timeline_alltimesorted(L):
    """Every lane record, sorted by time, de-duplicated by state: a record that does not change the running state is dropped."""
    s = None
    out = []
    for r in sorted(((r[0], r[1], r[2], j) for j, r in enumerate(L)), key=lambda x: (x[0], x[3])):
        if r[2] != s:
            out.append(r)
            s = r[2]
    return out


def episodes(tl):
    d = []
    for p, q in zip(tl, tl[1:]):
        if p[2] is True and q[2] is False:
            d.append(q[0] - p[0])
    return d


def enabled(tl, lo, hi):
    tot = 0
    s = None
    for r in tl:
        if r[0] < lo:
            s = r[2]
    cur = lo
    for r in tl:
        if lo <= r[0] < hi:
            if s is False:
                tot += r[0] - cur
            cur = r[0]
            s = r[2]
    if s is False:
        tot += hi - cur
    return tot


for p in sys.argv[1:]:
    with contextlib.redirect_stdout(io.StringIO()):
        d, reqs, phys, ordered, fire_rows = mr.analyse(p, "x")
    raw = d["raw"]
    L = raw["lane"]
    print(p)
    tli = [(x[0], x[1], x[2], x[4]) for x in phys]
    for name, tl in (("innermost", tli), ("outermost", timeline_outermost(L)), ("all-sorted-dedup", timeline_alltimesorted(L))):
        ep = episodes(tl)
        eps = sorted(ep)
        ages, ens = [], []
        for f in raw["fires"]:
            t = f[0]
            last_on = max((r for r in tl if r[0] < t and r[2] is True), key=lambda r: (r[0], r[3]))
            ages.append(t - last_on[0])
            ens.append(enabled(tl, t - 30000, t))
        print("  %-17s changes=%d episodes n=%d median=%s upper=%s | fire ages %d..%d | enabled %d..%d" % (
            name, len(tl), len(ep), statistics.median(ep), eps[len(eps) // 2], min(ages), max(ages), min(ens), max(ens)))
    ift = sorted(r["tEnd"] - r["tW"] for r in ordered if r["end"])
    n = len(ift)
    print("  in-flight n=%d around p90: idx %s" % (n, [(i, ift[i]) for i in range(int(0.9 * n) - 3, int(0.9 * n) + 3)]))
    q = statistics.quantiles(ift, n=10)
    q2 = statistics.quantiles(ift, n=10, method="inclusive")
    print("  statistics.quantiles exclusive p90=%s inclusive p90=%s; int(0.9n)=%d -> %d; round(0.9n)=%d" % (q[8], q2[8], int(0.9 * n), ift[int(0.9 * n)], round(0.9 * n)))
    ans = sorted(r["tEnd"] - r["tW"] for r in ordered if r["end"] == "A")
    print("  answered-only p90: int(0.9n)->%d nearest->%d" % (ans[int(0.9 * len(ans))], mr.pct_nearest(ans, 0.9)))
