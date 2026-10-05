# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/inspect_hist.py
# Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, modified 2026-10-05 only to close the files it opens
# (CodeQL py/file-not-always-closed on juniper-ml#2157); what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py.
# ---------------------------------------------------------------------------
import json
import sys

path = sys.argv[1]
with open(path) as fh:
    d = json.load(fh)
r = d["response"]
print({k: (type(v).__name__, (len(v) if hasattr(v, "__len__") else v)) for k, v in r.items()})
for k, v in r.items():
    if isinstance(v, list):
        rows = v
        print("list key", k, len(rows))
        for i, row in enumerate(rows):
            if isinstance(row, dict):
                m = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
                print(i, "epoch=", row.get("epoch"), "phase=", row.get("phase"), "has_kind=", "kind" in row, "acc=", m.get("accuracy"), "loss=", m.get("loss"), "hu=", row.get("network_topology"), "keys=", sorted(row.keys()))
            else:
                print(i, row)
    elif not isinstance(v, (dict, list)):
        print(k, v)
    else:
        print(k, json.dumps(v)[:600])
