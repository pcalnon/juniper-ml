#!/usr/bin/env python3
"""Lane A: print the head tree's line at each file:line the PR body cites."""

from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneA/head")
REFS = [
    "juniper_data/storage/base.py:547",
    "juniper_data/storage/local_fs.py:98",
    "juniper_data/storage/local_fs.py:183",
    "juniper_data/storage/local_fs.py:105",
    "juniper_data/storage/constants.py:44",
    "juniper_data/storage/constants.py:49",
    "juniper_data/api/app.py:237",
    "juniper_data/api/app.py:43",
    "juniper_data/api/routes/datasets.py:552",
    "juniper_data/api/routes/datasets.py:1156",
    "juniper_data/api/routes/datasets.py:1164",
]
for ref in REFS:
    path, line = ref.rsplit(":", 1)
    text = (HEAD / path).read_text(encoding="utf-8").splitlines()[int(line) - 1]
    print(f"{ref:45} {text.strip()[:120]}")
