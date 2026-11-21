#!/usr/bin/env python3
"""
Rebuild the ml-code carrier (round 3) on current origin/main: copy the round-2 carrier's files, three-way the rest.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3 rebuild)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; the round-2 carrier's
         tmp/flood4r2/ml-code/r2/manifest.json; validator findings ml-code-port-lens F6 and ml-code-claims-lens
         F1 / F10 (a plain copy of the carrier's shared files would revert what main gained since its base).

Usage (from the round-3 worktree root, HEAD at the origin/main the carrier is rebuilt on):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebuild.py <round-2 carrier root> <round-2 base sha> <out dir>

Reads the round-2 manifest (tmp/flood4r2/ml-code/r2/manifest.json under the carrier root) and checks every listed
file's sha256 in the carrier against it. A file that HEAD did not change since the round-2 base is copied (its mode
too, when it is new here).
A file that HEAD changed is rebuilt with ``git merge-file -p <carrier's copy> <base's copy> <HEAD's copy>``; the
three inputs and the merge go to <out dir>/rebuild/, and a merge with conflicts is written with its markers for
the resolve step. Writes <out dir>/rebuild/rebuild.json. The carrier is only read. Exit 1 on a sha256 mismatch.
"""
import hashlib
import json
import shutil
import subprocess  # nosec B404 -- fixed git argv, run in this worktree
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, check=False)  # nosec B603 B607 -- fixed argv


def main() -> int:
    carrier = Path(sys.argv[1]).resolve()
    base = sys.argv[2]
    out = Path(sys.argv[3]).resolve() / "rebuild"
    out.mkdir(parents=True, exist_ok=True)
    root = Path.cwd()
    with open(carrier / "tmp" / "flood4r2" / "ml-code" / "r2" / "manifest.json", encoding="utf-8") as fh:
        manifest = json.load(fh)
    changed = set(git("diff", "--name-only", base, "HEAD").stdout.decode("utf-8").splitlines())
    report = {"carrier": str(carrier), "base": base, "head": git("rev-parse", "HEAD").stdout.decode().strip(), "files": []}
    for entry in manifest["files"]:
        rel = entry["path"]
        source = carrier / rel
        actual = sha256(source)
        row = {"path": rel, "status": entry["status"], "carrier_sha256": actual, "manifest_sha256_matches": actual == entry["sha256"]}
        target = root / rel
        if rel in changed:
            stem = rel.replace("/", "__")
            base_copy, head_copy, carrier_copy = out / (stem + ".base"), out / (stem + ".main"), out / (stem + ".carrier")
            base_copy.write_bytes(git("show", "%s:%s" % (base, rel)).stdout)
            head_copy.write_bytes(git("show", "HEAD:%s" % rel).stdout)
            shutil.copyfile(source, carrier_copy)
            merged = git("merge-file", "-p", str(carrier_copy), str(base_copy), str(head_copy))
            (out / (stem + ".merged")).write_bytes(merged.stdout)
            target.write_bytes(merged.stdout)
            row.update({"rebuilt": "git merge-file -p <carrier> <base> <HEAD>", "merge_file_exit": merged.returncode, "conflicts": merged.returncode})
        else:
            existed = target.exists()
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if not existed:
                shutil.copymode(source, target)
            row["copied"] = sha256(target) == actual
            row["head_had_it"] = existed
        report["files"].append(row)
        print("%-72s %s" % (rel, "merge-file exit %d" % row["merge_file_exit"] if "merge_file_exit" in row else "copied"))
    with open(out / "rebuild.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    bad = [row["path"] for row in report["files"] if not row["manifest_sha256_matches"]]
    print("HEAD %s; files HEAD changed since %s that the carrier also changes: %s" % (report["head"], base[:8], sorted(r["path"] for r in report["files"] if "rebuilt" in r)))
    print("manifest sha256 mismatches: %s" % (bad or "none"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
