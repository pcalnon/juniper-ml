#!/usr/bin/env python3
"""
Prove juniper-data-client's tests/test_run_tests.py binds the behaviour its copy of util/run_tests.py added.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests rollout, copy 2 (prompts/thread-handoff_automated-prompts/
        HANDOFF_2026-11-25_run-tests-rollout-recurrence-copy-landed-data-client-copy-next.md, section 1)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)

A green suite proves the runner and the suite agree; it does not prove the suite would notice the runner breaking.
This copies a checkout (``--checkout``, without .git, tmp/ or caches) once per mutant into ``--work`` (under a
repo's gitignored tmp/), applies one textual mutation to the copy's util/run_tests.py (refused unless the old text
occurs exactly once), and runs the copy's ``tests/test_run_tests.py`` with ``-x``. A mutant the suite fails is
KILLED; one it passes SURVIVED. The unmutated control must pass, or nothing the mutants say means anything.

Usage: python3 util/ad-hoc/2026-11-26_run_tests_data_client_mutation_check.py --checkout DIR --work DIR [--only NAME ...]
Exit: 0 when the control passes and every mutant is killed; 1 otherwise. Writes nothing under the system temp dir.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 - runs pytest on a copy, fixed argv
import sys
import time
from pathlib import Path

# (name, old text, new text): each breaks one behaviour data-client's copy added or fixed.
MUTANTS = [
    ("junit-routing", 'token = f"{option}={lane_dir / Path(target).name}"', "token = token"),
    ("exit-5-accepted", "elif rc in planned.tolerated:", "elif False:"),
    ("step-env", 'own = {key: value for key, value in step.env.items() if key not in ("PYTHONPATH", "COVERAGE_FILE")}', "own = {}"),
    ("shell-var-expansion", "            if match and value is not None:\n", "            if False:\n"),
    ("cov-term-modifier", "if colon and kind in _COV_FILE_REPORTS and target else spec", "if colon and target else spec"),
    ("left-out-listing", 'left_out.append(title or "(unnamed step)")', "pass"),
    ("opt-in-table", 'why = scheduled or OPT_IN.get(name, "")', "why = scheduled"),
    ("install-fallbacks", 'return segments(list(itertools.takewhile(lambda token: token != "||", tokens)))', "return segments(tokens)"),
    ("rc-shape-refusal", "    raise UsageError(f'{where}: captures an exit code", "    return lines, ()\n    raise UsageError(f'{where}: captures an exit code"),
    ("changed-package-dirs", "    return name in exact or any(name == place or name.startswith(place + \"/\") for place in places)", "    return name in exact"),
    ("subfailed-lines", '_PT_PROBLEM = re.compile(r"^(?:FAILED|ERROR|SUBFAILED(?:\\(.*?\\))?) (\\S+::\\S+|\\S+\\.py)", re.M)', '_PT_PROBLEM = re.compile(r"^(?:FAILED|ERROR) (\\S+)", re.M)'),
    ("secret-env-hidden", 'env[str(key)] = None if unknown or "${{" in resolved else resolved', "env[str(key)] = resolved"),
    ("coverage-report-floor", "floor = (_COV_FLOOR.search(text) or _COV_REPORT_FLOOR.search(text))", "floor = (_COV_FLOOR.search(text))"),
    ("floor-is-a-gate", 'coverage_gate=label != "pytest"', 'coverage_gate=label == "coverage-gate"'),
    ("lane-files-selector", "        if candidate in by_file:\n", "        if False:\n"),
    ("shell-step-refused", '                raise UsageError(f"{where}: {line!r} needs a shell', '                continue\n                raise UsageError(f"{where}: {line!r} needs a shell'),
]
IGNORE = shutil.ignore_patterns(".git", "tmp", "__pycache__", "*.egg-info", ".pytest_cache", ".mypy_cache", "build", "dist")


def run_suite(copy: Path, timeout: float) -> tuple[int, str]:
    env = {key: value for key, value in os.environ.items() if key not in ("PYTHONPATH", "COVERAGE_FILE")}
    argv = [sys.executable, "-m", "pytest", "tests/test_run_tests.py", "-x", "-q", "-p", "no:cacheprovider", "--no-header"]
    proc = subprocess.run(argv, cwd=copy, env=env, capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603
    tail = (proc.stdout.strip().splitlines() or ["(no output)"])[-1]
    return proc.returncode, tail


def make_copy(checkout: Path, work: Path, name: str) -> Path:
    copy = work / name
    if copy.exists():
        shutil.rmtree(copy)
    shutil.copytree(checkout, copy, ignore=IGNORE, symlinks=True)
    return copy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--only", action="append", default=[], help="run only the named mutant(s)")
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    checkout, work = args.checkout.resolve(), args.work.resolve()
    if any(str(work).startswith(root) for root in ("/tmp", "/var/tmp")):  # tmp-path-literal: allow -- refused, never written
        raise SystemExit("--work must not be under the system temp directory")
    work.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rc, tail = run_suite(make_copy(checkout, work, "control"), args.timeout)
    print(f"{'PASS   ' if rc == 0 else 'FAIL   '}  control  ({tail})")
    if rc != 0:
        print("the unmutated control fails: no mutant result means anything")
        return 1
    survived = 0
    for name, old, new in MUTANTS:
        if args.only and name not in args.only:
            continue
        copy = make_copy(checkout, work, f"mutant-{name}")
        runner = copy / "util" / "run_tests.py"
        text = runner.read_text(encoding="utf-8")
        if text.count(old) != 1:
            print(f"ERROR    {name}: the old text occurs {text.count(old)} times, not once")
            survived += 1
            continue
        runner.write_text(text.replace(old, new), encoding="utf-8")
        rc, tail = run_suite(copy, args.timeout)
        killed = rc != 0
        survived += not killed
        print(f"{'KILLED ' if killed else 'SURVIVED'}  {name}  ({tail})")
    print(f"{survived} survived; {time.monotonic() - started:.0f}s; copies under {work}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
