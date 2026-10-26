"""
Evidence for juniper-ml#2330: E-C's new wall budget keeps every cell's identity, and its CI pin kills the regressions it exists for.

``p4/e-c-cascor-noise-robustness.yaml`` gains ``execution.max_wall_seconds: 5400`` (owner ruling
2026-10-26, the issue's option 1), and ``tests/test_experiment_suite_yamls.py`` gains
``WallBudgetContractTest.test_e_c_stays_above_its_surveyed_budget``. Two read-only checks:

1. identity -- expand and materialise every E-C cell from the suite at ``--base-ref`` and from the
   working tree, and compare the cell ids and the sha256 of each materialised config (what run_suite
   records as ``config_sha256``). The base config is juniper-cascor's ``spiral-baseline.yaml``, so this
   needs ``--project-dir`` (run_suite's JUNIPER_EXP_PROJECT_DIR rebase). Every cell must match.
2. mutants -- copy the test module and ``util/experiments/`` into a scratch tree, apply each regression
   the pin exists to catch, and run the pin there with JUNIPER_EXP_PROJECT_DIR unset, as CI runs it.
   The unmutated copy must pass and every mutant must fail the pin.

The default ``--base-ref`` is ``main`` ``2dceceec``, the last commit before the fix.

Usage:
    python3 -I util/ad-hoc/2026-10-26_e_c_wall_budget_2330_check.py --project-dir /path/to/Juniper [--base-ref <ref>]

Exit 0 when both checks pass, 1 when either fails, 2 on misuse.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2330; juniper-ml#2210 (util/ad-hoc/2026-10-25_driver_budget_survey.py)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import shutil
import subprocess  # nosec B404 - fixed argv: git show and the unittest runner
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITE_REL = "util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml"
TEST_REL = "tests/test_experiment_suite_yamls.py"
PIN = "tests.test_experiment_suite_yamls.WallBudgetContractTest.test_e_c_stays_above_its_surveyed_budget"
BASE_REF = "2dceceec49e6250f57165ef2b9df19dd62773bf8"
SHIPPED = "execution: {mode: sequential, continue_on_failure: true, per_run_timeout_seconds: 7200, stall_seconds: 1200, max_wall_seconds: 5400}"
# Each regression the pin exists to catch, as the replacement for the shipped execution line; None renames the suite.
MUTANTS = {
    "the wall budget deleted": "execution: {mode: sequential, continue_on_failure: true, per_run_timeout_seconds: 7200, stall_seconds: 1200}",
    "the wall budget back at the 3600 s default": "execution: {mode: sequential, continue_on_failure: true, per_run_timeout_seconds: 7200, stall_seconds: 1200, max_wall_seconds: 3600}",
    "the timeout at the surveyed 5850 s worst case": "execution: {mode: sequential, continue_on_failure: true, per_run_timeout_seconds: 5850, stall_seconds: 1200, max_wall_seconds: 5400}",
    "the suite renamed": None,
}


def _run_suite_module():
    spec = importlib.util.spec_from_file_location("run_suite", REPO_ROOT / "util" / "experiments" / "run_suite.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _identities(run_suite, doc: dict, suite_path: Path) -> "dict[str, str]":
    """``{cell_id: sha256 of the materialised config}``, resolving the base the way run_suite does."""
    cells = run_suite.expand_cells(doc, suite_path)
    unresolved = sorted({cell["config_path"] for cell in cells if not Path(cell["config_path"]).is_file()})
    if unresolved:
        raise SystemExit(f"error: base config does not resolve ({', '.join(unresolved)}); pass --project-dir")
    with tempfile.TemporaryDirectory() as tmp:
        return {cell["cell_id"]: hashlib.sha256(Path(run_suite.materialise_cell(cell, doc["suite"], Path(tmp), None)).read_bytes()).hexdigest() for cell in cells}


def check_identity(base_ref: str) -> bool:
    run_suite = _run_suite_module()
    suite_path = REPO_ROOT / SUITE_REL
    proc = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{base_ref}:{SUITE_REL}"], capture_output=True, text=True, timeout=30, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"error: git show {base_ref}:{SUITE_REL} failed: {proc.stderr.strip()}")
    with tempfile.TemporaryDirectory() as tmp:
        base_copy = Path(tmp) / suite_path.name
        base_copy.write_text(proc.stdout, encoding="utf-8")
        before = _identities(run_suite, run_suite.load_suite(base_copy), suite_path)
    after = _identities(run_suite, run_suite.load_suite(suite_path), suite_path)
    for cell_id in sorted(set(before) | set(after)):
        verdict = "MATCH" if before.get(cell_id) == after.get(cell_id) else "DIFFER"
        print(f"{verdict:<8}{cell_id}  {before.get(cell_id, '-')}  {after.get(cell_id, '-')}")
    same = before == after
    print(f"identity: {sum(before.get(c) == after.get(c) for c in after)} of {len(after)} cells match {base_ref[:8]} -- {'OK' if same else 'FAILED'}")
    return same


def _run_pin(tree: Path) -> "tuple[int, str]":
    env = {key: value for key, value in os.environ.items() if key != "JUNIPER_EXP_PROJECT_DIR"}
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", PIN], cwd=tree, env=env, capture_output=True, text=True, timeout=300, check=False)  # nosec B603
    return proc.returncode, proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""


def check_mutants() -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        (tree / "tests").mkdir()
        shutil.copy2(REPO_ROOT / TEST_REL, tree / TEST_REL)
        shutil.copytree(REPO_ROOT / "util" / "experiments", tree / "util" / "experiments", ignore=shutil.ignore_patterns("__pycache__"))
        suite = tree / SUITE_REL
        shipped = suite.read_text(encoding="utf-8")
        if shipped.count(SHIPPED) != 1:
            raise SystemExit(f"error: {SUITE_REL} does not carry the shipped execution line exactly once")
        code, last = _run_pin(tree)
        print(f"{'PASS' if code == 0 else 'FAIL':<9}control (unmutated)  {last}")
        ok &= code == 0
        for name, line in MUTANTS.items():
            if line is None:
                moved = suite.with_name("e-c-renamed.yaml")
                suite.rename(moved)
            else:
                suite.write_text(shipped.replace(SHIPPED, line), encoding="utf-8")
            code, last = _run_pin(tree)
            killed = code != 0 and last == "FAILED (failures=1)"
            print(f"{'KILLED' if killed else 'SURVIVED':<9}{name}  {last}")
            ok &= killed
            if line is None:
                moved.rename(suite)
            suite.write_text(shipped, encoding="utf-8")
    print(f"mutants: {'OK' if ok else 'FAILED'}")
    return ok


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--project-dir", required=True, help="the Juniper ecosystem root, holding juniper-cascor (run_suite's JUNIPER_EXP_PROJECT_DIR)")
    parser.add_argument("--base-ref", default=BASE_REF, help=f"the ref whose E-C suite the identity check compares against (default {BASE_REF[:8]}, the last main before the fix)")
    args = parser.parse_args(argv)
    if not (Path(args.project_dir) / "juniper-cascor").is_dir():
        parser.error(f"--project-dir {args.project_dir} holds no juniper-cascor checkout")
    os.environ["JUNIPER_EXP_PROJECT_DIR"] = args.project_dir
    identity = check_identity(args.base_ref)
    mutants = check_mutants()
    return 0 if identity and mutants else 1


if __name__ == "__main__":
    sys.exit(main())
