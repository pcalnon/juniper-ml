# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: extracts dash-renderer source from its source map.
# Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/srcmap_extract.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Print the sourcesContent entries of a JS source map whose source path contains a needle."""

import json
import sys

path, needle = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as fh:
    m = json.load(fh)
srcs = m["sources"]
contents = m.get("sourcesContent") or []
hits = [i for i, s in enumerate(srcs) if needle in s]
print("HITS:", [srcs[i] for i in hits])
for i in hits:
    print("=====", srcs[i])
    print(contents[i] if i < len(contents) else "<no sourcesContent>")
