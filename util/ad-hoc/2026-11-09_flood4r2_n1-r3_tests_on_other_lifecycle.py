"""
Run fix N-1's tests against another version of cascor's two lifecycle files, in a hermetic copy of the carrier tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off (adapted from round 2's tmp/flood4-fix/n1-r2/probes/new_tests_on_other_lifecycle.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge)

Usage: python3 <this> (--ref <git ref> | --dir <tree root>)

Copies the N-1 worktree's src/, conf/ and pyproject.toml into a temporary directory under the
worktree's own tmp/flood4-fix/n1-r3/hermetic/ (TMPDIR is not changed; the copy stays out of
juniper-ml's tmp/, where a cascor pyproject.toml could be mistaken for a release-train project),
swaps in src/api/lifecycle/manager.py and state_machine.py from a git ref or from another tree,
prints their sha256, and runs the new test module plus the state-machine suite with -rA, so
every test's outcome is listed. A provenance plugin proves the copy's manager was imported.
Run it through 2026-11-09_flood4r2_n1-r3_run_python.py's environment rules: this script itself
drops JUNIPER_CASCOR_LOG_DIR and sets PYTHONDONTWRITEBYTECODE=1 for the pytest it starts.
Exit: pytest's own.
"""

import argparse
import hashlib
import os
import shutil
import subprocess  # nosec B404 -- fixed-argv git and pytest
import sys
import tempfile
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
TREE = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
HERMETIC = TREE / "tmp" / "flood4-fix" / "n1-r3" / "hermetic"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
FILES = ("src/api/lifecycle/manager.py", "src/api/lifecycle/state_machine.py")
TESTS = ("src/tests/unit/api/test_lifecycle_paused_fit_return.py", "src/tests/unit/api/test_lifecycle_state_machine.py")
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "logs", "reports")
PLUGIN = 'import sys\n\n\ndef pytest_sessionfinish(session, exitstatus):\n    m = sys.modules.get("api.lifecycle.manager")\n    print("\\nPROVENANCE " + str(getattr(m, "__file__", None)))\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ref")
    group.add_argument("--dir")
    args = parser.parse_args()
    HERMETIC.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="other-lifecycle-", dir=HERMETIC) as tmp:
        tree = Path(tmp)
        for name in ("src", "conf"):
            shutil.copytree(TREE / name, tree / name, ignore=IGNORED)
        shutil.copy2(TREE / "pyproject.toml", tree / "pyproject.toml")
        for relative in FILES:
            if args.ref:
                text = subprocess.run(["git", "-C", str(TREE), "show", f"{args.ref}:{relative}"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607
            else:
                text = (Path(args.dir) / relative).read_text(encoding="utf-8")
            (tree / relative).write_text(text, encoding="utf-8")
            print(f"swapped in {relative}: sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}", flush=True)
        (tree / "_plugins").mkdir()
        (tree / "_plugins" / "_other_provenance.py").write_text(PLUGIN, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(tree / "_plugins")
        print(f"hermetic tree {tree}; lifecycle files from {args.ref or args.dir}; expected manager {tree / FILES[0]}", flush=True)
        argv = [PYTHON, "-m", "pytest", "-m", "unit and not slow", *TESTS, "-p", "no:cacheprovider", "-p", "_other_provenance", "-rA", "--timeout=120", "-q"]
        return subprocess.run(argv, cwd=tree, env=env, check=False).returncode  # nosec B603


if __name__ == "__main__":
    sys.exit(main())
