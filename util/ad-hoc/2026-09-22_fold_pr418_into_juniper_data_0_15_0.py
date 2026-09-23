#!/usr/bin/env python3
"""Fold juniper-data#418's [Unreleased] entry into the [0.15.0] section it will ship in.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-data 0.15.0 release, post-bump merge)

Why this exists
---------------
juniper-data#418 (``allow_truncation`` becomes a tri-state) merged AFTER the 0.15.0
version bump (#416) and correctly filed its entry under ``[Unreleased]``. That is the right
place for a normal change and the wrong place for this one, because **the Release creates
the tag at the current branch head** — so ``v0.15.0`` tags a tree that already contains
#418's generator code:

    juniper_data/generators/csv_import/generator.py    +57/-…
    juniper_data/generators/equities/generator.py      +52/-…
    juniper_data/generators/equities_seq/generator.py   +5/-…
    ... plus both params.py

The feature therefore ships in the 0.15.0 wheel either way. The only question is whether
the notes describe it, and a Release body is not re-cuttable. Leaving the entry where it is
would also mean a later 0.16.0 documents a feature that shipped in 0.15.0.

It is a behavioural reversal, not a tidy-up — its own entry says it "REVERSES a deliberate,
documented, test-pinned rule" — which is exactly the kind of change release notes exist for.

#417 is left alone: ``docs/DEVELOPER_CHEATSHEET.md`` only, nothing shipped.

A duplicate ``### Changed`` heading inside ``[0.15.0]`` is safe and intended:
``ceremony.changelog_version_section`` documents that a repeated category heading MERGES
rather than replaces.

This writes to a ``--root`` COPY, never the shared sibling checkout.

Idempotent: exits 0 without writing if [Unreleased] is already empty.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_VERSION_HEADING = "## [0.15.0] - 2026-09-22"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, help="path to the juniper-data tree to edit")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    target = Path(args.root) / "CHANGELOG.md"
    if not target.is_file():
        print(f"ERROR: no such file: {target}", file=sys.stderr)
        return 1

    text = target.read_text(encoding="utf-8")

    unrel = "## [Unreleased]\n"
    if text.count(unrel) != 1:
        print(f"ERROR: expected exactly one '## [Unreleased]', found {text.count(unrel)}", file=sys.stderr)
        return 1
    if text.count(_VERSION_HEADING) != 1:
        print(f"ERROR: expected exactly one {_VERSION_HEADING!r}", file=sys.stderr)
        return 1

    start = text.index(unrel) + len(unrel)
    ver_at = text.index(_VERSION_HEADING)
    body = text[start:ver_at].strip("\n")

    if not body:
        print("[Unreleased] is already empty; nothing to fold")
        return 0

    if args.check:
        print(f"WOULD FOLD {len(body.splitlines())} lines from [Unreleased] into {_VERSION_HEADING}")
        return 1

    ver_end = ver_at + len(_VERSION_HEADING)
    rebuilt = text[:start] + "\n" + _VERSION_HEADING + "\n\n" + body + "\n" + text[ver_end:]

    target.write_text(rebuilt, encoding="utf-8")
    print(f"folded {len(body.splitlines())} lines into {_VERSION_HEADING}; [Unreleased] left empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
