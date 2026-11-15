#!/usr/bin/env python3
"""Move a Python 3.15 CHANGELOG entry from a just-released section back under [Unreleased] (cascor#759, canopy#819).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (phase 1 of the Python 3.15 migration, juniper-cascor#759)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#758 (the v0.14.0 release proposal, merged 2026-11-15T01:15:14Z under the open #759) and
         juniper-canopy#818 (v0.10.0, merged 01:20:20Z under the open #819);
         util/ad-hoc/2026-11-14_py315_informational_juniper-cascor.py (the edits #759 carries)

Why this exists
---------------
#759 added its entry under ``## [Unreleased]`` / ``### Added``. #758 then renamed that section ``## [0.14.0]`` and
opened a fresh, empty ``[Unreleased]`` above it, so the server-side update-branch merge put #759's entry inside the
0.14.0 release, which does not contain the change. This cuts exactly that entry (from its bold lead to the next
top-level bullet) out of ``[0.14.0]`` and puts it under a new ``### Added`` in ``[Unreleased]``; every other byte is
kept. It refuses unless each anchor occurs exactly once.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_cascor_changelog_relocate.py <CHANGELOG.md>   # cascor#759 (defaults)
    python3 util/ad-hoc/2026-11-15_py315_cascor_changelog_relocate.py <CHANGELOG.md> \
        --entry-lead "- **CI runs the unit tests on Python 3.15 as well, as an informational leg that blocks nothing.**" \
        --next-lead "- **Regression tests harvested from the Cursor flood-4 test PRs**" --release "## [0.10.0] - 2026-11-15"
                                                                                          # canopy#819
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ENTRY_LEAD = "- **CI runs the tests on Python 3.15 as well, as informational legs that block nothing.**"
NEXT_LEAD = "- **API addition: `WebSocketManager.promote_to_active("
RELEASE = "## [0.14.0] - 2026-11-15"


def relocate(text: str, entry_lead: str = ENTRY_LEAD, next_lead: str = NEXT_LEAD, release: str = RELEASE) -> str:
    unreleased = f"## [Unreleased]\n\n{release}\n\n### Added\n\n"
    for anchor in (entry_lead, next_lead, unreleased):
        if text.count(anchor) != 1:
            raise SystemExit(f"anchor occurs {text.count(anchor)} times, want 1: {anchor[:60]!r}")
    start = text.index(entry_lead)
    end = text.index(next_lead)
    if not text.index(unreleased) + len(unreleased) == start < end:
        raise SystemExit("layout differs from the expected [Unreleased] / [0.14.0] / ### Added / entry order")
    entry = text[start:end]
    without = text[:start] + text[end:]
    moved = "## [Unreleased]\n\n### Added\n\n" + entry + f"\n{release}\n\n### Added\n\n"
    out = without.replace(unreleased, moved, 1)
    # The move adds exactly one "### Added" heading and two blank lines (after that heading, and between the moved
    # entry and the [0.14.0] heading); every other line must survive unchanged.
    delta = Counter(out.splitlines())
    delta.subtract(Counter(text.splitlines()))
    if {k: v for k, v in delta.items() if v} != {"### Added": 1, "": 2}:
        raise SystemExit(f"line multiset changed beyond one heading and two blank lines: {dict(delta)}; refusing")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("changelog", type=Path)
    ap.add_argument("--entry-lead", default=ENTRY_LEAD)
    ap.add_argument("--next-lead", default=NEXT_LEAD)
    ap.add_argument("--release", default=RELEASE, help="the released section heading the entry was filed under")
    args = ap.parse_args()
    path = args.changelog
    out = relocate(path.read_text(encoding="utf-8"), args.entry_lead, args.next_lead, args.release)
    path.write_text(out, encoding="utf-8")
    print(f"relocated the 3.15 entry under [Unreleased] in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
