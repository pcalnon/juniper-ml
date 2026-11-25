#!/usr/bin/env python3
"""
Extract an AskUserQuestion dialog (questions, options, answer, timestamps) from a Claude Code transcript (V26 claims).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 26 ports, session 11, validator V26 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (validation of the six ruling-26 PR texts' quotations of the ruling)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 26);
         juniper-canopy#814 (the model fix)

What it does
------------
Reads a transcript (JSON lines) given by path, finds every assistant ``tool_use`` named ``AskUserQuestion`` whose
input text contains ``--match`` (a plain substring), prints each question with its header, every option's label and
description verbatim, the tool_use timestamp, and the matching ``tool_result`` (the answer) with its timestamp.
Read-only; writes only to ``--out`` when given (JSON).

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_claims_dialog.py TRANSCRIPT --match "Port to all five" [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _records(path: Path):
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield lineno, json.loads(line)
            except json.JSONDecodeError:
                continue


def _content(rec: dict) -> list:
    msg = rec.get("message") or {}
    content = msg.get("content")
    return content if isinstance(content, list) else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--match", required=True, help="substring that must occur in the AskUserQuestion input")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    asks: dict[str, dict] = {}
    results: dict[str, dict] = {}
    for lineno, rec in _records(args.transcript):
        for item in _content(rec):
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use" and item.get("name") == "AskUserQuestion":
                text = json.dumps(item.get("input"), ensure_ascii=False)
                if args.match in text:
                    asks[item["id"]] = {"line": lineno, "timestamp": rec.get("timestamp"), "input": item.get("input")}
            elif item.get("type") == "tool_result":
                results[item.get("tool_use_id", "")] = {"line": lineno, "timestamp": rec.get("timestamp"), "content": item.get("content")}

    out = []
    for tool_id, ask in asks.items():
        answer = results.get(tool_id)
        out.append({"tool_use_id": tool_id, "ask": ask, "answer": answer})
        print(f"== AskUserQuestion {tool_id} (transcript line {ask['line']}, timestamp {ask['timestamp']})")
        for qi, question in enumerate(ask["input"].get("questions", []), 1):
            print(f"  Q{qi} header: {question.get('header')!r}")
            print(f"  Q{qi} question: {question.get('question')!r}")
            for oi, option in enumerate(question.get("options", []), 1):
                print(f"    option {oi} label: {option.get('label')!r}")
                print(f"    option {oi} description: {option.get('description')!r}")
        if answer is None:
            print("  ANSWER: (no tool_result found)")
        else:
            content = answer["content"]
            if isinstance(content, list):
                content = " ".join(part.get("text", "") for part in content if isinstance(part, dict))
            print(f"  ANSWER (transcript line {answer['line']}, timestamp {answer['timestamp']}):")
            print(f"    {content!r}")
    if not asks:
        print(f"no AskUserQuestion input contains {args.match!r}", file=sys.stderr)
        return 1
    if args.out is not None:
        with args.out.open("w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
