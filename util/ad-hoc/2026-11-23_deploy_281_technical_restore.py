#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Restore the technical "owner" that juniper-deploy#281's blind rename changed, on current deploy main.

Why this exists
---------------
juniper-deploy#281 (merged 2026-11-20 22:43Z, ``552756a1``) replaced every "owner" with "Overtoad". Its
person renames are right; five technical uses are not: two GitHub API placeholders
(``/repos/{owner}/{repo}``), one image-reference placeholder (``ghcr.io/<owner>/<name>:<tag>``) and two
"Code ownership" table cells describing CODEOWNERS. Each fix below names the exact text and how many
times it must occur, so a file that moved since is refused instead of half-edited.

Usage
-----
    python3 2026-11-23_deploy_281_technical_restore.py --out DIR [--ref main]

Writes the five repaired files under DIR at their repository paths and prints one line per file.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys

REPO = "pcalnon/juniper-deploy"
FIXES = {
    ".github/workflows/ci.yml": [("/repos/{Overtoad}/{repo}", "/repos/{owner}/{repo}", 1)],
    "tests/test_gitleaks_pr_scan.py": [("/repos/{Overtoad}/{repo}", "/repos/{owner}/{repo}", 1)],
    "scripts/verify_published_images.py": [("ghcr.io/<Overtoad>/<name>:<tag>", "ghcr.io/<owner>/<name>:<tag>", 1)],
    "docs/REFERENCE.md": [("Code Overtoadship rules", "Code ownership rules", 1)],
    "notes/AGENTS_MD_AUDIT_ANALYSIS_2026-04-02.md": [("Code Overtoadship", "Code ownership", 1)],
}


def fetch(path: str, ref: str) -> str:
    meta = json.loads(subprocess.run(["gh", "api", f"repos/{REPO}/contents/{path}?ref={ref}"], check=True, capture_output=True, text=True).stdout)
    if meta.get("content"):
        return base64.b64decode(meta["content"]).decode("utf-8")
    blob = json.loads(subprocess.run(["gh", "api", f"repos/{REPO}/git/blobs/{meta['sha']}"], check=True, capture_output=True, text=True).stdout)
    return base64.b64decode(blob["content"]).decode("utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="main")
    args = ap.parse_args(argv)
    for path, fixes in FIXES.items():
        text = fetch(path, args.ref)
        for old, new, times in fixes:
            found = text.count(old)
            if found != times:
                raise SystemExit(f"REFUSED {path}: expected {times} x {old!r}, found {found}")
            text = text.replace(old, new)
        target = os.path.join(args.out, path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"{path}: {', '.join(f'{o!r} -> {n!r}' for o, n, _ in fixes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
