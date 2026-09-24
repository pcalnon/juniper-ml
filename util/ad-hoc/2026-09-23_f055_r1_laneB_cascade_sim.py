# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: the eviction-cascade model (median time to the next applied response after a trigger).
# Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/cascade_sim.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Event simulation of the guarded lane after ONE mid-flight re-enable (gate write / watchdog fire).

Semantics, each from the frozen dash 4.2.0 renderer / dcc source:
  * running= sets disabled=true synchronously at dispatch (dash_renderer.dev.js:818-821);
  * a new request of the same callback evicts the `watched` one (:3027), whose result is then
    dropped (:2697-2704);
  * completeJob -> runningOff (disabled=false) runs for EVERY response, evicted or not
    (:925-937, :970, :979, :983; no `watched` check);
  * re-enabling a dcc.Interval starts a fresh setInterval: first tick one period later
    (Interval.react.js handleTimer); disabling clears it.
No further perturbations are injected, so this is a LOWER bound on the outage.

usage: python cascade_sim.py
"""

import random
import statistics


def outage_after_one_perturbation(r_lo, r_hi, rng, cap=3600.0):
    """Seconds from the perturbation to the next APPLIED response."""
    period = 1.0
    t = 0.0
    # one request in flight, dispatched at 0; perturb uniformly inside its flight
    r0 = rng.uniform(r_lo, r_hi)
    fetches = [{"start": 0.0, "end": r0, "evicted": False}]
    watched = 0
    p = rng.uniform(0.0, r0)
    enabled = True  # the perturbation re-enables
    tick_at = p + period
    t = p
    while t - p < cap:
        # next event: a tick (if enabled) or a completion
        pending = [(f["end"], i) for i, f in enumerate(fetches) if f["end"] > t]
        next_end, idx = min(pending) if pending else (float("inf"), None)
        if enabled and tick_at <= next_end:
            t = tick_at
            if watched is not None and fetches[watched]["end"] > t:
                fetches[watched]["evicted"] = True
            r = rng.uniform(r_lo, r_hi) + rng.uniform(0.0, 0.05)
            fetches.append({"start": t, "end": t + r, "evicted": False})
            watched = len(fetches) - 1
            enabled = False
            continue
        if idx is None:
            break
        t = next_end
        f = fetches[idx]
        if not f["evicted"] and idx == watched:
            return t - p
        if idx == watched:
            watched = None
        if not enabled:
            enabled = True
            tick_at = t + period
    return cap


rng = random.Random(55)
print("r (dispatch->completeJob)   n=2000 perturbations   outage until next applied response (s)")
print("  r_lo-r_hi     median     p75      p90     share > 60 s   share > 300 s")
for lo, hi in ((1.0, 2.0), (1.5, 3.1), (3.0, 5.0), (6.9, 7.6), (7.0, 8.0)):
    xs = [outage_after_one_perturbation(lo, hi, rng) for _ in range(2000)]
    xs.sort()
    q = lambda f: xs[int(f * (len(xs) - 1))]  # noqa: E731
    gt60 = sum(1 for x in xs if x > 60) / len(xs)
    gt300 = sum(1 for x in xs if x > 300) / len(xs)
    print(f"  {lo:.1f}-{hi:.1f}     {statistics.median(xs):7.1f}  {q(0.75):7.1f}  {q(0.90):7.1f}      {gt60:6.1%}        {gt300:6.1%}")
