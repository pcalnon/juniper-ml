#!/usr/bin/env python3
"""Lane A: for each commit that touched tests/test_service_fork_drift.py, list every guard_id and
its status, by importing that revision's GUARDS registry (read via git show; nothing written to the repo)."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map"
COMMITS = ["d1ce9958", "53751fac", "132832f0", "b9629de0", "ea24a19a", "f5222f9d"]

for c in COMMITS:
    src = subprocess.run(["git", "-C", W, "show", f"{c}:tests/test_service_fork_drift.py"], capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory(dir="/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA") as d:
        p = Path(d) / f"gate_{c}.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location(f"gate_{c}", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        rows = [(g.guard_id, g.status, tuple(sorted({s.repo for s in g.sites}))) for g in mod.GUARDS]
        fork = getattr(mod, "_FORK_REPOS", None)
    subj = subprocess.run(["git", "-C", W, "log", "-1", "--format=%ad %s", "--date=iso", c], capture_output=True, text=True).stdout.strip()
    print(f"== {c} {subj}")
    print(f"   _FORK_REPOS={fork}")
    for r in rows:
        print(f"   {r[0]:30s} {r[1]:10s} sites={r[2]}")
