#!/usr/bin/env python3
"""List every cross-session message in a transcript, whatever record shape carried it.

Covers: user records (text), queue-operation enqueue records (content), and
attachment records of type queued_command (prompt). De-duplicates by body text.
Also lists outgoing SendMessage tool_use calls. Writes full bodies to OUT.

Usage: xsession2.py <transcript.jsonl> OUT [--since ISO] [--until ISO]
"""
import json
import re
import sys

path, out = sys.argv[1], sys.argv[2]
since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else ""
until = sys.argv[sys.argv.index("--until") + 1] if "--until" in sys.argv else "9999"
with open(path, encoding="utf-8") as fh:
    raw = fh.read()
seen = set()
rows = []
for line in raw.split("\n"):
    if not line.strip():
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    ts = r.get("timestamp") or ""
    if not (since <= ts <= until):
        continue
    t = r.get("type")
    bodies = []
    if t == "queue-operation" and r.get("operation") == "enqueue":
        c = r.get("content")
        if isinstance(c, str) and "<cross-session-message" in c:
            bodies.append(("IN(queue)", c))
    elif t == "attachment":
        a = r.get("attachment") or {}
        p = a.get("prompt")
        if isinstance(p, str) and "<cross-session-message" in p:
            bodies.append(("IN(attach)", p))
    elif t == "user":
        msg = r.get("message") or {}
        c = msg.get("content")
        if isinstance(c, str) and c.lstrip().startswith("Another Claude session sent a message") or (isinstance(c, str) and c.lstrip().startswith("<cross-session-message")):
            bodies.append(("IN(user)", c))
        elif isinstance(c, list):
            for x in c:
                if isinstance(x, dict) and x.get("type") == "text":
                    tx = x.get("text", "")
                    if tx.lstrip().startswith("Another Claude session sent a message") or tx.lstrip().startswith("<cross-session-message"):
                        bodies.append(("IN(user)", tx))
    elif t == "assistant":
        msg = r.get("message") or {}
        c = msg.get("content")
        if isinstance(c, list):
            for x in c:
                if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") == "SendMessage":
                    inp = x.get("input") or {}
                    bodies.append(("OUT to=" + str(inp.get("to")), str(inp.get("message"))))
    for kind, body in bodies:
        m = re.search(r"<cross-session-message([^>]*)>(.*?)</cross-session-message>", body, re.S)
        core = m.group(2).strip() if m else body.strip()
        key = core[:300]
        if kind.startswith("IN") and key in seen:
            continue
        seen.add(key)
        hdr = m.group(1).strip() if m else ""
        name = re.search(r'from-name="([^"]*)"', hdr)
        rows.append((ts, kind, name.group(1) if name else "", core))
with open(out, "w", encoding="utf-8") as fo:
    for i, (ts, kind, name, core) in enumerate(rows, 1):
        print(f"{i:3d} {ts} {kind} {name} len={len(core)} :: {core[:110].replace(chr(10), ' ')}")
        fo.write(f"\n===== #{i} {ts} {kind} {name} =====\n{core}\n")
print(f"# {len(rows)} message(s) -> {out}")
