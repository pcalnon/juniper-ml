#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_verify_pr_blobs.py
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
#     Flood-4 session 10. Read a pushed commit back from GitHub and check that it changes exactly the listed paths and
#     that each blob equals the local final file (git blob sha, computed with `git hash-object`). Read-only.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_verify_pr_blobs.py --repo juniper-ml --commit SHA --final DIR --paths FILE
#####################################################################################################################################################################################################
"""Verify a pushed commit's blobs against a local frozen file set."""

import argparse
import json
import os
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--paths", required=True)
    args = parser.parse_args(argv)
    raw = subprocess.run(["gh", "api", "--paginate", f"repos/{args.owner}/{args.repo}/commits/{args.commit}"], capture_output=True, text=True, check=True).stdout
    data = json.loads(raw)
    remote = {f["filename"]: f["sha"] for f in data["files"]}
    with open(args.paths, encoding="utf-8") as handle:
        paths = [p.strip() for p in handle if p.strip()]
    bad = 0
    for path in paths:
        local = subprocess.run(["git", "hash-object", os.path.join(args.final, path)], capture_output=True, text=True, check=True).stdout.strip()
        if remote.get(path) != local:
            bad += 1
            print(f"MISMATCH {path}: remote {remote.get(path)} local {local}")
    extra = sorted(set(remote) - set(paths))
    for path in extra:
        print(f"EXTRA in commit: {path}")
    verified = data["commit"]["verification"]["verified"]
    print(f"commit {args.commit[:12]} verified={verified} parent={data['parents'][0]['sha'][:12]} files={len(remote)} listed={len(paths)} mismatches={bad} extra={len(extra)}")
    return 0 if (bad == 0 and not extra and verified) else 1


if __name__ == "__main__":
    sys.exit(main())
