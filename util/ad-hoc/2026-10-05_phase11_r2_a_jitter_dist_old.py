# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 2 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R2A.sffLXI/jitter_dist_old.py
# Written by Lane 11-R2A (measurement re-creation, on round 1's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round2.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Same as jitter_dist.py, over the 1b7cf44b (enclosing-record) timeline, to see whether 2 -> 1 is a shift or seed noise."""
import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path

S = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


old = load("ar_old", S / "tree_b1/util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py")
new = load("ar_new", S / "tree_b3/util/ad-hoc/2026-10-05_f058_watchdog_alias_replay.py")
SEEDS = {
    "repo": lambda seed, phi: seed * 100003 + phi,
    "altA": lambda seed, phi: 7 + seed * 7919 + phi * 13,
    "altB": lambda seed, phi: 99991 * (seed + 1) + phi,
    "altC": lambda seed, phi: 31337 + seed * 1000003 + phi * 7,
    "altD": lambda seed, phi: 4242 * (seed + 3) + phi * 101,
}
for p in sys.argv[1:]:
    d = json.loads(Path(p).read_text())
    raw = d["raw"]
    t_hi = max(t for t, *_ in raw["req"])
    for tag, mod in (("old", old), ("new", new)):
        tl = mod.lane_timeline(raw["lane"])
        cl = mod.clamp_windows(raw["gate"])
        row = []
        allj = []
        for label, fn in SEEDS.items():
            jit = []
            for phi in range(0, 5000, 100):
                for seed in range(10):
                    rng = random.Random(fn(seed, phi))
                    jit.append(len(mod.replay(tl, cl, mod.sample_times(0, t_hi, 5000, phi, 2500, rng), 30000)))
            allj += jit
            row.append(f"{label}: med {statistics.median(jit)} zero {sum(1 for j in jit if j == 0)}")
        print(f"{p.split('/')[-2]} {tag}: " + "; ".join(row) + f" | pooled n={len(allj)} median {statistics.median(allj)} share<=1 {sum(1 for j in allj if j <= 1) / len(allj):.3f} zero share {sum(1 for j in allj if j == 0) / len(allj):.3f}")
