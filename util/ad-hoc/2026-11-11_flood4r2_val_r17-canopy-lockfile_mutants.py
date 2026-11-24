"""
Run canopy's lockfile-regen regression test against the carrier's workflow, main's workflow and the validator's own mutants.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

Works ONLY on the validator's own copy of juniper-canopy. Each case writes one variant of
.github/workflows/lockfile-update.yml, runs the test file, restores the original bytes and checks the sha256.
The result-file path the step writes is read from the workflow text, never spelled here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TEST_FILE = "src/tests/regression/test_lockfile_regen_empty_payload.py"
WORKFLOW = ".github/workflows/lockfile-update.yml"
HTTP_OPEN = '          if [ "${GH_STATUS}" -ne 0 ]; then\n'
FINAL_JQ = "          jq -r '\"Signed lockfile commit: \" + .data.createCommitOnBranch.commit.url' \\\n"


def _errors_open(result: str) -> str:
    return f"          if jq -e '.errors' {result} > /dev/null 2>&1; then\n"


def _replacements(result: str) -> list[tuple[str, str, str, str]]:
    """(id, what it models, old, new). `old` must occur exactly once in the carrier's workflow."""
    errors_open = _errors_open(result)
    return [
        ("V01-errors-branch-no-exit", "the GraphQL-errors branch prints but does not exit", 'needs only the re-run."\n            exit 1\n', 'needs only the re-run."\n'),
        ("V02-http-branch-no-exit", "the HTTP-failure branch prints but does not exit", "            fi\n            exit 1\n          fi\n\n          jq -r", "            fi\n          fi\n\n          jq -r"),
        ("V04-capture-drops-stderr", "gh's stderr is not captured (streams unmasked, GH_STDERR empty)", "; } 2>&1) || GH_STATUS=$?", "; }) || GH_STATUS=$?"),
        ("V05-gh-message-to-stdout", "gh's message is re-printed to stdout instead of stderr", 'redact "${GH_STDERR}" >&2', 'redact "${GH_STDERR}"'),
        ("V06-errors-print-unmasked", "the GraphQL errors are printed without the mask", f"redact \"$(jq '.errors' {result})\"", f"jq '.errors' {result}"),
        ("V07-http-body-print-unmasked", "the HTTP-failure response body is printed without the mask", f'redact "$(jq . {result})"', f"jq . {result}"),
        ("V08-status-constant-1", "gh's exit status is recorded as a constant 1", "|| GH_STATUS=$?", "|| GH_STATUS=1"),
        ("V09-always-print-stderr", "an empty gh stderr is printed too (a blank stderr line on success)", 'if [ -n "${GH_STDERR}" ]; then', 'if [ -n "x${GH_STDERR}" ]; then'),
        ("V10-401-hint-always", "the 401 hint is printed on every HTTP failure", 'if [[ "${GH_STDERR}" == *"(HTTP 401)"* ]]; then', 'if [[ "${GH_STDERR}" == *""* ]]; then'),
        ("V11-mask-first-occurrence-only", "redact masks only the first occurrence of the token", '"${1//"${GH_TOKEN:-}"/***}"', '"${1/"${GH_TOKEN:-}"/***}"'),
        ("V12-http-branch-says-not-committed", "the HTTP-failure branch claims the lockfile was not committed", "so this log cannot show whether the lock commit landed.", "lockfile NOT committed."),
        ("V13-errors-branch-needs-gh-failure", "the errors branch is skipped when gh exits 0", errors_open, '          if [ "${GH_STATUS}" -ne 0 ] && jq -e \'.errors\' ' + result + " > /dev/null 2>&1; then\n"),
        ("V14-errors-check-any-json", "the errors check passes on any JSON body", errors_open, f"          if jq -e '.' {result} > /dev/null 2>&1; then\n"),
        ("V15-drop-branch-hint", "the branch-to-check line is gone", '            echo "Check ${BRANCH} for the lock commit before re-running this job."\n', ""),
        ("V16-status-swallowed", "gh's failure is swallowed with `|| true`", "|| GH_STATUS=$?", "|| true"),
        ("V17-http-branch-exit-0", "the HTTP-failure branch exits 0", "            fi\n            exit 1\n          fi\n\n          jq -r", "            fi\n            exit 0\n          fi\n\n          jq -r"),
        ("V18-errors-branch-exit-0", "the GraphQL-errors branch exits 0", 'needs only the re-run."\n            exit 1\n', 'needs only the re-run."\n            exit 0\n'),
        ("V19-drop-rerun-advice", "the gh-exit and re-run advice line is gone", '            echo "gh exited ${GH_STATUS}. Fix the cause above', '            : "gh exited ${GH_STATUS}. Fix the cause above'),
        ("V20-gh-message-unmasked", "gh's message is re-printed without the mask", 'redact "${GH_STDERR}" >&2', "printf '%s\\n' \"${GH_STDERR}\" >&2"),
        ("V21-drop-not-json-line", "the empty-or-not-JSON line is gone", "              echo \"The response body is empty or not JSON; gh's message above is the error.\"\n", "              :\n"),
        ("V22-http-status-threshold", "the HTTP-failure branch needs an exit status above 1", HTTP_OPEN, '          if [ "${GH_STATUS}" -gt 1 ]; then\n'),
        ("V23-errors-diagnostic-to-stderr", "the step's GraphQL diagnostic goes to stderr", 'echo "::error::createCommitOnBranch failed — lockfile NOT committed:"', 'echo "::error::createCommitOnBranch failed — lockfile NOT committed:" >&2'),
        ("V24-gh-exit-reported-constant", "the errors branch reports a constant exit status", 'echo "gh exited ${GH_STATUS}. Fix', 'echo "gh exited 1. Fix'),
    ]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _swap_checks(text: str, result: str) -> str:
    """V03: the HTTP-failure check runs before the GraphQL-errors check."""
    start_errors = text.index(_errors_open(result))
    start_http = text.index(HTTP_OPEN)
    start_final = text.index(FINAL_JQ)
    if not start_errors < start_http < start_final:
        raise SystemExit("unexpected block order")
    return text[:start_errors] + text[start_http:start_final] + text[start_errors:start_http] + text[start_final:]


def _run_pytest(copy: Path, python: str, out_dir: Path, case: str) -> dict[str, object]:
    junit = out_dir / f"{case}.junit.xml"
    log = out_dir / f"{case}.log"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([python, "-m", "pytest", TEST_FILE, "-p", "no:cacheprovider", f"--junitxml={junit}"], cwd=copy, env=env, capture_output=True, text=True, check=False, timeout=900)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(proc.stdout)
        fh.write("\n--- stderr ---\n")
        fh.write(proc.stderr)
    passed: list[str] = []
    failed: list[str] = []
    if junit.is_file():
        for case_el in ET.parse(junit).getroot().iter("testcase"):
            name = case_el.get("name", "")
            if case_el.find("failure") is not None or case_el.find("error") is not None:
                failed.append(name)
            elif case_el.find("skipped") is None:
                passed.append(name)
    return {"exit": proc.returncode, "passed": len(passed), "failed": sorted(failed), "log": str(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", required=True, type=Path, help="the validator's own juniper-canopy worktree")
    parser.add_argument("--main-wf", required=True, type=Path, help="main's lockfile-update.yml")
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", nargs="*", default=[])
    args = parser.parse_args()
    if "--val--" not in args.copy.name:
        raise SystemExit("refusing: --copy is not a validator worktree")
    args.out.mkdir(parents=True, exist_ok=True)
    workflow = args.copy / WORKFLOW
    original = workflow.read_bytes()
    original_sha = _sha256(original)
    text = original.decode("utf-8")
    result_paths = sorted(set(re.findall(r"(/\S*lockfile-commit-result\.json)", text)))
    if len(result_paths) != 1:
        raise SystemExit(f"expected one result path, found {result_paths}")
    result = result_paths[0]

    cases: list[tuple[str, str, str]] = [("carrier", "the carrier's workflow, unmodified", text), ("main", "main's whole workflow in place of the carrier's", args.main_wf.read_text(encoding="utf-8"))]
    cases.append(("V03-swap-check-order", "the HTTP-failure check runs before the GraphQL-errors check", _swap_checks(text, result)))
    for case_id, what, old, new in _replacements(result):
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{case_id}: old text occurs {count} times, expected 1")
        cases.append((case_id, what, text.replace(old, new)))

    results: list[dict[str, object]] = []
    for case_id, what, variant in cases:
        if args.only and case_id not in args.only:
            continue
        workflow.write_bytes(variant.encode("utf-8"))
        try:
            outcome = _run_pytest(args.copy, args.python, args.out, case_id)
        finally:
            workflow.write_bytes(original)
        restored = _sha256(workflow.read_bytes()) == original_sha
        verdict = "baseline" if case_id == "carrier" else ("killed" if outcome["failed"] else "SURVIVED")
        results.append({"id": case_id, "what": what, "result": verdict, "restored_sha256_matches": restored, **outcome})
        print(f"{case_id:36} {verdict:9} exit={outcome['exit']} passed={outcome['passed']} failed={len(outcome['failed'])} restored={restored}", flush=True)
        if not restored:
            raise SystemExit("restore failed")
    summary = {"copy": str(args.copy), "workflow_sha256": original_sha, "python": args.python, "results": results}
    name = "mutants.json" if not args.only else "mutants.partial.json"
    with open(args.out / name, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
