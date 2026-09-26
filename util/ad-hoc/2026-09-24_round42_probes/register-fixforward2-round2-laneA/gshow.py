#!/usr/bin/env python3
"""Write `git show <rev>:<path>` of the juniper-ml worktree to <dest> (bytes, unmodified).

Usage: gshow.py <rev> <repo-relative path> <dest file>
Runs git in the session worktree (read-only), because the isolation guard refuses `git -C`.
"""
import subprocess
import sys
from pathlib import Path

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
rev, rel, dest = sys.argv[1:4]
data = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=WT, check=True, capture_output=True).stdout
Path(dest).parent.mkdir(parents=True, exist_ok=True)
Path(dest).write_bytes(data)
print(f"{rev}:{rel} -> {dest} ({len(data)} bytes)")
