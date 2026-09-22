#!/usr/bin/env python3
"""Backfill the juniper-data [Unreleased] section with three undocumented image changes.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-data 0.15.0 release, trap-7 backfill)

Why this exists
---------------
Trap 7 of the release-train ceremony: ``ceremony.py`` renders BOTH the published GitHub
Release body and the archived notes from the package CHANGELOG's ``## [<version>]``
section, and **a Release body is not re-cuttable**. Whatever that section says at
``--execute`` time ships permanently.

Diffing ``git log v0.14.0..HEAD`` against the section found three behavioural changes with
zero coverage. They matter because a juniper-data Release mints a **container image** as
well as a wheel, and all three change what is inside that image:

- **#405** added ``**/tests/`` and ``**/reports/`` to ``.dockerignore``. The published
  0.14.0 image carried the whole test suite, because ``COPY juniper_data/`` is a
  DIRECTORY allowlist.
- **#408** added ``secrets/``, ``*.key``, ``*.pem``, ``.env`` and ``.env.*`` exclusions,
  plus ``util/check_image_no_secrets.py`` asserted on the smoke AND publish paths, and
  re-enabled the app-import smoke for releases.
- **#392 / #394** moved the ``juniper-ci-tools`` floor and ceiling.

Counts are taken from #408, which corrected #405's own figure by recounting inside the
pulled artifact: **87 named ``test_*.py``, 95 ``.py``, 190 files total** -- not the 22 that
#405's commit message states.

This writes to a ``--root`` COPY, never the sibling checkout, because ~20 concurrent
sessions share those working trees.

Idempotent: exits 0 without writing if the backfill is already present.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_MARKER = "the published image carried the whole test suite"

_CHANGED_SECTION = """### Changed

- **The published container image no longer carries the test suite** (#405). `COPY
  juniper_data/ ./juniper_data/` is a DIRECTORY allowlist, not a file-grained one, and
  `.dockerignore` had no tests rule -- so `juniper-data:0.14.0` shipped its whole suite.
  Measured inside the pulled artifact rather than inferred: **87 named `test_*.py`, 95
  `.py`, 190 files total** (#408 recounted this; #405's own message says 22).
  `juniper-canopy:0.8.0` shipped **zero**, because its `.dockerignore` already carried
  `src/tests/` -- the negative control that makes this a real gap rather than a guess. The
  `**` prefix is load-bearing and was verified against a discriminating control: a bare
  `tests/` matches the context root only and still copies nested test files.
- **`juniper-ci-tools` floor raised to `>=0.9.0` and ceiling widened to `<0.10.0`**
  (#394, #392).

"""

_FIXED_ENTRY = """- **`.dockerignore` carried no credential exclusions, and the release path never asserted
  that the app loads** (#408). Docker does not honour `.gitignore`, and the `COPY` is a
  directory allowlist, so a committed `secrets/`, `*.key`, `*.pem`, `.env` or `.env.*`
  would have shipped into a published production image. **Nothing leaked** -- the published
  0.14.0 image was pulled and inspected -- so this closes a latent gap rather than an
  incident. Adds `util/check_image_no_secrets.py`, asserted on both the smoke and publish
  paths; it walks `/app` **and** every installed `juniper*` package, because this image's
  `/app` holds only `['data']` and a top-level listing would pass vacuously, and it exits 2
  on an empty scan rather than reporting success. Also re-enables the import smoke for
  releases: the path that SHIPS previously asserted only torch posture, never that the
  application imports.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, help="path to the juniper-data tree to edit")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    target = Path(args.root) / "CHANGELOG.md"
    if not target.is_file():
        print(f"ERROR: no such file: {target}", file=sys.stderr)
        return 1

    text = target.read_text(encoding="utf-8")

    if _MARKER in text:
        print("backfill already present; nothing to do")
        return 0

    anchor = "## [Unreleased]\n\n### Fixed\n\n"
    if text.count(anchor) != 1:
        print(f"ERROR: expected exactly one '[Unreleased] -> ### Fixed' opening, found {text.count(anchor)}", file=sys.stderr)
        return 1

    if args.check:
        print(f"WOULD BACKFILL: {target}")
        return 1

    # Open a ### Changed section ahead of ### Fixed, and prepend the #408 entry to Fixed.
    replacement = "## [Unreleased]\n\n" + _CHANGED_SECTION + "### Fixed\n\n" + _FIXED_ENTRY + "\n"
    target.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
    print(f"backfilled {target}: 1 new ### Changed section (2 bullets) + 1 ### Fixed bullet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
