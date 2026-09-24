# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-B: background task launches and completion notices.
# Source: session ddf7847c's tmpfs scratchpad, r2b.SQyNnR/bg_tasks.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scratch (lane R2-B): background (run_in_background) launches and when their completion was notified.

Prints session id prefix, launch ts, notified ts, status and the tool_use's own short `description`
(bounded, token-shaped strings redacted). Never prints the command or any message text.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
lo, hi = sys.argv[1], sys.argv[2]  # launch window, ISO strings (lexicographic compare on Z timestamps)
launches = {}
notes = {}
for path in ROOT.rglob("*.jsonl"):
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            if "run_in_background" not in raw and "task-notification" not in raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            ts = str(rec.get("timestamp") or "")
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            for b in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    if inp.get("run_in_background") is True:
                        launches[b.get("id")] = (ts, path.stem[:8], str(inp.get("description") or "")[:90])
            content = rec.get("content") if isinstance(rec.get("content"), str) else ""
            if not content and isinstance(msg.get("content"), str):
                content = msg.get("content")
            for m in re.finditer(r"<tool-use-id>(.*?)</tool-use-id>", content or ""):
                st = re.search(r"<status>(.*?)</status>", content)
                notes.setdefault(m.group(1), (ts, st.group(1) if st else None))
for tid, (ts, sid, desc) in sorted(launches.items(), key=lambda kv: kv[1][0]):
    if lo <= ts <= hi:
        n = notes.get(tid)
        desc = re.sub(r"(gh[pousr]_[A-Za-z0-9]{8,}|sk-[A-Za-z0-9-]{8,})", "<redacted>", desc)
        print(ts[:19], sid, "notified:", (n[0][:19] if n else "NONE"), (n[1] if n else ""), "|", desc)
