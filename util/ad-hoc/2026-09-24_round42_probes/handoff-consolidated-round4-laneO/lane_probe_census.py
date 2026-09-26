#!/usr/bin/env python3
"""Read-only: count probe .py files per validation-lane scratch dir (root + scripts/), compare with the copier's LANES."""
import re
from pathlib import Path

SP = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
COPIER = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py")

lanes_src = re.search(r"LANES = \{(.*?)\n\}", COPIER.read_text(), re.S).group(1)
lanes = dict(re.findall(r'"([^"]+)": "([^"]+)"', lanes_src))

for top in sorted(p for p in SP.iterdir() if p.is_dir() and re.match(r"h[cv]\d", p.name)):
    for lane in sorted(p for p in top.iterdir() if p.is_dir()):
        key = f"{top.name}/{lane.name}"
        root = [f for f in lane.iterdir() if f.is_file() and f.suffix == ".py" and f.stat().st_size < 200_000]
        scr = [f for f in (lane / "scripts").iterdir() if f.is_file() and f.suffix == ".py"] if (lane / "scripts").is_dir() else []
        print(f"{key:14} py-root={len(root):3} py-scripts={len(scr):3} in-LANES={'yes -> ' + lanes[key] if key in lanes else 'NO'}")
