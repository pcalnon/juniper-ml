# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/crop.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Crop the Classification Metrics chart and the loss chart of dashboard_final.png at full resolution."""
import sys

from PIL import Image

SRC = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-juggling-spring/reports/2026-09-23_canopy-a-n2-generate-stage-train-render/01_spirals_control/dashboard_final.png"
OUT = sys.argv[1]
im = Image.open(SRC)
print(im.size)
s = 1600 / 995
# Classification Metrics block: displayed approx x 275..960, y 690..875
box = (int(275 * s), int(690 * s), int(960 * s), int(875 * s))
im.crop(box).save(f"{OUT}/acc_chart.png")
# left edge zoom: x 330..420 displayed, y 700..860
box2 = (int(330 * s), int(700 * s), int(420 * s), int(860 * s))
im.crop(box2).resize((int((box2[2] - box2[0]) * 4), int((box2[3] - box2[1]) * 4)), Image.NEAREST).save(f"{OUT}/acc_left_zoom.png")
# loss chart left edge
box3 = (int(330 * s), int(505 * s), int(420 * s), int(670 * s))
im.crop(box3).resize((int((box3[2] - box3[0]) * 4), int((box3[3] - box3[1]) * 4)), Image.NEAREST).save(f"{OUT}/loss_left_zoom.png")
print("ok")
