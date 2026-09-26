#!/usr/bin/env python3
"""Extract a CHANGELOG '## [X]' section at several refs and compare (read-only).

Usage: cl_section.py REPO VERSION REF [REF ...]
"""
import hashlib
import subprocess
import sys

repo, version = sys.argv[1], sys.argv[2]
refs = sys.argv[3:]


def section(text: str, ver: str) -> list[str]:
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## [") and line[4:].startswith(ver + "]"):
            start = i
            break
    if start is None:
        return []
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ["):
            end = j
            break
    return lines[start:end]


for ref in refs:
    out = subprocess.run(["git", "-C", repo, "show", f"{ref}:CHANGELOG.md"], capture_output=True, text=True)
    if out.returncode != 0:
        print(ref, "ERROR", out.stderr.strip())
        continue
    sec = section(out.stdout, version)
    h = hashlib.sha256("\n".join(sec).encode()).hexdigest()[:16]
    # also count Unreleased length
    un = section(out.stdout, "Unreleased")
    print(f"{ref[:12]:12}  [{version}] lines={len(sec)} sha={h}  heading={sec[0] if sec else None!r}  [Unreleased] lines={len(un)}")
