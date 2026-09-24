# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-F: transcript scan for a ready or arm of canopy#676.
# Source: session ddf7847c's tmpfs scratchpad, r2f.xB7Gf1/forkC/scan_676.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scan every transcript's EXECUTED tool_use inputs for ready/arm/merge commands naming 676.

Prints session id, timestamp, file (dir tail) and the matched command string (truncated) only.
"""
import json
import re
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
PAT = re.compile(r"(gh\s+pr\s+ready|gh\s+pr\s+merge|--auto\b|enablePullRequestAutoMerge|markPullRequestReadyForReview|safe_merge|auto-merge|automerge|/merge\b|ready_for_review|convertPullRequestToDraft|--undo)", re.I)
N676 = re.compile(r"(?<![0-9])676(?![0-9])")
hits = 0
files_scanned = 0
for p in sorted(ROOT.rglob("*.jsonl")):
    files_scanned += 1
    try:
        fh = p.open(encoding="utf-8", errors="replace")
    except Exception:
        continue
    with fh:
        for raw in fh:
            if "676" not in raw:
                continue
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if not isinstance(rec, dict):
                continue
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            if msg.get("role") != "assistant":
                continue
            c = msg.get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") or {}
                cmd = inp.get("command") if isinstance(inp, dict) else None
                if not isinstance(cmd, str):
                    cmd = json.dumps(inp)[:4000]
                if N676.search(cmd) and PAT.search(cmd):
                    hits += 1
                    # print only the lines of the command that carry the match
                    lines = [ln.strip() for ln in cmd.splitlines() if N676.search(ln) or PAT.search(ln)]
                    print(p.parent.name[-40:], p.stem[:8], rec.get("timestamp"), b.get("name"), "|", " ;; ".join(lines)[:400])
print("files scanned:", files_scanned, "hits:", hits)
