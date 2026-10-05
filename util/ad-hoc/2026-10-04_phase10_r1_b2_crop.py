# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/crop.py
# Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
import sys

from PIL import Image

src = sys.argv[1]
out = sys.argv[2]
box = tuple(int(v) for v in sys.argv[3].split(","))
scale = int(sys.argv[4]) if len(sys.argv) > 4 else 3
im = Image.open(src)
print("size", im.size)
c = im.crop(box)
c = c.resize((c.width * scale, c.height * scale), Image.NEAREST)
c.save(out)
print("saved", out, c.size)
