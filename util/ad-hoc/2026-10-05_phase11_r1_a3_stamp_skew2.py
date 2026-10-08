# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/stamp_skew2.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: the release trace and the alias replay re-run on a change-time (thunk-only) lane timeline."""
import importlib.util
import json
import random
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, S / "frozen/util/ad-hoc" / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


rt = load("rt", "2026-10-05_f058_census_v2_release_trace.py")
wd = load("wd", "2026-10-05_f058_watchdog_alias_replay.py")
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
allf = {"inst": [], "thunk": []}
for p in (EV / "2026-10-05_census_live.json", EV / "run2/2026-10-05_census_live.json"):
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    m = json.loads(json.dumps(d))
    m["raw"]["lane"] = [r for r in raw["lane"] if r[3] in ("", "SET_LAYOUT")]
    a = rt.analyze(d)
    b = rt.analyze(m)
    for k, res in (("inst", a), ("thunk", b)):
        allf[k] += [(f["episode_ms"], f["enabled_ms"]) for f in res["fires"]]
    print(f"{p.parent.name}: trace on change-time timeline: own {len(b['own'])} late {len(b['late'])} unassigned {len(b['unassigned'])}; false fires {sum(1 for f in b['fires'] if f['enabled_ms'] > 0)}/{len(b['fires'])}")
    print(f"   fire episode age ms inst {[f['episode_ms'] for f in a['fires']]}")
    print(f"   fire episode age ms thunk {[f['episode_ms'] for f in b['fires']]}")
    tl = rt.lane_timeline(m["raw"]["lane"])
    cl = wd.clamp_windows(raw["gate"])
    t_hi = max(t for t, *_ in raw["req"])
    for period in (5000, 6000, 7500):
        al = [len(wd.replay(tl, cl, wd.sample_times(0, t_hi, period, phi), 30000)) for phi in range(0, period, 10)]
        ji = []
        for phi in range(0, period, 100):
            for seed in range(10):
                rng = random.Random(seed * 100003 + phi)
                ji.append(len(wd.replay(tl, cl, wd.sample_times(0, t_hi, period, phi, period / 2, rng), 30000)))
        print(f"   change-time replay P={period}: aligned {wd.summary(al)} | jittered {wd.summary(ji)}")
for k, v in allf.items():
    print(k, "fires' episode age range", min(x[0] for x in v), max(x[0] for x in v), "enabled range", min(x[1] for x in v), max(x[1] for x in v))
