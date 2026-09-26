#!/usr/bin/env python3
"""Re-derive the 'Key leaks' AskUserQuestion call and its answer from session transcripts.

Usage: ruling_check.py <transcript.jsonl> [more.jsonl ...]
Prints, for each AskUserQuestion tool_use whose input mentions header 'Key leaks',
the tool_use timestamp, the matching tool_result timestamp and the answer tail.
"""
import json
import sys

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    recs = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    asks = {}
    for r in recs:
        msg = r.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion":
                inp = json.dumps(c.get("input"))
                if "Key leaks" in inp:
                    asks[c.get("id")] = (r.get("timestamp"), r.get("sessionId"), inp)
    for r in recs:
        msg = r.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id") in asks:
                ts, sid, inp = asks[c["tool_use_id"]]
                res = c.get("content")
                if isinstance(res, list):
                    res = " ".join(x.get("text", "") for x in res if isinstance(x, dict))
                print(f"file={path}")
                print(f"session={sid} asked={ts} answered={r.get('timestamp')}")
                print("answer tail:", str(res)[-400:])
                print("---")
    if not asks:
        print(f"file={path}: no 'Key leaks' AskUserQuestion")
