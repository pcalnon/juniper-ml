#!/usr/bin/env python3
"""Lane B: what 'Breaking changes:' verdict would notes_render give #428's section alone,
the genuine 0.16.0 section alone, and the two folded together? Read-only."""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

ML = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map")
sys.path.insert(0, str(ML / "util" / "release_train"))

import ceremony  # noqa: E402
import notes_render  # noqa: E402

base = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneB")
full = (base / "src" / "CHANGELOG.md").read_text(encoding="utf-8")
second_only = (base / "changelog_second_0160_only.md").read_text(encoding="utf-8")

first = ceremony.changelog_version_section(full, "0.16.0")
second = ceremony.changelog_version_section(second_only, "0.16.0")
folded: OrderedDict = OrderedDict()
for sec in (first, second):
    for k, v in sec.items():
        folded.setdefault(k, []).extend(v)

print("first (#428 only) is_breaking:", notes_render._is_breaking(first), "cats:", list(first))
print("second (genuine 0.16.0) is_breaking:", notes_render._is_breaking(second), "cats:", list(second))
print("folded is_breaking:", notes_render._is_breaking(folded), "cats:", list(folded))
