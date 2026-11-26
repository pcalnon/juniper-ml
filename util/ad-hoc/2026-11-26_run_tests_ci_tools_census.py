#!/usr/bin/env python3
"""
For each Juniper repo, read from its origin/main: the juniper-ci-tools pins its workflows install, its Python floor,
and its workflow jobs that run pytest or unittest -- the inputs to the run_tests engine-extraction proposal.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests rollout's engine-extraction proposal
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)

Fetches ``origin`` in each sibling primary (refs only; no working tree changes), then reads blobs at
``origin/main`` with ``git show`` / ``git ls-tree``: the primaries' checkouts can lag, origin/main cannot. A repo
whose primary is missing is reported, not skipped silently. Read-only apart from the fetch.

Usage: python3 util/ad-hoc/2026-11-26_run_tests_ci_tools_census.py [--no-fetch] [REPO ...]
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - git with a fixed argv
import sys
from pathlib import Path

REPOS = ["juniper-ml", "juniper-recurrence", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-data", "juniper-harcot", "juniper-cascor", "juniper-canopy", "juniper-deploy"]
PIN = re.compile(r"juniper-ci-tools(?:\[[^\]]*\])?\s*([<>=!~][^\"'\s]*)?")
FLOOR = re.compile(r'^requires-python\s*=\s*"([^"]+)"', re.M)
TEST_LINE = re.compile(r"^\s*(?:pytest\b|python3?(?:\.\d+)? -m (?:pytest|unittest)\b)", re.M)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)  # nosec B603 B607
    return proc.stdout if proc.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("repos", nargs="*", default=REPOS)
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--grep", metavar="REGEX", help="instead: print each workflow line at origin/main matching REGEX (git grep -E)")
    args = parser.parse_args()
    root = Path(git(Path(__file__).resolve().parent, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).parent.parent
    for name in args.repos:
        repo = root / name
        if not (repo / ".git").exists():
            print(f"{name}: no primary checkout at {repo}")
            continue
        if not args.no_fetch:
            git(repo, "fetch", "--quiet", "origin", "main")
        if args.grep:
            hits = git(repo, "grep", "-n", "-E", args.grep, "origin/main", "--", ".github/workflows").strip()
            print(f"== {name}: " + (f"\n{hits}" if hits else "no match"))
            continue
        sha = git(repo, "rev-parse", "origin/main").strip()[:10]
        files = [line for line in git(repo, "ls-tree", "-r", "--name-only", "origin/main", "--", ".github/workflows").splitlines() if line.endswith((".yml", ".yaml"))]
        pins: dict[str, set[str]] = {}
        tests: dict[str, int] = {}
        for path in files:
            text = git(repo, "show", f"origin/main:{path}")
            for match in PIN.finditer(text):
                pins.setdefault(match.group(1) or "(unpinned)", set()).add(Path(path).name)
            count = len(TEST_LINE.findall(text))
            if count:
                tests[Path(path).name] = count
        pyprojects = [line for line in git(repo, "ls-tree", "-r", "--name-only", "origin/main").splitlines() if line.endswith("pyproject.toml") and line.count("/") <= 1]
        floors = sorted({match.group(1) for path in pyprojects for match in FLOOR.finditer(git(repo, "show", f"origin/main:{path}"))})
        print(f"== {name} @ {sha}")
        print(f"   requires-python: {', '.join(floors) or '(no pyproject.toml)'}")
        print("   juniper-ci-tools: " + ("; ".join(f"{pin} in {', '.join(sorted(where))}" for pin, where in sorted(pins.items())) or "not installed by any workflow"))
        print("   test command lines: " + (", ".join(f"{wf} {count}" for wf, count in sorted(tests.items())) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
