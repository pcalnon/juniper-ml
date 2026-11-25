#!/usr/bin/env python3
"""Prove a ruling-26 port: its tests pass on the fixed workflow, fail on main's, and kill each one-line mutant (flood-4 session 11).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the ruling-26 lockfile-print ports, built in clones under tmp/flood4/session11/r26/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 26); juniper-canopy#814 (the model
    fix and its five mutants); tmp/flood4/session11/briefs/B26_lockfile_print_ports_builder.txt

For one clone, in order:
  fixed   run the given pytest command against the workflow as it stands (the fix);
  main    copy MAIN_COPY (main's lockfile-update.yml, extracted beforehand with `git show`) over the workflow and run it again;
  M1..M5  for each one-line mutant of the fix (canopy#814's five), apply it to the fixed text and run it again.
After every run the fixed workflow is written back and its sha256 checked against the one read at the start; a mismatch
stops the script. The script runs no git and writes nothing outside --out and the workflow file it swaps. pytest gets
--basetemp under --out, and TMPDIR and GIT_CEILING_DIRECTORIES point under --out too, so a step a test executes cannot
reach the system temp directory through them (the tests themselves also relocate the step's runner paths into tmp_path).

The mutants (each OLD must occur exactly once in the fixed workflow, or the script stops):
  M1 bare-call   the capture line back to `gh api graphql --input ... > ...` (the unreachable form); both strings are
                 read from the workflow's own capture line, so this script restates none of the step's runner paths
  M2 no-mask     redact() prints its argument unmasked
  M3 ne-1        the HTTP-failure branch tests `-ne 1` instead of `-ne 0`
  M4 http-403    the 401 hint matches `(HTTP 403)`
  M5 err-inv     gh's stderr is printed only when it is EMPTY

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_r26_proof.py --clone DIR --workflow REL --main-copy FILE --out DIR \
        --python PY [--expect-new NODEID_SUBSTR ...] -- PYTEST_ARGS...
Writes <out>/summary.json and <out>/summary.txt, one junit XML and one log per run. Exit 0 when: the fixed run has no
failure or error; every failure on main is a test whose id contains one of --expect-new (when given) and main fails at
least one; and every mutant fails at least one test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- runs pytest with a fixed interpreter and argv
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses junit XML that this script's own pytest runs wrote
from pathlib import Path

CAPTURE_PREFIX = "GH_STDERR=$({ "
CAPTURE_SUFFIX = "; } 2>&1) || GH_STATUS=$?"
OTHER_MUTANTS = [
    ("M2-no-mask", "printf '%s\\n' \"${1//\"${GH_TOKEN:-}\"/***}\"", "printf '%s\\n' \"${1}\""),
    ("M3-ne-1", 'if [ "${GH_STATUS}" -ne 0 ]; then', 'if [ "${GH_STATUS}" -ne 1 ]; then'),
    ("M4-http-403", '*"(HTTP 401)"*', '*"(HTTP 403)"*'),
    ("M5-err-inv", 'if [ -n "${GH_STDERR}" ]; then', 'if [ -z "${GH_STDERR}" ]; then'),
]
DROP_ENV = ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR")


def _mutants(fixed_text: str) -> list[tuple[str, str, str]]:
    """The five mutants. M1 turns the workflow's own capture line back into the bare call inside it."""
    captures = [line.strip() for line in fixed_text.splitlines() if line.strip().startswith(CAPTURE_PREFIX + "gh api graphql ") and line.strip().endswith(CAPTURE_SUFFIX)]
    if len(captures) != 1:
        raise SystemExit(f"STOP: expected one capture line in the fixed workflow, found {len(captures)}")
    capture = captures[0]
    return [("M1-bare-call", capture, capture[len(CAPTURE_PREFIX) : -len(CAPTURE_SUFFIX)]), *OTHER_MUTANTS]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _results(junit: Path) -> dict[str, str]:
    """{test id: passed|failed|error|skipped} from a pytest junit XML."""
    outcome: dict[str, str] = {}
    if not junit.is_file():
        return outcome
    root = ET.parse(junit).getroot()  # nosec B314 -- this run's own junit output
    for case in root.iter("testcase"):
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}"
        state = "passed"
        for child in case:
            if child.tag in ("failure", "error", "skipped"):
                state = {"failure": "failed", "error": "error", "skipped": "skipped"}[child.tag]
                break
        outcome[test_id] = state
    return outcome


def _run(label: str, args: argparse.Namespace, pytest_args: list[str]) -> dict:
    out: Path = args.out
    basetemp = out / f"basetemp_{label}"
    tmpdir = out / "tmpdir"
    tmpdir.mkdir(parents=True, exist_ok=True)
    junit = out / f"junit_{label}.xml"
    env = {key: value for key, value in os.environ.items() if key not in DROP_ENV}
    env["TMPDIR"] = str(tmpdir)
    env["GIT_CEILING_DIRECTORIES"] = str(out)
    argv = [args.python, "-m", "pytest", *pytest_args, f"--basetemp={basetemp}", f"--junitxml={junit}", "-p", "no:cacheprovider"]
    proc = subprocess.run(argv, cwd=args.clone, env=env, capture_output=True, text=True, check=False, timeout=1800)  # nosec B603 -- fixed interpreter, caller's pytest args
    (out / f"log_{label}.txt").write_text(f"$ {' '.join(argv)}\n(cwd {args.clone})\nexit {proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")
    results = _results(junit)
    failed = sorted(test for test, state in results.items() if state in ("failed", "error"))
    return {
        "label": label,
        "exit": proc.returncode,
        "counts": {state: sum(1 for value in results.values() if value == state) for state in ("passed", "failed", "error", "skipped")},
        "failed": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clone", type=Path, required=True)
    parser.add_argument("--workflow", required=True, help="repo-relative path of lockfile-update.yml")
    parser.add_argument("--main-copy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--expect-new", action="append", default=[], help="substring of a test id that is new in this port; main may fail only these")
    parser.add_argument("pytest_args", nargs="+")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    workflow = args.clone / args.workflow
    fixed_text = workflow.read_text(encoding="utf-8")
    fixed_sha = _sha256(workflow)
    backup = args.out / "fixed_workflow.yml"
    backup.write_text(fixed_text, encoding="utf-8")
    main_text = args.main_copy.read_text(encoding="utf-8")

    variants: list[tuple[str, str]] = [("fixed", fixed_text), ("main", main_text)]
    mutants = _mutants(fixed_text)
    (args.out / "mutants.json").write_text(json.dumps([{"name": name, "old": old, "new": new} for name, old, new in mutants], indent=2) + "\n", encoding="utf-8")
    for name, old, new in mutants:
        if fixed_text.count(old) != 1:
            print(f"STOP: mutant {name}: OLD occurs {fixed_text.count(old)} times in the fixed workflow, not once", file=sys.stderr)
            return 2
        variants.append((name, fixed_text.replace(old, new, 1)))

    runs = []
    for label, text in variants:
        workflow.write_text(text, encoding="utf-8")
        try:
            run = _run(label, args, args.pytest_args)
        finally:
            shutil.copyfile(backup, workflow)
        restored = _sha256(workflow)
        if restored != fixed_sha:
            print(f"STOP: after {label} the workflow's sha256 is {restored}, not the fixed {fixed_sha}", file=sys.stderr)
            return 3
        run["workflow_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        run["restored_sha256"] = restored
        runs.append(run)

    by_label = {run["label"]: run for run in runs}
    fixed_ok = by_label["fixed"]["counts"]["failed"] == 0 and by_label["fixed"]["counts"]["error"] == 0 and by_label["fixed"]["counts"]["passed"] > 0
    main_failed = by_label["main"]["failed"]
    main_ok = bool(main_failed) and (not args.expect_new or all(any(sub in test for sub in args.expect_new) for test in main_failed))
    mutants_ok = all(by_label[name]["failed"] for name, _old, _new in mutants)
    verdict = {"fixed_all_pass": fixed_ok, "main_fails_only_new_tests": main_ok, "every_mutant_killed": mutants_ok, "fixed_sha256": fixed_sha}
    (args.out / "summary.json").write_text(json.dumps({"verdict": verdict, "runs": runs}, indent=2) + "\n", encoding="utf-8")
    lines = [f"clone {args.clone}", f"workflow {args.workflow} fixed sha256 {fixed_sha}", f"pytest args: {' '.join(args.pytest_args)}", ""]
    for run in runs:
        lines.append(f"[{run['label']}] exit {run['exit']} {run['counts']} restored={run['restored_sha256'] == fixed_sha}")
        lines.extend(f"    FAILED {test}" for test in run["failed"])
    lines += ["", f"verdict: {json.dumps(verdict)}"]
    (args.out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if fixed_ok and main_ok and mutants_ok else 1


if __name__ == "__main__":
    sys.exit(main())
