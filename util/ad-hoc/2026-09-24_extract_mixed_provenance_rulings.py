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

Extended the same day for the "Key leaks" ruling (--topic key-leaks): session bc31e993 asked it at 10:22:00Z, and
the owner's answer is the tool_result recorded at 18:30:09Z, with no earlier answer anywhere in that transcript. That
topic selects by the question's header, "Key leaks", because other calls mention a key leak in passing (the
follow-up split's options do).

The transcripts are found by session id, never by a fixed path. When a session leaves its worktree, its transcripts
move from the worktree's project directory to the main checkout's, so the fixed path this held for 8f86dec2
(`-home-...-juniper-ml--claude-worktrees-hazy-beaming-map/`) stopped resolving on 2026-09-24.

Usage:
    python3 util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py                       # print
    python3 util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --write P             # also write markdown to P
    python3 util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks ... # the "Key leaks" ruling
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
SESSION_IDS = {
    "bc31e993": "bc31e993-97b0-4a01-ae04-cb39593eb647",
    "8f86dec2": "8f86dec2-21ea-43f2-911a-bb2314a822ec",
}
# A call is about the gap if any question names cascor#678's retain-on-omit mix or the provenance annotation.
MARKERS = ("mixed", "retain-on-omit", "provenance")
KEY_LEAKS_HEADER = "Key leaks"


def transcript(session: str) -> Path:
    """The session's transcript, wherever its project directory is now."""
    hits = sorted(PROJECTS.glob(f"*/{SESSION_IDS[session]}.jsonl"))
    if len(hits) != 1:
        raise SystemExit(f"session {session}: expected one transcript under {PROJECTS}, found {len(hits)}: {hits}")
    return hits[0]


def matches(questions: list, topic: str) -> bool:
    if topic == "key-leaks":
        return any(q.get("header") == KEY_LEAKS_HEADER for q in questions)
    text = json.dumps(questions, ensure_ascii=False).lower()
    return any(marker in text for marker in MARKERS)


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


def extract(session: str, path: Path, topic: str = "mixed-provenance") -> list[dict]:
    calls: dict[str, dict] = {}
    found: list[dict] = []
    for rec in records(path):
        for block in blocks(rec):
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                questions = block.get("input", {}).get("questions", [])
                if matches(questions, topic):
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


def render(calls: list[dict], topic: str = "mixed-provenance") -> str:
    if topic == "key-leaks":
        out = ["# Defect-register round 42 -- the owner's \"Key leaks\" ruling, verbatim", ""]
        out.append("Extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks` from the session transcripts. It")
        out.append(f"selects every AskUserQuestion call with a question headed \"{KEY_LEAKS_HEADER}\" and keeps the WHOLE call. The questions and options")
        out.append("are the call's input as sent, JSON-dumped; the answer is the tool_result as returned. Nothing is paraphrased.")
        return _render_calls(out, calls)
    out = ["# Defect-register round 42 -- the owner's rulings, verbatim", ""]
    out.append("Extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` from the two session transcripts. It selects every")
    out.append("AskUserQuestion call that mentions juniper-cascor's mixed-provenance gap and keeps the WHOLE call, so the rulings asked beside it")
    out.append("(the PR sweeper, juniper-data 0.16.0's contents, which session does the follow-ups) are recorded too. The questions and options")
    out.append("are the call's input as sent, JSON-dumped; the answer is the tool_result as returned. Nothing is paraphrased.")
    return _render_calls(out, calls)


def _render_calls(out: list[str], calls: list[dict]) -> str:
    for call in calls:
        out += ["", f"## Session `{call['session']}`, asked {call['asked_at']}, answered {call['answered_at']}", ""]
        out += ["Question(s) and options, as sent:", "", "```json", json.dumps(call["questions"], ensure_ascii=False, indent=2), "```", ""]
        out += ["Answer, as returned:", "", "```text", call["result"], "```"]
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--write", type=Path, help="also write the markdown record to this path")
    parser.add_argument("--topic", choices=("mixed-provenance", "key-leaks"), default="mixed-provenance")
    args = parser.parse_args()
    calls = [call for session in SESSION_IDS for call in extract(session, transcript(session), args.topic)]
    text = render(calls, args.topic)
    print(text)
    print(f"{len(calls)} matching AskUserQuestion call(s)")
    if args.write:
        args.write.write_text(text, encoding="utf-8")
        print(f"wrote {args.write}")
    return 0 if calls else 1


if __name__ == "__main__":
    raise SystemExit(main())
