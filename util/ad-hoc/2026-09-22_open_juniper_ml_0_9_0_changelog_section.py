#!/usr/bin/env python3
"""Move juniper-ml's CHANGELOG [Unreleased] bullets into a released [0.9.0] section.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-ml 0.9.0 release proposal)

Why this exists
---------------
``propose.py`` generates a release proposal only for ``UNRELEASED_CHANGES`` packages. juniper-ml
is ``BUMPED_NOT_RELEASED`` — ml#1991 already moved ``pyproject.toml`` to 0.9.0 and the
``AGENTS.md`` header with it — so ``propose.py`` proposes nothing and the remaining third of the
standard three-file shape has to be hand-authored.

``ceremony.py`` HALTS with ``changelog-section-missing`` until a non-empty ``## [0.9.0]`` section
exists, because that section is what it renders BOTH the published Release body and the archived
notes from. Verified by dry run before writing this.

Keeps an empty ``## [Unreleased]`` above the new section, which is what every prior release in
this file does and what ``propose.py`` emits for the packages it does handle.

Idempotent: exits 0 without writing if a ``[0.9.0]`` section already exists.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CHANGELOG = _REPO / "CHANGELOG.md"

_VERSION = "0.9.0"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--release-date", default="2026-09-22", help="ISO date for the section heading")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    text = _CHANGELOG.read_text(encoding="utf-8")
    heading = f"## [{_VERSION}] - {args.release_date}"

    if f"## [{_VERSION}]" in text:
        print(f"[{_VERSION}] section already present; nothing to do")
        return 0

    anchor = "## [Unreleased]\n"
    if text.count(anchor) != 1:
        print(f"ERROR: expected exactly one '## [Unreleased]', found {text.count(anchor)}", file=sys.stderr)
        return 1

    start = text.index(anchor)
    body_start = start + len(anchor)
    try:
        next_section = text.index("\n## [", body_start)
    except ValueError:
        print("ERROR: no following '## [' section to bound [Unreleased]", file=sys.stderr)
        return 1

    body = text[body_start:next_section].strip("\n")
    if not body:
        print("ERROR: [Unreleased] is empty — nothing to release", file=sys.stderr)
        return 1

    if args.check:
        print(f"WOULD MOVE {len(body.splitlines())} lines from [Unreleased] into {heading}")
        return 1

    rebuilt = anchor + "\n" + heading + "\n\n" + body + "\n"
    text = text[:start] + rebuilt + text[next_section:]

    _CHANGELOG.write_text(text, encoding="utf-8")
    print(f"opened {heading} with {len(body.splitlines())} lines; [Unreleased] left empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
