#!/usr/bin/env python3
"""Raise the [servers] juniper-data floor to >=0.15.0 and bump juniper-ml to 0.10.0.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (R-5 of HANDOFF_2026-09-22_decision-11-re-evaluated-and-two-releases-cut.md)

Why this exists
---------------
``juniper-ml[servers]`` floors ``juniper-data>=0.14.0``. The published 0.14.0 wheel ships the
``equities`` and ``equities_seq`` generators at ``VERSION = "3.0.0"``; 0.15.0 ships ``"5.0.0"`` --
the owner rulings of juniper-data#395 plus the regression fix of juniper-data#404. A fresh
resolve already takes 0.15.0, but in an environment that holds 0.14.0,
``pip install "juniper-ml[servers]==0.9.0"`` leaves it there (reproduced in a clean venv
2026-09-22). The floor ADMITS the superseded contract rather than delivering it -- the shape
0.9.0 fixed for ``juniper-canopy``, and the owner ruled the same way (2026-09-22, in session).

This is the canopy script (``2026-09-21_raise_canopy_floor_0_8_1.py``) with the data pin
substituted, plus one thing that script left to a hand edit: it opens the ``## [0.10.0]``
CHANGELOG section itself. The hand-edit route is where 0.9.0 went wrong -- its entry was
inserted by an unbounded ``str.partition`` that matched a ``### Changed`` heading inside the
already-released ``## [0.8.0]``. Here the insertion point is asserted exactly: the
``## [Unreleased]`` heading must be followed, after one blank line, by ``## [0.9.0]``, i.e.
``[Unreleased]`` must be EMPTY. If another session has filed an entry there, the script stops
rather than guessing which release that entry belongs to.

Every edit asserts its exact expected text and must match exactly once, so a missed or
duplicated site is a loud error rather than a silent no-op.

Usage
-----
    python3 util/ad-hoc/2026-09-22_raise_data_floor_0_15_0.py [--check]

Then regenerate README's compatibility table:
    python3 util/ad-hoc/2026-09-21_sync_readme_compat_table.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

_OLD_PIN = "juniper-data>=0.14.0"
_NEW_PIN = "juniper-data>=0.15.0"
_OLD_VER = "0.9.0"
_NEW_VER = "0.10.0"
_RELEASE_DATE = "2026-09-22"

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
    ("docs/REFERENCE.md", "|             | `juniper-data`                                                                           | `>=0.14.0`        |", "|             | `juniper-data`                                                                           | `>=0.15.0`        |", 1),
    # The declared version, and the AGENTS.md header that test_agents_md_version_drift pins to it.
    ("pyproject.toml", f'version = "{_OLD_VER}"', f'version = "{_NEW_VER}"', 1),
    ("AGENTS.md", f"**Version**: {_OLD_VER}", f"**Version**: {_NEW_VER}", 1),
]

#: The compatibility matrix gains a row rather than rewriting one -- the 0.9.x row is a true
#: statement about the published 0.9.0 and stays.
_MATRIX_ANCHOR = "| 0.9.x      | >=0.14.0     | >=0.11.0       | >=0.8.1        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |"
_MATRIX_NEW_ROW = "| 0.10.x     | >=0.15.0     | >=0.11.0       | >=0.8.1        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.2.0               |"

#: The matrix lead-in names the version it describes.
_LEADIN_OLD = f"`juniper-ml` {_OLD_VER} declares the following pins."
_LEADIN_NEW = f"`juniper-ml` {_NEW_VER} declares the following pins."

#: CHANGELOG: [Unreleased] must be empty -- its heading, one blank line, then the 0.9.0 heading.
_CL_ANCHOR = f"## [Unreleased]\n\n## [{_OLD_VER}] - "
_CL_SECTION = f"""## [{_NEW_VER}] - {_RELEASE_DATE}

### Changed

- **BREAKING (resolution): `[servers]` now floors `{_NEW_PIN}`, because 0.14.0 still serves the
  `equities` generators at the contract 0.15.0 replaced.** Read from the published wheels, not a
  checkout: 0.14.0 ships `equities` and `equities_seq` at `VERSION = "3.0.0"`, 0.15.0 at `"5.0.0"`.
  The two majors between them are the owner rulings of juniper-data#395 -- `adj_close` leaves the
  default feature matrix because `close / adj_close` encodes dividends paid *after* each row, and
  the SEC share history becomes an as-of join on the FILED date, so a restated period no longer
  rewrites when a value became knowable -- and the regression fix of juniper-data#404. PyPI never
  served the intermediate 4.0.0, so an upgrade goes straight from 3.0.0 to 5.0.0. The old floor did
  not *deliver* 0.14.0 -- a fresh resolve already takes 0.15.0 -- but it *admitted* it: in a clean
  venv holding `juniper-data==0.14.0`, `pip install "juniper-ml[servers]==0.9.0"` installs canopy,
  cascor and their dependencies and leaves juniper-data at 0.14.0, so "5.0.0 is what `pip install`
  serves" was true only of an unconstrained install. The same shape as 0.9.0's `juniper-canopy`
  floor, ruled the same way. Pre-flighted against real PyPI before the change --
  `juniper-canopy>=0.8.1` + `juniper-cascor>=0.11.0` + `{_NEW_PIN}` resolves in 60 packages with
  `juniper-service-core` 0.7.0 and `juniper-model-core` 0.3.2, both inside the existing caps, and
  the two juniper-data wheels declare identical base dependencies, so the raise adds no requirement
  edge. **Version bumped {_OLD_VER} -> {_NEW_VER} with it**, for the reason 0.9.0 gave:
  `docs/REFERENCE.md`'s compatibility matrix labels each row by the juniper-ml version carrying
  that floor set, so the `0.9.x` row is kept and a `0.10.x` row added. Minor per the pre-1.0
  convention at `util/release_train/detect.py:827`, since forbidding a previously-admitted version
  is breaking. Applied by `util/ad-hoc/2026-09-22_raise_data_floor_0_15_0.py`, which asserts each
  site's exact text, requires exactly one match apiece, and refuses to open this section unless
  `[Unreleased]` is empty.

"""


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


def _load(by_file: dict[str, str], rel: str) -> str:
    if rel not in by_file:
        by_file[rel] = (_REPO / rel).read_text(encoding="utf-8")
    return by_file[rel]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    changed_any = False
    by_file: dict[str, str] = {}

    for rel, old, new, expected in _EDITS:
        _load(by_file, rel)
        by_file[rel], did = _apply(by_file[rel], old, new, expected, f"{rel} [{old[:46]}]", args.check)
        changed_any |= did

    # The compatibility matrix: insert the new row directly after the 0.9.x row.
    ref = "docs/REFERENCE.md"
    _load(by_file, ref)
    if _MATRIX_NEW_ROW in by_file[ref]:
        print(f"  = {ref} [matrix row]: already present")
    else:
        if by_file[ref].count(_MATRIX_ANCHOR) != 1:
            raise SystemExit(f"ERROR: {ref}: expected exactly one 0.9.x matrix row")
        if args.check:
            print(f"  ~ {ref} [matrix row]: WOULD insert a 0.10.x row")
        else:
            by_file[ref] = by_file[ref].replace(_MATRIX_ANCHOR, _MATRIX_ANCHOR + "\n" + _MATRIX_NEW_ROW, 1)
            print(f"  + {ref} [matrix row]: inserted a 0.10.x row")
        changed_any = True

    by_file[ref], did = _apply(by_file[ref], _LEADIN_OLD, _LEADIN_NEW, 1, f"{ref} [matrix lead-in]", args.check)
    changed_any |= did

    # CHANGELOG: open the 0.10.0 section between an EMPTY [Unreleased] and the 0.9.0 heading.
    cl = "CHANGELOG.md"
    _load(by_file, cl)
    if f"## [{_NEW_VER}] - " in by_file[cl]:
        print(f"  = {cl} [{_NEW_VER} section]: already present")
    else:
        if by_file[cl].count(_CL_ANCHOR) != 1:
            raise SystemExit(f"ERROR: {cl}: [Unreleased] is not empty (or not directly above [{_OLD_VER}]); refusing to guess which release its entries belong to")
        if args.check:
            print(f"  ~ {cl} [{_NEW_VER} section]: WOULD open it below an empty [Unreleased]")
        else:
            by_file[cl] = by_file[cl].replace(_CL_ANCHOR, f"## [Unreleased]\n\n{_CL_SECTION}## [{_OLD_VER}] - ", 1)
            print(f"  + {cl} [{_NEW_VER} section]: opened below an empty [Unreleased]")
        changed_any = True

    if args.check:
        return 1 if changed_any else 0

    for rel, text in by_file.items():
        (_REPO / rel).write_text(text, encoding="utf-8")

    print("\nNow re-run util/ad-hoc/2026-09-21_sync_readme_compat_table.py to regenerate README's")
    print("Ecosystem Compatibility table from the new pyproject, then the test suite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
