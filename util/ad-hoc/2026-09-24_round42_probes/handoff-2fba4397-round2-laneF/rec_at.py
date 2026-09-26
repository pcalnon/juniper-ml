#!/usr/bin/env python3
"""Print the text of records at a timestamp prefix in any JSONL transcript (read-only).

Usage: rec_at.py PATH TS_PREFIX [MAXCHARS]
"""
import json
import sys

path, prefix = sys.argv[1], sys.argv[2]
maxc = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
with open(path, encoding="utf-8") as fh:
    data = fh.read()
for line in data.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    if not str(r.get("timestamp", "")).startswith(prefix):
        continue
    msg = r.get("message")
    c = msg.get("content") if isinstance(msg, dict) else None
    out = []
    if isinstance(c, str):
        out.append(c)
    elif isinstance(c, list):
        for p in c:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text":
                out.append(p.get("text", ""))
            elif p.get("type") == "tool_use":
                out.append("TOOL_USE " + json.dumps(p.get("input"), ensure_ascii=False))
            elif p.get("type") == "tool_result":
                cc = p.get("content")
                if isinstance(cc, str):
                    out.append("RESULT " + cc)
                elif isinstance(cc, list):
                    out.append("RESULT " + "\n".join(q.get("text", "") for q in cc if isinstance(q, dict)))
    print("=====", r.get("timestamp"), r.get("type"), "isCompactSummary=", r.get("isCompactSummary"), "isMeta=", r.get("isMeta"))
    print("\n".join(out)[:maxc])
