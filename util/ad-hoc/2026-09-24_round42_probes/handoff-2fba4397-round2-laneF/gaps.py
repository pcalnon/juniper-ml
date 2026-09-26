#!/usr/bin/env python3
"""Report record timestamps, the largest gaps, and the last few tool uses in a subagent transcript (read-only)."""
import json
import sys
from datetime import datetime

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    data = fh.read()
recs = []
for line in data.split("\n"):
    if not line.strip():
        continue
    try:
        recs.append(json.loads(line))
    except Exception:
        pass


def ts(r):
    t = r.get("timestamp")
    if not t:
        return None
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


stamps = [(ts(r), r) for r in recs if ts(r)]
print("records:", len(recs), "first:", stamps[0][0].isoformat(), "last:", stamps[-1][0].isoformat())
gaps = []
for (a, ra), (b, rb) in zip(stamps, stamps[1:]):
    gaps.append(((b - a).total_seconds(), a.isoformat(), b.isoformat()))
gaps.sort(reverse=True)
print("largest gaps (s, from, to):")
for g in gaps[:8]:
    print("  %.0f  %s -> %s" % g)
print("last tool uses:")
n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
tu = []
for t, r in stamps:
    msg = r.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), list):
        for p in msg["content"]:
            if isinstance(p, dict) and p.get("type") == "tool_use":
                inp = p.get("input", {})
                desc = inp.get("description") or inp.get("command") or inp.get("file_path") or ""
                tu.append((t.isoformat(), p.get("name"), str(desc)[:160]))
for x in tu[-n:]:
    print("  ", x)
# the first user record (brief) timestamps
print("user records with >2000 chars text:")
for t, r in stamps:
    if r.get("type") != "user":
        continue
    msg = r.get("message")
    c = msg.get("content") if isinstance(msg, dict) else None
    txt = ""
    if isinstance(c, str):
        txt = c
    elif isinstance(c, list):
        txt = "\n".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    if len(txt) > 2000:
        print("  ", t.isoformat(), len(txt))
