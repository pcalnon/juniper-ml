# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/cmd_head.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: print the first 160 characters of given tool calls' commands, with anything e-mail-shaped masked."""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
D = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
agent, suffixes = sys.argv[1], set(sys.argv[2:])
with open(D / f"agent-{agent}.jsonl", encoding="utf-8") as fh:
    for line in fh:
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue  # a partial line carries no tool call
        if o.get("type") != "assistant":
            continue
        for c in (o.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("id", "")[-6:] in suffixes:
                cmd = EMAIL.sub("<masked>", (c.get("input") or {}).get("command") or "")
                print(c.get("id")[-6:], repr(cmd[:160]))
