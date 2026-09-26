"""Full text of SendMessage calls at given timestamps, and every cross-session message received in a window. Read-only."""
import json
import sys

P = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-fizzy-hugging-dream/2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl"
mode = sys.argv[1]
raw = open(P, encoding="utf-8").read()
recs = [json.loads(line) for line in raw.split("\n") if line.strip()]
if mode == "sent":
    for r in recs:
        ts = r.get("timestamp", "")
        if not any(ts.startswith(p) for p in sys.argv[2:]):
            continue
        msg = r.get("message")
        if not isinstance(msg, dict):
            continue
        for c in msg.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "SendMessage":
                print("=== SENT", ts, "to", c["input"].get("to"))
                print(c["input"].get("message", ""))
elif mode == "received":
    lo, hi = sys.argv[2], sys.argv[3]
    for r in recs:
        ts = r.get("timestamp", "")
        if not (lo <= ts <= hi):
            continue
        msg = r.get("message")
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content")
        text = content if isinstance(content, str) else "\n".join(c.get("text", "") for c in (content or []) if isinstance(c, dict) and c.get("type") == "text")
        if "cross-session-message" in text or "Another Claude session" in text:
            print("=== RECEIVED", ts)
            print(text[:1800])
