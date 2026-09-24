#!/usr/bin/env python3
"""Lane A: APD-ML-007 -- would the ceremony's rendered 0.16.0 notes say "Breaking changes: NO"?
Runs the PR head's notes_render._is_breaking on the section changelog_version_section returns,
at each main commit between #428 and #435 (CHANGELOG via git show; read-only)."""
from __future__ import annotations

import re
import subprocess
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
D = "/home/pcalnon/Development/python/Juniper/juniper-data"
sys.path.insert(0, f"{S}/head/util/release_train")
import ceremony  # type: ignore  # noqa: E402
import notes_render  # type: ignore  # noqa: E402

for sha in ["7125e161", "af7831be", "35b44cc1", "3a76a4c5", "39d1cab2"]:
    text = subprocess.run(["git", "-C", D, "show", f"{sha}:CHANGELOG.md"], capture_output=True, text=True, check=True).stdout
    sec = ceremony.changelog_version_section(text, "0.16.0")
    print(f"== {sha}: categories={list(sec.keys())} bullets={sum(len(v) for v in sec.values())} _is_breaking={notes_render._is_breaking(sec)}")
    for cat, bullets in sec.items():
        for b in bullets:
            first = str(b).split("\n")[0]
            mark = notes_render._has_breaking_marker(str(b))
            print(f"   [{cat}] marker={mark} :: {first[:150]}")
