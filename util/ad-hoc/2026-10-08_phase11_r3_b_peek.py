# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/peek.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Peek at the transcript structure (keys, counts, sample records)."""
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    d = json.load(fh)
print("top keys:", list(d.keys()))
raw = d["raw"]
print("raw keys:", list(raw.keys()))
for k, v in raw.items():
    if isinstance(v, list):
        print(k, len(v), v[:3])
    else:
        print(k, type(v).__name__, str(v)[:300])
for k, v in d.items():
    if k == "raw":
        continue
    print("==", k, str(v)[:1500])
