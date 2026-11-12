#!/usr/bin/env python3
"""
Collect juniper-data's tests per CI lane (--collect-only) and name the ones no lane runs.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4, owner ruling 17: "data: 44 unrun tests")
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (re-derive the defect before the fix, prove the delta after it)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17 is recorded in the record-update PR)

WHAT IT DOES
Runs juniper-data's pytest with ``--collect-only`` (no test body runs) once per selection that a juniper-data
workflow uses, as of juniper-data main 272ff615:

    unit         ci.yml unit-tests:       -m "unit and not slow" juniper_data/tests/unit
    integration  ci.yml integration-tests: -m "integration and not slow" juniper_data/tests/integration
    gitleaks     ci.yml security:          juniper_data/tests/unit/test_gitleaks_config.py (by path, no -m)
    slow         ci.yml slow-tests (schedule/dispatch): -m "slow" (testpaths)
    scheduled    scheduled-tests.yml (schedule/dispatch): -m "slow or integration" (testpaths)
    all          no selection (testpaths), the universe
    unit_dir     juniper_data/tests/unit with no -m

and writes <out>/collect_<tag>.json: per-selection node ids and counts, the test_security.py counts, and a census
of every collected node that NO selection above runs ("no lane at all"), grouped by file, with the marker names
each such file uses. ``--tag`` names the tree state (before / after). ``--compare before after`` diffs two runs.

The interpreter is the JuniperData conda env. pytest's own addopts carry one ``-q``, so none is added (a second
collapses the listing to per-file counts). ``-p no:cacheprovider`` and ``-B`` keep the worktree clean; TMPDIR is
left exactly as the session gave it.

Usage:
    python3 <this> --worktree <juniper-data worktree> --out <dir> --tag <before|after>
    python3 <this> --out <dir> --compare <tagA> <tagB>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: the JuniperData interpreter running pytest --collect-only
import sys
from collections import Counter
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
SECURITY_FILE = "juniper_data/tests/unit/test_security.py"
SELECTIONS: dict[str, list[str]] = {
    "unit": ["-m", "unit and not slow", "juniper_data/tests/unit"],
    "integration": ["-m", "integration and not slow", "juniper_data/tests/integration"],
    "gitleaks": ["juniper_data/tests/unit/test_gitleaks_config.py"],
    "slow": ["-m", "slow"],
    "scheduled": ["-m", "slow or integration"],
    "all": [],
    "unit_dir": ["juniper_data/tests/unit"],
}
LANES = ("unit", "integration", "gitleaks", "slow", "scheduled")
PR_LANES = ("unit", "integration", "gitleaks")
MARK_RE = re.compile(r"pytest\.mark\.([A-Za-z_][A-Za-z0-9_]*)")
SUMMARY_RE = re.compile(r"(\d+(?:/\d+)? tests? collected.*|no tests collected.*|\d+ deselected.*)")


def _collect(worktree: Path, out: Path, tag: str, name: str, sel: list[str]) -> dict:
    argv = [PYTHON, "-B", "-m", "pytest", "--collect-only", "-p", "no:cacheprovider", "-p", "no:randomly", *sel]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(argv, cwd=worktree, env=env, capture_output=True, text=True, check=False)  # nosec B603
    log = out / f"collect_{tag}_{name}.log"
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={worktree}) {' '.join(argv)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    nodes = sorted({ln.strip() for ln in proc.stdout.splitlines() if ln.startswith("juniper_data/tests/") and "::" in ln})
    tail = [m.group(1) for ln in proc.stdout.splitlines() if (m := SUMMARY_RE.search(ln))]
    return {"argv": argv, "exit": proc.returncode, "count": len(nodes), "summary": tail[-1] if tail else "<none>", "log": str(log), "nodes": nodes}


def _file_marks(worktree: Path, rel: str) -> dict:
    with open(worktree / rel, encoding="utf-8") as fh:
        text = fh.read()
    module_mark = [ln.strip() for ln in text.splitlines() if ln.startswith("pytestmark")]
    return {"module_pytestmark": module_mark, "marks_used": sorted(Counter(MARK_RE.findall(text)))}


def _import_origin(worktree: Path) -> str:
    argv = [PYTHON, "-B", "-c", "import juniper_data; print(juniper_data.__file__)"]
    proc = subprocess.run(argv, cwd=worktree, capture_output=True, text=True, check=False)  # nosec B603
    return (proc.stdout.strip() or proc.stderr.strip()[-300:])


def run(worktree: Path, out: Path, tag: str) -> int:
    out.mkdir(parents=True, exist_ok=True)
    res = {name: _collect(worktree, out, tag, name, sel) for name, sel in SELECTIONS.items()}
    sets = {name: set(r["nodes"]) for name, r in res.items()}
    in_lane = set().union(*(sets[n] for n in LANES))
    in_pr_lane = set().union(*(sets[n] for n in PR_LANES))
    no_lane = sorted(sets["all"] - in_lane)
    sched_only = sorted((sets["all"] & in_lane) - in_pr_lane)
    by_file_no_lane = Counter(n.split("::", 1)[0] for n in no_lane)
    by_file_sched_only = Counter(n.split("::", 1)[0] for n in sched_only)
    sec_all = sorted(n for n in sets["unit_dir"] if n.startswith(SECURITY_FILE + "::"))
    sec_unit = sorted(n for n in sets["unit"] if n.startswith(SECURITY_FILE + "::"))
    record = {
        "worktree": str(worktree),
        "tag": tag,
        "interpreter": PYTHON,
        "juniper_data_imported_from_worktree_cwd": _import_origin(worktree),
        "selections": {name: {k: v for k, v in r.items() if k != "nodes"} for name, r in res.items()},
        "test_security": {
            "file": SECURITY_FILE,
            "collected_in_unit_dir": len(sec_all),
            "selected_by_unit_lane": len(sec_unit),
            "not_selected": sorted(set(sec_all) - set(sec_unit)),
            "not_selected_by_class": dict(Counter(n.split("::")[1] for n in set(sec_all) - set(sec_unit))),
        },
        "census_no_lane": {
            "total": len(no_lane),
            "by_file": {f: {"count": c, **_file_marks(worktree, f)} for f, c in sorted(by_file_no_lane.items())},
        },
        "census_scheduled_only": {"total": len(sched_only), "by_file": dict(sorted(by_file_sched_only.items()))},
        "nodes": {name: r["nodes"] for name, r in res.items()},
        "no_lane_nodes": no_lane,
    }
    dest = out / f"collect_{tag}.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
        fh.write("\n")
    brief = {k: record[k] for k in ("tag", "juniper_data_imported_from_worktree_cwd")}
    brief["selections"] = {n: f"exit={r['exit']} count={r['count']} [{r['summary']}]" for n, r in res.items()}
    brief["test_security"] = {k: v for k, v in record["test_security"].items() if k != "not_selected"}
    brief["census_no_lane"] = {"total": len(no_lane), "by_file": dict(sorted(by_file_no_lane.items()))}
    brief["census_scheduled_only"] = record["census_scheduled_only"]
    print(json.dumps(brief, indent=1))
    print(f"wrote {dest}")
    return 0 if all(r["exit"] == 0 for r in res.values()) else 1


def compare(out: Path, tag_a: str, tag_b: str) -> int:
    with open(out / f"collect_{tag_a}.json", encoding="utf-8") as fh:
        a = json.load(fh)
    with open(out / f"collect_{tag_b}.json", encoding="utf-8") as fh:
        b = json.load(fh)
    report: dict = {"a": tag_a, "b": tag_b, "per_selection": {}}
    for name in SELECTIONS:
        sa, sb = set(a["nodes"][name]), set(b["nodes"][name])
        report["per_selection"][name] = {"a": len(sa), "b": len(sb), "delta": len(sb) - len(sa), "added": sorted(sb - sa), "removed": sorted(sa - sb)}
    unit_added = set(report["per_selection"]["unit"]["added"])
    a_unselected = set(a["test_security"]["not_selected"])
    report["unit_added_equals_a_unselected_security_nodes"] = unit_added == a_unselected
    report["unit_removed"] = report["per_selection"]["unit"]["removed"]
    report["unit_added_outside_security_file"] = sorted(n for n in unit_added if not n.startswith(SECURITY_FILE + "::"))
    dest = out / f"compare_{tag_a}_{tag_b}.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps({n: {k: v for k, v in r.items() if k in ("a", "b", "delta")} | {"removed": len(r["removed"])} for n, r in report["per_selection"].items()}, indent=1))
    print("unit_added_equals_a_unselected_security_nodes:", report["unit_added_equals_a_unselected_security_nodes"])
    print("unit_added_outside_security_file:", report["unit_added_outside_security_file"])
    print(f"wrote {dest}")
    ok = report["unit_added_equals_a_unselected_security_nodes"] and not report["unit_removed"]
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tag")
    ap.add_argument("--compare", nargs=2, metavar=("TAG_A", "TAG_B"))
    args = ap.parse_args()
    if args.compare:
        return compare(args.out.resolve(), *args.compare)
    if not (args.worktree and args.tag):
        ap.error("--worktree and --tag are required unless --compare is given")
    return run(args.worktree.resolve(), args.out.resolve(), args.tag)


if __name__ == "__main__":
    sys.exit(main())
