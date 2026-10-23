#!/usr/bin/env python3
"""Move the [recurrence] extra to juniper-recurrence>=0.8.0,<0.9.0 and juniper-recurrence-model>=0.6.0,<0.7.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: P5 / W5.2 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py (the 0.7.0 raise this follows, ml#2262);
         juniper-recurrence#215 (W5.2's service half + the ``[torch]`` fix) / #220 (the 0.8.0 proposal)

Why this exists
---------------
juniper-recurrence 0.8.0 published on 2026-10-20 (W5.2: ``POST /v1/crossval`` selects over the ``trainval`` pool and cuts
a panel's folds on the global date per entity, ``embargo`` defaults to the look-back, a ``folding`` block on the
response; the ``[torch]`` extra resolves again). Its ``requires_dist`` is ``juniper-recurrence-model>=0.6.0,<0.7.0``
(0.6.0: the composed ``trainval`` view and the ``ticker_code`` / ``window_end_date`` keys). The meta-package's
``[recurrence]`` extra pinned ``juniper-recurrence>=0.7.0,<0.8.0`` and ``juniper-recurrence-model>=0.5.0,<0.6.0``: with
the recurrence ceiling lifted alone, the model cap ``<0.6.0`` would make the extra unsatisfiable (0.8.0 needs model
0.6.x), so the two move together, exactly as 0.6.1 -> 0.7.0 did. The model range becomes ``>=0.6.0,<0.7.0`` -- the
range 0.8.0 requires -- not a wider one.

The client floor (``juniper-recurrence-client>=0.3.0,<0.4.0``) stays; 0.8.0 changed no client contract (the client's
``crossval`` docstring is owed a ``folding`` / ``diagnostics`` mention, a client-package doc touch of its own).

Like the two scripts it follows: no version bump, no new release section (the release train cuts the version that
carries this), the entry goes first under ``[Unreleased]`` -> ``### Changed`` (one heading since juniper-ml#2283), and
no compatibility-matrix row. ``docs/QUICK_START.md``'s pip-list block (refreshed in #2283 to what 0.10.0 resolved on
2026-10-20) moves its two recurrence lines and its "resolved to on" date, since the block is re-resolved for this PR.
Every pin edit asserts its exact expected text and must match exactly once. ``AGENTS.md``'s ``**Last Updated**:`` is
set to the run's UTC date.

Usage
-----
    python3 util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py [--check] [--preflight-result "..."] [--resolved-on YYYY-MM-DD]

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
    ("juniper-recurrence>=0.7.0,<0.8.0", "juniper-recurrence>=0.8.0,<0.9.0"),
    ("juniper-recurrence-model>=0.5.0,<0.6.0", "juniper-recurrence-model>=0.6.0,<0.7.0"),
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
    ("docs/REFERENCE.md", "|             | `juniper-recurrence`                                                                     | `>=0.7.0,<0.8.0`  |", "|             | `juniper-recurrence`                                                                     | `>=0.8.0,<0.9.0`  |", 1),
    ("docs/REFERENCE.md", "| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.5.0,<0.6.0`  |", "| `recurrence`| `juniper-recurrence-model`                                                               | `>=0.6.0,<0.7.0`  |", 1),
    # docs/QUICK_START.md § 2. Verify: the sample `pip list` block (juniper-ml#2283 shape).
    ("docs/QUICK_START.md", "juniper-recurrence          0.7.x\n", "juniper-recurrence          0.8.x\n", 1),
    ("docs/QUICK_START.md", "juniper-recurrence-model    0.5.x\n", "juniper-recurrence-model    0.6.x\n", 1),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_ENTRY_MARKER = "`[recurrence]` now floors `juniper-recurrence>=0.8.0`"
_CL_ENTRY = f"""- **{_ENTRY_MARKER}** (`<0.9.0`) **and `juniper-recurrence-model>=0.6.0` (`<0.7.0`)**, the
  W5.2 release pair (P5 of `{_PLAN}`;
  approved 2026-10-20 with the session's merge approval, the ruling 0.7.0 reopened). The pins were
  `juniper-recurrence>=0.7.0,<0.8.0` and `juniper-recurrence-model>=0.5.0,<0.6.0`.
  - **Why both move.** recurrence 0.8.0's `requires_dist` is `juniper-recurrence-model>=0.6.0,<0.7.0`:
    its crossval pool is model 0.6.0's composed `trainval` view and its per-entity folds read the
    `ticker_code` / `window_end_date` keys that 0.6.0 writes. Lifting the recurrence ceiling alone would
    leave the extra unsatisfiable under the old model cap `<0.6.0`. The model range is the one 0.8.0
    requires, not a wider one.
  - **What 0.8.0 brings** to `pip install juniper-ml[recurrence]`: `POST /v1/crossval` selects over the
    `trainval` pool, so the reserved `test` partition is never in a fold; a multi-ticker artifact's folds
    are cut on the global date per entity with the embargo purged per entity; `embargo` defaults to the
    look-back (an explicit smaller value is honoured and logged); the optional `embargo_days`; a `folding`
    block on the response and on `GET /v1/crossval/status`; `dataset.split` reads `trainval`. The
    `[torch]` extra resolves again (0.7.0's was disjoint from its base floor).
  - **Pre-flighted against real PyPI** on RESOLVED_ON with
    `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`: PREFLIGHT_RESULT
  - The client floor `juniper-recurrence-client>=0.3.0,<0.4.0` stays (no client contract changed). The
    release train cuts the version that carries this (0.11.0 in the plan). `docs/QUICK_START.md`'s sample
    `pip list` block moves its two recurrence lines with the pins. Applied by
    `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py`, which asserts each site's exact text and
    requires exactly one match apiece.

"""

_RESOLVED_ON_RE = re.compile(r"^(Expected output \(with `\[all\]`\): 18 lines, one per package\. The versions are what `juniper-ml` 0\.10\.0\nresolved to on )(\d{4}-\d{2}-\d{2})( \(`pip install --dry-run` against PyPI)", re.MULTILINE)


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


def _set_resolved_on(text: str, date: str, check: bool) -> tuple[str, bool]:
    """Set the pip-list prose's 'resolved to on YYYY-MM-DD' date (docs/QUICK_START.md, juniper-ml#2283 shape)."""
    found = _RESOLVED_ON_RE.findall(text)
    if len(found) != 1:
        raise SystemExit(f"ERROR: docs/QUICK_START.md: expected exactly one 'resolved to on YYYY-MM-DD' prose line, found {len(found)}")
    if found[0][1] == date:
        print(f"  = docs/QUICK_START.md [resolved to on]: already {date}")
        return text, False
    if check:
        print(f"  ~ docs/QUICK_START.md [resolved to on]: WOULD set {date} (was {found[0][1]})")
        return text, True
    print(f"  + docs/QUICK_START.md [resolved to on]: set {date} (was {found[0][1]})")
    return _RESOLVED_ON_RE.sub(lambda m: m.group(1) + date + m.group(3), text, count=1), True


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
    """Put the entry first under [Unreleased]'s single ``### Changed``, creating that heading if absent."""
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
        raise SystemExit("ERROR: CHANGELOG.md [Unreleased]: more than one '### Changed' heading (juniper-ml#2283 merged them; re-run its tidy script first)")
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
    ap.add_argument("--resolved-on", default=datetime.now(timezone.utc).date().isoformat(), help="the UTC date the pip-list block was re-resolved (default: today)")
    args = ap.parse_args()

    changed_any = False
    by_file: dict[str, str] = {}

    for rel, old, new, expected in _EDITS:
        if rel not in by_file:
            by_file[rel] = (_REPO / rel).read_text(encoding="utf-8")
        by_file[rel], did = _apply(by_file[rel], old, new, expected, f"{rel} [{old.strip()[:60]}]", args.check)
        changed_any |= did

    by_file["docs/QUICK_START.md"], did = _set_resolved_on(by_file["docs/QUICK_START.md"], args.resolved_on, args.check)
    changed_any |= did

    by_file["CHANGELOG.md"] = (_REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    entry = _CL_ENTRY.replace("PREFLIGHT_RESULT", args.preflight_result).replace("RESOLVED_ON", args.resolved_on)
    by_file["CHANGELOG.md"], did = _insert_changelog_entry(by_file["CHANGELOG.md"], entry, args.check)
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
