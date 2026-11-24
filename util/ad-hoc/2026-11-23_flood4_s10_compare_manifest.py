#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_compare_manifest.py
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
#     Flood-4 session 10. Compare the sha256 of every file in a materialized set (the staged-blob manifest written by
#     2026-11-23_flood4_s10_materialize_staged.py) with a builder's recorded manifest.json, wherever in that JSON the
#     builder put {"path": ..., "sha256": ...} records. Prints match / differ / unrecorded. Read-only.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_compare_manifest.py --recorded BUILDER_MANIFEST.json --staged STAGED_MANIFEST.json
#####################################################################################################################################################################################################
"""Compare materialized files' sha256 with a builder's recorded manifest."""

import argparse
import json
import sys


def _collect(node, out, trail=""):
    if isinstance(node, dict):
        path = node.get("path") or node.get("file")
        digest = node.get("sha256") or node.get("final_sha256") or node.get("sha")
        if isinstance(path, str) and isinstance(digest, str) and len(digest) == 64:
            out.setdefault(path, set()).add((digest, trail))
        for key, value in node.items():
            if isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value) and "/" in key:
                out.setdefault(key, set()).add((value, trail))
            _collect(value, out, f"{trail}.{key}" if trail else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _collect(value, out, f"{trail}[{index}]")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recorded", required=True)
    parser.add_argument("--staged", required=True)
    args = parser.parse_args(argv)
    with open(args.recorded, encoding="utf-8") as handle:
        recorded_json = json.load(handle)
    with open(args.staged, encoding="utf-8") as handle:
        staged = {f["path"]: f.get("sha256") for f in json.load(handle)["files"]}
    recorded = {}
    _collect(recorded_json, recorded)
    print(f"recorded paths with a sha256: {len(recorded)}; staged files: {len(staged)}")
    counts = {"match": 0, "differ": 0, "unrecorded": 0}
    for path, digest in sorted(staged.items()):
        seen = recorded.get(path)
        if not seen:
            counts["unrecorded"] += 1
            print(f"  unrecorded  {path}")
        elif digest in {d for d, _ in seen}:
            counts["match"] += 1
            where = sorted({t for d, t in seen if d == digest})[:2]
            print(f"  match       {path}  (at {', '.join(where)})")
        else:
            counts["differ"] += 1
            print(f"  DIFFER      {path}  staged {str(digest)[:12]} recorded {sorted(d[:12] for d, _ in seen)}")
    print(", ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if counts["differ"] else 0


if __name__ == "__main__":
    sys.exit(main())
