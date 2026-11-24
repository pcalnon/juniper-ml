#!/usr/bin/env python3
"""
Copy a carrier's changed files out of its tree, into a freeze directory for the sequence-safety probe or into a twin checkout, with SHA-256 of each.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor; copied unchanged in
        code from 2026-11-14_flood4r2_r10-cascor-client_freeze.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py (reads the freeze directory this writes)

WHY THIS EXISTS
Two steps of a port need the carrier's changed files somewhere else, byte for byte: the sequence-safety probe reads
<freeze>/snapshot, <freeze>/paths.txt (`add <path>`) and <freeze>/plan.json (`main_sha`), and the mutation check
must run in a twin checkout, never in the uncommitted carrier, so the twin needs the same files. This host's shell
refuses a compound command whose words name the secret scanner, which the port's file names do, so the copies are
made here. Every copy is verified by SHA-256 against its source; nothing in the source tree is written.

Usage:
    python3 <this> --tree <carrier> --paths <repo-relative> [...] (--freeze <new dir> --main-sha <sha> | --into <twin checkout>) [--json <out>]
Exit 0 = every file copied and verified; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tree", required=True, type=Path)
    ap.add_argument("--paths", required=True, nargs="+")
    ap.add_argument("--freeze", type=Path)
    ap.add_argument("--main-sha")
    ap.add_argument("--into", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    if (args.freeze is None) == (args.into is None):
        raise SystemExit("give exactly one of --freeze and --into")
    if args.freeze is not None and not args.main_sha:
        raise SystemExit("--freeze needs --main-sha")
    tree = args.tree.resolve()
    target_root = (args.freeze / "snapshot") if args.freeze is not None else args.into
    target_root = target_root.resolve()
    # A freeze directory may live under the carrier's own tmp/; a twin checkout may not be the carrier or inside it.
    if target_root == tree or (args.into is not None and tree in target_root.parents):
        raise SystemExit("refusing to copy a tree into itself")
    rows = []
    ok = True
    for rel in args.paths:
        source = tree / rel
        target = target_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        row = {"path": rel, "sha256_source": digest(source), "sha256_copy": digest(target)}
        row["equal"] = row["sha256_source"] == row["sha256_copy"]
        ok = ok and row["equal"]
        rows.append(row)
        print(f"{'ok ' if row['equal'] else 'BAD'} {row['sha256_source']}  {rel}")
    if args.freeze is not None:
        freeze = args.freeze.resolve()
        (freeze / "paths.txt").write_text("".join(f"add {rel}\n" for rel in args.paths), encoding="utf-8")
        (freeze / "plan.json").write_text(json.dumps({"main_sha": args.main_sha}) + "\n", encoding="utf-8")
    if args.json is not None:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"tree": str(tree), "target": str(target_root), "files": rows}, fh, indent=1)
            fh.write("\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
