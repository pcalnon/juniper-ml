#!/usr/bin/env python3
"""
Re-run the validator's mutants of the juniper-data-client ruling-10 port against the FIXED-UP carrier, in a copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 6: the fix-up of the ruling-10 pilot port)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530;
         util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_mutants.py (the validator's script, whose MUTANTS list this loads)

WHY THIS EXISTS
The validator of the pilot port found twelve workflow edits that left all 25 cases of tests/test_gitleaks_pr_scan.py
green (its finding F1 and five minor ones), and proposed asserts that pin them. This shows, on the carrier's final
bytes, that each of those edits now turns a case red, and how many of the 25 cases fail on main's workflow.

WHAT IT DOES
It never edits the carrier. It works in a COPY: a detached worktree of the repository at the carrier's base commit.
  1. It copies the carrier's changed files into the copy (the paths `git status --porcelain` lists in the carrier)
     and proves each copy by sha256.
  2. Baseline: the whole test file, every case in the run, with the real engine required. It must be green.
  3. With --main-workflow: the base commit's own ci.yml in place of the carrier's, the whole file again.
  4. Each chosen mutant: one exact-once edit of ci.yml (the validator's own list, loaded from its script by path),
     the whole file again, then the file restored in a `finally` and the restore proved by sha256.
The cases run in four pytest processes at a time, each process a slice of the file's node ids, and every outcome is
read from that process's junit report. Every run has the six Sentry DSN variables set to the empty string.

Usage:
  2026-11-12_flood4r2_r10-data-client_validator_mutants.py --carrier <carrier worktree> --copy <copy worktree>
      --validator-script <the validator's mutants script> --engine <gitleaks 8.24.3> --python <interpreter> --out <dir>
      (--ids V01,V02,... | --survivors-from <the validator's mutants.json>) [--main-workflow] [--expect 25]

Exit 0 = the baseline passed --expect cases, every chosen mutant was killed and every restore was exact; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv: git reads, and the chosen interpreter running pytest
import sys
import xml.etree.ElementTree as ElementTree
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
CI = ".github/workflows/ci.yml"
TEST_FILE = "tests/test_gitleaks_pr_scan.py"
CARRIER_MARK = "--ci--gitleaks-pr-commit-scan--"
WORKERS = 4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_out(tree: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(tree), *args], capture_output=True, text=True, check=True).stdout  # nosec B603 B607


def changed_paths(carrier: Path) -> list[str]:
    """The carrier's changed and untracked paths, as `git status --porcelain` lists them."""
    return sorted(line[3:] for line in git_out(carrier, "status", "--porcelain").splitlines() if line.strip())


def overlay(carrier: Path, copy: Path, paths: list[str]) -> dict[str, str]:
    copied: dict[str, str] = {}
    for rel in paths:
        target = copy / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(carrier / rel, target)
        if sha256(target) != sha256(carrier / rel):
            raise SystemExit(f"{rel}: the copy differs from the carrier straight after copying")
        copied[rel] = sha256(target)
    return copied


def test_env(engine: str) -> dict[str, str]:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "PYTHONDONTWRITEBYTECODE": "1", "GITLEAKS_PARITY_REQUIRED": "1", "GITLEAKS_BIN": engine}
    for name in ("GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML"):
        env.pop(name, None)
    return env


def collect(python: str, copy: Path, env: dict[str, str]) -> list[str]:
    # No -q here: the repository's addopts already carry one, and a second would print a count per file, not the ids.
    res = subprocess.run([python, "-m", "pytest", TEST_FILE, "--collect-only", "-p", "no:cacheprovider"], cwd=copy, capture_output=True, text=True, env=env, check=False)  # nosec B603
    return [line.strip() for line in res.stdout.splitlines() if line.startswith(TEST_FILE + "::")]


def run_slice(python: str, copy: Path, env: dict[str, str], node_ids: list[str], out: Path, label: str, slot: int) -> dict[str, str]:
    """Run one slice of node ids in a pytest process of its own; return {case name: passed|failed|error|skipped|missing}."""
    junit = out / f"{label}.slot{slot}.junit.xml"
    basetemp = out / "basetemp" / f"{label}-slot{slot}"
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    argv = [python, "-m", "pytest", *node_ids, "-q", "--no-header", "-p", "no:cacheprovider", "--timeout=300", f"--basetemp={basetemp}", f"--junitxml={junit}", "-rfEs"]
    res = subprocess.run(argv, cwd=copy, capture_output=True, text=True, env=env, check=False)  # nosec B603
    (out / f"{label}.slot{slot}.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    outcomes = {node_id.split("::", 1)[1]: "missing" for node_id in node_ids}
    if junit.is_file():
        for case in ElementTree.parse(junit).getroot().iter("testcase"):
            name = case.get("name", "")
            if case.find("failure") is not None:
                outcomes[name] = "failed"
            elif case.find("error") is not None:
                outcomes[name] = "error"
            elif case.find("skipped") is not None:
                outcomes[name] = "skipped"
            else:
                outcomes[name] = "passed"
    return outcomes


def run_file(python: str, copy: Path, env: dict[str, str], node_ids: list[str], out: Path, label: str) -> dict:
    """The whole file, as WORKERS slices side by side; every case's outcome, and the counts."""
    for stale in (copy / "tests" / "__pycache__").glob("test_gitleaks_pr_scan*.pyc"):
        stale.unlink()
    slices = [node_ids[index::WORKERS] for index in range(WORKERS)]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(run_slice, python, copy, env, chunk, out, label, slot) for slot, chunk in enumerate(slices) if chunk]
        merged: dict[str, str] = {}
        for future in futures:
            merged.update(future.result())
    counts = {kind: sum(1 for outcome in merged.values() if outcome == kind) for kind in ("passed", "failed", "error", "skipped", "missing")}
    return {"counts": counts, "not_passed": sorted(name for name, outcome in merged.items() if outcome != "passed"), "outcomes": merged}


def write_record(out: Path, record: dict) -> None:
    with open(out / "mutants.json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
        fh.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--validator-script", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ids", help="comma-separated mutant ids of the validator's list")
    parser.add_argument("--survivors-from", type=Path, help="the validator's mutants.json: run the ids its totals.survived names")
    parser.add_argument("--main-workflow", action="store_true", help="also run the file with the base commit's ci.yml in place (label MAIN)")
    parser.add_argument("--expect", type=int, default=25, help="how many cases the baseline must pass (default 25, the whole file)")
    args = parser.parse_args()
    carrier, copy, out = args.carrier.resolve(), args.copy.resolve(), args.out.resolve()
    if CARRIER_MARK in str(copy) or copy == carrier:
        raise SystemExit("refusing to mutate the carrier worktree: --copy must be another tree")
    if git_out(copy, "rev-parse", "HEAD").strip() != git_out(carrier, "rev-parse", "HEAD").strip():
        raise SystemExit("the copy is not at the carrier's base commit")
    if args.ids:
        wanted = args.ids.split(",")
    elif args.survivors_from:
        wanted = list(json.loads(args.survivors_from.read_text(encoding="utf-8"))["totals"]["survived"])
    else:
        raise SystemExit("give --ids or --survivors-from")
    spec = importlib.util.spec_from_file_location("validator_mutants", args.validator_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    by_id = {mutant[0]: mutant for mutant in module.MUTANTS}
    unknown = [ident for ident in wanted if ident not in by_id]
    if unknown:
        raise SystemExit(f"not in the validator's list: {unknown}")

    out.mkdir(parents=True, exist_ok=True)
    paths = changed_paths(carrier)
    copied = overlay(carrier, copy, paths)
    target = copy / CI
    original = target.read_bytes()
    before = sha256(target)
    text = original.decode("utf-8")
    for ident in wanted:
        if text.count(by_id[ident][2]) != 1:
            raise SystemExit(f"{ident}: its pattern occurs {text.count(by_id[ident][2])} times in {CI} (expected 1)")
    env = test_env(args.engine)
    node_ids = collect(args.python, copy, env)
    record: dict = {
        "carrier": str(carrier),
        "copy": str(copy),
        "base_sha": git_out(copy, "rev-parse", "HEAD").strip(),
        "copied_from_carrier_sha256": copied,
        "engine_sha256": sha256(Path(args.engine)),
        "python": args.python,
        "validator_script": str(args.validator_script),
        "validator_script_sha256": sha256(args.validator_script),
        "collected": len(node_ids),
        "mutants": [],
    }
    record["baseline"] = run_file(args.python, copy, env, node_ids, out, "baseline")
    write_record(out, record)
    print(f"collected {len(node_ids)} cases; baseline: {record['baseline']['counts']}")
    if record["baseline"]["counts"]["passed"] != args.expect or len(node_ids) != args.expect:
        print(f"the baseline is not {args.expect} passed of {args.expect} collected: no mutant was run")
        return 1

    if args.main_workflow:
        try:
            target.write_bytes(git_out(copy, "show", f"HEAD:{CI}").encode("utf-8"))
            main_sha = sha256(target)
            on_main = run_file(args.python, copy, env, node_ids, out, "MAIN")
        finally:
            target.write_bytes(original)
        record["main_workflow"] = {"ci_sha256": main_sha, "restored": sha256(target) == before, "counts": on_main["counts"], "not_passed": on_main["not_passed"], "passed": sorted(name for name, outcome in on_main["outcomes"].items() if outcome == "passed")}
        write_record(out, record)
        print(f"main's workflow in place: {on_main['counts']}; still passing: {record['main_workflow']['passed']}")
        if not record["main_workflow"]["restored"]:
            raise SystemExit("MAIN: RESTORE FAILED")

    for ident in wanted:
        _, what, find, replace = by_id[ident]
        try:
            target.write_bytes(text.replace(find, replace).encode("utf-8"))
            mutated_sha = sha256(target)
            result = run_file(args.python, copy, env, node_ids, out, ident)
        finally:
            target.write_bytes(original)
        restored = sha256(target) == before
        killed_by = sorted(name for name, outcome in result["outcomes"].items() if outcome in ("failed", "error"))
        entry = {"id": ident, "what": what, "mutated_sha256": mutated_sha, "killed": bool(killed_by), "killed_by": killed_by, "counts": result["counts"], "restored": restored}
        record["mutants"].append(entry)
        write_record(out, record)
        print(f"{ident} {'KILLED  ' if entry['killed'] else 'SURVIVED'} {what}\n      by: {killed_by}  counts={result['counts']}  restored={restored}")
        if not restored:
            raise SystemExit(f"{ident}: RESTORE FAILED")

    # The cases read two of the carrier's files: the workflow and the test file itself.
    read_by_the_cases = (CI, TEST_FILE)
    record["totals"] = {
        "mutants": len(record["mutants"]),
        "killed": sum(1 for entry in record["mutants"] if entry["killed"]),
        "survived": [entry["id"] for entry in record["mutants"] if not entry["killed"]],
        "ci_sha256_before": before,
        "ci_sha256_after": sha256(target),
        "workflow_and_test_file_equal_the_carriers_after": all(sha256(copy / rel) == sha256(carrier / rel) for rel in read_by_the_cases),
    }
    write_record(out, record)
    print(json.dumps(record["totals"], indent=2))
    return 0 if not record["totals"]["survived"] and record["totals"]["ci_sha256_after"] == before else 1


if __name__ == "__main__":
    sys.exit(main())
