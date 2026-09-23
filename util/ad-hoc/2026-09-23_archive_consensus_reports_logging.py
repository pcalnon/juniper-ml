#!/usr/bin/env python3
"""Archive the logging-arc validators' final reports VERBATIM into the repo.

Project: juniper-ml
Sub-Project: ad-hoc tooling (logging redesign arc, cascor#573)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — one-off per validation round
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-22_archive_consensus_reports_canopy.py (the canopy arc's copy; same
         extraction, a canopy-specific heading); memory note
         reference_subagents_killed_by_session_limit_resume_with_sendmessage ("archive reports
         verbatim"); notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md

WHY

A subagent's report lives only in the session transcript
(``~/.claude/projects/<slug>/<session>/subagents/agent-<id>.jsonl``), which is local and
unversioned. The round-1 validation of the 2026-09-22 logging handoff showed why that matters. Its
reconciliation dropped one lane's finding, B1's P4 forward hazard, and the loss was found only by
re-reading the report in the transcript. A round-2 lane asked to check for residue needs the
round-1 reports as a SOURCE; a summary of them is exactly what it cannot trust.

This extracts the LAST assistant text block of each named agent. For a completed agent that block
is the final report; for one that is still running it is only a progress line. The status field
records which of the two it is. Each report goes under a heading with the agent's role. The output
is scanned for obvious secret shapes before writing, and the script refuses if one is found.

USAGE

    python3 util/ad-hoc/2026-09-23_archive_consensus_reports_logging.py \\
        --session-dir ~/.claude/projects/<slug>/<session> \\
        --round 1 \\
        --out reports/2026-09-23_logging-arc-handoff-consensus/round1_lane_reports.md \\
        a5b9c3c0ad46d0e9f="Lane A1 - git / GitHub state" ...
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECRET_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,}|AGE-SECRET-KEY-)")

HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_logging-arc-phase-1-complete-gate-opens-p2-and-p04-is-the-real-next-step.md"


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session-dir", required=True)
    ap.add_argument("--round", required=True, type=int)
    ap.add_argument("--out", required=True)
    ap.add_argument("agents", nargs="+", help='AGENT_ID="role label"')
    args = ap.parse_args(argv)

    sub = Path(args.session_dir).expanduser() / "subagents"
    parts = [
        "<!-- markdownlint-disable -->",
        "",
        f"# Logging arc — round-{args.round} validator reports, 2026-09-23 (verbatim)",
        "",
        "Archived by `util/ad-hoc/2026-09-23_archive_consensus_reports_logging.py` from the session's subagent",
        "transcripts. Each section is the agent's final report exactly as delivered. They are EVIDENCE, not",
        f"conclusions: the reconciliation, including where a report was itself corrected, is §8 of `{HANDOFF}`.",
        "",
    ]
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
