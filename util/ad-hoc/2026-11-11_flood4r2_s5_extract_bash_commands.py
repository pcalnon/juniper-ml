#!/usr/bin/env python3
"""
List the Bash commands a Claude Code session ran that match a pattern, from that session's transcript, so a later
session can repeat a procedure with the commands that were actually run instead of a paraphrase of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: repeating session 4's landing procedure)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_s5_extract_agent_prompts.py (the same reading of the same transcript)

Usage:
  2026-11-11_flood4r2_s5_extract_bash_commands.py <transcript.jsonl> <regex> [--max-chars N] [--since <ISO prefix>]

Prints, for every Bash tool call whose command matches <regex> (Python ``re.search``): the record's timestamp and the
command, cut to N characters (default 900). A transcript repeats a tool call when a message is re-sent, so identical
commands are printed once. It reads the transcript and writes nothing. Exit 0 = at least one match; 1 = none.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def option(argv: list[str], name: str, default: str) -> str:
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    transcript = Path(argv[1])
    pattern = re.compile(argv[2])
    max_chars = int(option(argv, "--max-chars", "900"))
    since = option(argv, "--since", "")
    seen: set[str] = set()
    with transcript.open(encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            if '"tool_use"' not in raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            stamp = str(record.get("timestamp", ""))
            if since and stamp < since:
                continue
            message = record.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use" or block.get("name") != "Bash":
                    continue
                arguments = block.get("input")
                command = str(arguments.get("command", "")) if isinstance(arguments, dict) else ""
                if not command or command in seen or not pattern.search(command):
                    continue
                seen.add(command)
                print(f"--- {stamp[:19]}")
                print(command[:max_chars] + (" …[cut]" if len(command) > max_chars else ""))
    print(f"matches: {len(seen)}")
    return 0 if seen else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
