#!/usr/bin/env python3
"""List CHANGELOG bullets filed under a RELEASED version that its archived release notes do not carry.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release-train verification
Author:      Paul Calnon
Created:     2026-09-23
Version:     0.1.0
License:     MIT License
Status:      single-use (the juniper-ml 0.10.0 ceremony pre-flight)

Why this exists
---------------
A PR authored against ``## [Unreleased]`` that merges AFTER a release moved ``[Unreleased]`` into
``## [<version>]`` lands its bullets under the RELEASED heading, with no merge conflict
(memory: reference_release_cut_under_an_open_pr_changelog_automerges_silently). juniper-ml#2002
merged 22 minutes after v0.9.0 was tagged and filed four bullets that way. The CHANGELOG then claims
0.9.0 shipped work that v0.9.0 does not contain, and the NEXT release's notes -- rendered from its
own section -- never mention it.

The archived ``notes/releases/RELEASE_NOTES_v<version>.md`` is the record of what the Release said,
and it cannot drift (a Release body is not re-cuttable). So: parse the CHANGELOG section with the
ceremony's own parser, and report every bullet whose first line is absent from the archive.

Usage
-----
    python3 util/ad-hoc/2026-09-23_released_section_drift.py --changelog CHANGELOG.md \
        --archive notes/releases/RELEASE_NOTES_v0.9.0.md --version 0.9.0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "util" / "release_train"))  # the modules import each other top-level

import ceremony  # noqa: E402


def _first_line(bullet: str) -> str:
    return bullet.splitlines()[0].strip() if bullet.strip() else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--changelog", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--version", required=True)
    args = ap.parse_args()

    sections = ceremony.changelog_version_section(Path(args.changelog).read_text(encoding="utf-8"), args.version)
    archive = Path(args.archive).read_text(encoding="utf-8")
    if not sections:
        print(f"ERROR: no [{args.version}] section in {args.changelog}")
        return 2

    total = drifted = 0
    for category, bullets in sections.items():
        for bullet in bullets:
            total += 1
            head = _first_line(bullet)
            if head and head not in archive:
                drifted += 1
                print(f"NOT IN RELEASE  [{args.version}] ### {category}: {head[:120]}")
    print(f"\n{drifted} of {total} [{args.version}] bullet(s) are absent from {args.archive}.")
    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
