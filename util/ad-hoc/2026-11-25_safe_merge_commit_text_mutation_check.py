#!/usr/bin/env python3
"""
Mutation check: tests/test_safe_merge.py must FAIL on every seeded defect in safe_merge's commit-text copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation (test-efficacy evidence)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/safe_merge.py (stored_commit_text, the local merge), tests/test_safe_merge.py (LocalMergeCommitTextTest),
         notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (finding 37)

Finding 37: juniper-ml#2548's local merge passed no commit text, so GitHub's default concatenation landed instead of
the curated message the operator had stored on the auto-merge net. The fix copies a net's non-empty headline and body
into the local `gh pr merge`. Each mutant below re-creates one way that copy could be wrong -- not made, made from the
wrong read, an empty or non-string value copied, one field dropped -- and the suite must fail on it.

The repository is not touched: both files are copied to a fresh directory under the repo's tmp/ (TMPDIR when set),
each mutant is written into the copy, and the suite runs there with PYTHONDONTWRITEBYTECODE=1. A suite that does not
end within two minutes counts as killed.

Usage: python3 util/ad-hoc/2026-11-25_safe_merge_commit_text_mutation_check.py
Exit: 0 every mutant killed; 1 a mutant survived or an anchor did not occur exactly once.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = "util/safe_merge.py"
SUITE = "tests/test_safe_merge.py"

# (name, old, new): `old` must occur exactly once in the tool.
MUTANTS = [
    ("the local merge passes no text", "                    *text,\n", ""),
    ("the text is read before the wait", "        text = stored_commit_text(after)\n", "        text = stored_commit_text(info)\n"),
    ("the body is not copied", '        flags += ["--body", body]\n', "        pass\n"),
    ("the headline is not copied", '        flags += ["--subject", headline]\n', "        pass\n"),
    ("an empty body is copied", "    if isinstance(body, str) and body:\n", "    if isinstance(body, str):\n"),
    ("an empty headline is copied", "    if isinstance(headline, str) and headline:\n", "    if isinstance(headline, str):\n"),
    ("a body that is not text is copied", "    if isinstance(body, str) and body:\n", "    if body:\n"),
    ("a headline that is not text is copied", "    if isinstance(headline, str) and headline:\n", "    if headline:\n"),
    ("the body goes in as the subject", '        flags += ["--body", body]\n', '        flags += ["--subject", body]\n'),
]


def run_suite(tree: Path) -> int | None:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([sys.executable, "-m", "unittest", "-f", SUITE], cwd=tree, env=env, capture_output=True, text=True, check=False, timeout=120)  # nosec B603
    except subprocess.TimeoutExpired:
        return None
    return proc.returncode


def main() -> int:
    tmp_root = Path(os.environ.get("TMPDIR") or (REPO / "tmp"))
    tmp_root.mkdir(parents=True, exist_ok=True)
    failures = 0
    with tempfile.TemporaryDirectory(dir=tmp_root, prefix="safe_merge_text_mutants_") as work:
        tree = Path(work)
        for relative in (TOOL, SUITE):
            (tree / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, tree / relative)
        baseline = run_suite(tree)
        print(f"baseline {SUITE}: exit={baseline}")
        if baseline != 0:
            return 1
        source = (tree / TOOL).read_text(encoding="utf-8")
        for name, old, new in MUTANTS:
            if source.count(old) != 1:
                print(f"[EDIT-FAILED] {name}: anchor occurs {source.count(old)} times")
                failures += 1
                continue
            (tree / TOOL).write_text(source.replace(old, new), encoding="utf-8")
            code = run_suite(tree)
            (tree / TOOL).write_text(source, encoding="utf-8")
            killed = code != 0
            failures += not killed
            print(f"[{'KILLED' if killed else 'SURVIVED'}] {name}" + (" (timed out)" if code is None else ""), flush=True)
    print(f"{len(MUTANTS) - failures} of {len(MUTANTS)} mutants killed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
