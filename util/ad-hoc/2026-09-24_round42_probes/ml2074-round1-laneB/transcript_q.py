#!/usr/bin/env python3
"""transcript_q.py JSONL [--ts TIMESTAMP] [--grep REGEX] [--max N]
Split records on "\n" (never splitlines). Print records matching the timestamp exactly, or records whose
serialized text matches REGEX, showing only the question/answer-bearing fields, truncated.
Prints no environment, no tool outputs beyond the matched text window."""
import json
import re
import sys

args = sys.argv[1:]
path = args[0]
ts = None
rx = None
mx = 20
width = 6000
if "--ts" in args:
    ts = args[args.index("--ts") + 1]
if "--grep" in args:
    rx = re.compile(args[args.index("--grep") + 1])
if "--max" in args:
    mx = int(args[args.index("--max") + 1])
if "--w" in args:
    width = int(args[args.index("--w") + 1])

raw = open(path, encoding="utf-8").read()
records = raw.split("\n")
print(f"# {len(records)} records")
shown = 0
for idx, rec in enumerate(records):
    if not rec.strip():
        continue
    try:
        d = json.loads(rec)
    except Exception:
        continue
    t = d.get("timestamp", "")
    if ts and t != ts:
        continue
    blob = json.dumps(d, ensure_ascii=False)
    if rx and not rx.search(blob):
        continue
    shown += 1
    print(f"=== record {idx} ts={t} type={d.get('type')} role={(d.get('message') or {}).get('role')}")
    msg = d.get("message") or {}
    content = msg.get("content")
    out = []
    if isinstance(content, str):
        out.append(content)
    elif isinstance(content, list):
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text":
                out.append("[text] " + c.get("text", ""))
            elif c.get("type") == "tool_use":
                out.append("[tool_use " + str(c.get("name")) + "] " + json.dumps(c.get("input"), ensure_ascii=False))
            elif c.get("type") == "tool_result":
                cc = c.get("content")
                if isinstance(cc, list):
                    cc = " ".join(x.get("text", "") for x in cc if isinstance(x, dict))
                out.append("[tool_result] " + str(cc))
    tur = d.get("toolUseResult")
    if tur is not None:
        out.append("[toolUseResult] " + json.dumps(tur, ensure_ascii=False))
    text = "\n".join(out)
    if rx:
        # show windows around matches
        for m in list(rx.finditer(text))[:6]:
            a = max(0, m.start() - width // 2)
            print("   ..." + text[a : m.end() + width // 2] + "...")
    else:
        print(text[:width])
    if shown >= mx:
        break
