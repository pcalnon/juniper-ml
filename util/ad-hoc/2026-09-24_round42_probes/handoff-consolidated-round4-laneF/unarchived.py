#!/usr/bin/env python3
"""Round 4 lane F probe: r4 L191-L192's recipe. Which transcripts contain "consolidated_r", which of
those agent ids are MISSING keys in fizzy's archiver, and does each transcript END with a text-only
assistant record (no tool_use)? Also: does any NON-lane transcript match the grep? Read-only."""
import glob
import json
import os
import re

FIZZY = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
paths = sorted(glob.glob("/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/*.jsonl"))
with open(f"{FIZZY}/util/ad-hoc/2026-09-24_archive_round42_reports.py", encoding="utf-8") as fh:
    src = fh.read()
missing_keys = dict(re.findall(r'"(a[0-9a-f]{16})":\s*\("([0-9a-f]{8})",\s*"([^"]+)"\)', src) and [(k, n) for k, _s, n in re.findall(r'"(a[0-9a-f]{16})":\s*\("([0-9a-f]{8})",\s*"([^"]+)"\)', src)])
print("MISSING keys parsed:", len(missing_keys))
for p in paths:
    with open(p, "rb") as fh:
        data = fh.read()
    if b"consolidated_r" not in data:
        continue
    aid = os.path.basename(p)[len("agent-"):-len(".jsonl")]
    meta = {}
    mp = p[:-len(".jsonl")] + ".meta.json"
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as fh:
            meta = json.load(fh)
    recs = [json.loads(x) for x in data.split(b"\n") if x.strip()]
    last = recs[-1]
    kinds = []
    c = last.get("message", {}).get("content")
    if isinstance(c, list):
        kinds = [x.get("type") for x in c if isinstance(x, dict)]
    ends_ok = last.get("type") == "assistant" and kinds and all(k == "text" for k in kinds)
    print(f"{aid}  {meta.get('description', '?')[:45]:45s} MISSING-key: {missing_keys.get(aid, '-')[:55]:55s} ends-with-report: {ends_ok}  last {last.get('timestamp')}")
