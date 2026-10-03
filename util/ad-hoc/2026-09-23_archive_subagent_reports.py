#!/usr/bin/env python3
"""
Archive subagent final reports verbatim from their transcripts into a notes/ consensus record.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation support (consensus rounds for the dynamic-workflow harness design)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Why this exists
---------------
A subagent's report lives ONLY in the session transcript
(~/.claude/projects/<slug>/<session>/subagents/agent-<id>.jsonl, last assistant text block):
local, unversioned, and gone with the machine. The standing rule is to archive validator
reports verbatim into notes/ as soon as they land. Re-emitting a 10K-token report through the
orchestrator's own output to write it down costs the same tokens again; copying it from the
transcript costs none. This script does the copy.

Usage
-----
    python3 util/ad-hoc/2026-09-23_archive_subagent_reports.py \
        --session-dir ~/.claude/projects/<slug>/<session-id> \
        --out notes/<RECORD>.md \
        --agent <agent-id>=<label> [--agent <agent-id>=<label> ...] \
        [--header-file <md file prepended when --out does not exist yet>] [--dry-run]

Each --agent adds one section "## Report <label>" followed by the agent's final assistant text
verbatim, with the message timestamp. Sections are appended; an agent whose label already heads
a section in --out is skipped, so the script is idempotent. The transcript is read-only.
Secret screen: the caller is responsible for reviewing the appended text; this script only
refuses to append when it sees an obvious credential pattern and says so.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

CREDENTIAL_PATTERNS = (
    re.compile(r"(?i)\b(passphrase|password|api[_-]?key|secret)\s*[:=]\s*['\"]?[A-Za-z0-9+/_\-]{12,}"),
    re.compile(r"\b(sk-ant-|ghp_|github_pat_)[A-Za-z0-9_\-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def last_assistant_text(transcript_path: str) -> tuple[str, str]:
    """Return (text, timestamp) of the last assistant message that carries a text block."""
    text, stamp = "", ""
    with open(transcript_path, errors="ignore") as handle:
        for line in handle:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "assistant":
                continue
            message = rec.get("message") or {}
            content = message.get("content") or []
            blocks = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text" and b.get("text")]
            if blocks:
                text = "\n".join(blocks)
                stamp = rec.get("timestamp", "")
    return text, stamp


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--agent", action="append", required=True, help="<agent-id>=<label>")
    parser.add_argument("--header-file", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    session_dir = os.path.expanduser(args.session_dir)
    existing = ""
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as handle:
            existing = handle.read()
    elif args.header_file:
        with open(args.header_file, encoding="utf-8") as handle:
            existing = handle.read().rstrip("\n") + "\n"

    appended = []
    for spec in args.agent:
        if "=" not in spec:
            print(f"bad --agent spec (want <id>=<label>): {spec}", file=sys.stderr)
            return 2
        agent_id, label = spec.split("=", 1)
        heading = f"## Report {label}"
        if heading in existing or any(heading in a for a in appended):
            print(f"skip {label}: section already present")
            continue
        path = os.path.join(session_dir, "subagents", f"agent-{agent_id}.jsonl")
        if not os.path.exists(path):
            print(f"NO ARTIFACT: {path}", file=sys.stderr)
            return 1
        text, stamp = last_assistant_text(path)
        if not text.strip():
            print(f"NO REPORT TEXT in {path}", file=sys.stderr)
            return 1
        for pattern in CREDENTIAL_PATTERNS:
            if pattern.search(text):
                print(f"REFUSED {label}: credential-shaped text matched {pattern.pattern!r}; review before archiving", file=sys.stderr)
                return 1
        when = stamp or datetime.now(timezone.utc).isoformat()
        section = f"\n\n---\n\n{heading}\n\n*Verbatim final message of agent `{agent_id}`, delivered {when}; transcript `subagents/agent-{agent_id}.jsonl`.*\n\n{text.rstrip()}\n"
        appended.append(section)
        print(f"archived {label}: {len(text)} chars from {os.path.basename(path)} ({when})")

    if not appended:
        return 0
    if args.dry_run:
        print(f"dry-run: would write {sum(len(s) for s in appended)} chars to {args.out}")
        return 0
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(existing.rstrip("\n") + "\n" + "".join(appended))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
