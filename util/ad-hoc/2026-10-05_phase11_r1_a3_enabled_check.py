# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/enabled_check.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-A3: recompute each fire's enabled time in the 30 s before it from analyze.py's episode construction
(log order, after-transitions), independently of the release trace's per-millisecond timeline."""
import importlib.util
import json
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad/lane11A3.psxzxh")
spec = importlib.util.spec_from_file_location("rt", S / "frozen/util/ad-hoc/2026-10-05_f058_census_v2_release_trace.py")
rt = importlib.util.module_from_spec(spec)
sys.modules["rt"] = rt
spec.loader.exec_module(rt)
EV = S / "frozen/reports/e2e-canopy-2026-09-02/f058-census-v2"
for p in (EV / "2026-10-05_census_live.json", EV / "run2/2026-10-05_census_live.json"):
    d = json.loads(p.read_text(encoding="utf-8"))
    raw = d["raw"]
    lane = sorted(raw["lane"], key=lambda x: x[0])  # analyze.py's construction
    eps, start = [], None
    for t, _b, after, _ty in lane:
        if after is True and start is None:
            start = t
        elif after is False and start is not None:
            eps.append((start, t))
            start = None
    res = rt.analyze(d)
    diffs = []
    for f in res["fires"]:
        t = f["t"]
        lo = t - 30000
        dis = sum(max(0, min(b, t) - max(a, lo)) for a, b in eps)
        en = 30000 - dis
        diffs.append((t, f["enabled_ms"], en))
    bad = [x for x in diffs if abs(x[1] - x[2]) > 2]
    print(p.parent.name, "fires", len(diffs), "enabled ms (trace, episodes) disagreements > 2 ms:", bad, "range", min(x[2] for x in diffs), max(x[2] for x in diffs))
