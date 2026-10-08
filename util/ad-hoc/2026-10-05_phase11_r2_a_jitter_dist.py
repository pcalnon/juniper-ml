# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/jitter_dist.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Distribution of the repo's jittered control (its own seeds, and other seed sets) at 5,000 ms."""
import collections
import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ar", S / "tree_b3/util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py")
ar = importlib.util.module_from_spec(spec)
sys.modules["ar"] = ar
spec.loader.exec_module(ar)

for p in sys.argv[1:]:
    d = json.loads(Path(p).read_text())
    raw = d["raw"]
    tl = ar.lane_timeline(raw["lane"])
    cl = ar.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    P = 5000
    for label, seedfn in (("repo seeds", lambda seed, phi: seed * 100003 + phi), ("alt seeds A", lambda seed, phi: 7 + seed * 7919 + phi * 13), ("alt seeds B", lambda seed, phi: 99991 * (seed + 1) + phi)):
        jit = []
        for phi in range(0, P, 100):
            for seed in range(10):
                rng = random.Random(seedfn(seed, phi))
                jit.append(len(ar.replay(tl, cl, ar.sample_times(0, t_hi, P, phi, P / 2, rng), 30000)))
        c = collections.Counter(jit)
        le1 = sum(v for k, v in c.items() if k <= 1) / len(jit)
        print(f"{p.split('/')[-2]} {label}: n={len(jit)} median {statistics.median(jit)} zero {c[0]} share<=1 {le1:.3f} dist {sorted(c.items())}")
