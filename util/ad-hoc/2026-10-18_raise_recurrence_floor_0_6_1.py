#!/usr/bin/env python3
"""Raise the [recurrence] floor to juniper-recurrence>=0.6.1, the release that carries the 2026-10-10 floors ruling.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-18
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W1.13 / M1 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py (the W1.13 raise this follows, ml#2232);
         juniper-recurrence#206 (the floors fix 0.6.1 carries)

Why this exists
---------------
juniper-recurrence 0.6.0 shipped without the owner's 2026-10-10 floors ruling: its ranges still admitted
juniper-recurrence-model ``>=0.3.0`` and juniper-data-client ``>=0.4.2``, so ``pip install -U
juniper-recurrence`` over a 0.5.0 environment kept model 0.3.0 and data-client 0.5.0, ``pip check`` was
clean, and the service started without the W1.4 rules or the W1.3 target checks. juniper-recurrence#206
raised the floors (model ``>=0.4.0``, data-client ``>=0.6.0``), and 0.6.1 published them to PyPI on
2026-10-18 (19:02Z). The owner ruled the same day that the meta-package's ``[recurrence]`` floor follows
to ``>=0.6.1``, so that ``pip install -U juniper-ml[recurrence]`` cannot resolve the stale pair either.

The meta-package's own model (``>=0.3.0``) and data-client (``>=0.5.0``) floors stay, as the extras
ruling of 2026-10-18 kept them: recurrence 0.6.1's floors do the forcing.

Like the W1.11 and W1.13 scripts it follows: no version bump, no new release section (the release train
cuts the version that carries this), the entry goes into ``[Unreleased]`` -> ``### Changed``, and no
compatibility-matrix row. Every pin edit asserts its exact expected text and must match exactly once.
``AGENTS.md``'s ``**Last Updated**:`` is set to the run's UTC date.

Usage
-----
    python3 util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py [--check]

Then regenerate README's compatibility table:
    python3 util/ad-hoc/2026-09-21_sync_readme_compat_table.py
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

#: (old pin, new pin) -- each moves in pyproject, the exact-string test, and the four documented tables.
_PINS: list[tuple[str, str]] = [
    ("juniper-recurrence>=0.6.0,<0.7.0", "juniper-recurrence>=0.6.1,<0.7.0"),
]

#: (path, exact old text, exact new text, expected occurrences)
_EDITS: list[tuple[str, str, str, int]] = []
for _old, _new in _PINS:
    _EDITS += [
        # The pin itself, and the exact-string contract that pins it.
        ("pyproject.toml", f'    "{_old}",', f'    "{_new}",', 1),
        ("tests/test_pyproject_extras.py", f'        "{_old}",', f'        "{_new}",', 1),
        # The three comma-joined extras tables (AGENTS / README / QUICK_START).
        ("README.md", f"`{_old}`", f"`{_new}`", 1),
        ("AGENTS.md", f"`{_old}`", f"`{_new}`", 1),
        ("docs/QUICK_START.md", f"`{_old}`", f"`{_new}`", 1),
    ]
# docs/REFERENCE.md's split-column extras table: the version lives in its own cell (same widths).
_EDITS += [
    ("docs/REFERENCE.md", "|             | `juniper-recurrence`                                                                     | `>=0.6.0,<0.7.0`  |", "|             | `juniper-recurrence`                                                                     | `>=0.6.1,<0.7.0`  |", 1),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_ENTRY_MARKER = "`[recurrence]` now floors `juniper-recurrence>=0.6.1`"
_CL_ENTRY = f"""- **{_ENTRY_MARKER}**, the release that carries the recurrence floors ruling
  (M1 of `{_PLAN}`; owner ruling 2026-10-18 UTC). The floor was `>=0.6.0`.
  - **Why 0.6.0 was not enough.** 0.6.0 shipped without the owner's 2026-10-10 floors ruling: it still
    admitted `juniper-recurrence-model>=0.3.0` and `juniper-data-client>=0.4.2`. Over a 0.5.0
    environment, `pip install -U juniper-recurrence` kept model 0.3.0 and data-client 0.5.0,
    `pip check` was clean, and the service started without the W1.4 rules (`float32`, finite `dt`,
    `target_dt`, `seq_lengths`) and without the model 0.4.0 target checks. juniper-recurrence#206
    raised the floors to model `>=0.4.0` and data-client `>=0.6.0`, and 0.6.1 published them on
    2026-10-18. Its `requires_dist` on PyPI carries both.
  - **The meta-package's own model (`>=0.3.0`) and data-client (`>=0.5.0`) floors stay**, as the
    extras ruling of 2026-10-18 kept them. recurrence 0.6.1's floors do the forcing: with this floor,
    `pip install -U juniper-ml[recurrence]` cannot resolve the stale pair either.
  - **Pre-flighted against real PyPI** on 2026-10-18 with
    `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`: `[recurrence]` resolves in 32 packages
    on Python 3.12, 3.13 and 3.14, with recurrence 0.6.1, model 0.4.0, client 0.3.0, data-client 0.6.0
    and service-core 0.7.1.
  - The release train cuts the version that carries this (0.11.0 in the plan). Applied by
    `util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py`, which asserts each site's exact text and
    requires exactly one match apiece.

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


_LAST_UPDATED_RE = re.compile(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", re.MULTILINE)


def _bump_last_updated(text: str, check: bool) -> tuple[str, bool]:
    """Set AGENTS.md's single ``**Last Updated**: YYYY-MM-DD`` header line to today's UTC date."""
    today = datetime.now(timezone.utc).date().isoformat()
    found = _LAST_UPDATED_RE.findall(text)
    if len(found) != 1:
        raise SystemExit(f"ERROR: AGENTS.md: expected exactly one '**Last Updated**: YYYY-MM-DD' line, found {len(found)}")
    target = f"**Last Updated**: {today}"
    if found[0] == target:
        print("  = AGENTS.md [Last Updated]: already today's UTC date")
        return text, False
    if check:
        print(f"  ~ AGENTS.md [Last Updated]: WOULD set {today}")
        return text, True
    print(f"  + AGENTS.md [Last Updated]: set {today}")
    return _LAST_UPDATED_RE.sub(target, text, count=1), True


def _insert_changelog_entry(text: str, check: bool) -> tuple[str, bool]:
    """Put the entry first under [Unreleased]'s ``### Changed``, creating that heading if absent."""
    start = text.find("## [Unreleased]\n")
    if start < 0 or text.count("## [Unreleased]\n") != 1:
        raise SystemExit("ERROR: CHANGELOG.md: expected exactly one '## [Unreleased]' heading")
    end = text.find("\n## [", start + 1)
    if end < 0:
        raise SystemExit("ERROR: CHANGELOG.md: no released section follows [Unreleased]")
    section = text[start:end]
    if _ENTRY_MARKER in section:
        print("  = CHANGELOG.md [Unreleased]: entry already present")
        return text, False
    if _ENTRY_MARKER in text:
        raise SystemExit("ERROR: CHANGELOG.md: the entry exists OUTSIDE [Unreleased]; refusing to add a second")
    if section.count("\n### Changed\n") > 1:
        raise SystemExit("ERROR: CHANGELOG.md: [Unreleased] has more than one '### Changed' heading")
    if "\n### Changed\n" in section:
        anchor = section.index("\n### Changed\n") + len("\n### Changed\n")
        if section[anchor : anchor + 1] != "\n":
            raise SystemExit("ERROR: CHANGELOG.md: '### Changed' in [Unreleased] is not followed by a blank line")
        new_section = section[: anchor + 1] + _CL_ENTRY + section[anchor + 1 :]
        how = "first entry under the existing '### Changed'"
    else:
        fixed = section.find("\n### Fixed\n")
        block = "\n### Changed\n\n" + _CL_ENTRY.rstrip("\n") + "\n"
        new_section = section[:fixed] + block + section[fixed:] if fixed >= 0 else section.rstrip("\n") + "\n" + block
        how = "a new '### Changed' heading"
    if check:
        print(f"  ~ CHANGELOG.md [Unreleased]: WOULD add the entry as {how}")
        return text, True
    print(f"  + CHANGELOG.md [Unreleased]: added the entry as {how}")
    return text[:start] + new_section + text[end:], True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()

    changed_any = False
    by_file: dict[str, str] = {}

    for rel, old, new, expected in _EDITS:
        if rel not in by_file:
            by_file[rel] = (_REPO / rel).read_text(encoding="utf-8")
        by_file[rel], did = _apply(by_file[rel], old, new, expected, f"{rel} [{old.strip()[:60]}]", args.check)
        changed_any |= did

    by_file["CHANGELOG.md"] = (_REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    by_file["CHANGELOG.md"], did = _insert_changelog_entry(by_file["CHANGELOG.md"], args.check)
    changed_any |= did

    by_file["AGENTS.md"], did = _bump_last_updated(by_file["AGENTS.md"], args.check)
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
