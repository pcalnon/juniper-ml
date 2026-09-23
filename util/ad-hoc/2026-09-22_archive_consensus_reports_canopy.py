#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Archive the 2026-09-22 canopy-arc validators' final reports VERBATIM into the repo.

A subagent's report lives only in the session transcript
(``~/.claude/projects/<slug>/<session>/subagents/agent-<id>.jsonl``), which is local,
unversioned, and lost with the machine. The 2026-09-21 backup arc had to be rebuilt from
eleven transcripts; the memory note
``reference_subagents_killed_by_session_limit_resume_with_sendmessage`` records the rule:
archive reports verbatim as soon as they land.

This extracts the LAST assistant text block of each named agent. That block is the final
report for a completed agent; for one that is still running it is only a progress line,
and the output says which it is. Each report is written under a heading carrying the
agent's role. The file opens with a markdownlint-disable (the reports are verbatim prose,
not repo-styled markdown). It is scanned for obvious secret shapes before writing, and the
script refuses if one is found.

Usage:
    python3 util/ad-hoc/2026-09-22_archive_consensus_reports_canopy.py \\
        --session-dir ~/.claude/projects/<slug>/<session> \\
        --out reports/e2e-canopy-2026-09-02/consensus/2026-09-22_validator_reports.md \\
        a52c9cc62e2d76ef9="Lane A1 - F-053 DOM vs server" ...
"""

import argparse
import json
import re
import sys
from pathlib import Path

SECRET_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,}|AGE-SECRET-KEY-)")


def last_text(jsonl: Path) -> tuple[str, str]:
    """Return (text, status) for the last assistant text block in the transcript."""
    text, status = "", "no-assistant-text"
    for raw in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") if isinstance(rec, dict) else None
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        blocks = content if isinstance(content, list) else [{"type": "text", "text": content}] if isinstance(content, str) else []
        for b in blocks:
            if isinstance(b, dict) and b.get("type") == "text" and (b.get("text") or "").strip():
                text, status = b["text"], "last-assistant-text"
    return text, status


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("agents", nargs="+", help='AGENT_ID="role label"')
    args = ap.parse_args()

    sub = Path(args.session_dir).expanduser() / "subagents"
    parts = ["<!-- markdownlint-disable -->", "",
             "# Canopy E2E arc — validator reports, 2026-09-22 (verbatim)", "",
             "Archived by `util/ad-hoc/2026-09-22_archive_consensus_reports_canopy.py` from the session's subagent",
             "transcripts. Each section is the agent's final report exactly as delivered; they are EVIDENCE for",
             "Phase 7 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, not conclusions — the",
             "reconciliation, including where a report was itself corrected, is in that phase.", ""]
    for spec in args.agents:
        aid, _, label = spec.partition("=")
        path = sub / f"agent-{aid}.jsonl"
        if not path.exists():
            print(f"REFUSED: no transcript for {aid} at {path}", file=sys.stderr)
            return 1
        text, status = last_text(path)
        if SECRET_RE.search(text):
            print(f"REFUSED: a secret-shaped string in {aid}'s report; archive by hand after review", file=sys.stderr)
            return 1
        parts += [f"## {label or aid}", "", f"*agent `{aid}` · {status} · {len(text)} chars*", "", text.strip(), "", "---", ""]
        print(f"{aid}: {status}, {len(text)} chars -- {label}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
