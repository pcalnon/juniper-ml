#!/usr/bin/env python3
"""
Prove juniper-ci-tools' tests/test_run_tests.py binds the behaviour of juniper_ci_tools.run_tests, the engine.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests engine extraction (notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-
        EXTRACTION-PROPOSAL.md § 4.4: "data-client's mutation check ... moves with the engine suite and is re-run")
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)

A green suite proves the engine and its suite agree; it does not prove the suite would notice the engine breaking.
For the control and for each mutant this copies ``--package`` (``juniper_ci_tools/``, ``tests/`` and
``pyproject.toml``) into ``--work/<name>/juniper-ci-tools/``, applies one textual mutation to the copy's
``juniper_ci_tools/run_tests.py`` (refused unless the old text occurs exactly once), and runs the copy's
``tests/test_run_tests.py`` with ``-x``, the copy first on PYTHONPATH. A mutant the suite fails is KILLED; one it
passes SURVIVED. The unmutated control must pass, or nothing the mutants say means anything.

The first 16 are juniper-data-client's (util/ad-hoc/2026-11-26_run_tests_data_client_mutation_check.py), ported to
the engine's text; the rest break what the extraction added or generalized. The suite's fake checkouts land in
the per-mutant directory's own ``tmp`` (the tests put them under the checkout above juniper-ci-tools/).

Usage: python3 util/ad-hoc/2026-11-26_run_tests_engine_mutation_check.py --work DIR [--package DIR] [-j N] [--only NAME ...]
Exit: 0 when the control passes and every mutant is killed; 1 otherwise. Writes nothing under the system temp dir.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 - runs pytest on a copy, fixed argv
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENGINE = Path("juniper_ci_tools") / "run_tests.py"

# (name, old text, new text): each breaks one behaviour.
MUTANTS = [
    # juniper-data-client's 16, on the engine's text
    ("junit-routing", 'token = f"{option}={lane_dir / Path(target).name}"', "token = token"),
    ("exit-5-accepted", "elif rc in planned.tolerated:", "elif False:"),
    ("step-env", 'own = {key: value for key, value in step.env.items() if key not in ("PYTHONPATH", "COVERAGE_FILE")}', "own = {}"),
    ("shell-var-expansion", "            if match and value is not None:\n", "            if False:\n"),
    ("cov-term-modifier", "if colon and kind in _COV_FILE_REPORTS and target else spec", "if colon and target else spec"),
    ("left-out-listing", 'left_out.append(title or "(unnamed step)")', "pass"),
    ("opt-in-table", "        if lane is not None and not lane.optional:\n            lane.optional, lane.why = True, why", "        if False:\n            lane.optional, lane.why = True, why"),
    ("install-fallbacks", 'return segments(list(itertools.takewhile(lambda token: token != "||", tokens)))', "return segments(tokens)"),
    ("rc-shape-refusal", "    raise UsageError(f'{where}: captures an exit code", "    return lines, ()\n    raise UsageError(f'{where}: captures an exit code"),
    ("changed-package-dirs", '    return name in exact or any(name == place or name.startswith(place + "/") for place in places)', "    return name in exact"),
    ("subfailed-lines", '_PT_PROBLEM = re.compile(r"^(?:FAILED|ERROR|SUBFAILED(?:\\(.*?\\))?) (\\S+::\\S+|\\S+\\.py)", re.M)', '_PT_PROBLEM = re.compile(r"^(?:FAILED|ERROR) (\\S+)", re.M)'),
    ("secret-env-hidden", 'env[str(key)] = None if unknown or "${{" in resolved else resolved', "env[str(key)] = resolved"),
    ("coverage-report-floor", "floor = (_COV_FLOOR.search(text) or _COV_REPORT_FLOOR.search(text))", "floor = (_COV_FLOOR.search(text))"),
    ("floor-is-a-gate", "coverage_gate=label in _GATE_LABELS", 'coverage_gate=label == "coverage-gate"'),
    ("lane-files-selector", "        if candidate in by_file:\n", "        if False:\n"),
    ("shell-step-refused", '                raise UsageError(f"{where}: {line!r} needs a shell', '                continue\n                raise UsageError(f"{where}: {line!r} needs a shell'),
    # what the extraction added or generalized
    ("keep-steps", "keeps = {pattern for pattern in keep if fnmatch.fnmatchcase(title, pattern)}", "keeps = set()"),
    ("stale-keep-refused", '        if stale:\n            raise UsageError(f"the spec keeps', '        if False:\n            raise UsageError(f"the spec keeps'),
    ("lane-directory", "package_dir = Path(os.path.normpath(checkout / directory.format(name=name))) if directory else _lane_dir(checkout, job, steps)", "package_dir = _lane_dir(checkout, job, steps)"),
    ("exact-job-runs-pytest", "elif self.jobs is not None and job_name in self.jobs:", "elif False:"),
    ("job-globs", "if self.jobs is not None and not any(fnmatch.fnmatchcase(job_name, glob) for glob in self.jobs):", "if False:"),
    ("step-lane-deps", "        if self.deps:\n", "        if False:\n"),
    ("step-lane-empty", '        if not jobs:\n            raise UsageError(f"{source}: found no command', '        if False:\n            raise UsageError(f"{source}: found no command'),
    ("commands-by-path", "            if not node and rel in (command.id, command.id.split()[0]):", "            if False:"),
    ("changed-runs-command", '            if name in job.id.split():\n                picks.append((job, f"runs {name}"', '            if False:\n                picks.append((job, f"runs {name}"'),
    ("ambiguous-test-file", "            if len(by_file[candidate]) > 1:", "            if False:"),
    ("test-file-scan-skips", 'dirs[:] = sorted(name for name in dirs if not name.startswith(".") and name not in _SKIPPED_DIRS and not name.endswith(".egg-info"))', "dirs[:] = sorted(dirs)"),
    ("env-flags", "        if getattr(args, flag.dest, False):\n            changes[flag.variable] = flag.value", "        if False:\n            changes[flag.variable] = flag.value"),
    ("command-lane-preflight", "            if missing:\n                verdict.refused = f\"{', '.join(missing)}", "            if False:\n                verdict.refused = f\"{', '.join(missing)}"),
    ("spec-groups", "(group == GROUP_ALL or group in lane.groups)", "(group == GROUP_ALL)"),
    ("unwired-hint", '            hint = f" ({spec.unwired_hint})" if spec.unwired_hint else ""', '            hint = ""'),
    ("strip-suffix-alias", "    if suffix:\n", "    if False:\n"),
    ("checkout-pyproject", "    if not spec.pyproject:\n        return True", "    if True:\n        return True"),
    ("stale-opt-in-refused", "    if stale:\n        raise UsageError(f\"the spec's opt_in names", "    if False:\n        raise UsageError(f\"the spec's opt_in names"),
    ("workflow-stem-primary", "        if job_id == primary:\n            return base", "        if False:\n            return base"),
    ("unittest-events", "            if not workflow_events(workflow) & self.events:", "            if not workflow_events(workflow):"),
    ("engine-recorded", '        "engine": {"module": ENGINE_MODULE, "version": ENGINE_VERSION},', '        "engine": None,'),
    ("argv-recorded", '        "argv": raw,', '        "argv": sys.argv[1:],'),
    ("jobs-not-a-mapping", '            rel = path.relative_to(found.checkout).as_posix()\n            jobs_map = workflow.get("jobs") or {}\n            if not isinstance(jobs_map, dict):\n                continue\n', '            rel = path.relative_to(found.checkout).as_posix()\n            jobs_map = workflow.get("jobs") or {}\n'),
    ("lane-collisions", '            if lane.name in lanes or lane.name in groups:\n                raise UsageError(f"{lane.source}: the lane name', '            if False:\n                raise UsageError(f"{lane.source}: the lane name'),
    ("py311-ran-nothing", 'if result.status == PASSED and self.filtered and job.kind == "unittest" and result.counts.get("ran") == 0:', "if False:"),
]


def copy_package(package: Path, dest: Path) -> None:
    dest.mkdir(parents=True)
    for name in ("juniper_ci_tools", "tests"):
        shutil.copytree(package / name, dest / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(package / "pyproject.toml", dest / "pyproject.toml")


def run_one(name: str, old: str | None, new: str | None, package: Path, work: Path, timeout: float) -> tuple[str, str, float, str]:
    root = work / name
    copy = root / "juniper-ci-tools"
    copy_package(package, copy)
    engine = copy / ENGINE
    if old is not None:
        text = engine.read_text(encoding="utf-8")
        if text.count(old) != 1:
            return name, f"BAD-MUTANT (old text occurs {text.count(old)} times)", 0.0, ""
        engine.write_text(text.replace(old, new), encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["PYTHONPATH"] = str(copy)
    started = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "--no-header", "tests/test_run_tests.py"], cwd=copy, env=env, capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603 - pytest on a copy, fixed argv
    except subprocess.TimeoutExpired:
        return name, "TIMEOUT", time.monotonic() - started, ""
    took = time.monotonic() - started
    tail = (proc.stdout.strip().splitlines() or [""])[-1]
    failed = next((line for line in proc.stdout.splitlines() if line.startswith("FAILED ")), "")
    if old is None:
        return name, "PASS" if proc.returncode == 0 else f"FAIL (exit {proc.returncode})", took, tail
    return name, "SURVIVED" if proc.returncode == 0 else "KILLED", took, failed or tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--package", default=str(Path(__file__).resolve().parents[2] / "juniper-ci-tools"))
    parser.add_argument("--work", required=True, help="a new directory under a repo's gitignored tmp/")
    parser.add_argument("-j", "--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()
    package = Path(args.package).resolve()
    work = Path(args.work).absolute()
    if str(work).startswith(("/tmp", "/var/tmp")):  # tmp-path-literal: allow -- the refusal itself
        raise SystemExit(f"--work {work}: never under the system temp directory")
    if work.exists():
        raise SystemExit(f"--work {work} exists: give a new directory")
    work.mkdir(parents=True)
    chosen = [mutant for mutant in MUTANTS if args.only is None or mutant[0] in args.only]
    control = run_one("control", None, None, package, work, args.timeout)
    print(f"{control[0]:<24} {control[1]:<10} {control[2]:6.1f}s  {control[3]}", flush=True)
    if control[1] != "PASS":
        print("the unmutated control did not pass: no mutant result means anything")
        return 1
    survived = 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for name, verdict, took, detail in pool.map(lambda mutant: run_one(*mutant, package, work, args.timeout), chosen):
            survived += verdict != "KILLED"
            print(f"{name:<24} {verdict:<10} {took:6.1f}s  {detail}", flush=True)
    print(f"{len(chosen) - survived} of {len(chosen)} mutants killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
