#!/usr/bin/env python3
"""Raise the [servers] juniper-data floor to >=0.17.0 (W1.11), without bumping juniper-ml's version.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W1.11 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         the 0.15.0 raise this follows, util/ad-hoc/2026-09-22_raise_data_floor_0_15_0.py (ml#2033)

Why this exists
---------------
``juniper-ml[servers]`` (and through it ``[all]``) floors ``juniper-data>=0.15.0``. Every
published juniper-data up to 0.16.0 serves ``equities_seq`` at generator ``5.0.0`` with
``task_type: classification``; juniper-data#437 (X8) relabelled it ``regression`` at ``6.0.0``
on ``main`` after v0.16.0 was cut, and 0.17.0 is the release that will carry it. The plan's
W1.11 raises the floor so the meta-package stops admitting the superseded label.

How this differs from the 0.15.0 script
---------------------------------------
* **No version bump and no new CHANGELOG release section.** The 0.15.0 raise was cut as a
  release in the same PR. This one is drafted BEFORE juniper-data 0.17.0 exists on PyPI and
  waits for it, so the version that carries it is decided by the release train
  (``util/release_train/propose.py`` moves ``[Unreleased]`` and bumps ``AGENTS.md`` with the
  version). The entry therefore goes into ``[Unreleased]`` -> ``### Changed``.
* **No compatibility-matrix row.** ``docs/REFERENCE.md``'s matrix labels each row with the
  juniper-ml version that carries the floor set, and that version does not exist yet. Its
  ``0.10.x`` row stays a true statement about the published 0.10.0.

Every pin edit asserts its exact expected text and must match exactly once, so a missed or
duplicated site is a loud error rather than a silent no-op. The CHANGELOG insertion is bounded
to the ``[Unreleased]`` section: the 0.9.0 entry went wrong by matching a ``### Changed``
heading inside an already-released section.

``AGENTS.md``'s ``**Last Updated**:`` header is set to the run's UTC date. The ``Verify AGENTS.md
Last Updated`` job fails any PR that edits AGENTS.md without changing that line, and it is
matched by pattern rather than by exact old text, so a rebase replay works whatever date ``main``
carries by then.

Usage
-----
    python3 util/ad-hoc/2026-10-08_raise_data_floor_0_17_0.py [--check]

Then regenerate README's compatibility table:
    python3 util/ad-hoc/2026-09-21_sync_readme_compat_table.py
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

_OLD_PIN = "juniper-data>=0.15.0"
_NEW_PIN = "juniper-data>=0.17.0"

#: (path, exact old text, exact new text, expected occurrences)
_EDITS: list[tuple[str, str, str, int]] = [
    # The pin itself, and the exact-string contract that pins it.
    ("pyproject.toml", f'    "{_OLD_PIN}",', f'    "{_NEW_PIN}",', 1),
    ("tests/test_pyproject_extras.py", f'        "{_OLD_PIN}",', f'        "{_NEW_PIN}",', 1),
    # The three comma-joined extras tables (AGENTS / README / QUICK_START).
    ("README.md", f"`{_OLD_PIN}`", f"`{_NEW_PIN}`", 1),
    ("AGENTS.md", f"`{_OLD_PIN}`", f"`{_NEW_PIN}`", 1),
    ("docs/QUICK_START.md", f"`{_OLD_PIN}`", f"`{_NEW_PIN}`", 1),
    # docs/REFERENCE.md's split-column extras table: the version lives in its own cell.
    ("docs/REFERENCE.md", "|             | `juniper-data`                                                                           | `>=0.15.0`        |", "|             | `juniper-data`                                                                           | `>=0.17.0`        |", 1),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_ENTRY_MARKER = f"`[servers]` now floors `{_NEW_PIN}`"
_CL_ENTRY = f"""- **BREAKING (resolution): {_ENTRY_MARKER}, so the meta-package stops admitting the
  juniper-data releases that serve `equities_seq` as `classification`** (W1.11 and F-P4 of
  `{_PLAN}`). Every published juniper-data up to 0.16.0 serves `equities_seq` at generator `5.0.0`
  with `task_type: classification` and `n_classes: 2`. juniper-data#437 (owner ruling X8)
  relabelled it `regression` at `6.0.0` after v0.16.0 was cut, and 0.17.0 is the release that
  carries it. The arrays did not change, and a recurrence fit reads `y_reg_*` under either
  version. What changed is the producer's stored metadata, and with it the `dataset_id`, which
  hashes the generator version. canopy already labels the pair `regression`, so a stack resolved
  under the old floor disagrees with its own producer about the dataset. The floor reaches `[all]`.
  The same release also carries juniper-data#451: under `fundamentals_fill="drop"`, an equities
  request whose `purchase_date` is a weekday or more after `start_date` is refused with a 400
  (W1.8). **Held for publication:** this was drafted on 2026-10-08, when PyPI's latest was
  0.16.0, so the floor cannot be satisfied until 0.17.0 is published. No CI job installs
  `[servers]`. The version that carries the floor (0.11.0 in the plan) is cut after publication,
  and the `0.11.x` row of `docs/REFERENCE.md`'s compatibility matrix lands with that bump. Applied
  by `util/ad-hoc/2026-10-08_raise_data_floor_0_17_0.py`, which asserts each site's exact text
  and requires exactly one match apiece.

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
        # Keep-a-Changelog order: Added, Changed, ... -- place it before '### Fixed' when present.
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
        by_file[rel], did = _apply(by_file[rel], old, new, expected, f"{rel} [{old.strip()[:46]}]", args.check)
        changed_any |= did

    by_file["CHANGELOG.md"] = (_REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    by_file["CHANGELOG.md"], did = _insert_changelog_entry(by_file["CHANGELOG.md"], args.check)
    changed_any |= did

    # AGENTS.md was loaded by the pin edits above; the header bump rides on the same text.
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
