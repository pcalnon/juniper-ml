#!/usr/bin/env python3
"""
Insert the ml-tests carrier's CHANGELOG entry under the current `## [Unreleased]` / `### Added`.

The entry goes directly BELOW round 1's tests-carrier entry (juniper-ml#2517), the last line of which is the
anchor, so it sits below an existing entry of its subsection (BRIEF_COMMON_R2 rule 9) and next to the entry it
continues. Refuses unless the anchor occurs exactly once and lies between `## [Unreleased]` and the next
`## [` heading, inside its `### Added`. Idempotent: an entry already present is left alone.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_changelog.py <entry file>   (run from the worktree root)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)
"""

import sys
from pathlib import Path

ANCHOR = "  in `tests/test_run_suite.py`'s, each without its link to a section only the docs carrier adds.\n"


def main() -> int:
    entry = Path(sys.argv[1]).read_text(encoding="utf-8")
    path = Path("CHANGELOG.md")
    text = path.read_text(encoding="utf-8")
    if entry in text:
        print("entry already present")
        return 0
    if text.count(ANCHOR) != 1:
        raise SystemExit(f"anchor found {text.count(ANCHOR)} times")
    at = text.index(ANCHOR) + len(ANCHOR)
    unreleased = text.index("## [Unreleased]")
    next_release = text.index("\n## [", unreleased + 1)
    added = text.index("### Added", unreleased)
    following = text.find("\n### ", added + 1)
    if not unreleased < added < at <= next_release or (0 <= following < at):
        raise SystemExit("anchor is not inside [Unreleased] / ### Added")
    path.write_text(text[:at] + "\n" + entry + text[at:], encoding="utf-8")
    print(f"entry inserted at offset {at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
