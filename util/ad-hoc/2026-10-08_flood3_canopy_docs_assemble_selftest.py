#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use self-test for 2026-10-08_flood3_canopy_docs_assemble.py: for each patch ALONE, the
# assembler's edit-operation replay must be byte-identical to GNU `patch -p1` applied to the base.
# A mismatch means the hunk parser mis-positions an operation, and the multi-patch result cannot be
# trusted either.
# Usage: ..._assemble_selftest.py --repo <wt> --base <sha> --scratch <dir> p1.patch [...]
"""Self-test the assembler's hunk replay against GNU patch."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("assemble", HERE / "2026-10-08_flood3_canopy_docs_assemble.py")
assemble = importlib.util.module_from_spec(spec)
sys.modules["assemble"] = assemble
spec.loader.exec_module(assemble)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("patches", nargs="+")
    args = ap.parse_args()
    bad = 0
    for pfile in args.patches:
        p = Path(pfile).resolve()
        sdir = Path(args.scratch) / f"selftest-{p.stem}"
        if sdir.exists():
            shutil.rmtree(sdir)
        sdir.mkdir(parents=True)
        ops = assemble.parse_patch(p.read_text(encoding="utf-8"))
        for path in ops:
            proc = subprocess.run(["git", "-C", args.repo, "show", f"{args.base}:{path}"], capture_output=True)
            dst = sdir / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(proc.stdout if proc.returncode == 0 else b"")
        res = subprocess.run(["patch", "-p1", "--no-backup-if-mismatch", "-d", str(sdir), "-i", str(p)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"{p.name}: GNU patch failed\n{res.stdout}{res.stderr}")
            bad += 1
            continue
        for path, file_ops in ops.items():
            proc = subprocess.run(["git", "-C", args.repo, "show", f"{args.base}:{path}"], capture_output=True, text=True)
            base = proc.stdout.splitlines(keepends=True) if proc.returncode == 0 else []
            merged, _conflicts = assemble.merge_ops(base, [(p.stem, file_ops)])
            want = (sdir / path).read_text(encoding="utf-8")
            got = "".join(merged) if merged is not None else None
            status = "OK" if got == want else "MISMATCH"
            if status != "OK":
                bad += 1
            print(f"{p.name} {path}: {status} ({len(file_ops)} ops)")
        shutil.rmtree(sdir)
    print(f"{'ALL OK' if not bad else f'{bad} FAILURES'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
