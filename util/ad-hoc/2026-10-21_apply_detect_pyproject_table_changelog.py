#!/usr/bin/env python3
"""Add the release-train detector's pyproject-table fix to CHANGELOG.md's [Unreleased] ### Fixed, on a fresh copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (the CHANGELOG half of the detect.py fix; kept so a silent revert costs one re-run)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/release_train/detect.py classify_pyproject_patch; tests/test_release_train_detect.py;
         util/ad-hoc/2026-10-20_apply_w5_5_w5_6_shared_docs.py (the --check shape this follows);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-recurrence-0-8-0-published-extras-and-compose-pins-landed-plan-v1-7-12.md
         (step 3, the juniper-ml release that carries the pins, which the defect blocked)

Why
---
CHANGELOG.md is a shared, ~210 KB file that lands from turing as its own signed commit, built from a fresh
``git show origin/main:CHANGELOG.md`` copy (a whole-file upload from an older base silently reverts concurrent
PRs). The insertion point is found, not anchored on today's first entry: the first ``### Fixed`` heading inside
``## [Unreleased]``, so a concurrent PR that adds its own Fixed entry does not break a re-run.

Usage
-----
    python3 util/ad-hoc/2026-10-21_apply_detect_pyproject_table_changelog.py --root DIR [--check]

``--root`` holds ``CHANGELOG.md``. The entry goes first under [Unreleased]'s ``### Fixed``; if the section has no
``### Fixed`` heading, or holds more than one, the script refuses and writes nothing. An entry already present is
skipped, so a re-run is a no-op. ``--check`` reports applied / pending and exits 1 when pending.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER = "- **The release-train detector no longer discounts a `pyproject.toml` hunk whose table its context does not name**"

ENTRY = """\
- **The release-train detector no longer discounts a `pyproject.toml` hunk whose table its context does not name**,
  so juniper-ml reads UNRELEASED_CHANGES (0.11.0) instead of UP_TO_DATE. `util/release_train/detect.py`'s
  `classify_pyproject_patch` took a hunk's TOML table only from a `[table]` line inside the hunk or from its `@@`
  trailer, and git's default trailer is the nearest line that starts with a letter
  (`@@ -81,9 +81,9 @@ doc-tools = [`), never a `[table]`. Every changed line of a hunk more than three lines below
  its header therefore fell to the NON-SHIP default, and a later hunk inherited the previous hunk's table. Since
  v0.10.0 the `[servers]` canopy and data floors and the `[recurrence]` recurrence and model ranges have moved
  (published 0.10.0 still pins `juniper-recurrence>=0.5.0,<0.6.0`), yet the meta-package, which ships nothing but
  `pyproject.toml` (`ship_paths: []`), read UP_TO_DATE with a CHANGELOG conflict, and `propose.py` had nothing to
  propose.
  - Each hunk now takes its table and extra from the HEAD file when the hunk's new-side lines sit at its stated
    position there (the cumulative tag..HEAD patch aligns with the checkout, as for the `.py` substantive check).
    A changed line whose table stays unknown (no aligned HEAD file, or a stale checkout) is UNCERTAIN, never
    NON-SHIP, and a `[[array.of.tables]]` header now ends the table before it.
  - Measured on the seven in-repo packages against `main`'s detector: juniper-ml moves UP_TO_DATE →
    UNRELEASED_CHANGES (0.11.0) and juniper-config-tools UP_TO_DATE → UNRELEASED_CHANGES (its `Typing :: Typed`
    classifier in `[project]`, unreleased since 0.1.0; its `[Unreleased]` is empty, so the manifest flags it
    under-documented); the other five are unchanged. The daily `release-train.yml` run is in report mode, so
    nothing is proposed by itself.
  - Nine new tests in `tests/test_release_train_detect.py`, one of them on real `git diff` output; all nine fail on
    `main`'s detector.
"""


def insert_entry(text: str) -> "tuple[str | None, str]":
    """(new text, status) -- new text is None when nothing is written."""
    if MARKER in text:
        return None, "applied"
    start = re.search(r"^## \[Unreleased\][^\n]*\n", text, re.MULTILINE)
    if start is None:
        return None, "REFUSED, no ## [Unreleased] heading"
    nxt = re.search(r"^## \[", text[start.end() :], re.MULTILINE)
    end = start.end() + nxt.start() if nxt else len(text)
    fixed = list(re.finditer(r"^### Fixed[ \t]*\n\n", text[start.end() : end], re.MULTILINE))
    if len(fixed) != 1:
        return None, f"REFUSED, [Unreleased] holds {len(fixed)} '### Fixed' headings (expected 1)"
    at = start.end() + fixed[0].end()
    return text[:at] + ENTRY + "\n" + text[at:], "pending"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    path: Path = args.root / "CHANGELOG.md"
    new, status = insert_entry(path.read_text(encoding="utf-8"))
    if new is None:
        print(f"CHANGELOG.md: {status}")
        return 1 if status.startswith("REFUSED") else 0
    if args.check:
        print("CHANGELOG.md: pending")
        return 1
    path.write_text(new, encoding="utf-8")
    print("CHANGELOG.md: applied now")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
