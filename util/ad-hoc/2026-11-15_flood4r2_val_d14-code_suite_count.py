"""
Count the `python3 -m unittest` lines of ci.yml's "Run Python regression tests" step, and AGENTS.md's stated count.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> <juniper-ml tree> [<juniper-ml tree> ...]
Scope: one step of one workflow file per tree (no directory walk), so the repo's tmp/ is never searched.
"""

import re
import sys
from pathlib import Path

WORKFLOW = Path(".github") / "workflows" / "ci.yml"
STEP = "- name: Run Python regression tests"


def count(tree: Path) -> tuple:
    lines = (tree / WORKFLOW).read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == STEP)
    indent = len(lines[start]) - len(lines[start].lstrip())
    suites = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("- name:") and len(line) - len(line.lstrip()) == indent:
            break
        match = re.match(r"python3 -m unittest -v (\S+)$", stripped)
        if match:
            suites.append(match.group(1))
    agents = re.search(r"the full ordered list of (\d+) `python3 -m unittest`", (tree / "AGENTS.md").read_text(encoding="utf-8"))
    return len(suites), len(set(suites)), int(agents.group(1)) if agents else None, "tests/test_ws_resume_answer_table_drift.py" in suites


def main() -> int:
    for arg in sys.argv[1:]:
        total, unique, stated, has_gate = count(Path(arg))
        print(f"{arg}\tci.yml regression step: {total} lines, {unique} unique\tAGENTS.md states {stated}\tnew gate listed: {has_gate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
