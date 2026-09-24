#!/usr/bin/env python3
"""
Extract, verbatim, the two owner rulings on juniper-cascor's mixed-provenance gap from the session transcripts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use extractor
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Two sessions working defect-register round 42 each asked the owner how juniper-cascor should annotate a
run whose partitions came from different sources (a partial fetch, then an inline train-only start that
keeps the fetched val/test). The register records the rulings, so it needs the exact question the owner
saw, the exact options, and the exact answer -- not a session's paraphrase of them. This reads each
session's transcript JSONL, finds every AskUserQuestion call whose text matches the gap, pairs it with its
tool_result by tool_use_id, and prints both unaltered (JSON-dumped, so nothing is re-flowed). The whole call
is kept, so the rulings asked in the same call (the PR sweeper, juniper-data 0.16.0, the follow-up split)
come with it.

The transcripts are split on "\\n" only: str.splitlines() also splits on U+0085 / U+2028, which occur
inside JSON string values and would tear a record in half.

Usage:
    python3 util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py            # print
    python3 util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --write P  # also write markdown to P
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
SESSIONS = {
    "bc31e993": PROJECTS / "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-happy-skipping-hollerith" / "bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl",
    "8f86dec2": PROJECTS / "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-hazy-beaming-map" / "8f86dec2-21ea-43f2-911a-bb2314a822ec.jsonl",
}
# A call is about the gap if any question names cascor#678's retain-on-omit mix or the provenance annotation.
MARKERS = ("mixed", "retain-on-omit", "provenance")


def records(path: Path):
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            yield json.loads(line)


def blocks(rec: dict) -> list:
    content = rec.get("message", {}).get("content")
    return content if isinstance(content, list) else []


def result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    return "\n".join(part.get("text", "") for part in content or [] if isinstance(part, dict))


def extract(session: str, path: Path) -> list[dict]:
    calls: dict[str, dict] = {}
    found: list[dict] = []
    for rec in records(path):
        for block in blocks(rec):
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                questions = block.get("input", {}).get("questions", [])
                text = json.dumps(questions, ensure_ascii=False).lower()
                if any(marker in text for marker in MARKERS):
                    calls[block["id"]] = {"session": session, "asked_at": rec.get("timestamp"), "tool_use_id": block["id"], "questions": questions}
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                call = calls.pop(block["tool_use_id"])
                call["answered_at"] = rec.get("timestamp")
                call["result"] = result_text(block)
                found.append(call)
    for call in calls.values():
        call["answered_at"], call["result"] = None, "(no tool_result found)"
        found.append(call)
    return found


def render(calls: list[dict]) -> str:
    out = ["# Defect-register round 42 -- the owner's rulings, verbatim", ""]
    out.append("Extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` from the two session transcripts. It selects every")
    out.append("AskUserQuestion call that mentions juniper-cascor's mixed-provenance gap and keeps the WHOLE call, so the rulings asked beside it")
    out.append("(the PR sweeper, juniper-data 0.16.0's contents, which session does the follow-ups) are recorded too. The questions and options")
    out.append("are the call's input as sent, JSON-dumped; the answer is the tool_result as returned. Nothing is paraphrased.")
    for call in calls:
        out += ["", f"## Session `{call['session']}`, asked {call['asked_at']}, answered {call['answered_at']}", ""]
        out += ["Question(s) and options, as sent:", "", "```json", json.dumps(call["questions"], ensure_ascii=False, indent=2), "```", ""]
        out += ["Answer, as returned:", "", "```text", call["result"], "```"]
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--write", type=Path, help="also write the markdown record to this path")
    args = parser.parse_args()
    calls = [call for session, path in SESSIONS.items() for call in extract(session, path)]
    text = render(calls)
    print(text)
    print(f"{len(calls)} matching AskUserQuestion call(s)")
    if args.write:
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write}")
    return 0 if calls else 1


if __name__ == "__main__":
    raise SystemExit(main())
