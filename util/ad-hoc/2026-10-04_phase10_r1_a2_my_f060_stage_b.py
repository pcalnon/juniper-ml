# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/my_f060_stage_b.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 10-A2 independent F-CANOPY-060 reproduction, stage B (canopy env).

Feeds what canopy receives (stage A's strings, sliced as the browser's reportFailure slices them:
detail[:300], detail_full[:4000]) to canopy's REAL DashboardManager._open_dataset_shortfall_prompt_handler
(1b2dd438) and reads the text of the modal body it returns.

Usage: python my_f060_stage_b.py <canopy src> <stage_a.json>
"""
import json
import logging
import sys

CANOPY_SRC, IN = sys.argv[1], sys.argv[2]
sys.path.insert(0, CANOPY_SRC)
from frontend.dashboard_manager import DashboardManager  # noqa: E402


def text_of(node):
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, (list, tuple)):
        return "".join(text_of(n) for n in node)
    return text_of(getattr(node, "children", None))


dm = object.__new__(DashboardManager)
dm.logger = logging.getLogger("lane10a2")
data = json.load(open(IN))
for name, case in data.items():
    closing = case["data_detail"].rsplit(". ", 1)[-1]
    first = case["data_detail"].split(". ", 1)[0]
    for stance, received in case["canopy_receives"].items():
        action = {"last": "start-button", "ts": 0.0, "success": False, "command": "start", "detail": received[:300], "detail_full": received[:4000]}
        is_open, body, ctx = dm._open_dataset_shortfall_prompt_handler(action)
        body_text = " | ".join(text_of(b) for b in body) if isinstance(body, list) else str(body)
        shown = text_of(body[1]) if isinstance(body, list) and len(body) > 1 else ""
        print(f"{name:26} {stance:24} prompt_open={is_open!s:5} len(received)={len(received):4} first-sentence shown={first in body_text!s:5} data closing shown={closing in body_text!s:5} cascor remedy in producer para={'To accept it,' in shown!s:5}")
    if name == "cap_equities_503_over_14":
        print("   producer paragraph shown (flag_off_silent_caller):", repr(shown) if stance else "")
        print("   options:", [text_of(li)[:60] for li in body[-1].children])
