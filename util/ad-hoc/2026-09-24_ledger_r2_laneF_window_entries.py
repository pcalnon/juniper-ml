# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-09-24: the ledger's round 2, Lane R2-F: transcript entries in the rate-limit window.
# Source: session ddf7847c's tmpfs scratchpad, r2f.xB7Gf1/forkC/window_entries.py
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
#   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
#   reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round2.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Count every timestamped transcript entry in a window; print ids, timestamps, record types only."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"


def ts(v):
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception:
        return None


start = ts(sys.argv[1])
end = ts(sys.argv[2])
verbose = len(sys.argv) > 3
tot = 0
files = 0
for p in sorted(ROOT.rglob("*.jsonl")):
    rows = []
    try:
        fh = p.open(encoding="utf-8", errors="replace")
    except Exception:
        continue
    with fh:
        for raw in fh:
            try:
                rec = json.loads(raw)
            except Exception:
                continue
            if not isinstance(rec, dict):
                continue
            tv = rec.get("timestamp")
            t = ts(tv) if isinstance(tv, str) else None
            if t is None or not (start <= t <= end):
                continue
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            role = msg.get("role")
            c = msg.get("content")
            if isinstance(c, list):
                ctypes = ",".join(sorted({str(b.get("type")) for b in c if isinstance(b, dict)}))
            elif isinstance(c, str):
                ctypes = "str"
            else:
                ctypes = "-"
            rows.append((t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", rec.get("type"), role, ctypes, "LIMIT" if "hit your weekly limit" in raw else ""))
    if rows:
        files += 1
        tot += len(rows)
        print(p.relative_to(ROOT).parent.name[-45:], p.stem[:8], "entries=%d" % len(rows), "first=%s" % rows[0][0], "last=%s" % rows[-1][0])
        if verbose:
            for r in rows:
                print("   ", *r)
print("files:", files, "entries:", tot)
