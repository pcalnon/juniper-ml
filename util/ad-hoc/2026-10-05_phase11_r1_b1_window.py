# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B1.oCpUdY/window.py
# Written by Lane 11-B1 (adversarial, dispositions and ratings, fold side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Print raw lane, req, gate and fire records in a time window of a census v2 transcript."""
import json
import sys
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
lo, hi = int(sys.argv[2]), int(sys.argv[3])
raw = d["raw"]
ev = []
for t, b, a, ty in raw["lane"]:
    if lo <= t <= hi:
        ev.append((t, "lane", f"{b}->{a} types={ty!r}"))
for t, k, rid, props in raw["req"]:
    if lo <= t <= hi:
        ev.append((t, "req", f"{k} id={rid} props={str(props)[:30]}"))
for t, b, v in raw["gate"]:
    if lo <= t <= hi:
        ev.append((t, "gate", f"{b}->{v}"))
for t, b, s in raw["fires"]:
    if lo <= t <= hi:
        ev.append((t, "fire", f"before={b} since={s}"))
for row in sorted(ev, key=lambda x: x[0]):
    print(*row)
