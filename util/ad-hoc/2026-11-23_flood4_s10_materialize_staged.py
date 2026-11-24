#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_materialize_staged.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-11-23
# Last Modified: 2026-11-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#     Flood-4 session 10. Copy a carrier's STAGED content (the index blobs, which the 2026-11-20..22 blind
#     "owner -> Overtoad" pass could not reach: it rewrote working-tree files only) out to --out, one file per staged
#     path, plus the HEAD version of each modified path under --out-base, and print a sha256 manifest. Read-only on the
#     carrier: it runs only `git ls-files`, `git diff --cached` and `git show`.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_materialize_staged.py --carrier DIR --out DIR --out-base DIR [--manifest FILE]
#####################################################################################################################################################################################################
"""Materialize a carrier's staged blobs (and their HEAD bases) without touching the carrier."""

import argparse
import hashlib
import json
import os
import subprocess
import sys


def _git(carrier, *args):
    proc = subprocess.run(["git", "-C", carrier, *args], capture_output=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--carrier", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--out-base", required=True)
    parser.add_argument("--manifest")
    args = parser.parse_args(argv)
    head = _git(args.carrier, "rev-parse", "HEAD").decode().strip()
    rows = _git(args.carrier, "diff", "--cached", "--name-status", "--no-renames", "-z").split(b"\0")
    entries = []
    it = iter([r for r in rows if r])
    for status in it:
        path = next(it).decode()
        entries.append((status.decode(), path))
    manifest = {"carrier": args.carrier, "head": head, "files": []}
    for status, path in entries:
        record = {"path": path, "status": status}
        if status != "D":
            data = _git(args.carrier, "show", f":{path}")
            dst = os.path.join(args.out, path)
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            with open(dst, "wb") as handle:
                handle.write(data)
            mode = _git(args.carrier, "ls-files", "-s", "--", path).decode().split()[0]
            os.chmod(dst, 0o700 if mode == "100755" else 0o600)
            record.update(sha256=hashlib.sha256(data).hexdigest(), mode=mode, overtoad=data.count(b"Overtoad"), owner=data.count(b"owner"))
        if status != "A":
            base = _git(args.carrier, "show", f"HEAD:{path}")
            dst = os.path.join(args.out_base, path)
            os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
            with open(dst, "wb") as handle:
                handle.write(base)
            record["base_sha256"] = hashlib.sha256(base).hexdigest()
        manifest["files"].append(record)
        print(f"{status}  {record.get('sha256', '-')[:16]}  Overtoad={record.get('overtoad', '-')!s:>3}  {path}")
    if args.manifest:
        with open(args.manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
    print(f"head={head[:12]} staged={len(entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
