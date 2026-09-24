#!/usr/bin/env python
"""Which Claude Code sessions on this host could have acted in a time window, and which hit a rate limit?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation (canopy E2E arc, Phase 9: who readied and armed canopy#676?)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: memory reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md;
         notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9, "The merge, out of order"

WHY THIS EXISTS. canopy#676 was marked ready and armed at 2026-09-23 22:28Z while held as a draft,
as `pcalnon`. GitHub cannot tell the owner from any session or automation holding his token. A
transcript scan for the COMMAND can only refute a named session; it cannot say whether any session
was able to act at all. This asks a different question of the same transcripts: in the window, which
sessions recorded any ASSISTANT TOOL CALL, and which recorded a rate-limit refusal ("You've hit your
weekly limit")? A session that made no tool call in the window did not run `gh`.

WHAT IT CANNOT SEE: the GitHub web or mobile UI, other hosts, claude.ai cloud sessions, IDE or
browser actions, and any process that is not a Claude Code session. A null result excludes Claude
Code sessions on this host, nothing more.

Prints only session ids, timestamps and counts -- never message text (transcripts can hold secrets).

Usage:
    python3 util/ad-hoc/2026-09-24_host_session_activity_window.py \
        --start 2026-09-23T21:00:00Z --end 2026-09-24T01:40:00Z
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
LIMIT_MARKER = "hit your weekly limit"


def _ts(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def scan(path, start, end):
    """Return (tool_calls_in_window, limit_hits_in_window, first_limit_ts, last_ts_in_window)."""
    calls = hits = 0
    first_limit = last_seen = None
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            ts = _ts(rec.get("timestamp")) if isinstance(rec, dict) else None
            if ts is None or not (start <= ts <= end):
                continue
            last_seen = ts if last_seen is None or ts > last_seen else last_seen
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            content = msg.get("content")
            if msg.get("role") == "assistant" and isinstance(content, list):
                calls += sum(1 for b in content if isinstance(b, dict) and b.get("type") == "tool_use")
            if LIMIT_MARKER in raw:
                hits += 1
                first_limit = ts if first_limit is None or ts < first_limit else first_limit
    return calls, hits, first_limit, last_seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args()
    start, end = _ts(args.start), _ts(args.end)
    if start is None or end is None or start >= end:
        print("REFUSED: --start/--end must be ISO timestamps with start < end", file=sys.stderr)
        return 2
    rows = []
    for path in sorted(ROOT.rglob("*.jsonl")):
        calls, hits, first_limit, last_seen = scan(path, start, end)
        if calls or hits:
            rows.append((path, calls, hits, first_limit, last_seen))
    total_calls = sum(r[1] for r in rows)
    print(f"window {args.start} .. {args.end}: {len(rows)} transcript(s) with a tool call or a limit hit; {total_calls} tool call(s)")
    for path, calls, hits, first_limit, last_seen in sorted(rows, key=lambda r: (r[4] or start)):
        rel = path.relative_to(ROOT)
        fl = first_limit.strftime("%H:%M:%SZ") if first_limit else "-"
        ls = last_seen.strftime("%Y-%m-%dT%H:%M:%SZ") if last_seen else "-"
        print(f"  {str(rel.parent.name)[-40:]:40s} {rel.stem[:8]:8s} tool_calls={calls:4d} limit_hits={hits:3d} first_limit={fl} last_entry={ls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
