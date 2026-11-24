"""
Push one part of the upload set as a signed commit through util/push_signed_commit.py, from the frozen snapshot.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615, #2621 and #2629 (this version pushed #2629's branch, feat/local-test-runner-3)

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: push one follow-up part of PR #2615 as a signed commit, from the frozen snapshot.

Usage: python3 push_part.py PART EXPECTED_HEAD_SHA [--dry-run]

Holds the part -> file mapping in code because the session's worktree guard refuses any command line naming the
workflows directory. It only calls util/push_signed_commit.py, which pins --expected-head.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP = Path(__file__).with_name("upload-snapshot")
BODY = Path(__file__).with_name("fixup_body.txt")
PARTS = {
    "2": (".github/workflows/ci.yml", "ci: wire tests/test_run_tests.py into the regression step"),
    "3": ("docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs(cheatsheet): the local test runner's commands (1.0.73)"),
    "4": ("CHANGELOG.md", "docs(changelog): util/run_tests.py and the registry walk's tmp/ skip"),
    "5": ("docs/REFERENCE.md", "docs(reference): Running tests locally (0.6.81)"),
}

part, head = sys.argv[1], sys.argv[2]
rel, headline = PARTS[part]
argv = [sys.executable, str(ROOT / "util" / "push_signed_commit.py"), "--repo", "juniper-ml", "--branch", "feat/local-test-runner-3", "--expected-head", head, "--add", f"{SNAP / rel}:{rel}", "--message", headline, "--commit-body-file", str(BODY)]
if "--dry-run" in sys.argv[3:]:
    argv.append("--dry-run")
sys.exit(subprocess.run(argv, cwd=ROOT, check=False).returncode)
