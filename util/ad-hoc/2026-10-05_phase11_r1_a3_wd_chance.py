# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/wd_chance.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-A3: is the replay's jittered control a fair chance baseline? Compare it with two other chance models
on the MEASURED lanes: (1) fixed 5,000 ms spacing for the predicate's clock but each sample's lane state read at an
independent random phase (spacing kept, phase randomized), (2) the same number of samples at uniform random times."""
import bisect
import importlib.util
import json
import random
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
spec = importlib.util.spec_from_file_location("wd", S / "frozen/util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py")
wd = importlib.util.module_from_spec(spec)
sys.modules["wd"] = wd
spec.loader.exec_module(wd)
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
RUNS = {"run1": EV / "2026-10-05_census_live.json", "run2": EV / "run2/2026-10-05_census_live.json"}


def replay_decoupled(timeline, clamps, clock_times, state_times, strand_ms):
    times = [t for t, _ in timeline]

    def disabled_at(t):
        i = bisect.bisect_right(times, t) - 1
        return timeline[i][1] if i >= 0 else False

    def clamped(t):
        return any(a <= t < b for a, b in clamps)

    since, n = None, 0
    for t, ts in zip(clock_times, state_times):
        if not disabled_at(ts) or clamped(ts):
            since = None
        elif since is None:
            since = t
        elif t - since >= strand_ms:
            since = None
            n += 1
    return n


for name, p in RUNS.items():
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    tl = wd.lane_timeline(raw["lane"])
    cl = wd.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    m1, m2, n_al, n_ji = [], [], [], []
    for phi in range(0, 5000, 100):
        for seed in range(10):
            rng = random.Random(seed * 100003 + phi)
            grid = wd.sample_times(0, t_hi, 5000, phi)
            n_al.append(len(grid))
            st = [min(max(t + rng.uniform(-2500, 2500), 0), t_hi - 1) for t in grid]
            m1.append(replay_decoupled(tl, cl, grid, st, 30000))
            rnd = sorted(rng.uniform(0, t_hi) for _ in grid)
            m2.append(len(wd.replay(tl, cl, rnd, 30000)))
            rng2 = random.Random(seed * 100003 + phi)
            n_ji.append(len(wd.sample_times(0, t_hi, 5000, phi, 2500, rng2)))
    print(f"{name}: samples per replay aligned {min(n_al)}-{max(n_al)}, jittered {min(n_ji)}-{max(n_ji)}")
    print(f"  spacing kept, phase randomized: {wd.summary(m1)}")
    print(f"  uniform random times, same count: {wd.summary(m2)}")
    # tail of the chance models at the observed count
    obs = len(raw["fires"])
    print(f"  P(>= observed {obs}) spacing-kept model: {sum(1 for x in m1 if x >= obs) / len(m1):.3f}; uniform model: {sum(1 for x in m2 if x >= obs) / len(m2):.3f}")
