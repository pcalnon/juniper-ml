#!/usr/bin/env python3
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# File Name:     2026-09-23_extract_agent_final_reports.py
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:   Extract a background agent's FINAL report, verbatim, from its session transcript
#                (the JSONL `tasks/<agent-id>.output` file Claude Code writes), so that a review
#                lane's findings can be archived in the repository before the session that ran it
#                ends and its /tmp transcript is reaped.
#
#    Why: consensus-review lanes return their findings only as their last message. The transcript
#    lives under /tmp and does not survive the session, and paraphrasing a report into a summary
#    loses exactly the detail a later round needs to check a fold against (see the memory note
#    "archive reports verbatim"). This writes the last assistant message's text, unedited.
#
#    Usage:
#      python util/ad-hoc/2026-09-23_extract_agent_final_reports.py OUTPUT_FILE [--label NAME] [--out PATH]
#
#    The final report is the text of the LAST assistant record in the file. Text blocks of that one
#    message are joined with a blank line; tool-use blocks are skipped. Exits 1 if the file holds no
#    assistant text at all, rather than writing an empty report.
#####################################################################################################################################################################################################

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def final_report(path: Path) -> str:
    """Return the text of the last assistant message in a transcript, or '' if there is none."""
    last = ""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "assistant":
                continue
            content = (record.get("message") or {}).get("content")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n\n".join(block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text")
            else:
                text = ""
            if text.strip():
                last = text
    return last


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_file", type=Path, help="an agent's tasks/<id>.output transcript")
    parser.add_argument("--label", default=None, help="heading written above the report")
    parser.add_argument("--out", type=Path, default=None, help="write here instead of stdout")
    args = parser.parse_args(argv)

    report = final_report(args.output_file)
    if not report.strip():
        print(f"no assistant text found in {args.output_file}", file=sys.stderr)
        return 1
    header = f"# {args.label}\n\n" if args.label else ""
    body = header + report.rstrip() + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
