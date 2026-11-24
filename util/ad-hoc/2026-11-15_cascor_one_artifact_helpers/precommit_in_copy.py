"""Copy an edited cascor tree into a fresh directory, `git init` + stage it there, and run pre-commit on named files.

Usage: python3 -I precommit_in_copy.py SRC_TREE DEST_DIR PRE_COMMIT_BIN FILE [FILE ...]
No commit is made. Prints pre-commit's output, then each named file whose content a hook changed, then exit=<code>.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    src, dest, pre_commit = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    files = sys.argv[4:]
    if dest.exists():
        print(f"REFUSED: {dest} exists")
        return 2
    shutil.copytree(src, dest, symlinks=True, ignore=shutil.ignore_patterns("tmp"))
    before = {f: digest(dest / f) for f in files}
    for argv in (["git", "init", "-q"], ["git", "add", "-A"]):
        proc = subprocess.run(argv, cwd=dest, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(f"{' '.join(argv)} failed: {proc.stderr}")
            return 2
    proc = subprocess.run([pre_commit, "run", "--files", *files], cwd=dest, capture_output=True, text=True, check=False)
    print(proc.stdout)
    print(proc.stderr)
    changed = [f for f in files if digest(dest / f) != before[f]]
    print("changed by hooks: " + (", ".join(changed) if changed else "none"))
    print(f"exit={proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
