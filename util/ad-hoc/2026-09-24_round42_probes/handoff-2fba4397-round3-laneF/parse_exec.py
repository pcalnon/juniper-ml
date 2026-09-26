"""Parse the executor transcript: user records, gaps, last records. Read-only."""
import glob
import json
import sys
from datetime import datetime

paths = glob.glob("/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl")
print("paths:", paths)
p = paths[0]
raw = open(p, encoding="utf-8").read()
recs = []
for line in raw.split("\n"):
    if not line.strip():
        continue
    recs.append(json.loads(line))
print("records:", len(recs))


def ts(r):
    t = r.get("timestamp")
    if not t:
        return None
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


def text_of(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    out = []
    for part in c or []:
        if isinstance(part, dict):
            if part.get("type") == "text":
                out.append(part.get("text", ""))
            elif part.get("type") == "tool_result":
                cc = part.get("content")
                if isinstance(cc, str):
                    out.append("[tool_result] " + cc[:200])
                elif isinstance(cc, list):
                    out.append("[tool_result] " + " ".join(x.get("text", "")[:200] for x in cc if isinstance(x, dict)))
            elif part.get("type") == "tool_use":
                out.append("[tool_use] " + json.dumps(part.get("input"))[:300])
    return "\n".join(out)


mode = sys.argv[1] if len(sys.argv) > 1 else "users"
if mode == "users":
    for r in recs:
        if r.get("type") == "user":
            m = r.get("message", {})
            c = m.get("content")
            is_tool_result = isinstance(c, list) and any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c)
            if is_tool_result:
                continue
            t = text_of(m)
            print("=== USER", r.get("timestamp"), "isMeta=", r.get("isMeta"), "len=", len(t))
            print(t[:600].replace("\n", " | "))
            print()
elif mode == "gaps":
    prev = None
    gaps = []
    for r in recs:
        t = ts(r)
        if t is None:
            continue
        if prev is not None:
            d = (t - prev).total_seconds()
            if d >= 300:
                gaps.append((prev.isoformat(), t.isoformat(), d))
        prev = t
    for g in gaps:
        print("GAP %s -> %s : %.1f s" % g)
    print("first ts:", recs[0].get("timestamp"), "last ts:", [r.get("timestamp") for r in recs if r.get("timestamp")][-1])
elif mode == "tail":
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    for r in recs[-n:]:
        m = r.get("message", {}) if isinstance(r.get("message"), dict) else {}
        print("---", r.get("type"), r.get("timestamp"), m.get("role"))
        print(text_of(m)[:700].replace("\n", " | "))
elif mode == "dump":
    target = sys.argv[2]
    for r in recs:
        if r.get("timestamp", "").startswith(target) and r.get("type") == "user":
            print(text_of(r.get("message", {})))
