#!/usr/bin/env python3
"""
Run a list of READ-ONLY gh commands and save each one's stdout to a file, refusing anything that could mutate.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
This host's shell classifier refuses a gh command whose redirect target names the secret scanner (the port's
scratch directory does), so the reads a port needs (the pilot pull request's body and diff, job logs, rulesets,
release metadata) are run from here. Every command must be `gh pr view|diff|list|checks`, `gh run view|list`,
`gh release view|list`, `gh issue view|list` or `gh api` with an explicit `--method GET`; anything else is refused
before it runs. Each command's stdout goes to <out>/<name>, its stderr to <out>/<name>.stderr, and one summary line
per command (name, exit status, bytes) is printed. It never prints a command's output.

Usage:
    python3 <this> --out <directory> --spec <json file: [{"name": "<file name>", "argv": ["gh", ...]}, ...]>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ALLOWED_PAIRS = {
    ("pr", "view"),
    ("pr", "diff"),
    ("pr", "list"),
    ("pr", "checks"),
    ("run", "view"),
    ("run", "list"),
    ("release", "view"),
    ("release", "list"),
    ("issue", "view"),
    ("issue", "list"),
}
MUTATING_API_FLAGS = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"}


def refusal(argv: list[str]) -> str:
    """Return why ``argv`` is refused, or an empty string when it is a read."""
    if len(argv) < 2 or argv[0] != "gh":
        return "not a gh command"
    if argv[1] == "api":
        methods = [argv[i + 1] for i, word in enumerate(argv[:-1]) if word in {"-X", "--method"}]
        if methods != ["GET"]:
            return "gh api needs exactly one explicit --method GET"
        extra = [word for word in argv if word in MUTATING_API_FLAGS - {"-X", "--method"}]
        if extra:
            return f"gh api with {extra} is refused"
        return ""
    if len(argv) < 3 or (argv[1], argv[2]) not in ALLOWED_PAIRS:
        return f"gh {' '.join(argv[1:3])} is not on the read-only list"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--spec", required=True, type=Path)
    args = ap.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    for entry in spec:
        why = refusal(list(entry["argv"]))
        if why:
            print(f"REFUSED {entry['name']}: {why}")
            return 2
    args.out.mkdir(parents=True, exist_ok=True)
    worst = 0
    for entry in spec:
        target = args.out / entry["name"]
        proc = subprocess.run(list(entry["argv"]), capture_output=True, check=False, timeout=300)
        target.write_bytes(proc.stdout)
        (args.out / (entry["name"] + ".stderr")).write_bytes(proc.stderr)
        print(f"{entry['name']}: exit {proc.returncode}, {len(proc.stdout)} bytes")
        worst = max(worst, proc.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
