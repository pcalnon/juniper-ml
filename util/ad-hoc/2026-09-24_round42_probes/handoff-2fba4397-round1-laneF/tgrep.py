#!/usr/bin/env python3
"""Grep a session transcript (JSONL) record by record.

Usage: tgrep.py <transcript.jsonl> REGEX [--types user,assistant] [--ctx N] [--max M] [--kinds text,tool_use,tool_result]
For each record whose flattened content matches REGEX, print timestamp, record type,
content kind, and N chars of context around each match (default 300).
"""
import json
import re
import sys

args = sys.argv[1:]
path, pat = args[0], args[1]
types = None
kinds = None
ctx = 300
mx = 50
if "--types" in args:
    types = set(args[args.index("--types") + 1].split(","))
if "--kinds" in args:
    kinds = set(args[args.index("--kinds") + 1].split(","))
if "--ctx" in args:
    ctx = int(args[args.index("--ctx") + 1])
if "--max" in args:
    mx = int(args[args.index("--max") + 1])
rx = re.compile(pat, re.IGNORECASE)
with open(path, encoding="utf-8") as fh:
    raw = fh.read()
count = 0
for line in raw.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    rtype = r.get("type")
    if types and rtype not in types:
        continue
    msg = r.get("message") or {}
    content = msg.get("content")
    parts = []
    if isinstance(content, str):
        parts.append(("text", content))
    elif isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            k = c.get("type")
            if k == "text":
                parts.append(("text", c.get("text", "")))
            elif k == "tool_use":
                parts.append(("tool_use", json.dumps(c.get("input"), ensure_ascii=False)))
            elif k == "tool_result":
                cc = c.get("content")
                if isinstance(cc, str):
                    parts.append(("tool_result", cc))
                elif isinstance(cc, list):
                    parts.append(("tool_result", " ".join(x.get("text", "") for x in cc if isinstance(x, dict))))
    for kind, text in parts:
        if kinds and kind not in kinds:
            continue
        for m in rx.finditer(text):
            count += 1
            if count > mx:
                break
            a, b = max(0, m.start() - ctx), min(len(text), m.end() + ctx)
            snippet = text[a:b].replace("\n", " | ")
            print(f"[{count}] {r.get('timestamp')} type={rtype} kind={kind} uuid={str(r.get('uuid'))[:8]}")
            print("   ", snippet)
            break
    if count > mx:
        break
print(f"# {min(count, mx)} match(es) shown")
