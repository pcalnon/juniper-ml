"""
Simulate landing fix N-1 (paused-fit wedge) and fix N-3 (ws resume losses) on juniper-cascor main, in both orders.

Claims lens, flood-4 round 2. Both carriers are uncommitted trees on origin/main 7640d420 and edit four shared files
(CHANGELOG.md, docs/DEVELOPER_CHEATSHEET.md, docs/api/API_SCHEMAS.md, docs/api/JUNIPER_CASCOR_API_REFERENCE.md).
For each file this runs `git merge-file -p <second> <base> <first>` (the rebuild the orchestrator uses) for both
landing orders and reports: conflicts, lines of either carrier lost, the stamp lines, and, for the CHANGELOG, the order
of the [Unreleased] subsections and their top-level entries. Inputs are read, never written; outputs go to the lens's
scratch directory.

Usage: python3 <this>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11
"""

import json
import re
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
N1 = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
N3 = JUNIPER / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
PRIMARY = JUNIPER / "juniper-cascor"
BASE = "7640d420be43f56df21375c11e0315cb11facc08"
OUT = Path(__file__).resolve().parents[2] / "tmp" / "flood4r2-val" / "n3-r2-claims-lens" / "merge-sim"
FILES = ["CHANGELOG.md", "docs/DEVELOPER_CHEATSHEET.md", "docs/api/API_SCHEMAS.md", "docs/api/JUNIPER_CASCOR_API_REFERENCE.md"]
STAMP = re.compile(r"^\*\*(Version|Date|Last Updated|Document Version)\*\*|^\*\*Version\*\*:")


def base_text(rel: str) -> str:
    return subprocess.run(["git", "-C", str(PRIMARY), "show", f"{BASE}:{rel}"], capture_output=True, text=True, check=True).stdout


def merge(second: Path, base: Path, first: Path) -> tuple:
    proc = subprocess.run(["git", "merge-file", "-p", str(second), str(base), str(first)], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def added_lines(carrier: str, base: str) -> list:
    base_set = set(base.splitlines())
    return [ln for ln in carrier.splitlines() if ln not in base_set and ln.strip()]


def unreleased_outline(text: str) -> list:
    lines = text.splitlines()
    start = lines.index("## [Unreleased]")
    out = []
    for ln in lines[start + 1 :]:
        if ln.startswith("## "):
            break
        if ln.startswith("### "):
            out.append(ln)
        elif ln.startswith("- **"):
            out.append("  " + ln[:110])
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for rel in FILES:
        name = rel.replace("/", "__")
        base_path = OUT / f"{name}.base"
        base_path.write_text(base_text(rel), encoding="utf-8")
        n1_path, n3_path = N1 / rel, N3 / rel
        base = base_path.read_text(encoding="utf-8")
        n1, n3 = n1_path.read_text(encoding="utf-8"), n3_path.read_text(encoding="utf-8")
        entry = {}
        for order, second, first in (("n1_first", n3_path, n1_path), ("n3_first", n1_path, n3_path)):
            code, text = merge(second, base_path, first)
            (OUT / f"{name}.{order}.merged").write_text(text, encoding="utf-8")
            merged_set = set(text.splitlines())
            entry[order] = {
                "conflicts": code,
                "n1_added_lines_missing": len([ln for ln in added_lines(n1, base) if ln not in merged_set]),
                "n3_added_lines_missing": len([ln for ln in added_lines(n3, base) if ln not in merged_set]),
                "stamp_lines": [ln for ln in text.splitlines() if STAMP.match(ln)],
            }
            if rel == "CHANGELOG.md" and code == 0:
                entry[order]["unreleased_outline"] = unreleased_outline(text)
        entry["stamps"] = {
            "base": [ln for ln in base.splitlines() if STAMP.match(ln)],
            "n1": [ln for ln in n1.splitlines() if STAMP.match(ln)],
            "n3": [ln for ln in n3.splitlines() if STAMP.match(ln)],
        }
        report[rel] = entry
    (OUT / "merge_sim.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
