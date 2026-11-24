"""
Rehearse the D-14 carriers' three-way rebuild onto today's origin/mains, in the validator's scratch only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator MN2, claims lens, flood-4 session 9)
Created: 2026-11-16
Status: ad-hoc - investigation
Retire when: RETAINED - ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Cursor flood-4 disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)

Usage: python3 <this file>   (after 2026-11-16_flood4r2_val_d14-claims_diffs.py has written <scratch>/diffs/)
For every carrier file that main changed since the carrier's base: `git merge-file -p <carrier> <base> <main>` into
<scratch>/threeway/<repo>/<file>.merged, the conflict count from its exit status, and the suite count of the merged
ci.yml. Never writes to either carrier.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
O = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
ML = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d"
CC = JUNIPER / "worktrees" / "juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d"
LENS = O / "tmp" / "flood4r2-val" / "d14-claims-lens"
DIFFS = LENS / "diffs"
OUT = LENS / "threeway"
CARRIERS = {"ml": ML, "cascor": CC}


def merge(repo, path):
    safe = path.replace("/", "__")
    base = DIFFS / repo / f"{safe}.base"
    main = DIFFS / repo / f"{safe}.main"
    work = OUT / repo / safe
    work.mkdir(parents=True, exist_ok=True)
    current = work / "carrier"
    shutil.copy2(CARRIERS[repo] / path, current)
    res = subprocess.run(["git", "merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", str(current), str(base), str(main)], capture_output=True, check=False)
    merged = work / "merged"
    merged.write_bytes(res.stdout)
    text = res.stdout.decode("utf-8")
    markers = [n for n, line in enumerate(text.splitlines(), 1) if line.startswith(("<<<<<<< ", ">>>>>>> ")) or line == "======="]
    return {"path": path, "exit": res.returncode, "conflicts": res.returncode if res.returncode > 0 else 0, "marker_lines": markers[:12], "merged": str(merged)}


def suite_count(text):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if "name: Run Python regression tests" in line)
    count = 0
    for line in lines[start + 1 :]:
        if re.match(r"^\s{6}- name: ", line):
            break
        if line.strip().startswith("python3 -m unittest"):
            count += 1
    return count


def main():
    summary = json.loads((DIFFS / "summary.json").read_text(encoding="utf-8"))
    results = {}
    for repo, res in summary.items():
        rows = []
        for row in res["files"]:
            if row["base_exists"] and row["main_changed_since_base"]:
                rows.append(merge(repo, row["path"]))
        results[repo] = {"base": res["base"], "main": res["main"], "merges": rows}
    ci_main = (DIFFS / "ml" / ".github__workflows__ci.yml.main").read_text(encoding="utf-8")
    ci_merged = (OUT / "ml" / ".github__workflows__ci.yml" / "merged").read_text(encoding="utf-8")
    results["ml"]["suite_count_main"] = suite_count(ci_main)
    results["ml"]["suite_count_merged"] = suite_count(ci_merged)
    (OUT / "summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for repo, res in results.items():
        for row in res["merges"]:
            print(f"{repo}: {row['path']}: merge-file exit {row['exit']} (conflicts {row['conflicts']}) markers at {row['marker_lines']}")
    print("ml suite count: main", results["ml"]["suite_count_main"], "merged", results["ml"]["suite_count_merged"])


if __name__ == "__main__":
    main()
