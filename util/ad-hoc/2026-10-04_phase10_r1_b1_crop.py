# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B1.8nGM/crop.py
# Written by Lane 10-B1 (adversarial, dispositions and ratings), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
import sys

from PIL import Image

src, out, box = sys.argv[1], sys.argv[2], tuple(int(v) for v in sys.argv[3].split(","))
img = Image.open(src)
print("size", img.size)
crop = img.crop(box)
crop = crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST)
crop.save(out)
print("saved", out, crop.size)
