"""Word counts of the Goal section (from '## Goal' to the next '## ') and the whole document, r2 vs r3."""
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
for name in ("handoff_session_r2_frozen.md", "handoff_session_r3_frozen.md"):
    lines = (S / name).read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith("## Goal"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    goal = " ".join(lines[start:end])
    print(f"{name}: Goal L{start + 1}-L{end} = {len(goal.split())} words; whole document {len(' '.join(lines).split())} words")
