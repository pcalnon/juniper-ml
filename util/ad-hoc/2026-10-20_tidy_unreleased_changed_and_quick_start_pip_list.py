#!/usr/bin/env python3
"""Merge [Unreleased]'s two ``### Changed`` headings in CHANGELOG.md and refresh docs/QUICK_START.md's pip-list block.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — one-off (two follow-ups carried by every recurrence-equities handoff since 2026-10-18)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: P5 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py (flagged the duplicate heading and used the first);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-w5-5-w5-6-landed-p5-code-complete-model-0-6-0-gate-parked.md

Why this exists
---------------
1. ``CHANGELOG.md``'s ``[Unreleased]`` section has carried two ``### Changed`` headings since 2026-10-18: the
   0.6.1 floor raise (juniper-ml#2243) added one *after* ``### Added`` when the section had none, and the 0.7.0
   raise (juniper-ml#2262) then found one and put its entry under a new first ``### Changed`` at the top, before
   ``### Added``. Keep a Changelog orders a release's groups Added / Changed / Fixed with one heading each; the
   release train's next cut would copy the duplicate into the release section verbatim. This moves the first
   block's entries to the head of the second block (newest first, as the entries already are within each block)
   and deletes the first heading, so the section reads Added / Changed / Fixed.

2. ``docs/QUICK_START.md`` § "2. Verify" shows what ``pip install juniper-ml[all]`` resolves to. The block still
   described juniper-ml 0.9.0 on 2026-09-22 (``juniper-recurrence 0.5.x``, model ``0.3.x``), two ``[recurrence]``
   raises ago. The versions below are what ``util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`` resolved
   for ``[all]`` against real PyPI on the run date (Python 3.12 / 3.13 / 3.14 agree on every juniper-* version).

Every edit asserts its exact expected text; "new text present, old absent" counts as applied, so the script is
idempotent and safe to re-run on a fresh ``origin/main`` copy before an API upload.

Usage
-----
    python3 util/ad-hoc/2026-10-20_tidy_unreleased_changed_and_quick_start_pip_list.py [--root DIR] [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

_CHANGED = "\n### Changed\n\n"
_ADDED = "\n### Added\n"

#: docs/QUICK_START.md: (exact old text, exact new text). The first pair is the prose, the second the block.
_QS_OLD_PROSE = """Expected output (with `[all]`): 18 lines, one per package. The versions are what `juniper-ml` 0.9.0
resolved to on 2026-09-22. A later release inside each extra's range (the table above) is expected,
not a failure. Two of these packages come in transitively: `juniper-cascor-model` and
`juniper-cascor-protocol`.
"""
_QS_NEW_PROSE = """Expected output (with `[all]`): 18 lines, one per package. The versions are what `juniper-ml` 0.10.0
resolved to on 2026-10-20 (`pip install --dry-run` against PyPI on Python 3.12, 3.13 and 3.14, which agree).
A later release inside each extra's range (the table above) is expected, not a failure. Two of these
packages come in transitively: `juniper-cascor-model` and `juniper-cascor-protocol`.
"""
_QS_OLD_BLOCK = """```bash
juniper-canopy              0.8.x
juniper-cascor              0.11.x
juniper-cascor-client       0.8.x
juniper-cascor-model        0.1.x
juniper-cascor-protocol     0.2.x
juniper-cascor-worker       0.6.x
juniper-ci-tools            0.9.x
juniper-config-tools        0.1.x
juniper-data                0.15.x
juniper-data-client         0.5.x
juniper-doc-tools           0.1.x
juniper-ml                  0.9.0
juniper-model-core          0.3.x
juniper-observability       0.4.x
juniper-recurrence          0.5.x
juniper-recurrence-client   0.3.x
juniper-recurrence-model    0.3.x
juniper-service-core        0.7.x
```
"""
_QS_NEW_BLOCK = """```bash
juniper-canopy              0.9.x
juniper-cascor              0.11.x
juniper-cascor-client       0.8.x
juniper-cascor-model        0.1.x
juniper-cascor-protocol     0.2.x
juniper-cascor-worker       0.6.x
juniper-ci-tools            0.9.x
juniper-config-tools        0.1.x
juniper-data                0.17.x
juniper-data-client         0.6.x
juniper-doc-tools           0.1.x
juniper-ml                  0.10.0
juniper-model-core          0.3.x
juniper-observability       0.4.x
juniper-recurrence          0.7.x
juniper-recurrence-client   0.3.x
juniper-recurrence-model    0.5.x
juniper-service-core        0.7.x
```
"""


def _merge_changed_headings(text: str, check: bool) -> tuple[str, bool]:
    start = text.find("## [Unreleased]\n")
    if start < 0 or text.count("## [Unreleased]\n") != 1:
        raise SystemExit("ERROR: CHANGELOG.md: expected exactly one '## [Unreleased]' heading")
    end = text.find("\n## [", start + 1)
    if end < 0:
        raise SystemExit("ERROR: CHANGELOG.md: no released section follows [Unreleased]")
    section = text[start:end]
    n_changed = section.count("\n### Changed\n")
    if n_changed == 1:
        print("  = CHANGELOG.md [Unreleased]: one '### Changed' heading; already merged")
        return text, False
    if n_changed != 2:
        raise SystemExit(f"ERROR: CHANGELOG.md [Unreleased]: expected 2 '### Changed' headings to merge, found {n_changed}")
    first = section.find(_CHANGED)
    added = section.find(_ADDED)
    if first < 0 or added < 0 or not first < added:
        raise SystemExit("ERROR: CHANGELOG.md [Unreleased]: expected the first '### Changed' block to precede '### Added'")
    entries = section[first + len(_CHANGED) : added]
    if not entries.startswith("- ") or not entries.endswith("\n"):
        raise SystemExit("ERROR: CHANGELOG.md [Unreleased]: the first '### Changed' block is not a run of list entries")
    rest = section[:first] + section[added:]
    second = rest.find(_CHANGED)
    if second < 0 or rest.count("\n### Changed\n") != 1:
        raise SystemExit("ERROR: CHANGELOG.md [Unreleased]: could not locate the surviving '### Changed' block")
    insert_at = second + len(_CHANGED)
    if not rest[insert_at:].startswith("- "):
        raise SystemExit("ERROR: CHANGELOG.md [Unreleased]: the surviving '### Changed' block does not open with an entry")
    merged = rest[:insert_at] + entries + "\n" + rest[insert_at:]
    n_entries = entries.count("\n- **")
    if check:
        print(f"  ~ CHANGELOG.md [Unreleased]: WOULD move {n_entries + 1} entr{'y' if n_entries == 0 else 'ies'} under the surviving '### Changed' and drop the first heading")
        return text, True
    print(f"  + CHANGELOG.md [Unreleased]: moved {n_entries + 1} entr{'y' if n_entries == 0 else 'ies'} under the surviving '### Changed' and dropped the first heading")
    return text[:start] + merged + text[end:], True


def _replace_once(text: str, old: str, new: str, where: str, check: bool) -> tuple[str, bool]:
    if old not in text and text.count(new) == 1:
        print(f"  = {where}: already at target")
        return text, False
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: {where}: expected exactly one occurrence of the old text, found {text.count(old)}")
    if check:
        print(f"  ~ {where}: WOULD rewrite")
        return text, True
    print(f"  + {where}: rewrote")
    return text.replace(old, new, 1), True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="tree to edit (default: this repo); a scratch copy of origin/main before an API upload")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    root = args.root.resolve()

    changed_any = False
    out: dict[Path, str] = {}

    cl_path = root / "CHANGELOG.md"
    text, did = _merge_changed_headings(cl_path.read_text(encoding="utf-8"), args.check)
    changed_any |= did
    if did:
        out[cl_path] = text

    qs_path = root / "docs" / "QUICK_START.md"
    text = qs_path.read_text(encoding="utf-8")
    text, did_a = _replace_once(text, _QS_OLD_PROSE, _QS_NEW_PROSE, "docs/QUICK_START.md [pip list prose]", args.check)
    text, did_b = _replace_once(text, _QS_OLD_BLOCK, _QS_NEW_BLOCK, "docs/QUICK_START.md [pip list block]", args.check)
    changed_any |= did_a or did_b
    if did_a or did_b:
        out[qs_path] = text

    if args.check:
        return 1 if changed_any else 0
    for path, body in out.items():
        path.write_text(body, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
