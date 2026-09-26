#!/usr/bin/env python3
"""Round 4 lane F probe: look for any file (any name, any extension, under 200 KB) whose sha256
starts 62f9b2bf -- the 00:21Z draft of document 2 that handoff-2fba4397-round2-laneO-amputation.md
cites by line as PEER. Searches the session scratchpad, the happy-skipping-hollerith worktree's
prompts/ and reports/, and fizzy's reports/. Read-only."""
import hashlib
import os

ROOTS = [
    "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad",
    "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/prompts",
    "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith/reports",
    "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports",
]
SKIP = {"primer-venv", "venv", ".venv", "node_modules", "__pycache__", "site-packages", ".git"}
n = 0
hits = []
for root in ROOTS:
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            full = os.path.join(dp, f)
            try:
                if os.path.islink(full) or os.path.getsize(full) > 200_000:
                    continue
                with open(full, "rb") as fh:
                    b = fh.read()
            except OSError:
                continue
            n += 1
            if hashlib.sha256(b).hexdigest().startswith("62f9b2bf"):
                hits.append(full)
print("files hashed:", n)
print("62f9b2bf hits:", hits)
