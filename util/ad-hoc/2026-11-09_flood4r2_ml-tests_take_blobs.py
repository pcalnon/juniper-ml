"""
Write each flood-4 round-2 ml-tests draft's NEW test file from its head blob into this worktree.

Only paths the draft ADDS in its own commits (see 2026-11-09_flood4r2_ml-tests_survey.py's
own/summary.json) and that the carrier takes are written; shared files (ci.yml, main-verify.yml,
docs/REFERENCE.md, CHANGELOG.md) are never copied -- their registrations are re-derived by the wiring
tool. A path that already exists in the worktree is refused unless --overwrite is given, so a second
run cannot silently replace a file the carrier has since fixed. Records each blob's sha and the
written file's sha256 in <scratch>/take_blobs.json.

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_take_blobs.py --scratch <dir> [--overwrite] N:path [N:path ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2)
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("items", nargs="+", help="N:path")
    args = ap.parse_args()
    out = []
    rc = 0
    for item in args.items:
        n, path = item.split(":", 1)
        ref = f"refs/flood4r2/pr/{int(n)}"
        target = Path(path)
        if target.exists() and not args.overwrite:
            print(f"#{n} {path}: exists, refused (pass --overwrite)")
            rc = 1
            continue
        blob = subprocess.run(["git", "rev-parse", f"{ref}:{path}"], capture_output=True, text=True, check=False)
        if blob.returncode != 0:
            print(f"#{n} {path}: no such blob at {ref}")
            rc = 1
            continue
        data = subprocess.run(["git", "cat-file", "blob", blob.stdout.strip()], capture_output=True, check=True).stdout
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        out.append({"pr": int(n), "path": path, "blob": blob.stdout.strip(), "sha256": digest, "bytes": len(data)})
        print(f"#{n} {path}: blob {blob.stdout.strip()[:12]} -> {len(data)} bytes sha256 {digest[:12]}")
    with open(Path(args.scratch) / "take_blobs.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return rc


if __name__ == "__main__":
    sys.exit(main())
