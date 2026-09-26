#!/usr/bin/env python3
"""List user-TYPED messages in a transcript: user records whose content is plain text,
excluding tool results, cross-session messages, compaction summaries and system reminders.

Usage: usertyped.py <transcript.jsonl> [--since ISO] [--chars N]
"""
import json
import sys

path = sys.argv[1]
since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else ""
chars = int(sys.argv[sys.argv.index("--chars") + 1]) if "--chars" in sys.argv else 1500
with open(path, encoding="utf-8") as fh:
    raw = fh.read()
for line in raw.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    if r.get("type") != "user" or (r.get("timestamp") or "") < since:
        continue
    if r.get("isMeta") or r.get("isCompactSummary") or r.get("isSidechain"):
        continue
    msg = r.get("message") or {}
    c = msg.get("content")
    texts = []
    if isinstance(c, str):
        texts.append(c)
    elif isinstance(c, list):
        if any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
            continue
        texts.extend(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    text = "\n".join(texts).strip()
    if not text:
        continue
    low = text.lstrip()
    if low.startswith("Another Claude session sent a message") or low.startswith("<cross-session-message"):
        continue
    if low.startswith("This session is being continued from a previous conversation"):
        print(f"--- {r.get('timestamp')} [compaction summary, {len(text)} chars]")
        continue
    print(f"--- {r.get('timestamp')} len={len(text)}")
    print(text[:chars])
