"""
Assemble the r28 carrier onto today's juniper-canopy origin/main in a validator clone, and record what was done.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code

Usage:
    python <this file> --clone <validator clone> --carrier <carrier dir with final/, paths.txt, final.sha256>
        --base <carrier base sha> --out <assemble.json> [--merged-reference <builder's merged file for one path>]

For every path in paths.txt: verify the carrier file's sha256 against final.sha256 (a mismatch stops); if main has not
changed the path since the base, copy the carrier file; otherwise three-way merge it with `git merge-file`
(current = main's file, base = the base's file, other = the carrier's file) and record the conflict count. A conflicted
file is left with its markers for a deliberate resolution; nothing is committed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - runs git on a local clone
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(clone: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True, check=check)  # nosec B603 B607


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clone", required=True)
    parser.add_argument("--carrier", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--work", required=True, help="directory for extracted base copies")
    args = parser.parse_args()
    clone, carrier, work = Path(args.clone), Path(args.carrier), Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    expected = {}
    for line in (carrier / "final.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split(None, 1)
            expected[rel.strip()] = digest
    head = git(clone, "rev-parse", "HEAD").stdout.strip()
    record = {"clone": str(clone), "head_before": head, "base": args.base, "files": []}
    for rel in [p.strip() for p in (carrier / "paths.txt").read_text(encoding="utf-8").splitlines() if p.strip()]:
        src = carrier / "final" / rel
        got = sha256(src)
        entry = {"path": rel, "carrier_sha256": got, "expected_sha256": expected.get(rel), "sha256_ok": got == expected.get(rel)}
        if not entry["sha256_ok"]:
            entry["action"] = "STOP: carrier sha256 mismatch"
            record["files"].append(entry)
            break
        changed = git(clone, "diff", "--quiet", args.base, head, "--", rel, check=False).returncode != 0
        entry["main_changed_since_base"] = changed
        dest = clone / rel
        if not changed:
            shutil.copy2(src, dest)
            entry["action"] = "copied (main unchanged since base)"
        else:
            base_copy = work / (rel.replace("/", "__") + ".base")
            base_copy.write_text(git(clone, "show", f"{args.base}:{rel}").stdout, encoding="utf-8")
            merge = subprocess.run(["git", "merge-file", "-L", "main", "-L", "base", "-L", "carrier", str(dest), str(base_copy), str(src)], capture_output=True, text=True, check=False)  # nosec B603 B607
            entry["action"] = "three-way merged with git merge-file (current=main, base=base, other=carrier)"
            entry["merge_file_exit"] = merge.returncode
            entry["conflicts"] = merge.returncode if merge.returncode > 0 else 0
        entry["result_sha256"] = sha256(dest)
        record["files"].append(entry)
    Path(args.out).write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps(record, indent=1))
    return 0 if all(f.get("sha256_ok") for f in record["files"]) else 1


if __name__ == "__main__":
    sys.exit(main())
