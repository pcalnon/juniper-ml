# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11B1.oCpUdY/misc.py
# Written by Lane 11-B1 (adversarial, dispositions and ratings, fold side), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Misc re-derivations: in-flight minimum, disabled-episode medians, and every mid-request re-enable with its outcome."""
import json
import sys
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raw = d["raw"]
req = {}
for t, kind, rid, props in raw["req"]:
    r = req.setdefault(rid, {"id": rid, "tW": None, "tEnd": None, "end": None})
    if kind == "W" and r["tW"] is None:
        r["tW"] = t
    elif kind in ("A", "X") and r["end"] is None:
        r["end"], r["tEnd"] = kind, t
reqs = sorted((r for r in req.values() if r["tW"] is not None), key=lambda r: r["tW"])
done = [r for r in reqs if r["end"]]
dur = sorted(r["tEnd"] - r["tW"] for r in done)
print("in-flight ms: min", dur[:3], "under 1000:", sum(1 for x in dur if x < 1000))


def in_flight(t):
    live = [r for r in reqs if r["tW"] <= t and (r["tEnd"] is None or r["tEnd"] > t)]
    return live[-1] if live else None


# every re-enable (fire, or gate write False with lane True before) while a request is in flight
events = [(t, "fire") for t, b, _s in raw["fires"] if b is True] + [(t, "gate") for t, b, v in raw["gate"] if b is True and v is False]
rows = []
for t, k in sorted(events):
    cur = in_flight(t)
    if cur is None:
        rows.append((t, k, None, None, None))
        continue
    rows.append((t, k, cur["id"], cur["end"], cur["tEnd"] - t))
mid = [x for x in rows if x[2] is not None]
print("re-enables with a request in flight:", len(mid), "evicting:", sum(1 for x in mid if x[3] == "X"))
gt1 = [x for x in mid if x[3] == "A" and x[4] > 1000]
print("non-evicting, in-flight answer landed > 1000 ms after the re-enable:", len(gt1), [(x[1], x[4]) for x in gt1])
print("non-evicting gate re-enables:", [(x[0], x[4]) for x in mid if x[1] == "gate" and x[3] == "A"])
print("evicting re-enables:", [(x[0], x[1], x[4]) for x in mid if x[3] == "X"])
