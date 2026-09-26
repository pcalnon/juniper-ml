#!/usr/bin/env python3
"""Read-only: in executor a46e715a6801b98ca's transcript, find the first record mentioning each pushed sha,
and the user-record timestamps. Prints timestamps, record types and at most 160 chars of context around the
sha (credential-shaped text is not expected there; the context is cut to the sha's neighbourhood only)."""
import json
import re
from pathlib import Path

hits = sorted(Path("/home/pcalnon/.claude/projects").glob("*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl"))
assert len(hits) == 1, hits
rows = [json.loads(l) for l in hits[0].read_text(encoding="utf-8").split("\n") if l.strip()]
print(f"{len(rows)} records; first {rows[0].get('timestamp')}; last {rows[-1].get('timestamp')} type={rows[-1].get('type')}")

users = []
for r in rows:
    if r.get("type") != "user":
        continue
    c = r.get("message", {}).get("content")
    if isinstance(c, str) or (isinstance(c, list) and any(b.get("type") == "text" for b in c)):
        n = len(c) if isinstance(c, str) else sum(len(b.get("text", "")) for b in c if b.get("type") == "text")
        users.append((r.get("timestamp"), n))
print("plain-text user records:", users)

for sha in ("d1c66a11", "94ce8b1f"):
    for r in rows:
        s = json.dumps(r.get("message", {}), ensure_ascii=False)
        if sha in s and r.get("type") == "user" and "tool_result" in s and re.search(r"(created|commit|oid|pushed|verified)", s, re.I):
            i = s.find(sha)
            ctx = re.sub(r"\s+", " ", s[max(0, i - 80): i + 80])
            print(f"{sha}: first tool_result mention at {r.get('timestamp')}: …{ctx}…")
            break
    else:
        print(f"{sha}: no tool_result mention")
