#!/usr/bin/env python3
"""Read-only: find ListAgents calls in session 2fba4397's main transcript after 01:00Z on 09-25; print result heads."""
import glob
import json
import re

SID = "2fba4397-7d9b-4929-8ca2-375b8168e1c8"
paths = glob.glob(f"/home/pcalnon/.claude/projects/*/{SID}.jsonl")
print("main transcripts:", len(paths))
calls = {}
MASK = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
for p in paths:
    with open(p, encoding="utf-8") as fh:
        for raw in fh:
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            ts = rec.get("timestamp", "")
            if ts < "2026-09-25T01:00":
                continue
            c = rec.get("message", {}).get("content")
            if not isinstance(c, list):
                continue
            for part in c:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "tool_use" and part.get("name") == "ListAgents":
                    calls[part.get("id")] = ts
                    print("CALL", ts)
                if part.get("type") == "tool_result" and part.get("tool_use_id") in calls:
                    body = part.get("content")
                    if isinstance(body, list):
                        body = "\n".join(x.get("text", "") for x in body if isinstance(x, dict))
                    body = MASK.sub("<email>", str(body))
                    print("RESULT", ts)
                    for line in body.split("\n")[:25]:
                        print("   ", line[:160])
