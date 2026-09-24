# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-F: every background launch and its completion.
# Source: session ddf7847c's tmpfs scratchpad, r2f.xB7Gf1/forkC/bg_all.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Across all transcripts: background launches (Bash run_in_background / Monitor / nohup / setsid) in a time range
whose command could ready, arm, merge or update-branch a PR. Prints session id, timestamp, command (truncated)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
lo, hi = sys.argv[1], sys.argv[2]
PAT = re.compile(r"(gh\s+pr\s+ready|gh\s+pr\s+merge|--auto\b|enablePullRequestAutoMerge|markPullRequestReadyForReview|safe_merge|shepherd|update-branch|/merge\b|watch_pr_states|wait_for_checks)", re.I)
allbg = 0
for p in sorted(ROOT.rglob("*.jsonl")):
    try:
        fh = p.open(encoding="utf-8", errors="replace")
    except Exception:
        continue
    with fh:
        for raw in fh:
            if "tool_use" not in raw:
                continue
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if not isinstance(rec, dict):
                continue
            t = rec.get("timestamp") or ""
            if not (lo <= t <= hi):
                continue
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            c = msg.get("content")
            if msg.get("role") != "assistant" or not isinstance(c, list):
                continue
            for b in c:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                name = b.get("name")
                cmd = str(inp.get("command") or "")
                is_bg = bool(inp.get("run_in_background")) or name == "Monitor" or re.search(r"\b(nohup|setsid|disown)\b", cmd) is not None
                if not is_bg:
                    continue
                allbg += 1
                if PAT.search(cmd):
                    print(p.parent.name[-38:], p.stem[:8], t, name, "|", cmd[:260].replace("\n", " ;; "))
print("background launches in range:", allbg)
