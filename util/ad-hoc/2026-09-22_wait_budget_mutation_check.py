#!/usr/bin/env python3
"""
Mutation-check TimeoutResolutionTest: each mutation re-breaks util/wait_for_checks.py's default
wait budget in one specific way, and the suite must go red for every one of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (verifies the item-10 fix of the 2026-09-09 CI-budget handoff)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md (§3 item 10)

Hermetic: every mutation runs in a throwaway tree (`.github/workflows/` marker, `util/`, `tests/`)
built under a TemporaryDirectory, so the working tree is never edited and no stale `.pyc` from a
previous mutation can answer for the current one (a fresh tree has no `__pycache__`). The unmutated
tree runs first as a control: a suite that is red WITHOUT a mutation proves nothing when it is red
with one. Exit codes are read from the subprocess directly, never through a pipe.

Usage:
    python3 util/ad-hoc/2026-09-22_wait_budget_mutation_check.py
Exit: 0 control green and every mutation red; 1 otherwise.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 -- fixed-argv unittest runs in a temp tree
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = "util/wait_for_checks.py"
SUITE = "tests.test_wait_for_checks.TimeoutResolutionTest"

# (name, old, new) -- `old` must occur exactly once in the target.
MUTATIONS = [
    (
        "CLI ignores the resolver (the old flat default)",
        "    timeout, source = resolve_timeout(args.repo, args.timeout)\n",
        "    timeout, source = (args.timeout if args.timeout is not None else DEFAULT_TIMEOUT), \"--timeout\"\n",
    ),
    (
        "resolver never reads the table",
        "        return int(mod.timeout_for(repo)), f\"measured budget for {repo} ({path.name} timeout_for)\"\n",
        "        return DEFAULT_TIMEOUT, f\"measured budget for {repo} ({path.name} timeout_for)\"\n",
    ),
    (
        "silent fallback (source no longer says FALLBACK)",
        "        return DEFAULT_TIMEOUT, f\"FALLBACK {DEFAULT_TIMEOUT}s -- {path.name} budgets unreadable ({type(exc).__name__}: {exc})\"\n",
        "        return DEFAULT_TIMEOUT, \"measured budget\"\n",
    ),
    (
        "budget not announced on stderr",
        "        print(f\"wait budget: {timeout}s ({source})\", file=sys.stderr)\n",
        "        pass\n",
    ),
    (
        "explicit --timeout loses to the table",
        "    if explicit is not None:\n        return explicit, \"--timeout\"\n",
        "    if False:\n        return explicit, \"--timeout\"\n",
    ),
]


def build_tree(dest: Path, target_text: str) -> None:
    (dest / ".github" / "workflows").mkdir(parents=True)
    (dest / "util").mkdir()
    (dest / "tests").mkdir()
    (dest / "util" / "wait_for_checks.py").write_text(target_text, encoding="utf-8")
    shutil.copy2(ROOT / "util" / "safe_merge.py", dest / "util" / "safe_merge.py")
    for name in ("__init__.py", "redacted_env.py", "test_wait_for_checks.py"):
        src = ROOT / "tests" / name
        if src.exists():
            shutil.copy2(src, dest / "tests" / name)


def run_suite(target_text: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        tree = Path(td)
        build_tree(tree, target_text)
        proc = subprocess.run(  # nosec B603 -- fixed argv
            [sys.executable, "-m", "unittest", SUITE],
            cwd=tree,
            capture_output=True,
            text=True,
            check=False,
        )
        tail = [ln for ln in proc.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:", "Ran ", "OK", "FAILED"))]
        return proc.returncode, "; ".join(tail[-6:])


def main() -> int:
    original = (ROOT / TARGET).read_text(encoding="utf-8")
    rc, summary = run_suite(original)
    print(f"control (unmutated): exit {rc} -- {summary}")
    if rc != 0:
        print("CONTROL IS RED -- a red mutation would prove nothing; stopping.")
        return 1
    ok = True
    for name, old, new in MUTATIONS:
        if original.count(old) != 1:
            print(f"[SKIP-AS-FAIL] {name}: anchor occurs {original.count(old)}x (expected 1) -- the mutation cannot be applied")
            ok = False
            continue
        rc, summary = run_suite(original.replace(old, new))
        verdict = "KILLED" if rc != 0 else "SURVIVED"
        ok &= rc != 0
        print(f"[{verdict}] {name}: exit {rc} -- {summary}")
    print("ALL MUTATIONS KILLED" if ok else "AT LEAST ONE MUTATION SURVIVED OR COULD NOT BE APPLIED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
