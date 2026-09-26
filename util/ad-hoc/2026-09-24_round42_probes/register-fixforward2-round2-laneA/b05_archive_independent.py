#!/usr/bin/env python3
"""Lane A round 2: independently verify the two new archived round-1 reports against their transcripts.

My own parser: group assistant rows by message.id (a message may span several JSONL rows), take the LAST
message's text blocks in order, and compare to the archived body after its header. Also prints the header
line, the agent's final stop reason if present, and whether any later row exists after the final message.
Also exercises the archiver's new unknown-session guard (B N9) by import.
"""
import importlib.util
import json
import re
from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head")
OUT = HEAD / "reports/2026-09-24_defect-register-round-42"
PROJECTS = Path.home() / ".claude/projects"
SESSION = "2fba4397-7d9b-4929-8ca2-375b8168e1c8"
HDR = re.compile(r"^<!-- Archived verbatim (\S+) from subagent (a[0-9a-f]{16}) of session ([0-9a-f]{8}) \(final message\)\. -->\n\n")

for name, aid in (("register-fixforward2-round1-laneA-reprobe.md", "a0511a4be64379a82"), ("register-fixforward2-round1-laneB-refute.md", "a4ae44a7ce58056a9")):
    hits = sorted(PROJECTS.glob(f"*/{SESSION}/subagents/agent-{aid}.jsonl"))
    print(f"== {name}: transcript hits {len(hits)}")
    rows = [json.loads(x) for x in hits[0].read_text(encoding="utf-8").split("\n") if x.strip()]
    order, texts = [], {}
    for r in rows:
        if r.get("type") != "assistant":
            continue
        mid = r["message"].get("id")
        if mid not in texts:
            order.append(mid)
            texts[mid] = []
        for b in r["message"]["content"]:
            if b.get("type") == "text":
                texts[mid].append(b["text"])
    last_mid = order[-1]
    mine = "\n".join(texts[last_mid])
    archived = (OUT / name).read_text(encoding="utf-8")
    m = HDR.match(archived)
    print("   header:", bool(m), m.groups() if m else None)
    body = archived[m.end():]
    print("   my parse == archived body:", mine.rstrip("\n") == body.rstrip("\n"), f"({len(mine)} vs {len(body)} chars)")
    print("   file ends with exactly one newline:", archived.endswith("\n") and not archived.endswith("\n\n"))
    tail_types = [r.get("type") for r in rows[rows.index([r for r in rows if r.get("type") == "assistant"][-1]) + 1:]]
    print("   rows after the final assistant row:", tail_types)

spec = importlib.util.spec_from_file_location("arch", HEAD / "util/ad-hoc/2026-09-24_archive_round42_reports.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    mod.subagents_dir("deadbeef")
    print("unknown session: NO EXIT (defect)")
except SystemExit as e:
    print("unknown session -> SystemExit:", e)
except KeyError as e:
    print("unknown session -> KeyError (the N9 defect):", e)
