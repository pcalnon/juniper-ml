"""
Assemble a flood-4 carrier onto a fresh clone of main: copy, or three-way merge, every carrier file; record assemble.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

For each path in the carrier's paths.txt:
  - checks the carrier file's sha256 against final.sha256 (a mismatch aborts: exit 2);
  - reads the file at BASE (base.txt) and at the clone's HEAD with `git show`;
  - if HEAD's copy equals BASE's (or both are absent), copies the carrier file over the clone's;
  - otherwise three-way merges (`git merge-file -p carrier base head`) and records conflicts.

Usage:
  python -I <this file> --carrier CARRIER_DIR --clone CLONE_DIR --out assemble.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_show(clone: pathlib.Path, rev: str, path: str) -> bytes | None:
    proc = subprocess.run(["git", "-C", str(clone), "show", f"{rev}:{path}"], capture_output=True, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", required=True, type=pathlib.Path)
    parser.add_argument("--clone", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()

    carrier: pathlib.Path = args.carrier
    clone: pathlib.Path = args.clone
    base = (carrier / "base.txt").read_text().strip()
    paths = [line.strip() for line in (carrier / "paths.txt").read_text().splitlines() if line.strip()]
    expected = {}
    for line in (carrier / "final.sha256").read_text().splitlines():
        if line.strip():
            digest, rel = line.split(None, 1)
            expected[rel.strip()] = digest

    head = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    records = []
    status = 0
    for rel in paths:
        src = carrier / "final" / rel
        data = src.read_bytes()
        digest = sha256_bytes(data)
        record: dict = {"path": rel, "carrier_sha256": digest, "expected_sha256": expected.get(rel)}
        if expected.get(rel) != digest:
            record["action"] = "BLOCKER_SHA_MISMATCH"
            records.append(record)
            status = 2
            continue
        at_base = git_show(clone, base, rel)
        at_head = git_show(clone, head, rel)
        record["base_sha256"] = sha256_bytes(at_base) if at_base is not None else None
        record["head_sha256"] = sha256_bytes(at_head) if at_head is not None else None
        dest = clone / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if at_base == at_head:
            shutil.copyfile(src, dest)
            record["action"] = "copy (main unchanged since base)" if at_base is not None else "copy (new file)"
        else:
            with tempfile.TemporaryDirectory(dir=str(args.out.parent)) as work:
                wb = pathlib.Path(work) / "base"
                wh = pathlib.Path(work) / "head"
                wb.write_bytes(at_base or b"")
                wh.write_bytes(at_head or b"")
                proc = subprocess.run(["git", "merge-file", "-p", str(src), str(wb), str(wh)], capture_output=True, check=False)
                dest.write_bytes(proc.stdout)
                record["action"] = "merge-file"
                record["merge_conflicts"] = proc.returncode
                if proc.returncode != 0:
                    status = max(status, 1)
        record["assembled_sha256"] = sha256_bytes(dest.read_bytes())
        records.append(record)

    out = {"carrier": str(carrier), "clone": str(clone), "base": base, "head": head, "files": records, "status": status}
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"head": head, "base": base, "status": status, "actions": [r["action"] for r in records]}, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main())
