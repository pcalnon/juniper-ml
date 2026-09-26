#!/usr/bin/env python3
"""List AskUserQuestion calls (headers + time) and their answers in a transcript after a timestamp (read-only)."""
import json
import sys

path, after = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as fh:
    data = fh.read()
calls = {}
for line in data.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    ts = str(r.get("timestamp", ""))
    msg = r.get("message")
    if not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
        continue
    for p in msg["content"]:
        if not isinstance(p, dict):
            continue
        if p.get("type") == "tool_use" and p.get("name") == "AskUserQuestion":
            qs = p.get("input", {}).get("questions", [])
            calls[p.get("id")] = (ts, [q.get("header") for q in qs])
        elif p.get("type") == "tool_result" and p.get("tool_use_id") in calls:
            asked, headers = calls.pop(p.get("tool_use_id"))
            if asked < after:
                continue
            c = p.get("content")
            txt = c if isinstance(c, str) else " ".join(x.get("text", "") for x in (c or []) if isinstance(x, dict))
            print(f"asked {asked} answered {ts} headers={headers}\n   {txt[:400]}")
for cid, (asked, headers) in calls.items():
    if asked >= after:
        print(f"asked {asked} UNANSWERED headers={headers}")
