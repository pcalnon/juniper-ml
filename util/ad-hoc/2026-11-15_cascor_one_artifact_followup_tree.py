#!/usr/bin/env python3
"""Build juniper-cascor's follow-up to #763 on a fresh main: the review changes, and nothing main gained since.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the follow-up pull request that carries juniper-cascor#763's review changes)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (writes both trees this compares)

Why
---
juniper-cascor#763 was squash-merged with its first commit before its review changes were pushed. The review changes
must therefore reach ``main`` in a new pull request, and ``util/open_signed_pr.py`` uploads WHOLE files. For each path:

- when ``main``'s copy still equals what #763 merged (``--merged``), the reviewed final copy (``--final``) is uploaded,
  so the pull request's diff is exactly the review changes;
- ``CHANGELOG.md`` takes ``main``'s copy, with #763's entry (the block ``--merged`` added to ``--merged-base``) replaced,
  exactly once, by the reviewed entry (the block ``--final`` added to the same base), so later entries survive;
- any other path ``main`` changed since is refused: it needs a hand merge.

    python3 -I util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py --main <main tree> --merged-base <#763's base tree> \\
        --merged <#763's tree> --final <reviewed tree> --out <empty directory> PATH [PATH ...]

Exit status: 0 when every path was written; 1 when one was refused (nothing written).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import shutil
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inserted_block(before: str, after: str) -> str:
    """The one contiguous block of lines ``after`` adds to ``before``; refuse anything else."""
    a, b = before.splitlines(keepends=True), after.splitlines(keepends=True)
    ops = [op for op in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes() if op[0] != "equal"]
    if len(ops) != 1 or ops[0][0] != "insert":
        raise SystemExit(f"REFUSED: expected one inserted block, found {[op[0] for op in ops]}")
    _, _, _, j1, j2 = ops[0]
    return "".join(b[j1:j2])


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--merged-base", required=True, type=Path)
    parser.add_argument("--merged", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    if args.out.exists():
        print(f"REFUSED: {args.out} exists")
        return 1
    written: dict[str, bytes] = {}
    for rel in args.paths:
        on_main, merged, final = args.main / rel, args.merged / rel, args.final / rel
        if on_main.is_file() and digest(on_main) == digest(merged):
            written[rel] = final.read_bytes()
            print(f"final copy    {rel}")
        elif rel == "CHANGELOG.md":
            old = inserted_block((args.merged_base / rel).read_text(encoding="utf-8"), merged.read_text(encoding="utf-8"))
            new = inserted_block((args.merged_base / rel).read_text(encoding="utf-8"), final.read_text(encoding="utf-8"))
            text = on_main.read_text(encoding="utf-8")
            if text.count(old) != 1:
                print(f"REFUSED: {rel}: main holds #763's entry {text.count(old)} times, expected 1")
                return 1
            written[rel] = text.replace(old, new).encode("utf-8")
            print(f"entry swapped {rel} ({len(old.splitlines())} lines -> {len(new.splitlines())})")
        else:
            print(f"REFUSED: {rel} changed on main since #763 merged: merge it by hand")
            return 1
    shutil.copytree(args.main, args.out, symlinks=True)
    for rel, data in written.items():
        (args.out / rel).parent.mkdir(parents=True, exist_ok=True)
        (args.out / rel).write_bytes(data)
    print(f"wrote {len(written)} path(s) into {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
