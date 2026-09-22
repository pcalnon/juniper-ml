#!/usr/bin/env python3
"""Raise the [servers] juniper-canopy floor to >=0.8.1 and bump juniper-ml to 0.9.0.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (canopy#631 floor correction)

Why this exists
---------------
Every juniper-canopy wheel from 0.5.0 through 0.8.0 publishes ZERO top-level modules:
``juniper_canopy/`` contains only ``__init__.py``, and ``import demo_mode`` raises
``ModuleNotFoundError``. 0.8.1 ships all 19. canopy#631, closed 2026-09-17.

``juniper-ml[servers]`` floors ``juniper-canopy>=0.7.0``, which ADMITS two of the broken
wheels. A default resolve takes 0.8.1 because pip prefers the newest, so the floor fails
to FORBID rather than actively delivering the break -- the same shape as the
``juniper-model-core>=0.1.0,<0.4.0`` cap, but with the opposite conclusion: that one was
left alone because the difference was documentation-only with no behavioural gain, and
here the admitted wheel cannot import its own dashboard.

The version bump travels with the floor change, and is not optional. ``docs/REFERENCE.md``'s
compatibility matrix labels each row by the juniper-ml version carrying that floor set --
its own prose says the 0.6.x row "covers 0.7.x too -- 0.7.0/0.7.1 changed no floor". A new
floor set therefore needs a version to label it. Pre-1.0, ``util/release_train/detect.py:827``
maps breaking-or-feature to MINOR, and forbidding a previously-admitted version is breaking:
0.8.0 -> 0.9.0.

Every edit asserts its exact expected text and must match exactly once, so a missed or
duplicated site is a loud error rather than a silent no-op. That is the lesson recorded in
``util/ad-hoc/2026-09-10_bump_extras_table.py``: a whole-line substitution that guesses
row shape quietly skips the row it guessed wrong about.

Usage
-----
    python3 util/ad-hoc/2026-09-21_raise_canopy_floor_0_8_1.py [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

_OLD_PIN = "juniper-canopy>=0.7.0"
_NEW_PIN = "juniper-canopy>=0.8.1"
_OLD_VER = "0.8.0"
_NEW_VER = "0.9.0"

#: (path, exact old text, exact new text, expected occurrences)
_EDITS: list[tuple[str, str, str, int]] = [
    # The pin itself.
    ("pyproject.toml", f'    "{_OLD_PIN}",', f'    "{_NEW_PIN}",', 1),
    ("tests/test_pyproject_extras.py", f'        "{_OLD_PIN}",', f'        "{_NEW_PIN}",', 1),
    # The three comma-joined extras tables (AGENTS / README / QUICK_START).
    ("README.md", f"`{_OLD_PIN}`", f"`{_NEW_PIN}`", 1),
    ("AGENTS.md", f"`{_OLD_PIN}`", f"`{_NEW_PIN}`", 1),
    ("docs/QUICK_START.md", f"`{_OLD_PIN}`", f"`{_NEW_PIN}`", 1),
    # docs/REFERENCE.md's split-column extras table: the version lives in its own cell.
    ("docs/REFERENCE.md", "| `juniper-canopy`                                                                         | `>=0.7.0`         |", "| `juniper-canopy`                                                                         | `>=0.8.1`         |", 1),
    # The declared version, and the AGENTS.md header that test_agents_md_version_drift pins to it.
    ("pyproject.toml", f'version = "{_OLD_VER}"', f'version = "{_NEW_VER}"', 1),
    ("AGENTS.md", f"**Version**: {_OLD_VER}", f"**Version**: {_NEW_VER}", 1),
]

#: The compatibility matrix gains a row rather than rewriting one -- the 0.8.x row is a true
#: statement about the published 0.8.0 and stays.
_MATRIX_ANCHOR = "| 0.8.x      | >=0.14.0     | >=0.11.0       | >=0.7.0        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |"
_MATRIX_NEW_ROW = "| 0.9.x      | >=0.14.0     | >=0.11.0       | >=0.8.1        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |"

#: The matrix lead-in names the version it describes.
_LEADIN_OLD = "`juniper-ml` 0.8.0 declares the following pins."
_LEADIN_NEW = "`juniper-ml` 0.9.0 declares the following pins."


def _apply(text: str, old: str, new: str, expected: int, where: str, check: bool) -> tuple[str, bool]:
    found = text.count(old)
    if found == 0 and text.count(new) >= expected:
        print(f"  = {where}: already at target")
        return text, False
    if found != expected:
        raise SystemExit(f"ERROR: {where}: expected {expected} occurrence(s) of {old!r}, found {found}")
    if check:
        print(f"  ~ {where}: WOULD rewrite {found} occurrence(s)")
        return text, True
    print(f"  + {where}: rewrote {found} occurrence(s)")
    return text.replace(old, new, expected), True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    changed_any = False
    by_file: dict[str, str] = {}

    for rel, old, new, expected in _EDITS:
        path = _REPO / rel
        if rel not in by_file:
            by_file[rel] = path.read_text(encoding="utf-8")
        by_file[rel], did = _apply(by_file[rel], old, new, expected, f"{rel} [{old[:46]}]", args.check)
        changed_any |= did

    # The compatibility matrix: insert the new row directly after the 0.8.x row.
    ref = "docs/REFERENCE.md"
    if ref not in by_file:
        by_file[ref] = (_REPO / ref).read_text(encoding="utf-8")
    if _MATRIX_NEW_ROW in by_file[ref]:
        print(f"  = {ref} [matrix row]: already present")
    else:
        if by_file[ref].count(_MATRIX_ANCHOR) != 1:
            raise SystemExit(f"ERROR: {ref}: expected exactly one 0.8.x matrix row")
        if args.check:
            print(f"  ~ {ref} [matrix row]: WOULD insert a 0.9.x row")
        else:
            by_file[ref] = by_file[ref].replace(_MATRIX_ANCHOR, _MATRIX_ANCHOR + "\n" + _MATRIX_NEW_ROW, 1)
            print(f"  + {ref} [matrix row]: inserted a 0.9.x row")
        changed_any = True

    by_file[ref], did = _apply(by_file[ref], _LEADIN_OLD, _LEADIN_NEW, 1, f"{ref} [matrix lead-in]", args.check)
    changed_any |= did

    if args.check:
        return 1 if changed_any else 0

    for rel, text in by_file.items():
        (_REPO / rel).write_text(text, encoding="utf-8")

    print("\nNow re-run util/ad-hoc/2026-09-21_sync_readme_compat_table.py to regenerate README's")
    print("Ecosystem Compatibility table from the new pyproject, then the test suite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
