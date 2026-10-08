# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-05: a probe from round 1 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, tools/dump.py
# Written by Lane 11-A3 (measurement re-creation, instrument-adequacy-first), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-05_validator_reports_phase11_round1.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/file-not-always-closed: it closes the files it opens),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Read-only overview of a census v2 transcript's raw logs."""
import collections
import json
import sys

with open(sys.argv[1]) as fh:
    d = json.load(fh)
raw = d["raw"]
kinds = collections.Counter(k for _t, k, _i, _p in raw["req"])
print("req record kinds", dict(kinds))
print("gate writes", raw["gate"])
print("fires", raw["fires"])
types = collections.Counter((b, a, ty) for _t, b, a, ty in raw["lane"])
for k, v in sorted(types.items(), key=lambda x: -x[1]):
    print("  lane rec", k, v)
print("lane records", len(raw["lane"]), "t0", raw["t0"])
print("max req t", max(t for t, *_ in raw["req"]), "max lane t", max(t for t, *_ in raw["lane"]))
print("triggers", json.dumps([{k: v for k, v in t.items() if k != "stats"} for t in d["triggers"]]))
print("baseline window", d["baseline_window_ms"], "idle window", d["idle_window_ms"])
# R records: which ids, when
rs = [(t, i) for t, k, i, _p in raw["req"] if k == "R"]
print("R records", rs[:20])
