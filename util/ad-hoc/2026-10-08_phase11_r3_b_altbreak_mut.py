# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 3 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r3b/altbreak_mut.py
# Written by Lane 11-R3B (adversarial, on round 2's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round3.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Mutation check of the round-2 alternation-break guard (release trace + alias replay at 7af6a381).

M1: one innermost change re-typed as a non-thunk record (logged only by a non-thunk record) -> expect a break.
M2: a consecutive PAIR of innermost changes (T->F then F->T, i.e. one whole enabled stretch) re-typed -> does the
    guard see it? And what do the fire rows read then?
Writes mutated transcripts into this scratch dir only."""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])
d = json.loads(src.read_text(encoding="utf-8"))
lane = d["raw"]["lane"]
inner_idx = sorted((i for i, r in enumerate(lane) if r[3] in ("", "SET_LAYOUT")), key=lambda i: (lane[i][0], i))
fire_t = 81743
# innermost changes before the fire
before = [i for i in inner_idx if lane[i][0] < fire_t]
last = before[-1]  # F->T that opened the current disabled episode
prev = before[-2]  # T->F that opened the enabled stretch before it
print("pair to retype:", lane[prev], lane[last])

m1 = json.loads(json.dumps(d))
m1["raw"]["lane"][last][3] = "ON_PROP_CHANGE"
(out / "m1.json").write_text(json.dumps(m1), encoding="utf-8")

m2 = json.loads(json.dumps(d))
m2["raw"]["lane"][prev][3] = "ON_PROP_CHANGE"
m2["raw"]["lane"][last][3] = "ON_PROP_CHANGE"
(out / "m2.json").write_text(json.dumps(m2), encoding="utf-8")
print("written m1.json m2.json")
