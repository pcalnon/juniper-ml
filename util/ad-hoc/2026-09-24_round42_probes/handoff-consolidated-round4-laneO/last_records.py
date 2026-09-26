#!/usr/bin/env python3
"""Read-only: for each subagent transcript of session 2fba4397, print metadata of its LAST record
(type, stop_reason, content block types, API-error flag, first 60 chars of text) -- no report bodies."""
import json
from pathlib import Path

d = sorted(Path("/home/pcalnon/.claude/projects").glob("*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents"))
assert len(d) == 1, d
for p in sorted(d[0].glob("agent-*.jsonl"), key=lambda q: q.stat().st_mtime):
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]
    last = rows[-1]
    msg = last.get("message", {}) if isinstance(last.get("message"), dict) else {}
    content = msg.get("content")
    kinds = [b.get("type") for b in content] if isinstance(content, list) else [type(content).__name__]
    text = ""
    if isinstance(content, list):
        text = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
    elif isinstance(content, str):
        text = content
    flags = {k: last[k] for k in ("isApiErrorMessage", "isMeta", "subtype") if k in last}
    print(f"{p.stem[6:]} n={len(rows):5} last={last.get('type'):10} ts={last.get('timestamp')} stop={msg.get('stop_reason')} kinds={kinds} flags={flags} head={text[:60]!r}")
