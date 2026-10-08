#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6a/transcripts2.py
# Written by Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Read-only: for Lanes 11-R4A and 11-R4B, list every Python run whose interpreter flags lack -B, with the
timestamp of the tool call, the script's basename, whether the command sets PYTHONDONTWRITEBYTECODE, and the
tool result's timestamp. Prints no transcript text beyond script basenames.
"""
import json
import re
from pathlib import Path

SUB = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")


def records(agent):
    with open(SUB / f"agent-{agent}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


for agent, lane in [("a787c1b146b28dbbe", "11-R4A"), ("abf8c493b595bcdb2", "11-R4B")]:
    recs = list(records(agent))
    env_set = False
    results = {}
    for rec in recs:
        msg = rec.get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    results[c.get("tool_use_id")] = rec.get("timestamp")
    print(f"== Lane {lane} ({agent})")
    n_all = 0
    for rec in recs:
        msg = rec.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not (isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash"):
                continue
            cmd = (c.get("input") or {}).get("command", "")
            if "PYTHONDONTWRITEBYTECODE" in cmd and "export" in cmd:
                env_set = True
            for m in re.finditer(r"\bpython3?((?:\s+-[A-Za-z]+)*)\s+(\S+\.py)", cmd):
                n_all += 1
                if "B" in m.group(1):
                    continue
                print(f"  call={rec.get('timestamp')} result={results.get(c.get('id'))} script={Path(m.group(2)).name} "
                      f"envvar_in_cmd={'PYTHONDONTWRITEBYTECODE' in cmd} exported_before={env_set}")
    print(f"  python runs in all: {n_all}")
