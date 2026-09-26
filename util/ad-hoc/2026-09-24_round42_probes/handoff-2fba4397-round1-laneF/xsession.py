#!/usr/bin/env python3
"""Dump cross-session messages from a session transcript (JSONL).

Usage: xsession.py <transcript.jsonl> <out.txt> [--grep REGEX]
Writes every user-type record whose text contains '<cross-session-message' to out.txt,
with its timestamp, and prints a one-line index (timestamp, sender attrs, length).
"""
import json
import re
import sys

path, out = sys.argv[1], sys.argv[2]
rx = None
if "--grep" in sys.argv:
    rx = re.compile(sys.argv[sys.argv.index("--grep") + 1], re.IGNORECASE)
with open(path, encoding="utf-8") as fh:
    raw = fh.read()
n = 0
with open(out, "w", encoding="utf-8") as fo:
    for line in raw.split("\n"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("type") != "user":
            continue
        msg = r.get("message") or {}
        content = msg.get("content")
        texts = []
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    if c.get("type") == "text":
                        texts.append(c.get("text", ""))
                    elif c.get("type") == "tool_result":
                        cc = c.get("content")
                        if isinstance(cc, str):
                            texts.append(cc)
                        elif isinstance(cc, list):
                            texts.extend(x.get("text", "") for x in cc if isinstance(x, dict))
        text = "\n".join(texts)
        if "<cross-session-message" not in text:
            continue
        if rx and not rx.search(text):
            continue
        n += 1
        head = re.search(r"<cross-session-message[^>]*>", text)
        print(f"{n:3d} {r.get('timestamp')} len={len(text)} {head.group(0)[:200] if head else ''}")
        fo.write(f"\n===== #{n} {r.get('timestamp')} =====\n")
        fo.write(text)
        fo.write("\n")
print(f"# {n} cross-session message record(s) -> {out}")
