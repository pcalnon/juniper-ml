#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-05
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Replay canopy's metrics-store strand watchdog over a MEASURED lane timeline, at every sampling phase.

The F-CANOPY-058 census v2 (``2026-10-04_f058_census_v2_live.py``) logged the watchdog's fires on canopy
``main``, each with the lane enabled for 10-15 s of the 30 s before it (``2026-10-05_f058_census_v2_release_trace.py``).
The shim logged the fires only, never the watchdog's non-firing samples, so WHY its samples kept landing on a
disabled lane is not in the transcript. The candidate is aliasing: the watchdog samples ``disabled`` on the 5 s
slow lane and resets only on a sample that sees it enabled, while the feeder's self-clocked cycle is close to
5 s, so successive samples drift slowly across the cycle and can sit in its disabled part for many samples in a
row.

This tests that candidate without the browser. It takes the lane's measured timeline (the ``after`` of each
change's innermost record, as the release trace reads it; it refuses a transcript whose innermost records do not
alternate) and runs canopy's watchdog function, verbatim
in logic (``dashboard_manager.py:2527-2546`` at ``60ae1870``), on samples every ``P`` ms starting at phase
``phi``, for every ``phi`` in ``[0, P)`` at ``--step`` ms, and for several periods ``P``:

    if (!disabled || applyInFlight) { since = null; return }
    if (!since) { since = now; return }
    if (now - since < 30000) return
    since = null; FIRE

``applyInFlight`` is true inside the T-apply clamp window recorded in the transcript's gate writes (the gate
writes ``true`` at the clamp and ``false`` at its release).

Two controls, both printed:

  * JITTERED: the same mean period, but each sample moved by a uniform offset in ``[-P/2, P/2]`` (seeded), which
    keeps the sampling RATE and destroys its PHASE: the fires such a sampler sees are the ones a lane disabled
    this much of the time produces by chance. Aligned fires well above the jittered ones mean the samples' phase
    coherence with the cycle, i.e. aliasing, is what produces them.
  * Other periods, 6,000 and 7,500 ms, further from the cycle.

What it cannot do: a replayed fire does not re-enable the replayed lane (the measured timeline already holds
the real fires' effects), and the real samples ride the renderer's queue, so their period is not exactly
5,000 ms. A replay whose aligned fire count is near the observed one, and well above the jittered count, makes
aliasing sufficient; it does not exclude a lock between the watchdog's samples and the feeder's cycle through
the renderer's queue. How it could have come out otherwise: if the predicate on this timeline could not reach
30 s of disabled-only samples, every phase would replay 0 fires; if phase did not matter, the aligned and
jittered counts would agree.

Usage:
    python3 <this file> <transcript.json> [--periods 4900,5000,5100,6000,7500] [--step 10] [--seeds 10]
"""

import argparse
import bisect
import json
import random
import statistics
import sys
from pathlib import Path


def lane_timeline(lane_log):
    """``[(t, disabled)]`` from the innermost record of each nested chain: a thunk (types ``''``) or ``SET_LAYOUT``.

    An enclosing dispatch logs a nested change again at its own, earlier entry time, so reading the enclosing
    records backdates every nested change (``2026-10-05_f058_census_v2_release_trace.py``'s ``lane_timeline``
    explains; round 1 of Phase 11's review, Lane 11-A2; the first version of this file read them).
    """
    inner = sorted(((t, i, after) for i, (t, _before, after, types) in enumerate(lane_log) if types in ("", "SET_LAYOUT")), key=lambda x: (x[0], x[1]))
    by_t = {}
    for t, _i, after in inner:
        by_t[t] = after
    return sorted(by_t.items())


def clamp_windows(gate_log):
    """Intervals during which the apply clamp held (gate wrote ``true``, until it wrote ``false``)."""
    out, start = [], None
    for t, _before, v in sorted(gate_log, key=lambda g: g[0]):
        if v is True and start is None:
            start = t
        elif v is False and start is not None:
            out.append((start, t))
            start = None
    return out


def sample_times(t_lo, t_hi, period, phase, jitter=0, rng=None):
    """Sample instants every ``period`` from ``t_lo + phase``, each moved by up to ``jitter`` either way."""
    out, t = [], t_lo + phase
    while t < t_hi:
        out.append(t + (rng.uniform(-jitter, jitter) if jitter else 0))
        t += period
    return sorted(x for x in out if t_lo <= x < t_hi)


def replay(timeline, clamps, samples, strand_ms):
    """Canopy's watchdog predicate, run at each instant in ``samples``; returns the fire instants."""
    times = [t for t, _ in timeline]

    def disabled_at(t):
        i = bisect.bisect_right(times, t) - 1
        return timeline[i][1] if i >= 0 else False

    def clamped(t):
        return any(a <= t < b for a, b in clamps)

    since, fires = None, []
    for t in samples:
        if not disabled_at(t) or clamped(t):
            since = None
        elif since is None:
            since = t
        elif t - since >= strand_ms:
            since = None
            fires.append(t)
    return fires


def summary(counts):
    return f"min {min(counts)}, median {statistics.median(counts)}, max {max(counts)}; zero in {sum(1 for c in counts if c == 0)} of {len(counts)}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--periods", default="4900,5000,5100,6000,7500", help="sampling periods, ms; 6000 and 7500 are controls")
    ap.add_argument("--step", type=int, default=10, help="phase step, ms, for the aligned replay")
    ap.add_argument("--seeds", type=int, default=10, help="jittered replays per phase (phases at 10 x --step)")
    ap.add_argument("--strand-ms", type=int, default=30000)
    args = ap.parse_args()
    d = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    raw = d["raw"]
    inner = sorted(((t, i, before, after) for i, (t, before, after, types) in enumerate(raw["lane"]) if types in ("", "SET_LAYOUT")), key=lambda x: (x[0], x[1]))
    breaks = sum(1 for a, b in zip(inner, inner[1:]) if b[2] != a[3])
    if breaks:
        # A lane change logged only by a non-thunk record would be missing from the timeline (round 2 of Phase 11's
        # review, Lane 11-R2B), and every replayed fire would rest on a timeline with holes in it. A disable and the
        # enable after it, both logged only so, leave no break and are not caught here (round 3, Lane 11-R3B).
        print(f"!! {breaks} alternation breaks in the innermost lane records: the timeline is incomplete; refusing", file=sys.stderr)
        return 2
    timeline = lane_timeline(raw["lane"])
    clamps = clamp_windows(raw["gate"])
    t_lo = 0
    t_hi = max(t for t, *_ in raw["req"])
    observed = [t for t, *_ in raw["fires"]]
    print(f"served {d.get('served_sha')}; lane records {len(raw['lane'])}; span {t_lo}-{t_hi} ms; clamp windows {clamps}")
    print(f"observed fires: {len(observed)} ({len(observed) / ((t_hi - t_lo) / 3.6e6):.1f} an hour)")
    for period in [int(x) for x in args.periods.split(",")]:
        aligned = [len(replay(timeline, clamps, sample_times(t_lo, t_hi, period, phi), args.strand_ms)) for phi in range(0, period, args.step)]
        jittered = []
        for phi in range(0, period, args.step * 10):
            for seed in range(args.seeds):
                rng = random.Random(seed * 100003 + phi)
                jittered.append(len(replay(timeline, clamps, sample_times(t_lo, t_hi, period, phi, period / 2, rng), args.strand_ms)))
        print(f"period {period} ms: aligned over {len(aligned)} phases {summary(aligned)} | jittered (+/-{period // 2} ms) over {len(jittered)} replays {summary(jittered)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
