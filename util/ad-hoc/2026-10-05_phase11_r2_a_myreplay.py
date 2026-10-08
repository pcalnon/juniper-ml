# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/myreplay.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R2A's own watchdog replay, over my own innermost timeline (myreader.innermost_state_machine)."""
import bisect
import json
import random
import statistics
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from myreader import innermost_state_machine  # noqa: E402


def run(path):
    with open(path) as fh:
        d = json.load(fh)
    raw = d["raw"]
    sm, _, an = innermost_state_machine(raw["lane"])
    assert not an
    times = [c["t"] for c in sm]
    vals = [c["a"] for c in sm]
    # clamp: gate wrote True then False
    g = sorted(raw["gate"])
    on = [t for t, b, v in g if v is True]
    off = [t for t, b, v in g if v is False and on and t > on[0]]
    clamp = (on[0], off[0])
    t_hi = max(r[0] for r in raw["req"])

    def disabled(t):
        i = bisect.bisect_right(times, t) - 1
        return vals[i] is True if i >= 0 else False

    def wd(samples):
        since, n = None, 0
        for t in samples:
            if (not disabled(t)) or (clamp[0] <= t < clamp[1]):
                since = None
            elif since is None:
                since = t
            elif t - since >= 30000:
                since = None
                n += 1
        return n

    out = {}
    for P in (5000, 6000, 7500):
        aligned = []
        for phi in range(0, P, 10):
            s = []
            t = phi
            while t < t_hi:
                s.append(t)
                t += P
            aligned.append(wd(s))
        rng = random.Random(20261005 + P)
        jit = []
        for rep in range(2000):
            phi = rng.uniform(0, P)
            s = []
            t = phi
            while t < t_hi:
                x = t + rng.uniform(-P / 2, P / 2)
                if 0 <= x < t_hi:
                    s.append(x)
                t += P
            s.sort()
            jit.append(wd(s))
        out[P] = (min(aligned), statistics.median(aligned), max(aligned), len(aligned), statistics.median(jit), sum(1 for j in jit if j == 0) / len(jit))
        print(f"{path.split('/')[-2]} P={P}: aligned min {out[P][0]} median {out[P][1]} max {out[P][2]} over {out[P][3]} phases; jittered (2000, own RNG) median {out[P][4]}, zero share {out[P][5]:.3f}")


for p in sys.argv[1:]:
    run(p)
