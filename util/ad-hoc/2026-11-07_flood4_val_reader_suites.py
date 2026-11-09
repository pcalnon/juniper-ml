"""
Flood-4 validation: run, one `python3 -m unittest -v <suite>` process each (6 in parallel), every top-level
suite the carrier adds or modifies PLUS every suite that reads ci.yml / docs/REFERENCE.md / CHANGELOG.md
(the files the carrier edits), in this carrier worktree; re-run every failing suite in the clean origin/main
worktree and report whether the failing test ids are identical there.

Usage: python3 <this> <out.json> <clean_main_tree> <suite-list-file>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"


def run(tree: Path, suite: str) -> dict[str, object]:
    if not (tree / suite).exists():
        return {"suite": suite, "rc": None, "absent": True}
    r = subprocess.run([sys.executable, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, timeout=1800)
    text = r.stdout + r.stderr
    ran = re.search(r"^Ran (\d+) tests?", text, re.M)
    return {"suite": suite, "rc": r.returncode, "ran": int(ran.group(1)) if ran else None, "failed": sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", text, re.M))), "last": text.strip().splitlines()[-1:] if text.strip() else []}


def main() -> int:
    out = Path(sys.argv[1])
    clean = Path(sys.argv[2])
    readers = [l.strip() for l in Path(sys.argv[3]).read_text().splitlines() if l.strip()]
    touched = [p for p in subprocess.run(["git", "diff", "--name-only", BASE, TREE], cwd=HERE, capture_output=True, text=True, check=True).stdout.split() if re.match(r"^tests/test_[^/]+\.py$", p)]
    suites = sorted(set(readers) | set(touched))
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda s: run(HERE, s), suites))
    failing = [r for r in results if r["rc"] not in (0, None)]
    main_results = {}
    for r in failing:
        m = run(clean, r["suite"])
        main_results[r["suite"]] = m
        r["clean_main_rc"] = m["rc"]
        r["clean_main_same_failed_ids"] = m.get("failed") == r["failed"]
    res = {"suites": len(suites), "touched": touched, "passed": sum(1 for r in results if r["rc"] == 0), "failing": failing, "all": results}
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"suites={len(suites)} (touched {len(touched)}) passed={res['passed']} failing={len(failing)}")
    for r in failing:
        print(f"  FAIL {r['suite']}: carrier failed {len(r['failed'])}; clean main rc={r['clean_main_rc']} same ids={r['clean_main_same_failed_ids']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
