# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/r4b_noB.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: in Lane 11-R4B's transcript, which python runs lacked -B? Prints timestamps, flags and .py basenames only."""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
T = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents/agent-abf8c493b595bcdb2.jsonl")
n_py = 0
with open(T, encoding="utf-8") as fh:
    for line in fh:
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue  # a partial line carries no tool call
        if o.get("type") != "assistant":
            continue
        for c in (o.get("message") or {}).get("content") or []:
            if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                continue
            cmd = (c.get("input") or {}).get("command") or ""
            for m in re.finditer(r"\bpython3?(\s+-\S+)*\s+(\S+\.py)", cmd):
                n_py += 1
                flags = m.group(0)
                has_b = " -B" in flags or "\t-B" in flags
                if not has_b:
                    print(o.get("timestamp"), "NO -B:", Path(m.group(2)).name)
print("python runs scanned:", n_py)
