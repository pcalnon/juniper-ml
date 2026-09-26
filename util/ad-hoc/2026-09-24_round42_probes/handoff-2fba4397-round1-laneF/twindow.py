#!/usr/bin/env python3
"""Dump every record of a transcript between two ISO timestamps, any type, raw-ish.

Usage: twindow.py <transcript.jsonl> START END [--grep REGEX] [--chars N]
"""
import json
import re
import sys

args = sys.argv[1:]
path, start, end = args[0], args[1], args[2]
chars = 1500
rx = None
if "--chars" in args:
    chars = int(args[args.index("--chars") + 1])
if "--grep" in args:
    rx = re.compile(args[args.index("--grep") + 1], re.IGNORECASE)
with open(path, encoding="utf-8") as fh:
    raw = fh.read()
for line in raw.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    ts = r.get("timestamp") or ""
    if not (start <= ts <= end):
        continue
    blob = json.dumps(r, ensure_ascii=False)
    if rx and not rx.search(blob):
        continue
    print(f"--- {ts} type={r.get('type')} subtype={r.get('subtype')} uuid={str(r.get('uuid'))[:8]}")
    print(blob[:chars])
