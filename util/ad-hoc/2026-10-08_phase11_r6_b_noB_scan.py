# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/noB_scan.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: for a given lane transcript, list python runs and whether each carries -B or a no-bytecode env.

Prints timestamps, flags and .py basenames only, never the command text.
"""

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
D = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")
agent = sys.argv[1]
pattern = sys.argv[2] if len(sys.argv) > 2 else ""
results = {}
with open(D / f"agent-{agent}.jsonl", encoding="utf-8") as fh:
    for line in fh:
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue  # a partial line carries no tool call
        if o.get("type") == "user":
            for c in (o.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    results[c.get("tool_use_id")] = o.get("timestamp")
            continue
        if o.get("type") != "assistant":
            continue
        for c in (o.get("message") or {}).get("content") or []:
            if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                continue
            cmd = (c.get("input") or {}).get("command") or ""
            env_nob = "PYTHONDONTWRITEBYTECODE" in cmd
            for m in re.finditer(r"\bpython3?((?:\s+-\S+)*)\s+(\S+\.py)", cmd):
                if pattern and pattern not in m.group(2):
                    continue
                has_b = "-B" in m.group(1).split()
                print(o.get("timestamp"), c.get("id")[-6:], "-B" if has_b else "NO-B", "env-nob" if env_nob else "", Path(m.group(2)).name)
# result timestamps for the listed tool ids
if pattern:
    with open(D / f"agent-{agent}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue  # a partial line carries no tool call
            if o.get("type") != "assistant":
                continue
            for c in (o.get("message") or {}).get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use" and pattern in ((c.get("input") or {}).get("command") or ""):
                    print("  result for", c.get("id")[-6:], "at", results.get(c.get("id")))
