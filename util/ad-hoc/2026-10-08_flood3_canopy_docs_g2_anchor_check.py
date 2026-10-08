#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice, group G2)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. Every markdown link with a `#fragment` on an ADDED line of `git diff`
# in <repo> is resolved against the GitHub-style heading slugs of its target file (same file
# when the link has no path). Exists because `juniper-check-doc-links` 0.1.x passed a deliberately
# broken cross-file anchor in a mutation check, so it cannot vouch for anchors.
# Usage: 2026-10-08_flood3_canopy_docs_g2_anchor_check.py <repo>
"""Resolve the anchors of links added in a working-tree diff."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"\]\(([^)\s]*#[^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def slugs(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    out: set[str] = set()
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        # CommonMark: any ``` line OPENS a fence, but only a BARE ``` line (no info string)
        # closes one. Toggling on every ``` line inverted the state inside
        # docs/ci_cd/CICD_REFERENCE.md, where a ```text line sits inside a ```yaml block,
        # and every heading after it read as code (fixed by canopy-docs, 2026-10-08).
        stripped = line.strip()
        if not in_fence and stripped.startswith("```"):
            in_fence = True
            continue
        if in_fence:
            if re.fullmatch(r"```+", stripped):
                in_fence = False
            continue
        m = HEADING.match(line)
        if not m:
            continue
        text = m.group(2)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> text
        text = text.replace("`", "").replace("*", "")
        slug = re.sub(r"[^\w\- ]", "", text.lower(), flags=re.UNICODE).replace(" ", "-")
        n = seen.get(slug, 0)
        out.add(slug if n == 0 else f"{slug}-{n}")
        seen[slug] = n + 1
    return out


def main(argv: list[str]) -> int:
    repo = Path(argv[0])
    diff = subprocess.run(["git", "-C", str(repo), "diff", "-U0"], capture_output=True, text=True, check=True).stdout
    current = None
    bad = 0
    checked = 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = repo / line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++") or current is None:
            continue
        for target in LINK.findall(line):
            ref, _, frag = target.partition("#")
            if ref.startswith("http"):
                continue
            tfile = (current.parent / ref).resolve() if ref else current
            checked += 1
            if not tfile.is_file():
                print(f"MISSING FILE  {current.relative_to(repo)} -> {target}")
                bad += 1
            elif frag not in slugs(tfile):
                print(f"BAD ANCHOR    {current.relative_to(repo)} -> {target}")
                bad += 1
    print(f"checked {checked} anchored links, {bad} bad")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
