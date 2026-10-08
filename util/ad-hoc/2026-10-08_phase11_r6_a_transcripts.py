#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6a/transcripts.py
# Written by Lane 11-R6A (measurement re-creation, artifact-first, on round 5's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Read-only: (1) in Lane 11-R4B's transcript, find Bash commands running codeql_check.py and report only their
timestamps and whether -B was passed; (2) compare each round-5 lane's last assistant text with the archived report.

Prints timestamps, lengths and match flags only -- never transcript text.
"""
import json
import re
from pathlib import Path

SUB = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-dreamy-fluttering-kite/06e8868d-0c1f-4457-b7cb-b35e525032ef/subagents")
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")


def records(agent):
    with open(SUB / f"agent-{agent}.jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def tool_uses(rec):
    msg = rec.get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                yield c


def last_assistant_text(agent):
    last = None
    for rec in records(agent):
        if rec.get("type") != "assistant":
            continue
        msg = rec.get("message") or {}
        content = msg.get("content")
        texts = []
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        elif isinstance(content, str):
            texts = [content]
        t = "".join(texts)
        if t.strip():
            last = t
    return last


print("== Lane 11-R4B (abf8c493b595bcdb2): Bash commands naming codeql_check.py")
for rec in records("abf8c493b595bcdb2"):
    for tu in tool_uses(rec):
        if tu.get("name") != "Bash":
            continue
        cmd = (tu.get("input") or {}).get("command", "")
        if "codeql_check.py" in cmd and re.search(r"\bpython3?\b", cmd):
            runs = re.findall(r"python3?((?:\s+-\w+)*)\s+\S*codeql_check\.py", cmd)
            print(f"  ts={rec.get('timestamp')} runs={len(runs)} flags={[r.strip() for r in runs]}")

print("== Lane 11-R4B: every python run without -B (timestamp, script basename only)")
for rec in records("abf8c493b595bcdb2"):
    for tu in tool_uses(rec):
        if tu.get("name") != "Bash":
            continue
        cmd = (tu.get("input") or {}).get("command", "")
        for m in re.finditer(r"\bpython3?((?:\s+-[A-Za-z]+)*)\s+(\S+\.py)", cmd):
            if "B" not in m.group(1):
                print(f"  ts={rec.get('timestamp')} script={Path(m.group(2)).name}")

report = (W / "reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md").read_text(encoding="utf-8")
for agent, lane in [("abbb8479da1ec5a2f", "Lane 11-R5A"), ("ae4dfd4f5bbf0e3d0", "Lane 11-R5B")]:
    t = last_assistant_text(agent)
    print(f"== {lane} ({agent}): last assistant text {len(t)} chars; verbatim in report file: {t.strip() in report}")
