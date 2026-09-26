"""Print user-side records (incl. teammate messages) of the main transcript at given timestamp prefixes. Read-only."""
import json
import sys

P = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-fizzy-hugging-dream/2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl"
prefixes = sys.argv[1:]
raw = open(P, encoding="utf-8").read()
for line in raw.split("\n"):
    if not line.strip():
        continue
    r = json.loads(line)
    ts = r.get("timestamp", "")
    if not any(ts.startswith(p) for p in prefixes):
        continue
    msg = r.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    parts.append(c.get("text", ""))
                elif c.get("type") == "tool_use":
                    parts.append("[tool_use " + str(c.get("name")) + "] " + json.dumps(c.get("input"), ensure_ascii=False)[:600])
                elif c.get("type") == "tool_result":
                    cc = c.get("content")
                    parts.append("[tool_result] " + (cc if isinstance(cc, str) else json.dumps(cc, ensure_ascii=False))[:300])
        text = "\n".join(parts)
    else:
        text = ""
    print("===", ts, r.get("type"), (msg or {}).get("role") if isinstance(msg, dict) else "")
    print(text[:900])
