#!/usr/bin/env python3
"""Round 4 lane F probe: word counts of the Goal (## Goal heading up to ## Key context) in r3 and r4,
and of the whole document; also the header's Written line vs the file's mtime."""
import os
import datetime

R4 = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hc4/consolidated_r4_frozen.md"
R3 = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42/handoff-frozen/handoff-consolidated-r3.md"
LIVE = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md"

for name, path in (("r3", R3), ("r4", R4)):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    g = next(i for i, ln in enumerate(lines) if ln.startswith("## Goal"))
    k = next(i for i, ln in enumerate(lines) if ln.startswith("## Key context"))
    incl = sum(len(ln.split()) for ln in lines[g:k])
    excl = sum(len(ln.split()) for ln in lines[g + 1:k])
    total = sum(len(ln.split()) for ln in lines)
    print(f"{name}: Goal L{g+1}-L{k} incl heading {incl} words, excl heading {excl}; whole doc {total} words; lines {len(lines)}")
for p in (LIVE, R4):
    print(datetime.datetime.fromtimestamp(os.stat(p).st_mtime, datetime.timezone.utc).isoformat(), os.path.basename(p))
