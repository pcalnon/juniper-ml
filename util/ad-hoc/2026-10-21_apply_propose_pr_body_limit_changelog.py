#!/usr/bin/env python3
"""Add the release-train proposal's PR-body-limit fix to CHANGELOG.md's [Unreleased] ### Fixed, on a fresh copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (the CHANGELOG half of the propose.py PR-body fix; kept so a silent revert costs one re-run)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/release_train/propose.py PR_BODY_MAX / _fitted_pr_body; tests/test_release_train_propose.py;
         util/ad-hoc/2026-10-21_apply_detect_pyproject_table_changelog.py (the detector fix this follows, same shape)

Why
---
CHANGELOG.md lands from turing as its own signed commit built from a fresh ``git show origin/main:CHANGELOG.md``
copy, so the insertion point is found -- the first ``### Fixed`` heading inside ``## [Unreleased]`` -- rather than
anchored on whichever entry is first today.

Usage
-----
    python3 util/ad-hoc/2026-10-21_apply_propose_pr_body_limit_changelog.py --root DIR [--check]

``--root`` holds ``CHANGELOG.md``. The entry goes first under [Unreleased]'s ``### Fixed``; if the section has no
``### Fixed`` heading, or holds more than one, the script refuses and writes nothing. An entry already present is
skipped, so a re-run is a no-op. ``--check`` reports applied / pending and exits 1 when pending.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER = "- **The release-train proposal keeps its PR body under GitHub's 65,536-character limit**"

ENTRY = """\
- **The release-train proposal keeps its PR body under GitHub's 65,536-character limit**, and refuses an
  over-long one before any write. `util/release_train/propose.py` inlined the whole drafted release notes in the
  proposal PR body, and `execute_proposal` opens the PR only after the release branch and its signed commit
  exist. juniper-ml 0.11.0's draft is 88,548 B, so its body came to 90,219 characters, which GitHub refuses
  ("Body is too long"), and `--execute` would have left `release/juniper-ml-v0.11.0` and its commit with no PR
  (the juniper-ml#2227 half-written class). A draft that would carry the body past the limit, counted in UTF-8
  bytes (never fewer than characters), is now replaced by a pointer to the `[<version>]` section that the PR's own
  CHANGELOG diff shows in full; the ceremony's archive PR still carries the final notes. `execute_proposal`
  raises before `create_branch` when a body is still over the limit. The 0.11.0 body is now 1,909 B. Four tests
  in `tests/test_release_train_propose.py`.
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
    fixed = list(re.finditer(r"^### Fixed[ \t]*\n\n", text[start.end() : end], re.MULTILINE))
    if len(fixed) != 1:
        return None, f"REFUSED, [Unreleased] holds {len(fixed)} '### Fixed' headings (expected 1)"
    at = start.end() + fixed[0].end()
    return text[:at] + ENTRY + "\n" + text[at:], "pending"


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
