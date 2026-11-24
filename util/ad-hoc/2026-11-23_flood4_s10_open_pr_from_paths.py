#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-11-23_flood4_s10_open_pr_from_paths.py
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
#     Flood-4 session 10. Open a GitHub-signed PR (util/open_signed_pr.py) from a frozen directory of final files and a
#     paths list, refusing unless the target repository's main is still the base the files were built on: a whole-file
#     upload onto a moved main silently reverts whatever main changed in those files.
#
# Usage:
#     python3 util/ad-hoc/2026-11-23_flood4_s10_open_pr_from_paths.py --repo juniper-ml --branch B --expect-base SHA
#         --final DIR --paths FILE --title-file F --commit-body-file F --body-file F [--dry-run]
#####################################################################################################################################################################################################
"""Open a signed PR from a frozen file set, guarded by the expected base."""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OPEN_SIGNED_PR = os.path.join(os.path.dirname(HERE), "open_signed_pr.py")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--expect-base", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--paths", required=True)
    parser.add_argument("--title-file", required=True)
    parser.add_argument("--commit-body-file", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    head = subprocess.run(["gh", "api", f"repos/{args.owner}/{args.repo}/commits/main", "--jq", ".sha"], capture_output=True, text=True, check=True).stdout.strip()
    if not head.startswith(args.expect_base):
        print(f"REFUSED: {args.repo} main is {head[:12]}, not the expected base {args.expect_base}; re-derive first")
        return 3
    with open(args.paths, encoding="utf-8") as handle:
        paths = [p.strip() for p in handle if p.strip()]
    cmd = [sys.executable, OPEN_SIGNED_PR, "--owner", args.owner, "--repo", args.repo, "--branch", args.branch]
    for path in paths:
        local = os.path.join(args.final, path)
        if not os.path.isfile(local):
            print(f"REFUSED: {local} is missing")
            return 3
        cmd += ["--add", f"{local}:{path}"]
    with open(args.title_file, encoding="utf-8") as handle:
        title = handle.read().strip()
    cmd += ["--message", title, "--commit-body-file", args.commit_body_file, "--title", title, "--body-file", args.body_file]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"main = {head[:12]} (expected {args.expect_base}); {len(paths)} files")
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
