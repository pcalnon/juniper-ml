# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/wd_more.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-A3: where the observed fire counts sit in the replay's distributions; the real sampler's phase."""
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

for name, p in RUNS.items():
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    tl = wd.lane_timeline(raw["lane"])
    cl = wd.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    obs = len(raw["fires"])
    times = [t for t, _ in tl]

    def dis(t):
        i = bisect.bisect_right(times, t) - 1
        return tl[i][1] if i >= 0 else False

    for period in (4900, 5000, 5100):
        al = [len(wd.replay(tl, cl, wd.sample_times(0, t_hi, period, phi), 30000)) for phi in range(0, period, 10)]
        ge = sum(1 for c in al if c >= obs) / len(al)
        print(f"{name} P={period}: aligned share of phases with >= {obs} fires (observed): {ge:.3f}")
    # small jitter: the real samples ride the renderer queue; +/-250 and +/-500 ms
    for j in (100, 250, 500, 1000):
        cnt = []
        for phi in range(0, 5000, 100):
            for seed in range(10):
                rng = random.Random(seed * 7919 + phi)
                cnt.append(len(wd.replay(tl, cl, wd.sample_times(0, t_hi, 5000, phi, j, rng), 30000)))
        print(f"{name} P=5000 jitter +/-{j} ms: {wd.summary(cnt)}")
    # The 6 samples a fire implies at exactly 5,000 ms steps: is any of them on an enabled lane, and how far is the nearest disabled time?
    print(f"{name}: per fire, the implied samples at f - k*5000 (k=1..6) found enabled by the measured lane")
    for f, *_ in raw["fires"]:
        badk = [k for k in range(1, 7) if not dis(f - k * 5000)]
        if badk:
            # how far would the sample have to move to see a disabled lane?
            moves = []
            for k in badk:
                x = f - k * 5000
                m = next((dt for dt in range(1, 3000) if dis(x - dt) or dis(x + dt)), None)
                moves.append((k, m))
            print(f"   fire @{f}: enabled at k={badk}; nearest disabled within (k, ms) {moves}")
