#!/usr/bin/env python3
"""Compare the worktree's untracked #2089 files with PR #2089's head blobs (read-only; git show only)."""
import subprocess
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
HEAD = "a2fa3ad830623528ad4737cbd2cad03c4be51c12"
paths = [p for p in (W / "util/ad-hoc/2026-09-24_round42_probes").rglob("*") if p.is_file()]
paths += [W / "util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py", W / "util/ad-hoc/2026-09-24_open_round42_session2fba4397_probes_pr.py"]
same = diff = missing = 0
for p in sorted(paths):
    rel = p.relative_to(W).as_posix()
    r = subprocess.run(["git", "-C", str(W), "show", f"{HEAD}:{rel}"], capture_output=True)
    if r.returncode != 0:
        missing += 1
        print("NOT ON PR:", rel)
        continue
    if r.stdout == p.read_bytes():
        same += 1
    else:
        diff += 1
        print("DIFFERS:", rel, "local", len(p.read_bytes()), "pr", len(r.stdout))
print(f"same={same} differ={diff} not_on_pr={missing} total={len(paths)}")
