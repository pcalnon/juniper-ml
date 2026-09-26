#!/usr/bin/env python3
"""Read-only: show the SHAPE (type, flags, content kinds, first 50 chars) of API-error records and of the
last record in a few subagent transcripts that contain one. No report bodies are printed."""
import json
from pathlib import Path

FILES = [
    "-home-pcalnon-Development-python-Juniper-juniper-ml/05434a69-5602-495e-a7a8-1103cfdf3890/subagents/agent-a3d67e293c8ff595d.jsonl",
    "-home-pcalnon-Development-python-Juniper-juniper-ml/0a852d44-65ca-46ac-953b-84e8bae98e9c/subagents/agent-a3c38866fe3a3c00e.jsonl",
    "-home-pcalnon-Development-python-Juniper-juniper-ml/0a852d44-65ca-46ac-953b-84e8bae98e9c/subagents/agent-a841de27cfb79b907.jsonl",
]


def shape(r):
    msg = r.get("message") if isinstance(r.get("message"), dict) else {}
    c = msg.get("content")
    kinds = [b.get("type") for b in c] if isinstance(c, list) else [type(c).__name__]
    text = " ".join(b.get("text", "") for b in c if b.get("type") == "text") if isinstance(c, list) else (c if isinstance(c, str) else "")
    return f"type={r.get('type')} api_err={r.get('isApiErrorMessage')} stop={msg.get('stop_reason')} kinds={kinds} head={text[:50]!r}"


for f in FILES:
    p = Path("/home/pcalnon/.claude/projects") / f
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]
    errs = [i for i, r in enumerate(rows) if r.get("isApiErrorMessage")]
    print(p.name, f"n={len(rows)} api-error records at {errs[:5]}")
    for i in errs[:2]:
        print("   err:", shape(rows[i]))
    print("  last:", shape(rows[-1]), "| last index is an api-error record:", (len(rows) - 1) in errs)
