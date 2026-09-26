#!/usr/bin/env python3
"""Round 4 lane F probe: print the lines of the round-42 reports that contain given needles.
Usage: context.py <report-glob> <needle> [<needle> ...]   (read-only; redacts email-shaped text)"""
import glob
import os
import re
import sys

D = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
pattern, needles = sys.argv[1], sys.argv[2:]
for path in sorted(glob.glob(os.path.join(D, pattern))):
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if any(n in line for n in needles):
                print(f"{os.path.basename(path)}:{i}: {EMAIL.sub('<REDACTED>', line.rstrip())[:400]}")
