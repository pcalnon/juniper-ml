"""
Record, per carried draft, how the carried file differs from the draft's head blob (the carrier's fixes).

For every new test file taken from a draft head (take_blobs.json, written by
2026-11-09_flood4r2_ml-tests_take_blobs.py), writes <scratch>/fix_diffs/pr<N>_<file>.diff.txt: a unified diff from
the draft's blob to the file as it now stands. An empty diff means the file is carried byte-for-byte. For a draft
whose hunks were applied to an existing file (#2480, #2507), the carrier's whole diff of that file against the
base is written instead, to read beside the draft's own diff in <scratch>/own/. Prints one summary line per file.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_fix_diffs.py --scratch <dir> --base <sha> [N:path ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt (manifest "fixes": what the carrier changed vs the draft, and why)
"""

import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("modified", nargs="*", help="N:path of an existing file a draft's hunks were applied to")
    args = ap.parse_args()
    out = Path(args.scratch) / "fix_diffs"
    out.mkdir(parents=True, exist_ok=True)
    with open(Path(args.scratch) / "take_blobs.json", encoding="utf-8") as fh:
        taken = json.load(fh)
    for row in taken:
        blob = subprocess.run(["git", "cat-file", "blob", row["blob"]], capture_output=True, text=True, check=True).stdout
        final = Path(row["path"]).read_text(encoding="utf-8")
        diff = "".join(difflib.unified_diff(blob.splitlines(True), final.splitlines(True), f"draft #{row['pr']} head blob {row['blob'][:12]}", f"carried {row['path']}"))
        name = f"pr{row['pr']}_{Path(row['path']).stem}.diff.txt"
        (out / name).write_text(diff, encoding="utf-8")
        changed = sum(1 for ln in diff.splitlines() if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
        print(f"#{row['pr']} {row['path']}: {'byte-for-byte' if not diff else f'{changed} changed lines'}")
    for item in args.modified:
        n, path = item.split(":", 1)
        diff = subprocess.run(["git", "diff", args.base, "--", path], capture_output=True, text=True, check=True).stdout
        (out / f"pr{n}_{Path(path).stem}.carrier.diff.txt").write_text(diff, encoding="utf-8")
        print(f"#{n} {path}: carrier diff written ({len(diff.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
