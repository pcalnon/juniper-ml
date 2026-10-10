#!/usr/bin/env python3
"""
Summarize markdownlint findings per file and rule, using the pre-commit-pinned markdownlint-cli binary.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-04
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (archiving its lane reports)

Run it on scratch COPIES (markdownlint is invoked without --fix, so nothing is rewritten, but copies keep the
evidence untouched while validators read it). The binary path is the pre-commit cache entry for markdownlint-cli
v0.42.0, the version `.pre-commit-config.yaml` pins; pass ``--binary`` if your cache differs. Prefer
``pre-commit run markdownlint --files ...`` for the authoritative gate.

Usage
-----
    python3 util/ad-hoc/2026-10-04_markdownlint_rule_summary.py --config .markdownlint.yaml FILE_OR_DIR...
"""
import argparse
import collections
import glob
import os
import subprocess
import sys
from pathlib import Path


def default_binary() -> str:
    for cand in glob.glob(os.path.expanduser("~/.cache/pre-commit/repo*/node_env-default/bin/markdownlint")):
        pkg = Path(cand).parents[2] / "package.json"
        if pkg.exists() and '"version": "0.42.0"' in pkg.read_text():
            return cand
    return "markdownlint"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--binary", default=None)
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    targets = []
    for p in map(Path, args.paths):
        targets += sorted(str(x) for x in p.glob("*.md")) if p.is_dir() else [str(p)]
    proc = subprocess.run([args.binary or default_binary(), "--config", args.config, *targets], capture_output=True, text=True)
    counts = collections.Counter()
    for line in (proc.stdout + proc.stderr).splitlines():
        if ".md:" not in line:
            continue
        path, rest = line.split(".md:", 1)
        parts = rest.split()
        rule = next((t for t in parts if t.startswith("MD")), "?").split("/")[0]
        counts[(Path(path + ".md").name, rule)] += 1
    for (name, rule), n in sorted(counts.items()):
        print(f"{n:5d}  {name}  {rule}")
    print("exit", proc.returncode, "total", sum(counts.values()))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
