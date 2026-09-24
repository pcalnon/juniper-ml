#!/usr/bin/env python3
"""Lane A: APD-ML-007 -- what the release ceremony's changelog_version_section returns for
juniper-data 0.16.0 at each relevant main commit (CHANGELOG read via git show; read-only)."""
from __future__ import annotations

import re
import subprocess
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
D = "/home/pcalnon/Development/python/Juniper/juniper-data"
sys.path.insert(0, f"{S}/head/util/release_train")
sys.path.insert(0, f"{S}/head/util")
sys.path.insert(0, f"{S}/head")

try:
    import ceremony  # type: ignore
except Exception as exc:  # pragma: no cover
    from importlib import import_module
    print("direct import failed:", exc)
    ceremony = import_module("util.release_train.ceremony")

log = subprocess.run(["git", "-C", D, "log", "--first-parent", "--format=%H %cI %s", "7125e161^..origin/main"], capture_output=True, text=True, check=True).stdout.strip().splitlines()
for line in reversed(log):
    sha, when, subj = line.split(" ", 2)
    text = subprocess.run(["git", "-C", D, "show", f"{sha}:CHANGELOG.md"], capture_output=True, text=True).stdout
    heads = [(i + 1, ln) for i, ln in enumerate(text.split("\n")) if re.match(r"^##\s*\[", ln)][:4]
    n0160 = sum(1 for ln in text.split("\n") if re.match(r"^##\s*\[?0\.16\.0(\]|\s|$)", ln.strip()))
    sec = ceremony.changelog_version_section(text, "0.16.0")
    nb = {k: len(v) for k, v in sec.items()}
    # count bullets under [Unreleased]
    lines = text.split("\n")
    try:
        u = next(i for i, ln in enumerate(lines) if re.match(r"^##\s*\[Unreleased\]", ln, re.I))
        nxt = next(i for i in range(u + 1, len(lines)) if re.match(r"^##\s", lines[i]) and not lines[i].startswith("###"))
        unreleased_bullets = sum(1 for ln in lines[u + 1:nxt] if re.match(r"^\s*[-*]\s", ln) and not ln.startswith("  "))
    except StopIteration:
        unreleased_bullets = None
    print(f"== {sha[:8]} {when} {subj[:90]}")
    print(f"   version headings (first 4): {heads}")
    print(f"   '## [0.16.0]' headings: {n0160}; section bullets by category: {nb} (total {sum(nb.values())}); top-level bullets under [Unreleased]: {unreleased_bullets}")
    breaking = [b for v in sec.values() for b in v if "BREAKING" in str(b).upper()]
    print(f"   bullets mentioning BREAKING in the rendered section: {len(breaking)}")
