#!/usr/bin/env python3
"""Move the [recurrence] extra to juniper-recurrence>=0.7.0,<0.8.0 and juniper-recurrence-model>=0.5.0,<0.6.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: P5 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py (the 0.6.1 raise this follows, ml#2243);
         juniper-recurrence#212 / #213 (the W5.8 (B) service half and the 0.7.0 proposal)

Why this exists
---------------
juniper-recurrence 0.7.0 published on 2026-10-19 (W5.8 (B) + W5.9 + W5.10: ``default_ridge: "gcv"`` on a model
that standardises the linear readout's memory block; a ``diagnostics`` block on every fit). Its ``requires_dist``
is ``juniper-recurrence-model>=0.5.0,<0.6.0``. The meta-package's ``[recurrence]`` extra pinned
``juniper-recurrence>=0.6.1,<0.7.0`` and ``juniper-recurrence-model>=0.3.0,<0.5.0``: with the recurrence ceiling
lifted alone, the model cap ``<0.5.0`` would make the extra unsatisfiable (0.7.0 needs model 0.5.x), so the two
move together. The model range becomes ``>=0.5.0,<0.6.0`` -- exactly the range 0.7.0 requires -- rather than
admitting 0.6.0, which 0.7.0 refuses (0.6.0 is recurrence 0.8.0's floor; the next raise moves both again).

The client floor (``juniper-recurrence-client>=0.3.0,<0.4.0``) stays; 0.7.0 changed no client contract.

Like the 0.6.1 script it follows: no version bump, no new release section (the release train cuts the version that
carries this), the entry goes into ``[Unreleased]`` -> ``### Changed``, and no compatibility-matrix row. Every pin
edit asserts its exact expected text and must match exactly once. ``AGENTS.md``'s ``**Last Updated**:`` is set to
the run's UTC date.

Usage
-----
    python3 util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py [--check]

Then regenerate README's compatibility table:
    python3 util/ad-hoc/2026-09-21_sync_readme_compat_table.py
and pre-flight against PyPI:
    python3 util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py --extra recurrence --extra all
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

#: (old pin, new pin) -- each moves in pyproject, the exact-string test, and the four documented tables.
_PINS: list[tuple[str, str]] = [
    ("juniper-recurrence>=0.6.1,<0.7.0", "juniper-recurrence>=0.7.0,<0.8.0"),
    ("juniper-recurrence-model>=0.3.0,<0.5.0", "juniper-recurrence-model>=0.5.0,<0.6.0"),
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
    ("docs/REFERENCE.md", "|             | `juniper-recurrence`                                                                     | `>=0.6.1,<0.7.0`  |", "|             | `juniper-recurrence`                                                                     | `>=0.7.0,<0.8.0`  |", 1),
    ("docs/REFERENCE.md", "| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.3.0,<0.5.0`  |", "| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.5.0,<0.6.0`  |", 1),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_ENTRY_MARKER = "`[recurrence]` now floors `juniper-recurrence>=0.7.0`"
_CL_ENTRY = f"""- **{_ENTRY_MARKER}** (`<0.8.0`) **and `juniper-recurrence-model>=0.5.0` (`<0.6.0`)**, the
  P5 release pair (W5.8 (B), W5.9, W5.10 of `{_PLAN}`;
  approved 2026-10-19 with the session's merge approval, the ruling 0.7.0 reopened). The pins were
  `juniper-recurrence>=0.6.1,<0.7.0` and `juniper-recurrence-model>=0.3.0,<0.5.0`.
  - **Why both move.** recurrence 0.7.0's `requires_dist` is `juniper-recurrence-model>=0.5.0,<0.6.0`:
    its `default_ridge` is `"gcv"`, which is safe only on model 0.5.0's train-fold standardisation of the
    linear readout's memory block. Lifting the recurrence ceiling alone would leave the extra
    unsatisfiable under the old model cap `<0.5.0`. The model range is the one 0.7.0 requires, not a
    wider one: 0.7.0 refuses model 0.6.0, which is recurrence 0.8.0's floor (W5.2, on an open PR); the
    next raise moves both again.
  - **What 0.7.0 brings** to `pip install juniper-ml[recurrence]`: `POST /v1/crossval` on the equities
    row no longer blows up under the default readout (the W5.1 note's −2.1e4 becomes −0.195 on the E-H
    artifact), and every fit carries a `diagnostics` block (`readout`, `theta`, `ridge_mode` /
    `ridge_selected`, `gamma`, `gcv_at_edge` / `null_model`).
  - **0.7.0's own `[torch]` extra is unresolvable** (`juniper-recurrence-model[torch]>=0.4.0,<0.5.0`
    against the base `>=0.5.0`); `[recurrence]` installs the base distribution and is unaffected. The
    fix rides on juniper-recurrence#215 for 0.8.0.
  - **Pre-flighted against real PyPI** on 2026-10-19 with
    `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`: PREFLIGHT_RESULT
  - The client floor `juniper-recurrence-client>=0.3.0,<0.4.0` stays (no client contract changed). The
    release train cuts the version that carries this (0.11.0 in the plan). Applied by
    `util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py`, which asserts each site's exact text and
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


def _insert_changelog_entry(text: str, entry: str, check: bool) -> tuple[str, bool]:
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
        # Pre-existing on 2026-10-19: [Unreleased] carries two '### Changed' headings (the second after
        # '### Added'). The entry goes under the first; merging the two is a separate tidy-up.
        print(f"  ! CHANGELOG.md [Unreleased]: {section.count(chr(10) + '### Changed' + chr(10))} '### Changed' headings; using the first")
    if "\n### Changed\n" in section:
        anchor = section.index("\n### Changed\n") + len("\n### Changed\n")
        if section[anchor : anchor + 1] != "\n":
            raise SystemExit("ERROR: CHANGELOG.md: '### Changed' in [Unreleased] is not followed by a blank line")
        new_section = section[: anchor + 1] + entry + section[anchor + 1 :]
        how = "first entry under the existing '### Changed'"
    else:
        fixed = section.find("\n### Fixed\n")
        block = "\n### Changed\n\n" + entry.rstrip("\n") + "\n"
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
    ap.add_argument("--preflight-result", default="PREFLIGHT_RESULT", help="the sentence recording the PyPI pre-flight (replaces the placeholder in the CHANGELOG entry)")
    args = ap.parse_args()

    changed_any = False
    by_file: dict[str, str] = {}

    for rel, old, new, expected in _EDITS:
        if rel not in by_file:
            by_file[rel] = (_REPO / rel).read_text(encoding="utf-8")
        by_file[rel], did = _apply(by_file[rel], old, new, expected, f"{rel} [{old.strip()[:60]}]", args.check)
        changed_any |= did

    by_file["CHANGELOG.md"] = (_REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    by_file["CHANGELOG.md"], did = _insert_changelog_entry(by_file["CHANGELOG.md"], _CL_ENTRY.replace("PREFLIGHT_RESULT", args.preflight_result), args.check)
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
