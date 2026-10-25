#!/usr/bin/env python3
"""R-ML-SERVERS: raise the [servers] floors to juniper-cascor 0.12.0 and juniper-data 0.17.1, without bumping juniper-ml.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: R-ML-SERVERS in §5 of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md;
         juniper-ml#2314 (the [tools] half of the same security floors, released as juniper-ml 0.11.1);
         util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py (the W1.13 raise this follows, ml#2232);
         written by the recurrence-arc session (worktree cuddly-knitting-stardust) and adopted, after review,
         by the session that opened R-ML-SERVERS's PR, when the owner assigned the PR there (2026-10-25)

Why this exists
---------------
juniper-ml#2314 floored the two shared security patches under ``[tools]`` (``juniper-observability>=0.4.1``,
``juniper-service-core>=0.7.1,<0.8.0``) and left ``[servers]`` until the server releases that floor them were on
PyPI, because a floor on an unpublished release makes an extra unresolvable. juniper-data 0.17.1 reached PyPI on
2026-10-23 and juniper-cascor 0.12.0 on 2026-10-25, so this raises ``[servers]`` to them.

Like the W1.13 script it follows: no version bump, no new release section (the owner's cut carries this), the
entry goes into ``[Unreleased]`` -> ``### Security``, and no compatibility-matrix row (the ``0.11.x`` row is
labelled with the juniper-ml release, so it moves with the cut). Every pin edit asserts its exact expected text
and must match exactly once. ``AGENTS.md``'s ``**Last Updated**:`` is set to the run's UTC date.

Usage
-----
    python3 util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py [--check]

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
    ("juniper-cascor>=0.11.0", "juniper-cascor>=0.12.0"),
    ("juniper-data>=0.17.0", "juniper-data>=0.17.1"),
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
    ("docs/REFERENCE.md", "|             | `juniper-cascor`                                                                         | `>=0.11.0`        |", "|             | `juniper-cascor`                                                                         | `>=0.12.0`        |", 1),
    ("docs/REFERENCE.md", "|             | `juniper-data`                                                                           | `>=0.17.0`        |", "|             | `juniper-data`                                                                           | `>=0.17.1`        |", 1),
]

_PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
_SELF = "util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py"
_PREFLIGHT = "util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py"

_ENTRY_MARKER = "`[servers]` floors `juniper-cascor>=0.12.0` and `juniper-data>=0.17.1`"
_CL_ENTRY = f"""- **{_ENTRY_MARKER}**, up from `>=0.11.0` and `>=0.17.0`: the two server releases that floor
  the shared security patches (R-ML-SERVERS in §5 of `{_PLAN}`). This is the `[servers]` half of juniper-ml#2314,
  which floored `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0` under `[tools]` and left
  `[servers]` until both releases were on PyPI, because a floor on an unpublished release makes the extra
  unresolvable.
  - **juniper-cascor 0.12.0** (PyPI 2026-10-25) floors both patches unconditionally, so an upgrade of `[servers]`
    over an environment that holds observability 0.4.0 or service-core 0.7.0 now moves them too. It also carries
    cascor's own fixes: a non-ASCII `X-API-Key` is a 401, not a 500 whose Sentry event could carry the real key;
    `FailedAuthThrottle.check()` stays bounded; `APIKeyAuth` checks every configured key; and the CLI's own Sentry
    init stops sending frame-local variables.
  - **juniper-data 0.17.1** (PyPI 2026-10-23) differs from 0.17.0 only in its version string and those two floors,
    measured on the published wheels (the builder's setuptools version aside). Both floors sit under its `[api]`
    extra, and `[servers]` installs bare `juniper-data`, so in a `[servers]` environment the patches arrive through
    cascor 0.12.0. The data floor keeps `[servers]` level with the image juniper-deploy#258 pins.
  - The extras tables in `README.md` (both), `AGENTS.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md` move with
    the pins. The `0.11.x` row of `docs/REFERENCE.md`'s compatibility matrix moves with the release that carries
    this, which is the owner's cut. Applied by `{_SELF}`, which asserts each site's exact text and requires exactly
    one match apiece.
  - **Pre-flighted against real PyPI** on 2026-10-25 with `{_PREFLIGHT}`, which resolves Linux x86_64 wheels and
    installs nothing. `[servers]` resolves in 61 packages and `[all]` in 95, on Python 3.12, 3.13 and 3.14, with
    cascor 0.12.0, data 0.17.1, observability 0.4.1 and service-core 0.7.1 (and juniper-cascor-worker 0.6.1 under
    `[all]`). A control with `juniper-cascor>=0.13.0`, which is not on PyPI, fails it.

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
    """Put the entry first under [Unreleased]'s ``### Security``, creating that heading if absent."""
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
    if section.count("\n### Security\n") > 1:
        raise SystemExit("ERROR: CHANGELOG.md: [Unreleased] has more than one '### Security' heading")
    if "\n### Security\n" in section:
        anchor = section.index("\n### Security\n") + len("\n### Security\n")
        if section[anchor : anchor + 1] != "\n":
            raise SystemExit("ERROR: CHANGELOG.md: '### Security' in [Unreleased] is not followed by a blank line")
        new_section = section[: anchor + 1] + _CL_ENTRY + section[anchor + 1 :]
        how = "first entry under the existing '### Security'"
    else:
        # Keep a Changelog puts Security last, so a new heading closes the section.
        new_section = section.rstrip("\n") + "\n\n### Security\n\n" + _CL_ENTRY.rstrip("\n") + "\n"
        how = "a new '### Security' heading"
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
