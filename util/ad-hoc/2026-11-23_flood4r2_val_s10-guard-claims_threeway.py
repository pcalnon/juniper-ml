#!/usr/bin/env python3
"""
Three-way the agent guard 1.4.0 carrier's 16 staged files onto a main ref, into a scratch directory only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; the carrier's staged copies and their base copies

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_threeway.py <repo dir> <main ref> <manifest.json>
        <staged dir> <base dir> <out dir>

For each modified file: base = the base copy, ours = `git show <main ref>:<path>` (never a working-tree copy),
theirs = the staged copy; `git merge-file -p` writes the result under <out dir>. For each added file: whether
<main ref> already holds the path. Nothing in <repo dir> is written: no index, no working tree, no ref.
"""

from __future__ import annotations

import hashlib
import json
import subprocess  # nosec B404 -- read-only git plumbing and git merge-file into a scratch dir
import sys
from pathlib import Path


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)  # nosec B603 B607
    if check and proc.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), proc.stderr.decode("utf-8", "replace")))
    return proc


def main(argv: list) -> int:
    repo, ref, manifest, staged, base, out = Path(argv[1]), argv[2], Path(argv[3]), Path(argv[4]), Path(argv[5]), Path(argv[6])
    out.mkdir(parents=True, exist_ok=True)
    main_sha = git(repo, "rev-parse", ref).stdout.decode().strip()
    files = json.loads(manifest.read_text(encoding="utf-8"))["files"]
    report = {"main_ref": ref, "main_sha": main_sha, "files": []}
    for entry in files:
        path = entry["path"]
        row = {"path": path, "status": entry["status"]}
        shown = git(repo, "show", "%s:%s" % (main_sha, path), check=False)
        if entry["status"] == "A":
            row["on_main"] = shown.returncode == 0
            if shown.returncode == 0:
                row["main_sha256"] = hashlib.sha256(shown.stdout).hexdigest()
                row["same_as_staged"] = row["main_sha256"] == entry["sha256"]
            report["files"].append(row)
            continue
        ours = out / "ours" / path
        ours.parent.mkdir(parents=True, exist_ok=True)
        ours.write_bytes(shown.stdout)
        row["main_sha256"] = hashlib.sha256(shown.stdout).hexdigest()
        row["main_equals_base"] = row["main_sha256"] == entry["base_sha256"]
        merged = subprocess.run(["git", "merge-file", "-p", "-L", "origin-main", "-L", "base-9d9ec797", "-L", "staged", str(ours), str(base / path), str(staged / path)], capture_output=True, check=False)  # nosec B603 B607
        result = out / "merged" / path
        result.parent.mkdir(parents=True, exist_ok=True)
        result.write_bytes(merged.stdout)
        row["conflicts"] = merged.returncode
        row["merged_sha256"] = hashlib.sha256(merged.stdout).hexdigest()
        row["merged_equals_staged"] = row["merged_sha256"] == entry["sha256"]
        report["files"].append(row)
        print("%-50s conflicts=%s main==base=%s merged==staged=%s" % (path, row["conflicts"], row["main_equals_base"], row["merged_equals_staged"]))
    for row in report["files"]:
        if row["status"] == "A":
            print("%-50s added; already on main=%s" % (row["path"], row["on_main"]))
    (out / "threeway.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("main %s" % main_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
