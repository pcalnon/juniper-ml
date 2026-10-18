#!/usr/bin/env python3
"""Admit the W1.13 releases: raise the [recurrence] ceilings and the canopy / recurrence floors, without bumping juniper-ml.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-18
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W1.13 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-08_raise_data_floor_0_17_0.py (the W1.11 raise this follows, ml#2190)

Why this exists
---------------
The P1 release train (W1.13) published juniper-recurrence-model 0.4.0 (2026-10-13), juniper-recurrence
0.6.0 and juniper-canopy 0.9.0 (both 2026-10-17). ``juniper-ml[recurrence]`` capped
``juniper-recurrence-model<0.4.0`` and ``juniper-recurrence<0.6.0``, so the meta-package could install
neither recurrence release. The release train's propagation records this edge as ``escaped -> deferred
(juniper-ml meta stays manual per Q-META)``, so it is done by hand. The owner also ruled (2026-10-18 UTC)
to raise two floors, each to its security release: ``juniper-canopy>=0.9.0`` (High) and
``juniper-recurrence>=0.6.0`` (Medium, W1.14).

Like the W1.11 script it follows: no version bump, no new release section (the release train cuts the
version that carries this), the entry goes into ``[Unreleased]`` -> ``### Changed``, and no
compatibility-matrix row (that row is labelled with the juniper-ml version, which does not exist yet).
Every pin edit asserts its exact expected text and must match exactly once. ``AGENTS.md``'s
``**Last Updated**:`` is set to the run's UTC date.

Usage
-----
    python3 util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py [--check]

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
    ("juniper-canopy>=0.8.1", "juniper-canopy>=0.9.0"),
    ("juniper-recurrence-model>=0.3.0,<0.4.0", "juniper-recurrence-model>=0.3.0,<0.5.0"),
    ("juniper-recurrence>=0.5.0,<0.6.0", "juniper-recurrence>=0.6.0,<0.7.0"),
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
    ("docs/REFERENCE.md", "| `servers`   | `juniper-canopy`                                                                         | `>=0.8.1`         |", "| `servers`   | `juniper-canopy`                                                                         | `>=0.9.0`         |", 1),
    ("docs/REFERENCE.md", "| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.3.0,<0.4.0`  |", "| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.3.0,<0.5.0`  |", 1),
    ("docs/REFERENCE.md", "|             | `juniper-recurrence`                                                                     | `>=0.5.0,<0.6.0`  |", "|             | `juniper-recurrence`                                                                     | `>=0.6.0,<0.7.0`  |", 1),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_ENTRY_MARKER = "`[servers]` now floors `juniper-canopy>=0.9.0`"
_CL_ENTRY = f"""- **BREAKING (resolution): {_ENTRY_MARKER}, and `[recurrence]` admits the W1.13 releases, with
  `juniper-recurrence>=0.6.0,<0.7.0` and `juniper-recurrence-model>=0.3.0,<0.5.0`** (W1.13 of
  `{_PLAN}`). The meta-package could not install either new recurrence release. `[recurrence]`
  capped `juniper-recurrence<0.6.0` and `juniper-recurrence-model<0.4.0`, and both caps were
  escaped: model 0.4.0 was published on 2026-10-13, and recurrence 0.6.0 and canopy 0.9.0 on
  2026-10-17.
  - **The two ceilings rise to the next minor**: `<0.5.0` for the model, `<0.7.0` for the app.
  - **Two floors rise, each to a security release** (owner ruling, 2026-10-18 UTC).
    - `juniper-canopy>=0.9.0`, up from `>=0.8.1`. 0.9.0 is rated High. It refuses an outbound key
      with padding, a line break or a non-ASCII character where the key is read. It keeps a
      padded `CANOPY_API_KEY` out of the logs and Sentry, compares every API key without
      short-circuiting, and picks up the juniper-observability 0.4.1 and juniper-service-core 0.7.1
      patches.
    - `juniper-recurrence>=0.6.0`, up from `>=0.5.0`. 0.6.0 is rated Medium. It carries W1.14: a
      5xx no longer relays the data client's text, which could quote a padded
      `JUNIPER_DATA_API_KEY`, and a padded key is refused at load. It also picks up the same two
      shared patches.

    The model and data-client floors do not move, because recurrence 0.6.0 itself admits model
    `>=0.3.0` and data-client `>=0.4.2`.
  - **Pre-flighted against real PyPI** on 2026-10-18, with
    `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py` (new). It runs pip's resolver over
    Linux x86_64 wheels and installs nothing.
    - **`[servers]`** resolves in 61 packages on Python 3.12, 3.13 and 3.14: canopy 0.9.0, cascor
      0.11.0, data 0.17.0, service-core 0.7.1, observability 0.4.1.
    - **`[recurrence]`** resolves in 32 packages on all three: recurrence 0.6.0, model 0.4.0, client
      0.3.0, data-client 0.6.0, service-core 0.7.1.
    - **`[all]`** resolves in 76 packages on 3.13 and 3.14. **On 3.12 it was not confirmed** from the
      host that ran this: one attempt hit an interrupted wheel download, and the re-run was stopped
      for low host memory. Both extras this change touches do resolve on 3.12.
  - The release train cuts the version that carries this (0.11.0 in the plan), and the `0.11.x` row of
    `docs/REFERENCE.md`'s compatibility matrix lands with that bump. Applied by
    `util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py`, which asserts each site's exact
    text and requires exactly one match apiece.

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
