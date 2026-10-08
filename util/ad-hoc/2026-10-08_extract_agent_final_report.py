#!/usr/bin/env python3
"""2026-10-08_extract_agent_final_report.py -- save a background agent's FINAL message from its transcript.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (agent-report capture)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

WHY THIS EXISTS

The harness refuses report files from subagents ("subagents should return findings as text"), so an
evaluator's report exists only as its final assistant message -- in the orchestrator's context and in
the agent's JSONL transcript. Context is summarised away; the transcript is the durable copy. This
writes the LAST assistant message's text blocks to a markdown file without echoing it, so a large
report can be preserved without flooding the orchestrator's context.

Usage:
    2026-10-08_extract_agent_final_report.py --transcript <agent>.output --out <file.md>

Exit: 0 written; 1 no assistant text found; 2 unreadable transcript.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def last_assistant_text(path: Path) -> str | None:
    last = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "assistant":
                continue
            content = (rec.get("message") or {}).get("content")
            if isinstance(content, str):
                texts = [content]
            else:
                texts = [b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text"]
            text = "\n".join(t for t in texts if t and t.strip())
            if text.strip():
                last = text
    return last


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        text = last_assistant_text(Path(args.transcript))
    except OSError as exc:
        print(f"unreadable transcript: {exc}", file=sys.stderr)
        return 2
    if not text:
        print("no assistant text found", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
