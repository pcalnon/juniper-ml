"""
Copy a flood-4 carrier's changed files (every non-util/ad-hoc manifest path) from the builder's
worktree into the validator's own worktree, recording sha256 of source and copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 carrier validation, sub-package slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (BRIEF_VALIDATE.txt)

Usage: python3 <this> <manifest.json> <source worktree> <dest worktree> <record.json>
"""

import hashlib
import json
import os
import shutil
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    manifest_path, src_root, dst_root, record_path = argv[1:5]
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    rows = []
    for entry in manifest["files"]:
        rel = entry["path"]
        status = entry["status"]
        if rel.startswith("util/ad-hoc/"):
            rows.append({"path": rel, "status": status, "action": "skipped (util/ad-hoc)"})
            continue
        src = os.path.join(src_root, rel)
        dst = os.path.join(dst_root, rel)
        if status == "deleted":
            if os.path.exists(dst):
                os.remove(dst)
            rows.append({"path": rel, "status": status, "action": "deleted"})
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        rows.append({"path": rel, "status": status, "action": "copied", "src_sha256": sha256(src), "dst_sha256": sha256(dst)})
    bad = [r for r in rows if r.get("action") == "copied" and r["src_sha256"] != r["dst_sha256"]]
    with open(record_path, "w") as fh:
        json.dump({"source": src_root, "dest": dst_root, "rows": rows, "mismatches": bad}, fh, indent=2)
    copied = sum(1 for r in rows if r.get("action") == "copied")
    print(f"copied={copied} skipped={sum(1 for r in rows if r['action'].startswith('skipped'))} mismatches={len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
