# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-B: every transcript entry in the 21:41-01:40Z window.
# Source: session ddf7847c's tmpfs scratchpad, r2b.SQyNnR/entries_in_window.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Scratch (lane R2-B): every transcript entry in a window -- file stem, timestamp, record type, role. No text."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
start = datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
end = datetime.fromisoformat(sys.argv[2].replace("Z", "+00:00"))
rows = []
for path in ROOT.rglob("*.jsonl"):
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            ts = rec.get("timestamp")
            try:
                t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (AttributeError, ValueError):
                continue
            if start <= t <= end:
                msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
                kinds = []
                content = msg.get("content")
                if isinstance(content, list):
                    kinds = sorted({b.get("type") for b in content if isinstance(b, dict)})
                rows.append((ts, path.parent.name[-30:], path.stem[:8], rec.get("type"), msg.get("role"), ",".join(k for k in kinds if k), rec.get("isMeta")))
for r in sorted(rows):
    print(*r)
print("total", len(rows))
