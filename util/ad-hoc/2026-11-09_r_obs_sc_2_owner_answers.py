#!/usr/bin/env python3
"""
List every AskUserQuestion call in the named sessions' transcripts, with the owner's answer and when it was given.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consolidated plan record)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc -- single-use extractor
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md v1.15.15 (R-OBS-SC-2's record);
         util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py (the pattern)

Why
---
Plan v1.15.15 records the owner's rulings on R-OBS-SC-2, given across four sessions (e97264c3, f58cf63e, b4208d23,
e21d1414). Their handoffs paraphrase the answers, and one of them says P3 D-03 had no recorded answer while an earlier
one records it. The plan dates an answer from the transcript's ``tool_result`` timestamp, the moment the answer
reached the session, so this reads the transcripts rather than the handoffs.

What it prints
--------------
For each AskUserQuestion ``tool_use`` in each session, in transcript order: when it was asked (the assistant entry's
timestamp), when it was answered (the paired ``tool_result``'s timestamp), each question's header, and the result
text verbatim. ``--full`` also prints each question's text; by default it is cut to ``--width`` characters.

The transcripts are found by session-id prefix under ``~/.claude/projects/*/``, never by a fixed path: a session's
transcript moves when it leaves its worktree. They are split on "\\n" only, because ``str.splitlines()`` also splits
on U+0085 and U+2028, which occur inside JSON string values.

Usage
-----
    python3 util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py e97264c3 f58cf63e b4208d23 e21d1414 [--full]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"


def transcript(prefix: str) -> Path:
    """The one transcript whose session id starts with ``prefix``."""
    hits = sorted(PROJECTS.glob(f"*/{prefix}*.jsonl"))
    if len(hits) != 1:
        raise SystemExit(f"session {prefix}: expected one transcript under {PROJECTS}, found {len(hits)}: {hits}")
    return hits[0]


def result_text(content: object) -> str:
    """A tool_result's text, whether it is a string or a list of text blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return repr(content)


def scan(path: Path) -> list[dict]:
    asked: dict[str, dict] = {}
    order: list[str] = []
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    for line in raw.split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            continue
        for block in message["content"]:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                asked[block["id"]] = {"asked_at": entry.get("timestamp"), "questions": block.get("input", {}).get("questions", []), "answered_at": None, "answer": None}
                order.append(block["id"])
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in asked:
                record = asked[block["tool_use_id"]]
                record["answered_at"] = entry.get("timestamp")
                record["answer"] = result_text(block.get("content"))
    return [asked[i] for i in order]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sessions", nargs="+", help="session-id prefixes")
    ap.add_argument("--full", action="store_true", help="print each question's text in full")
    ap.add_argument("--width", type=int, default=240)
    args = ap.parse_args()

    for prefix in args.sessions:
        path = transcript(prefix)
        calls = scan(path)
        print(f"== {prefix}: {path.name}: {len(calls)} AskUserQuestion call(s)")
        for n, call in enumerate(calls, 1):
            print(f"-- call {n}: asked {call['asked_at']}, answered {call['answered_at']}")
            for q in call["questions"]:
                text = q.get("question", "")
                if not args.full and len(text) > args.width:
                    text = text[: args.width] + "..."
                print(f"   [{q.get('header', '')}] {text}")
            print("   ANSWER: " + json.dumps(call["answer"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
