# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B2.KZI9rh/model6.py
# Written by Lane 11-B2 (adversarial, claims beyond evidence, escalate side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-B2 model 6 (a MODEL, not a measurement): watchdog false fires per hour on a synthetic healthy lane.

Lane: cycles of [disabled R ms][enabled E ms], R ~ N(R0, sdR), E ~ N(E0, sdE) clipped >= 1000 (the 1 s tick).
Sampler: every 5000 ms (+-200 ms uniform jitter); canopy's predicate (dashboard_manager.py:2531-2545 at 60ae1870).
A fire re-anchors nothing here (the replay's simplification too). 20 lanes x 2 h per setting.
"""
import random
import statistics

STRAND = 30000


def lane(rng, hours, R0, sdR, E0, sdE):
    t, out = 0.0, []
    end = hours * 3.6e6
    while t < end:
        r = max(300.0, rng.gauss(R0, sdR))
        e = max(1000.0, rng.gauss(E0, sdE))
        out.append((t, t + r))  # disabled interval
        t += r + e
    return out, end


def fires(intervals, end, rng, period=5000.0, jit=200.0):
    i, since, n = 0, None, 0
    t = rng.uniform(0, period)
    while t < end:
        s = t + rng.uniform(-jit, jit)
        while i < len(intervals) and intervals[i][1] <= s:
            i += 1
        dis = i < len(intervals) and intervals[i][0] <= s < intervals[i][1]
        if not dis:
            since = None
        elif since is None:
            since = s
        elif s - since >= STRAND:
            since = None
            n += 1
        t += period
    return n


rng = random.Random(11)
for R0 in (2800, 4000, 5500, 7000):
    for E0 in (2100,):
        rates = []
        for _ in range(20):
            iv, end = lane(rng, 2, R0, 450, E0, 450)
            rates.append(fires(iv, end, rng) / 2)
        cyc = R0 + E0
        print(f"R0 {R0} ms, E0 {E0} ms (cycle ~{cyc} ms, disabled {R0 / cyc:.0%}): false fires/h median {statistics.median(rates):.1f} (min {min(rates):.1f}, max {max(rates):.1f})")
