"""List the peer session's Write/Edit calls on its handoff file, with timestamps and the key strings. Read-only."""
import json
import sys

P = "/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647.jsonl"
TARGET = "HANDOFF_2026-09-24_round-42-follow-up-lane"
KEYS = ("APD-ECO-013 stays open", "once the three bytes-compare", "No forward has been confirmed", "README rows", "ride juniper-ml#2089", "closes when F4")
raw = open(P, encoding="utf-8").read()
since = sys.argv[1] if len(sys.argv) > 1 else "2026-09-25T00:00"
for line in raw.split("\n"):
    if not line.strip():
        continue
    r = json.loads(line)
    ts = r.get("timestamp", "")
    if ts < since:
        continue
    msg = r.get("message")
    if not isinstance(msg, dict) or msg.get("role") != "assistant":
        continue
    for part in msg.get("content") or []:
        if not isinstance(part, dict) or part.get("type") != "tool_use":
            continue
        inp = part.get("input") or {}
        path = inp.get("file_path", "") or ""
        if TARGET not in path:
            continue
        blob = json.dumps(inp, ensure_ascii=False)
        hits = [k for k in KEYS if k in blob]
        new = inp.get("new_string") or inp.get("content") or ""
        old = inp.get("old_string") or ""
        print(ts, part.get("name"), "hits:", hits)
        if old:
            print("    OLD:", old[:220].replace("\n", " | "))
        print("    NEW:", new[:220].replace("\n", " | "))
