#!/usr/bin/env python3
"""List Agent tool launches in a transcript: timestamp, description, and which of the given SHAs the prompt names.

Usage: agents.py <transcript.jsonl> SHA [SHA ...]
"""
import json
import sys

path, shas = sys.argv[1], sys.argv[2:]
with open(path, encoding="utf-8") as fh:
    raw = fh.read()
ids = {}
for line in raw.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    msg = r.get("message") or {}
    c = msg.get("content")
    if not isinstance(c, list):
        continue
    for x in c:
        if not isinstance(x, dict):
            continue
        if x.get("type") == "tool_use" and x.get("name") in ("Agent", "Task"):
            inp = x.get("input") or {}
            p = str(inp.get("prompt", ""))
            named = [s for s in shas if s in p]
            ids[x.get("id")] = r.get("timestamp")
            print(f"{r.get('timestamp')} LAUNCH desc={inp.get('description')!r} type={inp.get('subagent_type')} names={named}")
        if x.get("type") == "tool_result" and x.get("tool_use_id") in ids:
            cc = x.get("content")
            if isinstance(cc, list):
                cc = " ".join(y.get("text", "") for y in cc if isinstance(y, dict))
            s = str(cc)
            import re
            m = re.search(r"agentId: ?([a-f0-9]{17})|agent[_ ]id[^a-f0-9]*([a-f0-9]{17})", s)
            print(f"    -> result at {r.get('timestamp')}: {(m.group(1) or m.group(2)) if m else s[:120]!r}")
