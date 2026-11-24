#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Recover a file's text from the Claude Code transcripts that wrote it.

Why this exists
---------------
The owner's blind "owner -> Overtoad" substitution (2026-11-20..22) rewrote untracked files on disk, so
a file that never reached git has no clean copy anywhere except the session transcripts, which the pass
did not touch. Replaying the Write and Edit tool calls recorded for a path gives its last written text.
That text is only a candidate: a file also edited by a shell command is not fully described by its tool
calls, so the caller must verify it, e.g. that the blind substitution of it reproduces the damaged bytes.

Usage
-----
    python3 2026-11-23_transcript_file_original.py --name BASENAME --out FILE TRANSCRIPT.jsonl [...]

Prints every Write/Edit found for BASENAME in timestamp order, replays them, writes the result to --out
and prints its sha256. Exits 1 when no Write is found. An Edit whose old_string is missing is skipped
and reported: it failed at the time, or a shell command edited the file in between.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys


def events(paths: list[str], name: str) -> list[tuple[str, str, dict]]:
    found = []
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if name not in line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = record.get("message") or {}
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    tool_input = block.get("input") or {}
                    if block.get("name") in ("Write", "Edit") and str(tool_input.get("file_path", "")).endswith("/" + name):
                        found.append((record.get("timestamp", ""), block["name"], tool_input))
    found.sort(key=lambda item: item[0])
    return found


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("transcripts", nargs="+")
    args = ap.parse_args(argv)
    found = events(args.transcripts, args.name)
    text = None
    for stamp, tool, tool_input in found:
        print(f"{stamp} {tool} {tool_input.get('file_path')}")
        if tool == "Write":
            text = tool_input.get("content", "")
        elif text is None:
            print("  Edit before any Write: skipped")
        else:
            old, new = tool_input.get("old_string", ""), tool_input.get("new_string", "")
            if old not in text:
                # the tool call itself failed at the time (its tool_result was an error), or a shell
                # command changed the file in between; the caller's verification decides which
                print("  SKIPPED: old_string not found (a failed Edit, or a shell edit in between)")
                continue
            text = text.replace(old, new) if tool_input.get("replace_all") else text.replace(old, new, 1)
    if text is None:
        print("no Write found")
        return 1
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"sha256 {hashlib.sha256(text.encode()).hexdigest()}  {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
