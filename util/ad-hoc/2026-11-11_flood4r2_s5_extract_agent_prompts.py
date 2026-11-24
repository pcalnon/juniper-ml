#!/usr/bin/env python3
"""
Extract the subagent briefs a Claude Code session issued (its Agent tool calls) from that session's transcript, so a
later session can relaunch a killed agent with the brief it was actually given instead of a paraphrase.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: session 4's five agents died on the weekly API limit)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md

Usage:
  2026-11-11_flood4r2_s5_extract_agent_prompts.py <transcript.jsonl> <out_dir> [--since <ISO timestamp prefix>]

Writes one file per Agent call, <out_dir>/<NNN>_<slug of the description>.txt (the brief verbatim, under a short
header), and prints an index: sequence number, timestamp, subagent type, isolation, model, brief length, description.
It reads the transcript and writes only under <out_dir>. Exit 0 = at least one brief found; 1 = none.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AGENT_TOOL_NAMES = frozenset({"Agent", "Task"})


def agent_calls(transcript: Path, since: str) -> list[dict]:
    calls: list[dict] = []
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
                if not isinstance(block, dict) or block.get("type") != "tool_use" or block.get("name") not in AGENT_TOOL_NAMES:
                    continue
                arguments = block.get("input")
                if not isinstance(arguments, dict):
                    continue
                calls.append(
                    {
                        "timestamp": stamp,
                        "description": str(arguments.get("description", "")),
                        "subagent_type": str(arguments.get("subagent_type", "")),
                        "isolation": str(arguments.get("isolation", "")),
                        "model": str(arguments.get("model", "")),
                        "effort": str(arguments.get("effort", "")),
                        "prompt": str(arguments.get("prompt", "")),
                    }
                )
    return calls


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()[:60] or "agent"


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    transcript = Path(argv[1])
    out_dir = Path(argv[2])
    since = argv[4] if len(argv) > 4 and argv[3] == "--since" else ""
    calls = agent_calls(transcript, since)
    out_dir.mkdir(parents=True, exist_ok=True)
    for number, call in enumerate(calls, start=1):
        name = f"{number:03d}_{slug(call['description'])}.txt"
        header = "\n".join(
            [
                f"# timestamp: {call['timestamp']}",
                f"# description: {call['description']}",
                f"# subagent_type: {call['subagent_type'] or '(default)'}",
                f"# isolation: {call['isolation'] or '(none)'}",
                f"# model: {call['model'] or '(inherit)'}  effort: {call['effort'] or '(default)'}",
                "# ---- brief follows verbatim ----",
                "",
            ]
        )
        (out_dir / name).write_text(header + call["prompt"] + "\n", encoding="utf-8")
        print(f"{number:03d}  {call['timestamp'][:19]}  type={call['subagent_type'] or '-':16s} iso={call['isolation'] or '-':8s} " f"model={call['model'] or '-':6s} len={len(call['prompt']):6d}  {call['description']}")
    print(f"briefs: {len(calls)}  written under: {out_dir}")
    return 0 if calls else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
