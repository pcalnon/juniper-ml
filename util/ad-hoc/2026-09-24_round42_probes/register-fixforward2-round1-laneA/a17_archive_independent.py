#!/usr/bin/env python3
"""Lane A: independent check that each archived round-42 report equals its agent's final message.

My own parser, not the repo script's: for each report whose header names an agent and session, find
agent-<id>.jsonl anywhere under ~/.claude/projects/*/<session-uuid>/subagents/ (the session uuid resolved by
prefix from the directory names, not from the script's table), group ALL assistant rows by message.id, and
take the text blocks of the LAST message id in file order (a message split across rows is reassembled).
Also reports how many transcript copies exist per agent (a moved session could leave two).
"""
import json
import pathlib
import re

S = pathlib.Path(__file__).resolve().parent
OUT = S / "eco/juniper-ml/reports/2026-09-24_defect-register-round-42"
PROJ = pathlib.Path.home() / ".claude/projects"
HDR = re.compile(r"^<!-- Archived verbatim \S+ from subagent (a[0-9a-f]{16}) of session ([0-9a-f]{8}) \(final message\)\. -->\n\n")

ok = bad = 0
for f in sorted(OUT.glob("*.md")):
    text = f.read_text(encoding="utf-8")
    m = HDR.match(text)
    if not m:
        continue
    aid, sess = m.group(1), m.group(2)
    copies = sorted(PROJ.glob(f"*/{sess}*/subagents/agent-{aid}.jsonl"))
    if not copies:
        print(f"  NOFILE {f.name}")
        bad += 1
        continue
    finals = set()
    for c in copies:
        order, texts = [], {}
        for line in c.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("type") != "assistant":
                continue
            mid = r["message"].get("id") or id(r)
            if mid not in texts:
                order.append(mid)
                texts[mid] = []
            texts[mid].extend(b.get("text", "") for b in r["message"]["content"] if b.get("type") == "text")
        last = next(mid for mid in reversed(order) if any(t.strip() for t in texts[mid]))
        finals.add("\n".join(t for t in texts[last] if t))
    body = text[m.end():].rstrip("\n")
    same = [fin.rstrip("\n") == body for fin in finals]
    status = "OK" if all(same) else "DIFFER"
    ok += status == "OK"
    bad += status != "OK"
    print(f"  {status:6} {f.name} (copies={len(copies)}, distinct finals={len(finals)})")
print(f"OK {ok}, not OK {bad}")
