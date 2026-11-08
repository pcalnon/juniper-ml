#!/usr/bin/env python3
"""
Scan Claude Code session transcripts for shell commands run inside a time window.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md

Why this exists
---------------
On yamaguchi, systemd recorded that the /sys API filesystems (debugfs, tracefs,
configfs, fusectl -- and, with them, securityfs and bpffs, which have no unit file
and so left no timestamp) were unmounted together at 2026-10-27 17:55:28 CDT
(22:55:28Z). The system journal, syslog and auth.log all begin AFTER that
instant, so the only surviving record of what ran on the host then is the
session transcripts under ~/.claude/projects/. This script reads them.

What it reads and prints
------------------------
Every ``*.jsonl`` under ``--root`` (default ``~/.claude/projects``), line by line.
An entry is kept when its ISO ``timestamp`` falls inside [--since, --until] and it
carries one of:

* an assistant ``tool_use`` block for ``Bash`` (its ``input.command``),
* a user ``<bash-input>`` block (a ``!`` command typed by the owner),
* a ``tool_result`` whose text matches ``--result-regex`` (default: mount/umount
  vocabulary), so a command's *output* that mentions an unmount is also seen.

``--command-regex`` filters commands (default: match everything). Output is a
time-sorted table: UTC timestamp, session file (relative), kind, first line of the
command (truncated to --width).

Secrets: commands are passed through a redactor that masks the token shapes this
ecosystem uses (GitHub PATs, ``sk-`` keys, AWS key ids, ``password=`` /
``token=`` assignments, URL credentials). It is a guard, not a guarantee -- read
before quoting.

It is read-only. It never writes outside stdout.

Usage
-----
    python3 util/ad-hoc/2026-11-07_transcript_window_scan.py \\
        --since 2026-10-27T22:40:00Z --until 2026-10-27T23:05:00Z

    # every mount-vocabulary command ever run, any time:
    python3 util/ad-hoc/2026-11-07_transcript_window_scan.py \\
        --since 2026-01-01T00:00:00Z --until 2027-01-01T00:00:00Z \\
        --command-regex '\\b(u?mount|unshare|nsenter|chroot|rbind|make-r?(shared|slave|private))\\b'
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RESULT_REGEX = r"\b(umount|unmount|securityfs|/sys/kernel/security|rbind|make-rshared|make-rslave)\b"

_REDACTIONS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "<REDACTED-GH-TOKEN>"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "<REDACTED-GH-PAT>"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "<REDACTED-SK>"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "<REDACTED-AWS-KEY-ID>"),
    (re.compile(r"(?i)((?:password|passwd|passphrase|token|secret|api[_-]?key)\s*[=:]\s*)\S+"), r"\1<REDACTED>"),
    (re.compile(r"(https?://)[^/\s:@]+:[^/\s@]+@"), r"\1<REDACTED>@"),
]


def redact(text: str) -> str:
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def parse_ts(value: str) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def iter_blocks(entry: dict):
    """Yield (kind, text) pairs of interest from one transcript entry."""
    message = entry.get("message")
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if isinstance(content, str):
        if "<bash-input>" in content:
            for match in re.finditer(r"<bash-input>(.*?)</bash-input>", content, re.S):
                yield "owner-!", match.group(1)
        return
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "tool_use" and block.get("name") == "Bash":
            command = (block.get("input") or {}).get("command")
            if isinstance(command, str):
                yield "bash", command
        elif btype == "text":
            text = block.get("text")
            if isinstance(text, str) and "<bash-input>" in text:
                for match in re.finditer(r"<bash-input>(.*?)</bash-input>", text, re.S):
                    yield "owner-!", match.group(1)
        elif btype == "tool_result":
            inner = block.get("content")
            if isinstance(inner, list):
                inner = "\n".join(part.get("text", "") for part in inner if isinstance(part, dict))
            if isinstance(inner, str):
                yield "result", inner


def scan(root: Path, since: datetime, until: datetime, command_re: re.Pattern, result_re: re.Pattern, width: int):
    rows = []
    files = sorted(root.rglob("*.jsonl"))
    for path in files:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if mtime < since:  # a transcript last written before the window cannot hold entries inside it
            continue
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if '"timestamp"' not in line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = parse_ts(entry.get("timestamp"))
                    if ts is None or ts < since or ts > until:
                        continue
                    for kind, text in iter_blocks(entry):
                        if kind == "result":
                            if not result_re.search(text):
                                continue
                            hit = result_re.search(text)
                            start = max(0, hit.start() - 80)
                            snippet = text[start : hit.end() + 120]
                        else:
                            if not command_re.search(text):
                                continue
                            snippet = text
                        first = " | ".join(part.strip() for part in redact(snippet).splitlines() if part.strip())
                        rows.append((ts, str(path.relative_to(root)), kind, entry.get("cwd", ""), first[:width]))
        except OSError as exc:
            print(f"# unreadable: {path}: {exc}", file=sys.stderr)
    rows.sort(key=lambda row: row[0])
    return len(files), rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    parser.add_argument("--since", required=True, help="ISO-8601 UTC, e.g. 2026-10-27T22:40:00Z")
    parser.add_argument("--until", required=True, help="ISO-8601 UTC")
    parser.add_argument("--command-regex", default=".", help="filter for bash / owner-! commands")
    parser.add_argument("--result-regex", default=DEFAULT_RESULT_REGEX, help="filter for tool_result text")
    parser.add_argument("--no-results", action="store_true", help="skip tool_result matching")
    parser.add_argument("--width", type=int, default=400)
    args = parser.parse_args(argv)

    since = parse_ts(args.since)
    until = parse_ts(args.until)
    if since is None or until is None or since > until:
        parser.error("--since/--until must be ISO-8601 and since <= until")
    result_re = re.compile(r"(?!x)x") if args.no_results else re.compile(args.result_regex)
    nfiles, rows = scan(Path(args.root), since, until, re.compile(args.command_regex), result_re, args.width)
    print(f"# root={args.root} files={nfiles} window=[{since.isoformat()} .. {until.isoformat()}] rows={len(rows)}")
    for ts, rel, kind, cwd, text in rows:
        print(f"{ts.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z\t{kind}\t{rel}\tcwd={cwd}\t{text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
