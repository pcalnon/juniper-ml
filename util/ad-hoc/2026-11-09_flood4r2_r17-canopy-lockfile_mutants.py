"""
Mutation and revert checks for the owner-ruling-17 fix in juniper-canopy's lockfile-update.yml.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4, owner ruling 17 ("canopy: dead error path"); juniper-canopy
         src/tests/regression/test_lockfile_regen_empty_payload.py

For each mutant, the workflow file in the canopy worktree is rewritten with ONE exact
string replacement (the old text must occur exactly once), stale ``__pycache__`` under the
test's directory is removed, the regression test file runs under the given interpreter
with a JUnit report, and the original bytes are written back and checked by sha256. The
``main`` case swaps in main's whole workflow instead of one line, which shows the new tests
fail on main. Any restore mismatch stops the run with exit 2.

Usage::

    python3 util/ad-hoc/2026-11-09_flood4r2_r17-canopy-lockfile_mutants.py \
        --worktree <canopy worktree> --python <interpreter> --main-copy <main's lockfile-update.yml> \
        --out <dir under that worktree's tmp/>

Writes ``<out>/mutants.json`` and one JUnit XML and log per case. Exit 0 when every mutant
is killed, the main case fails the new tests, and every restore matched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - runs pytest on the canopy worktree
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses the JUnit XML this script's own pytest run wrote
from pathlib import Path

WORKFLOW = Path(".github/workflows/lockfile-update.yml")
TEST_FILE = Path("src/tests/regression/test_lockfile_regen_empty_payload.py")
NEW_TESTS = (
    "test_a_graphql_error_that_fails_gh_prints_the_steps_diagnostic",
    "test_an_http_failure_prints_that_the_commit_is_unknown",
    "test_gh_output_is_printed_with_the_token_masked",
)

MUTANTS = [
    {
        "id": "M1-bare-gh-call",
        "what": "drop `|| GH_STATUS=$?`: the gh call is bare again under set -e",
        "old": "; } 2>&1) || GH_STATUS=$?",
        "new": "; } 2>&1)",
    },
    {
        "id": "M2-no-token-mask",
        "what": "redact prints its argument unmasked",
        "old": "printf '%s\\n' \"${1//\"${GH_TOKEN:-}\"/***}\"",
        "new": "printf '%s\\n' \"${1}\"",
    },
    {
        "id": "M3-http-branch-condition",
        "what": "the HTTP-failure branch tests -ne 1 instead of -ne 0",
        "old": 'if [ "${GH_STATUS}" -ne 0 ]; then',
        "new": 'if [ "${GH_STATUS}" -ne 1 ]; then',
    },
    {
        "id": "M4-401-hint-pattern",
        "what": "the 401 hint matches (HTTP 403) instead of (HTTP 401)",
        "old": '*"(HTTP 401)"*',
        "new": '*"(HTTP 403)"*',
    },
    {
        "id": "M5-stderr-print-inverted",
        "what": "gh's captured stderr is printed only when it is empty",
        "old": 'if [ -n "${GH_STDERR}" ]; then',
        "new": 'if [ -z "${GH_STDERR}" ]; then',
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def failed_tests(junit: Path) -> list[str]:
    if not junit.is_file():
        return ["<no junit report>"]
    root = ET.parse(junit).getroot()  # nosec B314 - our own pytest's report
    names = []
    for case in root.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            names.append(case.get("name", "?"))
    return names


def run_pytest(worktree: Path, python: str, out: Path, case_id: str) -> dict:
    pycache = worktree / TEST_FILE.parent / "__pycache__"
    if pycache.is_dir():
        shutil.rmtree(pycache)
    junit = out / f"{case_id}.junit.xml"
    log = out / f"{case_id}.log"
    command = [python, "-m", "pytest", str(TEST_FILE), "-p", "no:cacheprovider", "-q", f"--junitxml={junit}"]
    proc = subprocess.run(command, cwd=worktree, capture_output=True, text=True, check=False, timeout=600)  # nosec B603 - fixed argv
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {"pytest_exit": proc.returncode, "failed": failed_tests(junit), "junit": str(junit), "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--main-copy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    worktree = args.worktree.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    target = worktree / WORKFLOW
    original = target.read_bytes()
    original_sha = sha256(target)
    results = []
    problems = []

    baseline = run_pytest(worktree, args.python, out, "baseline-fixed")
    results.append({"id": "baseline-fixed", "what": "the fixed tree, unmutated", **baseline})
    if baseline["pytest_exit"] != 0:
        problems.append("baseline fails")

    cases = [{"id": "main", "what": "main's whole lockfile-update.yml (609a26a3) in place of the fix", "replace_all": args.main_copy.read_bytes()}] + MUTANTS
    for mutant in cases:
        try:
            if "replace_all" in mutant:
                target.write_bytes(mutant["replace_all"])
            else:
                text = original.decode("utf-8")
                if text.count(mutant["old"]) != 1:
                    problems.append(f"{mutant['id']}: old text occurs {text.count(mutant['old'])} times; not applied")
                    continue
                target.write_bytes(text.replace(mutant["old"], mutant["new"]).encode("utf-8"))
            outcome = run_pytest(worktree, args.python, out, mutant["id"])
        finally:
            target.write_bytes(original)
        restored = sha256(target) == original_sha
        killed = outcome["pytest_exit"] != 0 and bool(outcome["failed"])
        row = {"id": mutant["id"], "what": mutant["what"], **outcome, "killed": killed, "restored_sha256_matches": restored}
        if mutant["id"] == "main":
            row["new_tests_failing_on_main"] = sorted({name.split("[")[0] for name in outcome["failed"]} & set(NEW_TESTS))
            row["old_tests_failing_on_main"] = sorted({name.split("[")[0] for name in outcome["failed"]} - set(NEW_TESTS))
        results.append(row)
        if not restored:
            print(f"RESTORE MISMATCH after {mutant['id']}", file=sys.stderr)
            (out / "mutants.json").write_text(json.dumps({"results": results, "problems": problems + ["restore mismatch"]}, indent=2) + "\n", encoding="utf-8")
            return 2
        if not killed:
            problems.append(f"{mutant['id']} survived")

    final_sha = sha256(target)
    report = {"workflow": str(WORKFLOW), "original_sha256": original_sha, "final_sha256": final_sha, "results": results, "problems": problems}
    (out / "mutants.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in results:
        print(f"{row['id']:26} pytest_exit={row['pytest_exit']} killed={row.get('killed', '-')} restored={row.get('restored_sha256_matches', '-')} failed={row['failed']}")
    print(f"original sha256 {original_sha}; final sha256 {final_sha}; problems: {problems}")
    return 0 if not problems and final_sha == original_sha else 1


if __name__ == "__main__":
    sys.exit(main())
