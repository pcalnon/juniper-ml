"""
Rebuild a D-14 carrier three-way onto a newer main: every file the carrier modified becomes
``git merge-file -p <carrier copy> <old base copy> <new main copy>``; every file it added (and every provenance
helper) is copied as it is. The three inputs, the merged output and a summary (conflict count per file) are kept
under ``--evidence`` so that each resolution can be checked afterwards.

The carrier's files are READ from ``--from-root`` (which may be another checkout: only plain file reads happen
there); the old base and the new main blobs are read with ``git show`` from ``--repo``; results are written under
``--to-root``. A file with conflicts is written WITH its conflict markers (resolve by hand, then re-run the stamps
helper); the exit status is 0 when no file conflicts, 1 when any does, 2 on an error.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_rebuild.py --repo <checkout holding the objects>
        --from-root <carrier as it is> --to-root <tree on the new main> --manifest <carrier manifest.json>
        --base <old base sha> --main <new main sha> --evidence <dir> [--helpers]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def blob(repo: Path, rev: str, rel: str) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"], capture_output=True, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"git show {rev}:{rel} failed: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--from-root", required=True, type=Path)
    parser.add_argument("--to-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--helpers", action="store_true", help="also copy the manifest's provenance_helpers")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = list(manifest["files"])
    if args.helpers:
        entries += [dict(entry, status="added") for entry in manifest.get("provenance_helpers", [])]

    summary = {"base": args.base, "main": args.main, "from_root": str(args.from_root), "to_root": str(args.to_root), "files": []}
    conflicted = 0
    for entry in entries:
        rel = entry["path"]
        source = args.from_root / rel
        target = args.to_root / rel
        ours = source.read_bytes()
        row = {"path": rel, "status": entry["status"], "carrier_sha256": sha(ours)}
        if entry["status"] == "added":
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            row["action"] = "copied"
            row["result_sha256"] = sha(target.read_bytes())
        elif entry["status"] == "modified":
            base = blob(args.repo, args.base, rel)
            theirs = blob(args.repo, args.main, rel)
            work = args.evidence / rel.replace("/", "__")
            work.mkdir(parents=True, exist_ok=True)
            (work / "carrier").write_bytes(ours)
            (work / "base").write_bytes(base)
            (work / "main").write_bytes(theirs)
            done = subprocess.run(
                ["git", "merge-file", "-p", "-L", "carrier", "-L", f"base {args.base[:8]}", "-L", f"main {args.main[:8]}", str(work / "carrier"), str(work / "base"), str(work / "main")],
                capture_output=True,
                check=False,
            )
            if done.returncode < 0 or done.returncode > 127:
                print(f"merge-file error on {rel}: {done.stderr.decode(errors='replace')}", file=sys.stderr)
                return 2
            (work / "merged").write_bytes(done.stdout)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(done.stdout)
            row.update(
                action="merged",
                conflicts=done.returncode,
                main_changed=sha(base) != sha(theirs),
                carrier_kept_unchanged=done.stdout == ours,
                result_sha256=sha(done.stdout),
            )
            conflicted += 1 if done.returncode else 0
        else:
            print(f"unsupported status {entry['status']} for {rel}", file=sys.stderr)
            return 2
        summary["files"].append(row)

    summary["conflicted_files"] = conflicted
    args.evidence.mkdir(parents=True, exist_ok=True)
    (args.evidence / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    for row in summary["files"]:
        extra = f" conflicts={row['conflicts']} main_changed={row['main_changed']}" if row["action"] == "merged" else ""
        print(f"{row['action']:7} {row['path']}{extra}")
    print(f"conflicted files: {conflicted}")
    return 1 if conflicted else 0


if __name__ == "__main__":
    sys.exit(main())
