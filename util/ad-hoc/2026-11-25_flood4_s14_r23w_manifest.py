"""
Assemble the r23w carrier: copy the changed files out of the clone into final/, write paths.txt and final.sha256,
and print the files[] section of manifest.json (path, status, sha256 in the clone and in final/, main's sha256).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — one-off (flood-4 session 14, builder r23w: ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Usage: python3 <this file> --clone <clone dir> --status <file holding `git status --short` of the clone>
       --main-dir <a copy of main's tree, or of the files main has> --out <carrier dir> --files-json <out json>
Every path in the status file is copied to <out>/final/<path>; the copy's sha256 must equal the clone's.
A modified path's main sha256 is read from <main-dir>/<path> when that file exists there.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--clone", required=True, type=Path)
    ap.add_argument("--status", required=True, type=Path)
    ap.add_argument("--main-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--files-json", required=True, type=Path)
    args = ap.parse_args()
    rows, paths = [], []
    for line in args.status.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        code, rel = line[:2].strip(), line[3:].strip()
        status = {"M": "modified", "??": "added", "A": "added"}.get(code, code)
        src = args.clone / rel
        dest = args.out / "final" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        main_copy = args.main_dir / rel
        row = {"path": rel, "status": status, "sha256": _sha(dest), "clone_sha256_equal": _sha(src) == _sha(dest)}
        if status == "modified":
            row["main_sha256"] = _sha(main_copy) if main_copy.is_file() else None
        rows.append(row)
        paths.append(rel)
    (args.out / "paths.txt").write_text("\n".join(paths) + "\n", encoding="utf-8")
    (args.out / "final.sha256").write_text("".join(f"{r['sha256']}  {r['path']}\n" for r in rows), encoding="utf-8")
    args.files_json.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    bad = [r["path"] for r in rows if not r["clone_sha256_equal"]]
    print(f"{len(rows)} files ({sum(r['status'] == 'modified' for r in rows)} modified, {sum(r['status'] == 'added' for r in rows)} added); copy mismatches: {bad or 'none'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
