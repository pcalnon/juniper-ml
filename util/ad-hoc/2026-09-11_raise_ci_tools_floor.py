#!/usr/bin/env python3
"""
Raise a repo's ``juniper-ci-tools`` dependency FLOOR to ``>=0.9.0``.

Project: juniper-ml
Sub-Project: cross-repo tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc -- one fan-out (9 repos), then retire.
Related: juniper-ml#1869 (the 0.8.0 -> 0.9.0 bump),
         util/ad-hoc/2026-09-10_widen_ci_tools_ceiling.py (part 1, the ceilings).

Part 3 of the release sequence from the 2026-09-05 SemVer ruling:

  1. widen the consumer CEILINGS  -- done 2026-09-10, 47 pin lines across 9 repos
  2. cut the Release             -- done 2026-09-11 (juniper-ci-tools-v0.9.0)
  3. raise the FLOORS            -- this script, and ONLY once the wheel is on PyPI

**Run this only after the wheel is actually published.** A floor pinned at a version PyPI
does not serve makes every `pip install` in the range unsatisfiable, which is why the
ordering is strict. ``--require-published`` (default on) refuses unless PyPI serves 0.9.0.

What a floor bump does and does not do
--------------------------------------
It does NOT change what installs. Every pin is a range ``>=X,<0.10.0`` and pip resolves the
newest match, so 0.9.0 is already what lands once it publishes. Raising the floor records
the *requirement* -- that this repo is entitled to assume the working-directory-aware
``juniper-lint-workflow-paths`` -- so a later edit cannot silently reintroduce a version
whose lint reports a false positive on a monorepo lane.

Target set is the same as the ceiling script's: ``.github/workflows/*.yml`` plus
``AGENTS.md``. ``notes/``, ``reports/``, ``prompts/`` and ``util/fleet_triage/`` carry the
old string as historical record and are never rewritten; ``CLAUDE.md`` is a symlink to
``AGENTS.md`` and is never written.

Usage
-----
    python3 util/ad-hoc/2026-09-11_raise_ci_tools_floor.py <worktree-path> [--dry-run]

Exit 0 = rewritten (or dry-run), 1 = nothing to do, 2 = refused.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

TARGET_FLOOR = "0.9.0"
# Only pins already carrying the widened ceiling are touched: a pin still at <0.9.0 means
# part 1 did not land in this repo, and raising its floor would make it unsatisfiable.
OLD = re.compile(r"juniper-ci-tools>=0\.[0-9.]+,<0\.10\.0")
NEW = f"juniper-ci-tools>={TARGET_FLOOR},<0.10.0"
STALE_CEILING = re.compile(r"juniper-ci-tools>=0\.[0-9.]+,<0\.9\.0")


def published(version: str) -> bool:
    with urllib.request.urlopen("https://pypi.org/pypi/juniper-ci-tools/json", timeout=30) as fh:
        return version in json.load(fh)["releases"]


def targets(root: Path) -> list[Path]:
    found = sorted((root / ".github" / "workflows").glob("*.yml"))
    agents = root / "AGENTS.md"
    if agents.is_file() and not agents.is_symlink():
        found.append(agents)
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("worktree", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--require-published", action="store_true", default=True)
    ap.add_argument("--no-require-published", dest="require_published", action="store_false")
    args = ap.parse_args(argv)

    root: Path = args.worktree
    if not (root / ".github" / "workflows").is_dir():
        print(f"ERROR: no .github/workflows/ under {root}", file=sys.stderr)
        return 2

    if args.require_published and not published(TARGET_FLOOR):
        print(
            f"REFUSED: PyPI does not serve juniper-ci-tools {TARGET_FLOOR} yet. A floor at an "
            f"unpublished version makes every pin unsatisfiable -- wait for the pypi environment "
            f"gate to be approved and the publish job to finish.",
            file=sys.stderr,
        )
        return 2

    total = 0
    for path in targets(root):
        text = path.read_text(encoding="utf-8")
        if STALE_CEILING.search(text):
            print(f"ERROR: {path.relative_to(root)} still caps <0.9.0 -- part 1 did not land here", file=sys.stderr)
            return 2
        new_text, count = OLD.subn(NEW, text)
        # subn counts every match, including pins already at the target floor.
        moved = len([m for m in OLD.findall(text) if f">={TARGET_FLOOR}," not in m])
        if count and new_text != text and not args.dry_run:
            path.write_text(new_text, encoding="utf-8")
        if moved:
            total += moved
            print(f"  {'would raise' if args.dry_run else 'raised'} {moved:2d}  {path.relative_to(root)}")

    if not total:
        print(f"nothing to do under {root} (every pin already >={TARGET_FLOOR})")
        return 1

    print(f"{'would raise' if args.dry_run else 'raised'} {total} pin line(s) to >={TARGET_FLOOR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
