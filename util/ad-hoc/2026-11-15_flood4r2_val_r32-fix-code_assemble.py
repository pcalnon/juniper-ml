#!/usr/bin/env python3
"""
Assemble the r32 pause carrier's five files three-way onto a validator's own juniper-cascor worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (Cursor flood-4 round 2, validator LN1, code lens on the r32 pause fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor carrier r32-pause-fix (fix/lifecycle-pause-check-then-act, base a1b0409d, docs on 7802aef5)

The carrier is only READ. For each carried path the script takes the carrier's bytes, the bytes of
the revision the carrier was built on (``--code-base`` for code, ``--doc-base`` for the two documents
the builder rebuilt on the document carrier's merge) and the bytes of the target worktree's HEAD, and
writes ``git merge-file -p <carrier> <base> <head>`` into the target. A new file is copied. Every
input and output is hashed into ``--out``; a merge with conflicts is reported, never written.

Usage:
  2026-11-15_flood4r2_val_r32-fix-code_assemble.py --carrier <B> --target <own worktree> --work <dir> --out <json>
Exit: 0 when every path was written without a conflict; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 -- fixed-argv version-control reads
import sys
from pathlib import Path

PATHS = (
    ("src/api/lifecycle/manager.py", "code"),
    ("src/tests/unit/api/test_lifecycle_pause_check_then_act.py", "new"),
    ("docs/api/API_SCHEMAS.md", "doc"),
    ("docs/api/JUNIPER_CASCOR_API_REFERENCE.md", "doc"),
    ("CHANGELOG.md", "doc"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _show(repo: Path, rev: str, path: str) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, check=True)  # nosec B603 B607 -- fixed argv
    return done.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--code-base", default="a1b0409df7058d1c28f7e0f943975a4f76ff79fc")
    parser.add_argument("--doc-base", default="7802aef5a1a79e8280cf8d7e5f5c8151e7036416")
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(["git", "-C", str(args.target), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    report = {"carrier": str(args.carrier), "target": str(args.target), "target_head": head, "code_base": args.code_base, "doc_base": args.doc_base, "paths": []}
    ok = True
    for rel, kind in PATHS:
        carrier_bytes = (args.carrier / rel).read_bytes()
        entry = {"path": rel, "kind": kind, "carrier_sha256": _sha(carrier_bytes)}
        if kind == "new":
            result = carrier_bytes
            entry["conflicts"] = 0
        else:
            base_rev = args.code_base if kind == "code" else args.doc_base
            base_bytes = _show(args.target, base_rev, rel)
            head_bytes = _show(args.target, "HEAD", rel)
            stem = rel.replace("/", "__")
            files = {name: work / f"{stem}.{name}" for name in ("carrier", "base", "head")}
            files["carrier"].write_bytes(carrier_bytes)
            files["base"].write_bytes(base_bytes)
            files["head"].write_bytes(head_bytes)
            merged = subprocess.run(["git", "merge-file", "-p", str(files["carrier"]), str(files["base"]), str(files["head"])], capture_output=True, check=False)  # nosec B603 B607
            result = merged.stdout
            entry.update({"base_rev": base_rev, "base_sha256": _sha(base_bytes), "head_sha256": _sha(head_bytes), "head_equals_base": base_bytes == head_bytes, "conflicts": merged.returncode})
        entry["result_sha256"] = _sha(result)
        entry["result_equals_carrier"] = result == carrier_bytes
        if entry["conflicts"] != 0:
            ok = False
            entry["written"] = False
        else:
            (args.target / rel).write_bytes(result)
            entry["written"] = True
        report["paths"].append(entry)
        print(json.dumps({k: entry[k] for k in ("path", "conflicts", "result_equals_carrier", "written")}), flush=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
