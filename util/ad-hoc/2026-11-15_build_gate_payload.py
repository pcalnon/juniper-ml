#!/usr/bin/env python3
"""Build the pre-push gate's payload directory: the files to be pushed, the public text, and the added lines alone.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the release-train gap fixes and the one-artifact publish ports)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_pre_push_gate_run.bash (the gate this feeds: PAYLOAD_DIR/files, text, added)

Why
---
The plan's §9 gate scans exactly the files to be pushed and every other public text, then gives a masked read of the
ADDED lines. Building those three directories by hand for each push is where a file gets left out; this derives them
from the same path list the upload uses. A path absent from the base tree counts as wholly added.

    python3 -I util/ad-hoc/2026-11-15_build_gate_payload.py --out PAYLOAD_DIR --tree TREE --base-tree BASE \\
        --text FILE [--text FILE ...] REL [REL ...]

Exit status: 0; 2 when PAYLOAD_DIR exists or a named file is missing.
"""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from pathlib import Path


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--base-tree", required=True, type=Path)
    parser.add_argument("--text", action="append", default=[], type=Path)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    if args.out.exists():
        print(f"REFUSED: {args.out} exists")
        return 2
    missing = [p for p in args.paths if not (args.tree / p).is_file()] + [str(t) for t in args.text if not t.is_file()]
    if missing:
        print(f"REFUSED: missing {missing}")
        return 2
    for sub in ("files", "text", "added"):
        (args.out / sub).mkdir(parents=True)
    total = 0
    for rel in args.paths:
        new = (args.tree / rel).read_text(encoding="utf-8").splitlines(keepends=True)
        base_path = args.base_tree / rel
        old = base_path.read_text(encoding="utf-8").splitlines(keepends=True) if base_path.is_file() else []
        (args.out / "files" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.tree / rel, args.out / "files" / rel)
        added = [line[1:] for line in difflib.unified_diff(old, new, n=0) if line.startswith("+") and not line.startswith("+++")]
        (args.out / "added" / (rel.replace("/", "__") + ".added")).write_text("".join(added), encoding="utf-8")
        total += len(added)
        print(f"{len(added):5d} added line(s)  {rel}{'' if old else '  (new)'}")
    for text in args.text:
        shutil.copyfile(text, args.out / "text" / text.name)
    print(f"{len(args.paths)} file(s), {total} added line(s), {len(args.text)} text file(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
