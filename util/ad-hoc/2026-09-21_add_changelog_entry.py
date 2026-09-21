#!/usr/bin/env python3
"""Insert the README-compat-table changelog entry under [Unreleased] -> ### Fixed.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (decision-11 floor record repair)

Scripted rather than hand-edited so the change survives a rebase onto a moved main --
CHANGELOG.md is the single most contended file in this repo, and a held-open PR that
re-uploads it whole reverts whatever merged underneath. See HANDOFF_2026-09-12 section 4.

Idempotent: exits 0 without writing if the entry is already present.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CHANGELOG = _REPO / "CHANGELOG.md"

_MARKER = "README.md's `Ecosystem Compatibility` pin table shipped to PyPI advertising the 0.6.0 floors"

_ENTRY = """- **{marker}.** The file carries TWO
  pin tables and only one was guarded. `tests/test_pyproject_extras.py` pinned the
  "Available Extras" table to `pyproject.toml`, so that one tracked the decision-11 bump
  correctly; the flat `| Package | Pin |` table forty lines above it was not covered by any
  test and was last touched at 0.6.0. It named that version in its own lead-in sentence
  ("The pyproject pins matching `juniper-ml` 0.6.0"), carried five stale floors
  (`juniper-canopy>=0.5.0` for `>=0.7.0`, `juniper-cascor>=0.5.0` for `>=0.11.0`,
  `juniper-data>=0.6.0` for `>=0.14.0`, `juniper-data-client>=0.4.1` for `>=0.5.0`,
  `juniper-cascor-client>=0.5.0` for `>=0.8.0`) and omitted five packages outright
  (`juniper-model-core`, `juniper-service-core`, and the whole `[recurrence]` trio).
  **`README.md` is the `long_description`**, so those rows are what
  pypi.org/project/juniper-ml served for 0.8.0 -- verified from the published wheel's
  `METADATA`, not the checkout, where line 82 reads "matching `juniper-ml` 0.6.0" while
  line 136 of the same document lists the correct `[servers]` floors. Two tables in one
  published page, disagreeing. Table regenerated from `pyproject.toml` by
  `util/ad-hoc/2026-09-21_sync_readme_compat_table.py` (15 packages, version 0.8.0), and
  `ReadmeCompatTableTest` added to the existing `tests/test_pyproject_extras.py` -- the
  existing suite, deliberately, because juniper-ml's CI regression list is hand-maintained
  and a new `tests/test_*.py` would never be invoked. Three mutations confirm the guard is
  not vacuous: a reverted pin, a stale lead-in version, and a deleted row each fail it.
""".format(
    marker=_MARKER
)


def main() -> int:
    text = _CHANGELOG.read_text(encoding="utf-8")

    if _MARKER in text:
        print("changelog entry already present; nothing to do")
        return 0

    anchor = "## [Unreleased]"
    if anchor not in text:
        print("ERROR: no [Unreleased] section", file=sys.stderr)
        return 1

    head, _, tail = text.partition(anchor)
    fixed = "\n### Fixed\n\n"
    if fixed not in tail:
        print("ERROR: no '### Fixed' under [Unreleased]", file=sys.stderr)
        return 1

    before, _, after = tail.partition(fixed)
    text = head + anchor + before + fixed + _ENTRY + "\n" + after

    _CHANGELOG.write_text(text, encoding="utf-8")
    print("inserted changelog entry under [Unreleased] -> ### Fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
