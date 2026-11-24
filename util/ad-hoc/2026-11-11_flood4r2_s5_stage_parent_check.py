#!/usr/bin/env python3
"""
Check that a cumulative landing stage was built on what main now holds: for every path the stage changes, main's copy
must be byte-identical to the parent copy the stage's manifest recorded, and the frozen copy to the stage's own.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: landing juniper-data's three carriers as cumulative stages)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (writes <freeze>/main and <freeze>/snapshot),
         tmp/flood4/session5/data-landing/stage<N>/manifest.json (files[]: path, status, sha256, parent_sha256)

Usage:
  2026-11-11_flood4r2_s5_stage_parent_check.py <stage manifest.json> <freeze dir>

A stage N tree is "the tree stage N-1 produced, plus this stage's change". It is valid to land on a main only when that
main equals stage N-1's tree on every path stage N touches. The manifest records each path's parent copy as
``parent_sha256`` (absent or null for a file the stage adds). This compares it with <freeze>/main/<path> (main's copy at
freeze time; no file there for an added path), and compares ``sha256`` with <freeze>/snapshot/<path> (what will be
pushed). Exit 0 = every path matches on both sides; 1 = at least one differs (each is printed) and the freeze must not
be pushed: rebuild that path on the live main first.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    manifest = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    freeze = Path(argv[2])
    bad = 0
    for entry in manifest["files"]:
        path = entry["path"]
        parent_expected = entry.get("parent_sha256")
        parent_actual = sha256_of(freeze / "main" / path)
        frozen_actual = sha256_of(freeze / "snapshot" / path)
        parent_ok = parent_actual == parent_expected
        frozen_ok = frozen_actual == entry["sha256"]
        bad += (not parent_ok) + (not frozen_ok)
        parent_text = "main == parent" if parent_ok else f"MAIN DIFFERS FROM PARENT (main {str(parent_actual)[:12]}, parent {str(parent_expected)[:12]})"
        frozen_text = "frozen == stage" if frozen_ok else f"FROZEN DIFFERS FROM STAGE (frozen {str(frozen_actual)[:12]}, stage {entry['sha256'][:12]})"
        print(f"{'ok ' if parent_ok and frozen_ok else 'BAD'}  {path}: {parent_text}; {frozen_text}")
    print(f"paths: {len(manifest['files'])}  mismatches: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
