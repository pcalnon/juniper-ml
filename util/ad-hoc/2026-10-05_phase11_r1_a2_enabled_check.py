# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, a2/enabled_check.py
# Written by Lane 11-A2 (measurement re-creation, raw-transcript-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Brute-force check of 'ms ENABLED in the 30 s before each fire', with several window/record-set variants."""
import importlib.util, sys, io, contextlib
spec = importlib.util.spec_from_file_location("myreader", "/tmp/tmp.AFzDbAMY9I/myreader.py")
mr = importlib.util.module_from_spec(spec); sys.modules["myreader"] = mr; spec.loader.exec_module(mr)


def state_series(changes, T):
    """changes: [(t, after)] sorted; returns list s[ms] = disabled value at ms (change at t applies from t)."""
    s = [None] * (T + 1)
    cur = None
    j = 0
    for ms in range(T + 1):
        while j < len(changes) and changes[j][0] <= ms:
            cur = changes[j][1]
            j += 1
        s[ms] = cur
    return s


for p in sys.argv[1:]:
    with contextlib.redirect_stdout(io.StringIO()):
        d, reqs, phys, ordered, fire_rows = mr.analyse(p, "x")
    raw = d["raw"]
    T = max(x[0] for x in raw["lane"]) + 10
    # variant A: physical changes (innermost '' + layout)
    chA = [(x[0], x[2]) for x in phys]
    sA = state_series(chA, T)
    # variant B: ALL lane records in array order sorted by time (stable)
    chB = sorted([(x[0], x[2]) for x in raw["lane"]], key=lambda r: r[0])
    sB = state_series(chB, T)
    # variant C: outermost records only (the LAST of each nesting chain = the record whose next record is not an outer of the same chain)
    L = raw["lane"]
    outer = []
    for j, r in enumerate(L):
        nxt = L[j + 1] if j + 1 < len(L) else None
        if nxt is not None and nxt[3] not in ("", "SET_LAYOUT") and (nxt[1], nxt[2]) == (r[1], r[2]) and nxt[0] <= r[0]:
            continue
        outer.append((r[0], r[2]))
    outer.sort(key=lambda r: r[0])
    sC = state_series(outer, T)
    print(p)
    for f in raw["fires"]:
        t = f[0]
        a = sum(1 for ms in range(t - 30000, t) if sA[ms] is False)
        a2 = sum(1 for ms in range(t - 30000, t + 1) if sA[ms] is False)
        b = sum(1 for ms in range(t - 30000, t) if sB[ms] is False)
        c = sum(1 for ms in range(t - 30000, t) if sC[ms] is False)
        print("  fire %7d  phys[t-30s,t)=%5d  phys[t-30s,t]=%5d  allrecs=%5d  outermost=%5d" % (t, a, a2, b, c))
