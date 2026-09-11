#!/usr/bin/env python3
"""
Widen a repo's ``juniper-ci-tools`` dependency CEILING from ``<0.9.0`` to ``<0.10.0``.

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-09-10
Status: ad-hoc -- one fan-out (8 repos), then retire.
Related: juniper-ml#1869 (the 0.8.0 -> 0.9.0 bump this exists to unblock),
         juniper-ml#1836 (the lint false positive 0.9.0 fixes).

Why this exists
---------------
juniper-ci-tools 0.9.0 adds public API, so it is a MINOR bump. Every consumer currently
caps the dependency at ``<0.9.0``, which means the 0.9.0 wheel would reach **none** of
them. Per the 2026-09-05 ruling (juniper-cascor-client 0.7.1 -> 0.8.0): version from the
change, then fix whatever the number breaks -- and the fix is a two-part change with a
strict order. Part 1, here, is widening the CEILINGS, and it must land **before** the
Release is cut or the artefact is uninstallable. Part 2, raising the FLOORS to ``>=0.9.0``,
waits until the wheel is actually on PyPI -- a floor pinned at an unpublished version
resolves nothing.

Widening a ceiling is safe and inert: it only admits more versions. CI keeps installing
0.8.0 until 0.9.0 publishes, so nothing changes behaviourally on merge. It also needs no
lockfile refresh -- the resolved pin is fixed by ``--constraint requirements.lock``, so a
wider ceiling leaves the sorted-pins diff identical (only a FLOOR bump forces a regen).

What it rewrites
----------------
``.github/workflows/*.yml`` and ``AGENTS.md`` only. ``CLAUDE.md`` is a symlink to
``AGENTS.md`` in every repo that has one, so it is deliberately NOT written -- writing it
would replace the symlink with a regular file.

``notes/``, ``reports/``, ``prompts/`` and ``util/fleet_triage/predict_merge.py`` also
contain the old string and are deliberately skipped: they are historical records of what
a pin *was*, not live pins.

The lower bound is preserved exactly (``>=0.1.0``, ``>=0.6.0`` and ``>=0.8.0`` all occur);
only the upper bound moves.

Usage
-----
    python3 util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py <worktree-path> [--dry-run]

Exit 0 = rewritten (or dry-run), 1 = nothing to do, 2 = refused (path missing, or a
``<0.9.0`` reference survived the rewrite).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OLD = re.compile(r"(juniper-ci-tools>=0\.[0-9.]+,)<0\.9\.0")
NEW = r"\1<0.10.0"
STALE = re.compile(r"juniper-ci-tools>=0\.[0-9.]+,<0\.9\.0")


def targets(root: Path) -> list[Path]:
    """Live-pin files only: the workflows, plus AGENTS.md when present."""
    found = sorted((root / ".github" / "workflows").glob("*.yml"))
    agents = root / "AGENTS.md"
    if agents.is_file() and not agents.is_symlink():
        found.append(agents)
    return found


def rewrite(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    new_text, count = OLD.subn(NEW, text)
    if count and not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return count


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("worktree", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    root: Path = args.worktree
    if not (root / ".github" / "workflows").is_dir():
        print(f"ERROR: no .github/workflows/ under {root}", file=sys.stderr)
        return 2

    total = 0
    for path in targets(root):
        n = rewrite(path, args.dry_run)
        if n:
            total += n
            print(f"  {'would rewrite' if args.dry_run else 'rewrote'} {n:2d}  {path.relative_to(root)}")

    if not total:
        print(f"nothing to do under {root}")
        return 1

    print(f"{'would widen' if args.dry_run else 'widened'} {total} pin line(s)")

    if args.dry_run:
        return 0

    # Refuse to report success while a live <0.9.0 pin survives. Scoped to the files this
    # script owns -- a match in notes/ is a historical record and must NOT be rewritten.
    survivors = [p.relative_to(root) for p in targets(root) if STALE.search(p.read_text(encoding="utf-8"))]
    if survivors:
        print(f"ERROR: <0.9.0 still present in {survivors}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
