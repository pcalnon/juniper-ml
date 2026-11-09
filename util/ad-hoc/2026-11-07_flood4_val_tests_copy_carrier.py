"""
Copy a flood-4 carrier's changed (non-util/ad-hoc) files into this validator worktree, read-only on the source.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 tests carrier, slice B)
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 carrier validation (BRIEF_VALIDATE.txt); juniper-ml tests carrier on origin/main 303ccc0b

Usage: python3 <this> <manifest.json> <carrier worktree> <dest worktree> <out.json>

Reads the manifest's "files" list, copies every added/modified path that is not under util/ad-hoc/
from the carrier worktree into the destination worktree, deletes "deleted" paths, and records the
sha256 of source and destination for each copied file so the copy is provably byte-identical.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    manifest_path, src_root, dst_root, out_path = (Path(a) for a in argv[1:5])
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    rows = []
    for entry in manifest["files"]:
        rel = entry["path"]
        if rel.startswith("util/ad-hoc/"):
            continue
        src = src_root / rel
        dst = dst_root / rel
        if entry["status"] == "deleted":
            if dst.exists():
                dst.unlink()
            rows.append({"path": rel, "status": "deleted"})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        rows.append({"path": rel, "status": entry["status"], "src_sha256": _sha(src), "dst_sha256": _sha(dst)})
    mismatches = [r for r in rows if r.get("src_sha256") != r.get("dst_sha256")]
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"copied": rows, "mismatches": mismatches}, fh, indent=1)
    print(f"copied {len(rows)} paths, {len(mismatches)} sha mismatches -> {out_path}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
