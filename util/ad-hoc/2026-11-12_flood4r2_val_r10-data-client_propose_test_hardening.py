"""
Build the validator's proposed hardening of tests/test_gitleaks_pr_scan.py as a unified diff (a/ and b/ paths).

The edits fold into existing cases, so the file keeps its 25 cases and every count the port's texts state. Each edit's
old text must occur exactly once in the carrier's file. The diff is written to <out>/0001-test-pin-the-blocking-wiring.diff
and applies with ``git apply -p1``.

What each edit kills (ids from 2026-11-12_flood4r2_val_r10-data-client_mutants.py):
  scan step continue-on-error (V01), job-level continue-on-error / if / rename (V02, V03, V21), the self-test's
  `|| true` or -k (V04, V05), the digest check's `|| true` or self-hash (V06, V07), install continue-on-error (V08),
  the report upload's `if: always()` and path (V09, V10), and an unanchored `remerge` filter (V19).

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_propose_test_hardening.py <carrier test file> <out dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

REL = "tests/test_gitleaks_pr_scan.py"

EDITS: list[tuple[str, str]] = [
    # constants
    (
        "ON_PULL_REQUEST = \"github.event_name == 'pull_request'\"\n",
        "ON_PULL_REQUEST = \"github.event_name == 'pull_request'\"\n"
        "UPLOAD_STEP = \"Upload Security Reports\"\n"
        "#: The self-test step's whole command: an `|| true`, a -k or a --deselect after it would let the real-engine cases fail or never run.\n"
        "SELF_TEST_COMMAND = \"python -m pytest tests/test_gitleaks_pr_scan.py -v -v --timeout=120\"\n"
        "#: The install step's digest line, whole: the pinned digest against the downloaded file, and nothing after it.\n"
        "DIGEST_CHECK = 'echo \"${GITLEAKS_SHA256}  ${RUNNER_TEMP}/${asset}\" | sha256sum --check --strict'\n",
    ),
    # the self-test's whole command, and the job that holds it
    (
        "    assert all(\"if\" not in s and \"continue-on-error\" not in s for s in runs), \"the real-engine run must be unconditional and blocking\"\n",
        "    assert all(\"if\" not in s and \"continue-on-error\" not in s for s in runs), \"the real-engine run must be unconditional and blocking\"\n"
        "    assert [str(s[\"run\"]).strip() for s in runs] == [SELF_TEST_COMMAND], \"the real-engine run must be this command and nothing more\"\n"
        "    # `Security Scans` is a required check under that name. A job-level `if` reports a skipped job as passed, and a\n"
        "    # job-level continue-on-error lets a failed scan pass the run.\n"
        "    job = _workflow()[\"jobs\"][\"security\"]\n"
        "    assert job.get(\"name\") == \"Security Scans\"\n"
        "    assert \"if\" not in job and \"continue-on-error\" not in job, \"the job must run on every event, and its failure must fail the run\"\n",
    ),
    # the install step
    (
        "    assert install.get(\"if\") == ON_PULL_REQUEST\n    env = install.get(\"env\", {})\n",
        "    assert install.get(\"if\") == ON_PULL_REQUEST\n    assert \"continue-on-error\" not in install\n    env = install.get(\"env\", {})\n",
    ),
    (
        "    assert \"sha256sum --check --strict\" in run, \"the tarball must be checked against the pinned digest\"\n",
        "    assert DIGEST_CHECK in [line.strip() for line in run.splitlines()], \"the tarball must be checked against the pinned digest, and a mismatch must stop the step\"\n",
    ),
    # the scan step, and the upload of its report
    (
        "    assert scan.get(\"if\") == ON_PULL_REQUEST\n    assert scan.get(\"env\") == {\n",
        "    assert scan.get(\"if\") == ON_PULL_REQUEST\n    assert \"continue-on-error\" not in scan, \"a leak must fail the job\"\n    assert scan.get(\"env\") == {\n",
    ),
    (
        "    assert order == sorted(order), \"the action, then the install, then the scan, then the self-test that needs the binary\"\n",
        "    assert order == sorted(order), \"the action, then the install, then the scan, then the self-test that needs the binary\"\n"
        "    # The scan writes its report and then fails on a leak: the upload has to run anyway, and take the report's directory.\n"
        "    upload = steps[_index(steps, UPLOAD_STEP)]\n"
        "    assert upload.get(\"if\") == \"always()\" and upload.get(\"with\", {}).get(\"path\") == \"reports/security/\", \"a failed scan must still upload its report\"\n"
        "    assert _index(steps, UPLOAD_STEP) > _index(steps, PR_SCAN_STEP)\n",
    ),
    # the filter deletes git's notes and nothing else: a scanned line that holds the word mid-line must survive it
    (
        "    repo, base, _, head = _merge_whose_conflict_note_says_commit(tmp_path, \"conflicted-path\", \"resolved=1\\n\")\n",
        "    repo, base, _, head = _merge_whose_conflict_note_says_commit(tmp_path, \"conflicted-path\", \"resolved=1  # never remerge by hand\\n\")\n",
    ),
    (
        "    assert \"+resolved=1\" in engine_saw, \"the merge commit's own change must still reach the engine\"\n",
        "    assert \"+resolved=1  # never remerge by hand\" in engine_saw, \"the merge commit's own change must still reach the engine, the word remerge in it included\"\n",
    ),
]


def main() -> int:
    source, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    original = source.read_text(encoding="utf-8")
    text = original
    for old, new in EDITS:
        if text.count(old) != 1:
            raise SystemExit(f"an edit's old text occurs {text.count(old)} times (expected 1):\n{old}")
        text = text.replace(old, new)
    # Not named test_*.py: this scratch directory sits inside a juniper-ml checkout.
    (out / "hardened_gitleaks_pr_scan.py.txt").write_text(text, encoding="utf-8")
    diff = difflib.unified_diff(original.splitlines(keepends=True), text.splitlines(keepends=True), f"a/{REL}", f"b/{REL}", n=3)
    (out / "0001-test-pin-the-blocking-wiring.diff").write_text("".join(diff), encoding="utf-8")
    print(f"{len(EDITS)} edits; wrote {out / '0001-test-pin-the-blocking-wiring.diff'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
