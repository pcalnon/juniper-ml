#!/usr/bin/env python3
"""
Run named unittest suites alone in two trees and compare the failing and erroring test ids, tree by tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, landing)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: "the four known host failures also fail on a clean main")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)

Why: a carrier's run of CI's regression list fails four suites on this host. They are known host failures only if a
clean main fails the SAME tests, not merely the same suites. This runs each suite alone (`python3 -m unittest -v
<suite>`, as CI does) in each tree and prints, per suite, the failing ids on each side and whether the sets are equal.

Usage:
    python3 <this> --tree-a <carrier tree> --tree-b <clean main tree> --out <json> <suite> [<suite> ...]
Run it through tmp/flood4/session8/runenv.bash so python3 is the env's and the Sentry variables are empty.
Exit 0 = every suite fails the same ids in both trees (or passes in both); 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: python3 -m unittest in the caller's own trees
import sys
from pathlib import Path

ID_RE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)


def run(tree: Path, suite: str) -> dict:
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, timeout=900)  # nosec B603
    ids = sorted({f"{kind} {cls}.{name}" for kind, name, cls in ID_RE.findall(proc.stderr)})
    tail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""
    return {"rc": proc.returncode, "ids": ids, "last_line": tail}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree-a", required=True, type=Path)
    parser.add_argument("--tree-b", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("suites", nargs="+")
    args = parser.parse_args()
    report = {"python": sys.version.split()[0], "executable": sys.executable, "tree_a": str(args.tree_a), "tree_b": str(args.tree_b), "suites": {}}
    same_everywhere = True
    for suite in args.suites:
        a = run(args.tree_a, suite)
        b = run(args.tree_b, suite)
        same = a["ids"] == b["ids"] and (a["rc"] == 0) == (b["rc"] == 0)
        same_everywhere &= same
        report["suites"][suite] = {"a": a, "b": b, "same": same}
        print(f"{suite}: a rc={a['rc']} ({a['last_line']}) | b rc={b['rc']} ({b['last_line']}) | same failing ids: {same} ({len(a['ids'])} vs {len(b['ids'])})")
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("python", report["python"], report["executable"])
    return 0 if same_everywhere else 1


if __name__ == "__main__":
    sys.exit(main())
