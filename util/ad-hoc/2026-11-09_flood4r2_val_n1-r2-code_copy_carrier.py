"""
Copy the n1 round-2 carrier's changed files into a validator worktree and record their checksums.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, n1 r2 code lens)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 11, cascor paused-fit wedge)

Usage: python3 <this> <dest-worktree> <manifest-json-out>

The carrier is read only: ``git status --porcelain`` lists its changed and untracked files and each
is copied byte for byte. Files under ``tmp/`` are skipped (they are the builder's evidence, not the
change). The manifest names every file with its sha256 in the carrier and in the destination.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        digest.update(fh.read())
    return digest.hexdigest()


def _changed_files() -> list:
    out = subprocess.run(["git", "-C", str(CARRIER), "status", "--porcelain", "--untracked-files=all"], check=True, capture_output=True, text=True).stdout
    files = []
    for line in out.splitlines():
        status, name = line[:2], line[3:]
        if name.startswith("tmp/"):
            continue
        if "D" in status:
            files.append((name, "deleted"))
        else:
            files.append((name, status.strip()))
    return files


def main() -> int:
    dest = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2]).resolve()
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    records = []
    for name, status in _changed_files():
        src, dst = CARRIER / name, dest / name
        if status == "deleted":
            if dst.exists():
                dst.unlink()
            records.append({"file": name, "status": status})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        records.append({"file": name, "status": status, "sha256_carrier": _sha256(src), "sha256_dest": _sha256(dst)})
    mismatched = [r["file"] for r in records if r.get("sha256_carrier") != r.get("sha256_dest") and r["status"] != "deleted"]
    manifest = {"carrier": str(CARRIER), "dest": str(dest), "dest_head": head, "files": records, "mismatched": mismatched}
    with open(out_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"copied {len(records)} files into {dest} (HEAD {head[:8]}); mismatched: {mismatched}")
    return 1 if mismatched else 0


if __name__ == "__main__":
    sys.exit(main())
