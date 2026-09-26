#!/usr/bin/env python3
"""Read-only: word counts of the Goal section (from '## Goal' to the line before the next '## ') in r3 and r4, and whole-file counts."""
from pathlib import Path

R4 = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hc4/consolidated_r4_frozen.md")
R3 = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42/handoff-frozen/handoff-consolidated-r3.md")

for name, p in (("r3", R3), ("r4", R4)):
    lines = p.read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## Goal"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    goal = lines[start:end]
    print(f"{name}: Goal L{start + 1}-L{end} = {sum(len(l.split()) for l in goal)} words (heading excluded: {sum(len(l.split()) for l in goal[1:])}); whole file {sum(len(l.split()) for l in lines)} words")
