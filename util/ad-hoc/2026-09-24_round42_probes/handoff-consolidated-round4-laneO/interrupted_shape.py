#!/usr/bin/env python3
"""Read-only: shape of the last two records of executor adf9f5dbe46b1b03c (session 8f86dec2), which died when
its parent session ended ("[Request interrupted by user]" per memory). No body text beyond 50 chars."""
import json
from pathlib import Path

hits = sorted(Path("/home/pcalnon/.claude/projects").glob("*/8f86dec2-21ea-43f2-911a-bb2314a822ec/subagents/agent-adf9f5dbe46b1b03c.jsonl"))
print(hits)
rows = [json.loads(l) for l in hits[0].read_text(encoding="utf-8").split("\n") if l.strip()]
for r in rows[-2:]:
    msg = r.get("message") if isinstance(r.get("message"), dict) else {}
    c = msg.get("content")
    kinds = [b.get("type") for b in c] if isinstance(c, list) else [type(c).__name__]
    text = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text") if isinstance(c, list) else (c if isinstance(c, str) else "")
    print(f"type={r.get('type')} api_err={r.get('isApiErrorMessage')} stop={msg.get('stop_reason')} kinds={kinds} head={text[:50]!r}")
