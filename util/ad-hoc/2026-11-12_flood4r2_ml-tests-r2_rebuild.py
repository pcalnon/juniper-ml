#!/usr/bin/env python3
"""
Rebuild the predecessor's carrier files on the current origin/main (round 2 of the flood-4 "ml-tests" carrier).

Round 1 built the carrier as an uncommitted tree on an older main (--base). For every path its manifest lists:

  * main did not change the path since --base (or it exists in neither)  -> the predecessor's copy is COPIED;
  * main changed it  -> `git merge-file -p <predecessor's copy> <base's copy> <main's copy>` is run, its output and
    conflict count are kept under <scratch>/merge_raw/, and
      - a path named in --rederive is NOT written from the merge: its registrations, counts and stamps are
        re-derived on main's copy by the wiring tools (the merge output is kept as the cross-check);
      - any other path is written from the merge when it has no conflict, and refused when it has one.

Also kept, per modified path, under <scratch>/p_diffs/: the base copy and the predecessor's unified diff against it
(what round 1 changed, for the "nothing lost" comparison).

Usage (from this worktree's root, HEAD = origin/main):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_rebuild.py --predecessor <abs dir> --manifest <abs json>
        --base <sha> --scratch <dir> [--rederive PATH ...] [--skip-prefix util/ad-hoc/] [--dry-run]

Exit 0 when every path was copied, merged cleanly, or left to re-derivation; 1 when a merge outside --rederive
has a conflict.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (a carrier on an older base is rebuilt three-way)
"""

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _git(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], capture_output=True, check=False)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--predecessor", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--rederive", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    pred, scratch = Path(args.predecessor), Path(args.scratch)
    raw_dir, diff_dir = scratch / "merge_raw", scratch / "p_diffs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)
    with open(args.manifest, encoding="utf-8") as fh:
        files = json.load(fh)["files"]
    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    rows, failed = [], False
    for entry in files:
        path = entry["path"]
        flat = path.replace("/", "__")
        src = pred / path
        base_blob = _git("show", f"{args.base}:{path}")
        main_blob = _git("show", f"HEAD:{path}")
        in_base, in_main = base_blob.returncode == 0, main_blob.returncode == 0
        row = {"path": path, "predecessor_status": entry["status"], "predecessor_sha256": _sha(src), "in_base": in_base, "in_main": in_main}
        if in_base:
            (diff_dir / f"{flat}.base").write_bytes(base_blob.stdout)
            delta = difflib.unified_diff(base_blob.stdout.decode().splitlines(True), src.read_text(encoding="utf-8").splitlines(True), f"base/{path}", f"predecessor/{path}")
            (diff_dir / f"{flat}.diff").write_text("".join(delta), encoding="utf-8")
        main_moved = (in_base != in_main) or (in_base and base_blob.stdout != main_blob.stdout)
        row["main_changed_since_base"] = main_moved
        dest = Path(path)
        if not main_moved:
            row["how"] = "copied"
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
        else:
            base_file, main_file = raw_dir / f"{flat}.base", raw_dir / f"{flat}.main"
            base_file.write_bytes(base_blob.stdout if in_base else b"")
            main_file.write_bytes(main_blob.stdout if in_main else b"")
            merged = _git("merge-file", "-p", "-L", "predecessor", "-L", "base", "-L", "main", str(src), str(base_file), str(main_file))
            (raw_dir / f"{flat}.raw").write_bytes(merged.stdout)
            row["merge_conflicts"] = merged.returncode
            if path in args.rederive:
                row["how"] = "re-derived"
                row["note"] = "left at main's copy here; registrations, counts and stamps are applied by the wiring tools"
            elif merged.returncode == 0:
                row["how"] = "three-way"
                if not args.dry_run:
                    dest.write_bytes(merged.stdout)
            else:
                row["how"] = "REFUSED: three-way conflict outside --rederive"
                failed = True
        if not args.dry_run and row["how"] in ("copied", "three-way"):
            row["sha256"] = _sha(dest)
            row["identical_to_predecessor"] = row["sha256"] == row["predecessor_sha256"]
        rows.append(row)
        print(f"{row['how']:<11} {path}" + (f"  (merge conflicts: {row['merge_conflicts']})" if "merge_conflicts" in row else ""))
    with open(scratch / "rebuild.json", "w", encoding="utf-8") as fh:
        json.dump({"head": head, "base": args.base, "predecessor": str(pred), "rows": rows}, fh, indent=2)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
