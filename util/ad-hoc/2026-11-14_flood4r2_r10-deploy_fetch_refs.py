#!/usr/bin/env python3
"""
Copy named files out of sibling repositories' refs (``git show <ref>:<path>``) into a scratch directory, with sha256.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         juniper-data-client#260 (the pilot port); juniper-cascor-client#196 (the second port)

WHY THIS EXISTS
A port starts from the pilot's final files as they sit on that repository's main, and the two new `run:` blocks must
arrive byte-identical to juniper-data's on ITS current main. This host's shell refuses loops and redirects around
git, so the reference copies are taken here: one `git show` per entry, read-only, never a checkout. Each entry's
bytes go to <out>/<name>; a JSON index (name, repo, ref, path, sha256, bytes) goes to <out>/index.json.

Usage:
    python3 <this> --out <directory> --spec <json file: [{"name": "...", "repo": "<abs path>", "ref": "origin/main",
        "path": "<repo-relative>"}, ...]>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - fixed argv: git show of a named ref and path
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path)
    args = ap.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    args.out.mkdir(parents=True, exist_ok=True)
    index = []
    worst = 0
    for entry in spec:
        proc = subprocess.run(["git", "-C", entry["repo"], "show", f"{entry['ref']}:{entry['path']}"], capture_output=True, check=False, timeout=120)  # nosec B603 B607
        if proc.returncode != 0:
            print(f"{entry['name']}: git show exited {proc.returncode}: {proc.stderr.decode(errors='replace').strip()[:200]}")
            worst = 1
            continue
        (args.out / entry["name"]).write_bytes(proc.stdout)
        index.append({**entry, "sha256": hashlib.sha256(proc.stdout).hexdigest(), "bytes": len(proc.stdout)})
        print(f"{entry['name']}: {len(proc.stdout)} bytes")
    (args.out / "index.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")
    return worst


if __name__ == "__main__":
    sys.exit(main())
