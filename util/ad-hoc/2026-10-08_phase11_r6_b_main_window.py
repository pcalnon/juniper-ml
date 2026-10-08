# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/main_window.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: did the orchestrator's main transcript run any Python between two UTC times? Timestamps and basenames only."""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
P = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef.jsonl")
lo, hi = sys.argv[1], sys.argv[2]
n = 0
with open(P, encoding="utf-8") as fh:
    for line in fh:
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue  # a partial line carries no tool call
        ts = o.get("timestamp") or ""
        if not (lo <= ts <= hi) or o.get("type") != "assistant":
            continue
        for c in (o.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                n += 1
                cmd = (c.get("input") or {}).get("command") or ""
                pys = [Path(m.group(2)).name for m in re.finditer(r"\bpython3?((?:\s+-\S+)*)\s+(\S+\.py)", cmd)]
                print(ts, c.get("name"), pys)
print("tool calls in window:", n)
