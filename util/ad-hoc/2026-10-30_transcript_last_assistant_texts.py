#!/usr/bin/env python3
"""
Print the last N assistant text blocks and AskUserQuestion prompts of a Claude Code session transcript.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-30
Status: ad-hoc — investigation (flood-3 record, ninth update)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_flood3-second-continuation-rows-fixed-owner-calls-open.md (item 1.0)

Why this exists
---------------
A live session can sit for days on an unanswered question dialog, and its ListAgents row says only
``waiting``. To learn what it is waiting on, read its transcript (``~/.claude/projects/<project dir>/<session
id>.jsonl``): this prints each recent assistant text block with its timestamp, and the questions of any
``AskUserQuestion`` call, truncated. It found that session ``[901969]`` (worktree ``iridescent-sniffing-snail``)
had been waiting since 2026-10-28 20:58Z on three questions this flood-3 pass had already resolved.

    python3 -I util/ad-hoc/2026-10-30_transcript_last_assistant_texts.py <transcript.jsonl> <N>

Transcripts are private session data: read them locally, never copy them into a repository. Exit 0.
"""

import json
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    path, count = sys.argv[1], int(sys.argv[2])
    texts = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("type") != "assistant":
                continue
            for block in (record.get("message") or dict()).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and block.get("text", "").strip():
                    texts.append((record.get("timestamp", "?"), block["text"].strip()))
                elif block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                    questions = [q.get("question", "")[:300] for q in (block.get("input") or dict()).get("questions", [])]
                    texts.append((record.get("timestamp", "?"), "ASKUSERQUESTION: " + " || ".join(questions)))
    for stamp, text in texts[-count:]:
        print(f"--- {stamp}\n{text[:900]}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
