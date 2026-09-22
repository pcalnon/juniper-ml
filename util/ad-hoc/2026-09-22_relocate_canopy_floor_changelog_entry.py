#!/usr/bin/env python3
"""Move the canopy-floor CHANGELOG entry out of [0.8.0] and into [Unreleased], and add #1987.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-ml 0.9.0 release, mis-placed entry repair)

Why this exists
---------------
``util/ad-hoc/2026-09-21_add_canopy_floor_changelog.py`` had a scoping bug. It did::

    head, _, tail = text.partition("## [Unreleased]")
    if "\\n### Changed\\n\\n" in tail:
        before, _, after = tail.partition("\\n### Changed\\n\\n")

``tail`` is the whole REST OF THE FILE, not the [Unreleased] section, so ``partition`` found
the first ``### Changed`` anywhere below -- which was inside the already-released
``## [0.8.0] - 2026-09-11`` section. The canopy floor entry landed there (ml#1991).

Two consequences, both caught before the 0.9.0 ceremony ran:

1. The 0.9.0 Release notes would have **omitted the floor change** -- the entire point of
   the release -- because ``ceremony.py`` renders from the ``## [<version>]`` section and a
   Release body is not re-cuttable.
2. The published 0.8.0's section now documents a floor that 0.8.0 does **not** carry.
   0.8.0 shipped ``juniper-canopy>=0.7.0``.

This moves the block verbatim into [Unreleased] and adds the one other shippable change
since v0.8.0 that had no entry: ml#1987, which added the pin-capping rule comment
(APD-ML-001) to ``pyproject.toml``. Comment-only, so it reaches no wheel metadata -- said
plainly rather than dressed up.

The search is bounded to the [Unreleased] slice this time, and every anchor must match
exactly once.

Idempotent: exits 0 without writing if the entry is already inside [Unreleased].
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CHANGELOG = _REPO / "CHANGELOG.md"

_ENTRY_MARKER = "`[servers]` now floors `juniper-canopy>=0.8.1`"

_PIN_RULE_ENTRY = """- **The pin-capping rule is now stated beside the pins** (#1987, APD-ML-001). `pyproject.toml`
  gained a comment block recording why some first-party pins carry a `<` ceiling and some do
  not: shared LIBRARIES a consumer imports are capped, so a breaking `0.(Y+1)` cannot be
  auto-adopted, while the rest are floored only. Comment-only — it reaches no wheel metadata
  and changes no resolution; it exists so the next reader cannot mistake the asymmetry for
  an oversight.
"""


def _unreleased_bounds(text: str) -> tuple[int, int]:
    start = text.index("## [Unreleased]")
    nxt = text.index("\n## [", start + 1)
    return start, nxt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    text = _CHANGELOG.read_text(encoding="utf-8")
    start, end = _unreleased_bounds(text)

    if _ENTRY_MARKER in text[start:end]:
        print("canopy entry is already inside [Unreleased]; nothing to do")
        return 0

    if _ENTRY_MARKER not in text:
        print("ERROR: canopy entry not found anywhere in CHANGELOG.md", file=sys.stderr)
        return 1

    # Carve the misplaced "### Changed\n\n<entry>\n" block out of the released section.
    entry_pos = text.index(_ENTRY_MARKER)
    block_start = text.rindex("\n### Changed\n\n", start, entry_pos)
    # The block ends at the next heading of any level after the entry.
    tail_from_entry = text[entry_pos:]
    offsets = [tail_from_entry.index(h) for h in ("\n### ", "\n## ") if h in tail_from_entry]
    if not offsets:
        print("ERROR: could not find the heading that terminates the misplaced block", file=sys.stderr)
        return 1
    block_end = entry_pos + min(offsets)

    block = text[block_start:block_end]
    if _ENTRY_MARKER not in block:
        print("ERROR: carved block does not contain the entry; refusing to guess", file=sys.stderr)
        return 1

    if args.check:
        print(f"WOULD MOVE a {len(block)}-char '### Changed' block from the released section into [Unreleased]")
        return 1

    # Remove it from the released section first, then re-anchor against the updated text.
    text = text[:block_start] + text[block_end:]
    start, end = _unreleased_bounds(text)

    # Keep-a-Changelog order: Changed goes ahead of the first Fixed inside [Unreleased].
    fixed_rel = text[start:end].index("\n### Fixed\n")
    insert_at = start + fixed_rel

    entry_body = block.split("\n### Changed\n\n", 1)[1].rstrip("\n")
    new_block = "\n### Changed\n\n" + entry_body + "\n\n" + _PIN_RULE_ENTRY

    text = text[:insert_at] + new_block + text[insert_at:]
    _CHANGELOG.write_text(text, encoding="utf-8")
    print("moved the canopy floor entry into [Unreleased] and added the #1987 pin-rule entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
