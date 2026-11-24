#!/usr/bin/env python3
"""
Build the manifest of juniper-cascor's rebuilt stop-then-start carrier from its tree and its check outputs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt (DELIVERABLES), tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt
         (a carrier built on an older base is rebuilt three-way; checkpoint the manifest)

Mechanical parts only; the hand-written parts (design notes, extra checks, open questions) are
read from ``--hand`` and merged in unchanged. For every carrier file it records:

- status against ``--base`` (added / modified) and the file's sha256;
- ``kept_from_predecessor`` or ``changed_by_me``, by comparing with the first builder's copy
  under ``--predecessor`` (a directory holding the six files at their repository paths);
- the rebuild: whether ``--old-base`` .. ``--base`` changed the file, and that
  ``git merge-file -p <carrier> <old base> <base>`` returns the carrier's own bytes (a file main
  did not change needs no three-way, and the merge proves it);
- with ``--sibling``, a PREDICTION of the three-way against a main that holds the sibling
  carrier: ``git merge-file -p <carrier> <base> <sibling's copy>`` and its conflict count. The
  sibling's tree is only read.

It also summarises the lane, mutant and stress JSON files it is pointed at, and compares the
two unit lanes' JUnit files test by test. Nothing is judged here beyond those comparisons.

Usage:
  2026-11-11_flood4r2_r17-cascor_manifest.py --tree <carrier> --base <sha> --old-base <sha>
      --predecessor <dir> --scratch <dir> --hand <json> --out <manifest.json>
      [--sibling <other carrier's worktree>] [--unit-main <json> --unit-fix <json>]
      [--int-main <json> --int-fix <json>] [--mutants <json> ...] [--stress <json> ...]
Exit: 0 when the manifest was written and every rebuild check held; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 -- fixed-argv git reads
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses JUnit files written by this work's own pytest runs
from pathlib import Path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(tree: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(tree), *args], capture_output=True, check=False)  # nosec B603 B607 -- fixed argv


def _blob(tree: Path, ref: str, path: str) -> bytes | None:
    proc = _git(tree, "show", f"{ref}:{path}")
    return proc.stdout if proc.returncode == 0 else None


def _merge(scratch: Path, name: str, ours: bytes, base: bytes, theirs: bytes) -> tuple:
    """Run ``git merge-file -p ours base theirs`` on copies; return (conflict count, merged bytes)."""
    work = scratch / "three_way" / name.replace("/", "__")
    work.mkdir(parents=True, exist_ok=True)
    paths = {}
    for label, data in (("ours", ours), ("base", base), ("theirs", theirs)):
        paths[label] = work / label
        paths[label].write_bytes(data)
    proc = subprocess.run(["git", "merge-file", "-p", str(paths["ours"]), str(paths["base"]), str(paths["theirs"])], capture_output=True, check=False)  # nosec B603 B607 -- fixed argv
    (work / "merged").write_bytes(proc.stdout)
    return proc.returncode, proc.stdout


def _junit(path: Path) -> dict:
    outcomes = {}
    for case in ET.parse(path).getroot().iter("testcase"):  # nosec B314 -- our own pytest output
        test_id = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None or case.find("error") is not None:
            outcomes[test_id] = "fail"
        elif case.find("skipped") is not None:
            outcomes[test_id] = "skip"
        else:
            outcomes[test_id] = "pass"
    return outcomes


def _lane(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    counts = data.get("counts") or {}
    gate = "" if data.get("coverage_gate_exit") is None else f"; coverage gate exit {data['coverage_gate_exit']}"
    result = f"{counts.get('passed')} passed, {counts.get('failures')} failed, {counts.get('errors')} errors (pytest exit {data.get('pytest_exit')}{gate})"
    return {"result": result} | {key: data.get(key) for key in ("tree", "lane", "python", "pytest_exit", "coverage_gate_exit", "coverage_total_line", "provenance_ok", "counts", "failing", "log", "junit")} | {"argv": " ".join(data.get("argv", []))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--old-base", required=True)
    parser.add_argument("--predecessor", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--hand", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--sibling", type=Path)
    parser.add_argument("--unit-main", type=Path)
    parser.add_argument("--unit-fix", type=Path)
    parser.add_argument("--int-main", type=Path)
    parser.add_argument("--int-fix", type=Path)
    parser.add_argument("--mutants", type=Path, action="append", default=[])
    parser.add_argument("--stress", type=Path, action="append", default=[])
    args = parser.parse_args()
    tree = args.tree.resolve()
    scratch = args.scratch.resolve()
    hand = json.loads(args.hand.read_text(encoding="utf-8"))
    ok = True

    head = _git(tree, "rev-parse", "HEAD").stdout.decode().strip()
    base = _git(tree, "rev-parse", args.base).stdout.decode().strip()
    old_base = _git(tree, "rev-parse", args.old_base).stdout.decode().strip()
    porcelain = _git(tree, "status", "--porcelain", "--untracked-files=all").stdout.decode().splitlines()
    files = []
    for line in porcelain:
        code, path = line[:2], line[3:]
        current = (tree / path).read_bytes()
        entry = {"path": path, "status": "added" if code == "??" or "A" in code else "modified", "sha256": _sha256(current)}
        before = args.predecessor / path
        if before.exists():
            entry["predecessor_sha256"] = _sha256(before.read_bytes())
            entry["provenance"] = "kept_from_predecessor" if entry["predecessor_sha256"] == entry["sha256"] else "changed_by_me"
        else:
            entry["provenance"] = "added_by_me"
        old_blob, new_blob = _blob(tree, old_base, path), _blob(tree, base, path)
        entry["main_changed_it_since_old_base"] = old_blob != new_blob
        if old_blob is not None and new_blob is not None:
            conflicts, merged = _merge(scratch, f"rebuild/{path}", current, old_blob, new_blob)
            entry["rebuild_three_way"] = {"conflicts": conflicts, "result_equals_carrier": merged == current}
            ok = ok and conflicts == 0 and merged == current
        else:
            entry["rebuild_three_way"] = "not applicable: the file is new on both bases"
        if args.sibling is not None:
            theirs = args.sibling / path
            if new_blob is not None and theirs.exists() and theirs.read_bytes() != new_blob:
                conflicts, merged = _merge(scratch, f"sibling/{path}", current, new_blob, theirs.read_bytes())
                markers = [number for number, text in enumerate(merged.decode("utf-8", errors="replace").splitlines(), start=1) if text.startswith("<<<<<<< ")]
                entry["against_a_main_holding_the_sibling"] = {"needs_three_way": True, "predicted_conflicts": conflicts, "conflict_marker_lines_in_merged": markers, "merged_copy": str(scratch / "three_way" / f"sibling/{path}".replace("/", "__") / "merged")}
            else:
                entry["against_a_main_holding_the_sibling"] = {"needs_three_way": False}
        files.append(entry)

    checks = []
    for label, path in (("unit lane on main", args.unit_main), ("unit lane on the carrier", args.unit_fix), ("integration lane on main", args.int_main), ("integration lane on the carrier", args.int_fix)):
        if path is not None:
            checks.append({"what": label, **_lane(path)})
    junit_comparison = None
    if args.unit_main is not None and args.unit_fix is not None:
        main_cases = _junit(Path(json.loads(args.unit_main.read_text(encoding="utf-8"))["junit"]))
        fix_cases = _junit(Path(json.loads(args.unit_fix.read_text(encoding="utf-8"))["junit"]))
        shared = sorted(set(main_cases) & set(fix_cases))
        only_fix = sorted(set(fix_cases) - set(main_cases))
        junit_comparison = {
            "shared_tests": len(shared),
            "shared_tests_whose_outcome_changed": [test for test in shared if main_cases[test] != fix_cases[test]],
            "only_on_main": sorted(set(main_cases) - set(fix_cases)),
            "only_on_the_carrier": len(only_fix),
            "only_on_the_carrier_modules": sorted({test.split("::")[0] for test in only_fix}),
            "only_on_the_carrier_outcomes": sorted({fix_cases[test] for test in only_fix}),
        }
    mutations = []
    for path in args.mutants:
        data = json.loads(path.read_text(encoding="utf-8"))
        for result in data["results"]:
            mutations.append({"campaign": str(path), "id": result["id"], "group": result.get("group"), "mutant": result.get("description"), "tests_run": result.get("tests_run"), "result": result.get("verdict"), "tests": result.get("tests"), "failed": len(result.get("failed") or []), "log": result.get("log")})
        checks.append({"what": f"mutation campaign {path.parent.name}: the checkout's manager.py and state_machine.py unchanged by it", "result": "pass" if data["unchanged"] else "fail", "sha256_before": data["sha256_before"], "sha256_after": data["sha256_after"]})
        ok = ok and bool(data["unchanged"])
    for path in args.stress:
        data = json.loads(path.read_text(encoding="utf-8"))
        checks.append({"what": f"stress repeat ({data['label']})", "result": "pass" if data["exit"] == 0 and not data["failed"] else "fail", **data, "log": str(path.with_suffix(".log"))})

    manifest = {
        "repo": "juniper-cascor",
        "carrier": "r17-cascor-stop-start",
        "base_sha": base,
        "old_base_sha": old_base,
        "head_sha": head,
        "head_is_base": head == base,
        "worktree": str(tree),
        "files": files,
        **{key: value for key, value in hand.items() if key not in ("checks", "open_questions")},
        "junit_comparison_unit_main_vs_carrier": junit_comparison,
        "checks": checks + hand.get("checks", []),
        "mutations": mutations,
        "open_questions": hand.get("open_questions", []),
    }
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": [(entry["path"], entry["status"], entry["provenance"]) for entry in files], "rebuild_ok": ok, "checks": len(manifest["checks"]), "mutations": len(mutations)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
