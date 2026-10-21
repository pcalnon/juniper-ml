#!/usr/bin/env python3
"""Add the release-train proposal's README compatibility-table fix to CHANGELOG.md's [Unreleased] ### Fixed, on a fresh copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (the CHANGELOG half of the propose.py README fix; kept so a silent revert costs one re-run)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/release_train/propose.py set_readme_compat_version / _README_COMPAT_HEADING; tests/test_release_train_propose.py;
         util/ad-hoc/2026-10-21_apply_propose_pr_body_limit_changelog.py (the previous propose.py fix, same shape)

Why
---
CHANGELOG.md lands from turing as its own signed commit built from a fresh ``git show origin/main:CHANGELOG.md``
copy, so the insertion point is found rather than anchored on whichever entry is first today. Unlike the previous
fix's script, this one must also handle the [Unreleased] that a release cut leaves empty (juniper-ml 0.11.0,
2026-10-21): with no ``### Fixed`` heading it adds one, before ``### Security`` if that exists (the Keep a Changelog
order), else at the end of the section.

Usage
-----
    python3 util/ad-hoc/2026-10-21_apply_propose_readme_compat_changelog.py --root DIR [--check]

``--root`` holds ``CHANGELOG.md``. The entry goes first under [Unreleased]'s ``### Fixed``. If the section holds more
than one ``### Fixed`` heading, the script refuses and writes nothing. An entry already present is skipped, so a
re-run is a no-op. ``--check`` reports applied / pending and exits 1 when pending.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER = "- **The release-train proposal now moves README's \"Ecosystem Compatibility\" table**"

ENTRY = """\
- **The release-train proposal now moves README's "Ecosystem Compatibility" table**, so a generated juniper-ml
  proposal is green as generated. `tests/test_pyproject_extras.py` `ReadmeCompatTableTest` holds that table to
  `pyproject.toml` in two ways, and `util/release_train/propose.py` satisfied neither.
  - **The lead-in.** "The pyproject pins matching `juniper-ml` X:" must name the pyproject version, and the
    generator never moved it. The 0.11.0 proposal (#2306) was the first generated since that guard landed (#1972).
    Its bare form fails Regression Tests with `'0.10.0' != '0.11.0'`, and #2306 carried a hand co-change commit. The
    meta's own bump now rewrites the line. A missing lead-in is never invented; the co-change checklist flags it
    REQUIRED instead.
  - **The rows.** Each pin also has a split-column Package / Pin row, and step 5b-ii moved only README's
    `### Extras` table, so an escaping in-repo bump shipped red. Simulated on `main`, the juniper-config-tools
    0.2.0 proposal (against the meta's `<0.2.0` ceiling) fails `test_compat_table_matches_pyproject`. The
    split-column editor `docs/REFERENCE.md` already used, re-anchored on `## Ecosystem Compatibility`, now moves the
    row in the same README edit as the extras table.
  - The proposal PR body no longer tells the reviewer of every escaping bump that the generator "has a known gap"
    and "will fail 3 arms". #1460 added that warning, and #1478 closed the gap a day later without removing it.
  - `docs/REFERENCE.md`'s compatibility sentence and matrix row remain a manual co-change for the meta's own bump,
    and the co-change checklist now says so.
  - New: `util/ad-hoc/2026-10-21_simulate_release_proposal.py` builds one proposal on a scratch copy and runs the 17
    suites that read the version, the pins, README or REFERENCE, against an untouched baseline. Both proposals
    above regress one suite on `main` and none with the fix. Ten new tests in
    `tests/test_release_train_propose.py`, eight of which fail against `main`'s module.
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
    section = text[start.end() : end]
    fixed = list(re.finditer(r"^### Fixed[ \t]*\n\n", section, re.MULTILINE))
    if len(fixed) > 1:
        return None, f"REFUSED, [Unreleased] holds {len(fixed)} '### Fixed' headings (expected at most 1)"
    if fixed:
        at = start.end() + fixed[0].end()
        return text[:at] + ENTRY + "\n" + text[at:], "pending"
    # No ### Fixed yet: add one before ### Security (Keep a Changelog order), else at the end of the section.
    security = re.search(r"^### Security[ \t]*\n", section, re.MULTILINE)
    at = start.end() + security.start() if security else end
    head = text[:at].rstrip("\n") + "\n\n"
    return head + "### Fixed\n\n" + ENTRY + "\n" + text[at:].lstrip("\n"), "pending"


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
