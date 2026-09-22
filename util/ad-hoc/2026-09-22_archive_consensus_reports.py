#!/usr/bin/env python3
"""Archive a consensus round's subagent reports verbatim into a notes/ record.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- reconciliation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md
             notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md

A subagent's report exists only inside the session transcript, so it is lost the moment the
session ends -- which is why the consensus procedure requires archiving it. Retyping one out of
context is neither verbatim nor reliable, so this reads the agent's own JSONL and lifts the
FINAL assistant message, which is the report.

It refuses to write if a report carries credential-shaped content: a validator that measured a
secret file can quote a value by accident, and `notes/` is committed to a PUBLIC repository.
The screen is tuned to the shape of THIS arc's secrets -- 30-40 characters containing one of
`* @ $ %` -- because that is the class the repository's own gitleaks rule provably misses
(round 1, Lane B3 finding 11). A generic high-entropy screen buries a real hit in hundreds of
hyphenated English compounds; this one returned 16 hits across five files, all classifiable by
eye. A clean result is therefore a claim about these secrets' shape, not a general clean bill.

Usage:
    python3 util/ad-hoc/2026-09-22_archive_consensus_reports.py --out notes/<RECORD>.md \\
        --report '<Heading>=<agent-id>' [--report ...] [--check]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TASKS = Path(
    "/home/pcalnon/.claude/projects/"
    "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-buzzing-painting-meteor/"
    "1f771cb0-1009-4763-8a32-16517ac8b4b5/subagents"
)

# 30-40 chars, >=3 character classes, contains one of * @ $ %, not a path or a URL.
SECRET_SHAPED = re.compile(r"(?<![\w/.-])(?=[^\s]{30,40}(?![^\s]))(?=[^\s]*[*@$%])[A-Za-z0-9*@$%^&#!_.+=~-]{30,40}(?![^\s])")
ENC_V1 = re.compile(r"enc-v1:[A-Za-z0-9+/=]{8,}")
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")


def final_report(agent_id: str) -> str:
    path = TASKS / f"agent-{agent_id}.jsonl"
    if not path.is_file():
        raise SystemExit(f"no transcript for {agent_id} at {path}")
    last = ""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get("message") or {}
            if rec.get("type") != "assistant" and msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            else:
                continue
            if text.strip():
                last = text
    if not last.strip():
        raise SystemExit(f"no assistant text found in {path}")
    return last.rstrip() + "\n"


def screen(name: str, body: str) -> list[str]:
    problems = []
    for label, rx in (("credential-shaped token", SECRET_SHAPED), ("enc-v1 value", ENC_V1), ("JWT", JWT)):
        hits = rx.findall(body)
        if hits:
            problems.append(f"{name}: {len(hits)} {label}(s) -- classify each before archiving")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", action="append", required=True, metavar="HEADING=AGENT_ID")
    ap.add_argument("--header", default=None, help="path to a markdown preamble")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--allow-shaped", action="store_true",
                    help="archive anyway; use only after classifying every hit by hand")
    args = ap.parse_args()

    parts: list[str] = []
    if args.header:
        parts.append(Path(args.header).read_text(encoding="utf-8").rstrip() + "\n")

    problems: list[str] = []
    for spec in args.report:
        heading, _, agent_id = spec.partition("=")
        body = final_report(agent_id)
        problems += screen(heading, body)
        print(f"  {heading}: {len(body):,} bytes from agent {agent_id}")
        parts.append(
            f"\n---\n\n## {heading}\n\n"
            f"Subagent id `{agent_id}` ({len(body):,} characters). Archived verbatim.\n\n"
            "<!-- markdownlint-disable -->\n\n"
            f"{body}\n"
            "<!-- markdownlint-enable -->\n"
        )

    if problems:
        for p in problems:
            print(f"  SHAPED: {p}", file=sys.stderr)
        if not args.allow_shaped:
            print("\nrefusing to archive; re-run with --allow-shaped once each hit is classified",
                  file=sys.stderr)
            return 2

    text = "".join(parts)
    if args.check:
        print(f"\n--check: would write {args.out} ({len(text):,} bytes); nothing written")
        return 0
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"\nwrote {args.out} ({len(text):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
