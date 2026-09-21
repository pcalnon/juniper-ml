#!/usr/bin/env python3
"""Insert the canopy-floor changelog entry under [Unreleased] -> ### Changed.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (canopy#631 floor correction)

Creates the ``### Changed`` subsection if [Unreleased] does not have one yet, placing it
after ``### Added`` and before ``### Fixed`` to match Keep a Changelog ordering.

Scripted rather than hand-edited because CHANGELOG.md is the most contended file in this
repo: a held-open PR that re-uploads it whole reverts whatever merged underneath, and the
doc screens cannot see it (every invocation passes ``--exclude CHANGELOG.md``).

Idempotent: exits 0 without writing if the entry is already present.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CHANGELOG = _REPO / "CHANGELOG.md"

_MARKER = "`[servers]` now floors `juniper-canopy>=0.8.1`"

_ENTRY = """- **{marker}, because every canopy wheel from 0.5.0
  through 0.8.0 cannot import its own dashboard.** Those wheels publish **zero** top-level
  modules -- `juniper_canopy/` contains only `__init__.py`, and the 19 modules canopy's own
  shipped code imports are absent, so `import backend.service_backend` dies at
  `No module named 'validation_gate'`. 0.8.1 ships all of them (juniper-canopy#631, closed
  2026-09-17). Read from the published wheels, not a checkout; 0.8.0 was checked too, so the
  boundary is exactly 0.8.0 -> 0.8.1. A default resolve already took 0.8.1 because pip prefers
  the newest, so the old floor *admitted* the broken wheels rather than delivering them -- the
  same shape as the `juniper-model-core>=0.1.0,<0.4.0` cap that
  `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §10 left alone
  as "a consumer break for no behavioural gain". The reasoning inverts here: there the admitted
  version differed only in a docstring, here it does not load. Pre-flighted against real PyPI
  before the change -- `juniper-canopy>=0.8.1` + `juniper-cascor>=0.11.0` + `juniper-data>=0.14.0`
  resolves in 60 packages with `juniper-service-core` 0.7.0 and `juniper-model-core` 0.3.2, both
  inside the existing caps. **Version bumped 0.8.0 -> 0.9.0 with it**, and not cosmetically:
  `docs/REFERENCE.md`'s compatibility matrix labels each row by the juniper-ml version carrying
  that floor set, so a new floor set needs a version to label it and the `0.8.x` row is *added
  to* rather than rewritten -- rewriting it would make it a false statement about the published
  0.8.0. Minor per the pre-1.0 convention at `util/release_train/detect.py:827`, since forbidding
  a previously-admitted version is breaking. Applied by
  `util/ad-hoc/2026-09-21_raise_canopy_floor_0_8_1.py`, which asserts each of the ten sites'
  exact text and requires exactly one match apiece.
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

    changed = "\n### Changed\n\n"
    if changed in tail:
        before, _, after = tail.partition(changed)
        tail = before + changed + _ENTRY + "\n" + after
    else:
        # No Changed subsection yet: open one before ### Fixed, else before ### Added.
        for successor in ("\n### Fixed\n\n", "\n### Added\n\n"):
            if successor in tail:
                before, _, after = tail.partition(successor)
                tail = before + changed + _ENTRY + successor + after
                break
        else:
            print("ERROR: [Unreleased] has neither ### Fixed nor ### Added to anchor against", file=sys.stderr)
            return 1

    _CHANGELOG.write_text(head + anchor + tail, encoding="utf-8")
    print("inserted changelog entry under [Unreleased] -> ### Changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
