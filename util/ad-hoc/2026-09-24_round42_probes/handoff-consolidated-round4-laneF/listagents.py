#!/usr/bin/env python3
"""Round 4 lane F probe: every ListAgents call in session 2fba4397's main transcript, with its
timestamp and result text (session names and states only). Read-only."""
import glob
import json

path = glob.glob("/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl")[0]
recs = []
with open(path, "rb") as fh:
    for raw in fh.read().split(b"\n"):
        if raw.strip():
            try:
                recs.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
uses = {}
for r in recs:
    if r.get("type") != "assistant":
        continue
    for x in r.get("message", {}).get("content", []) or []:
        if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") == "ListAgents":
            uses[x["id"]] = r.get("timestamp")
for r in recs:
    if r.get("type") != "user":
        continue
    c = r.get("message", {}).get("content")
    if not isinstance(c, list):
        continue
    for x in c:
        if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in uses:
            cc = x.get("content")
            if isinstance(cc, list):
                cc = "".join(y.get("text", "") for y in cc if isinstance(y, dict))
            if uses[x["tool_use_id"]] >= "2026-09-25T01:30":
                print("=====", uses[x["tool_use_id"]], "->", r.get("timestamp"))
                print(str(cc)[:3000])
