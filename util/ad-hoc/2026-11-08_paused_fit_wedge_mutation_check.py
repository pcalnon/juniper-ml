#!/usr/bin/env python3
"""Paused-fit wedge mutation check: each new lifecycle test kills the mutant it targets.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-08
Status:      ad-hoc -- one-off verification
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     the "paused-fit wedge", §4 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md;
             juniper-service-core/tests/test_lifecycle_paused_fit_return.py

For each mutant, ``juniper-service-core`` is copied into ``--scratch`` and
``juniper_service_core/lifecycle/manager.py`` in the copy is mutated: by exact text
substitutions (each refused unless its old text occurs exactly once), or, for ``fix-reverted``, by
replacing the whole file with ``--main-manager`` (``main``'s manager, so the fix reverted). The
package's whole suite then runs against the copy, which ``PYTHONPATH`` puts ahead of any
installed copy, with the checkout's ``juniper-model-core`` behind it (CI installs both
editable). Each run first proves the copy is what gets imported. Every mutant runs against:

- the NEW suite (this branch): it must FAIL, and every test named in ``killers`` must be among
  the failures;
- the OLD suite (the copy without ``tests/test_lifecycle_paused_fit_return.py``, which is
  ``main``'s suite): it must PASS. That is what makes the new file necessary, not decorative.

An unmutated copy runs first under both suites and must PASS, or nothing below means anything.

Each copy is removed once its run is over; its ``pytest.log`` stays in ``--scratch``. Left in a
checkout's ``tmp/``, a copy's ``pyproject.toml`` would be picked up by juniper-ml's
``tests/test_release_train_registry.py``, which walks ``tmp/`` too. ``TMPDIR`` is left as the
session set it: pointed at a deep scratch path, it can push ``multiprocessing`` back to the system
temp dir.

Exit status: 0 when every row matches its expectation, 1 when a row does not, 2 on a usage or
setup error (an interpreter that will not run, a mutant's text not found exactly once, the copy
not the module imported, pytest exiting with anything but 0 or 1).

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py --python <interpreter> \\
        --scratch <repo>/tmp/<dir> --main-manager <main's lifecycle/manager.py> \\
        [--suites new,old] [--json-out <file>]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "juniper-service-core"
MODEL_CORE = REPO_ROOT / "juniper-model-core"
MANAGER = "juniper_service_core/lifecycle/manager.py"
NEW_TEST_FILE = "tests/test_lifecycle_paused_fit_return.py"

_T = "tests/test_lifecycle_paused_fit_return.py::"
SETTLES = (_T + "test_fit_that_returns_while_paused_settles_completed[after-last-event]", _T + "test_fit_that_returns_while_paused_settles_completed[eventless-fit]")
HTTP = _T + "test_resume_then_start_after_a_paused_fit_returned_over_http"
STOP_CONTROL = _T + "test_stop_that_races_a_paused_completion_still_settles_stopped"
RAISES_PAUSED = _T + "test_fit_that_raises_while_paused_settles_failed_and_releases_the_pause"
STALE_RETURN_RUNNING = _T + "test_a_stopped_runs_fit_that_returns_leaves_a_newer_running_run_alone"
STALE_RETURN = _T + "test_a_stopped_runs_fit_that_returns_leaves_a_newer_paused_run_alone"
STALE_RAISE = _T + "test_a_stopped_runs_fit_that_raises_leaves_a_newer_paused_run_alone"
STALE_INTERRUPT = _T + "test_a_stopped_runs_interrupt_leaves_a_newer_runs_monitor_alone"
RESULT = _T + "test_only_the_run_that_completes_records_its_result"

_SETTLE_GUARD = "                if not self._stop_event.is_set() and self._thread is threading.current_thread():\n"
_PAUSED_RELEASE = "                        self.state_machine.handle_command(LifecycleCommand.RESUME)\n                        self._pause_event.set()\n"
_FAILURE_GUARD = "                if self._thread is threading.current_thread():\n                    self.state_machine.mark_failed(str(exc))\n"
_INTERRUPT_GUARD = '                if self._thread is threading.current_thread():\n                    self.monitor.set_run_context(status="stopped", phase="idle")\n'
_FAILURE_RELEASE = "                    # A run that failed while paused has no pause left to hold. Left closed, the\n                    # gate would block a direct run() on this manager at its first event.\n                    self._pause_event.set()\n"
_RESULT_UNDER_THE_GUARD = "                    self._last_result = result\n"


class SetupError(Exception):
    """The check could not run as designed; no verdict below it would mean anything."""


@dataclasses.dataclass(frozen=True)
class Mutant:
    mutant_id: str
    edits: tuple[tuple[str, str], ...]  # (old, new) pairs applied to manager.py; empty for fix-reverted
    killers: tuple[str, ...]  # NEW-suite tests that must be among the failures
    targets: str


MUTANTS = [
    Mutant("fix-reverted", (), (*SETTLES, HTTP, RAISES_PAUSED, STALE_RETURN_RUNNING, STALE_RETURN, STALE_RAISE, STALE_INTERRUPT, RESULT), "the whole fix (main's manager.py)"),
    Mutant("paused-completion-keeps-the-gate-closed", ((_PAUSED_RELEASE, "                        self.state_machine.handle_command(LifecycleCommand.RESUME)\n"),), SETTLES, "the pause-gate release of a paused completion"),
    Mutant("paused-completion-settles-stopped", ((_PAUSED_RELEASE, _PAUSED_RELEASE.replace("LifecycleCommand.RESUME", "LifecycleCommand.STOP")),), SETTLES, "COMPLETED, not STOPPED"),
    Mutant("completion-without-the-ownership-guard", ((_SETTLE_GUARD, "                if not self._stop_event.is_set():\n"),), (STALE_RETURN_RUNNING, STALE_RETURN), "the ownership guard on a completion (the stale-return regression)"),
    Mutant("failure-without-the-ownership-guard", ((_FAILURE_GUARD, _FAILURE_GUARD.replace("if self._thread is threading.current_thread():", "if True:")),), (STALE_RAISE,), "the ownership guard on a failure"),
    Mutant("interrupt-without-the-ownership-guard", ((_INTERRUPT_GUARD, _INTERRUPT_GUARD.replace("if self._thread is threading.current_thread():", "if True:")),), (STALE_INTERRUPT,), "the ownership guard on an interrupt"),
    Mutant("failure-keeps-the-gate-closed", ((_FAILURE_RELEASE, ""),), (RAISES_PAUSED,), "the pause-gate release of a failure"),
    Mutant("completion-ignores-a-stop", ((_SETTLE_GUARD, "                if self._thread is threading.current_thread():\n"),), (STOP_CONTROL,), "a stop that races the completion still wins (pre-existing guard)"),
    Mutant("result-recorded-outside-the-guard", ((_RESULT_UNDER_THE_GUARD, "                self._last_result = result\n"),), (RESULT,), "only the settle that completes a run records its result (main's position)"),
]

_FAILED_LINE = re.compile(r"^FAILED (\S+?)(?: - .*)?$")
_SUMMARY_LINE = re.compile(r"^=* ?(?:\d+ (?:failed|passed|skipped|deselected|errors?|xfailed|xpassed|warnings?)(?:, )?)+ in [0-9.]+s")


def _copy_package(dest_root: Path) -> Path:
    dest = dest_root / PACKAGE
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(REPO_ROOT / PACKAGE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache", "build", "dist", ".coverage*"))
    return dest


def _apply(copy: Path, mutant: Mutant, main_manager: Path) -> None:
    target = copy / MANAGER
    if not mutant.edits:
        shutil.copyfile(main_manager, target)
        return
    text = target.read_text(encoding="utf-8")
    for old, new in mutant.edits:
        count = text.count(old)
        if count != 1:
            raise SetupError(f"{mutant.mutant_id}: an edit's old text occurs {count} times in {MANAGER}, not once")
        text = text.replace(old, new, 1)
    target.write_text(text, encoding="utf-8")


def _env(copy: Path, work: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(copy), str(MODEL_CORE)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    logs = work / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    env["JUNIPER_SERVICE_LOG_DIR"] = str(logs)
    return env


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """``subprocess.run``, with an interpreter that cannot be started reported as a setup error."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)
    except OSError as exc:
        raise SetupError(f"cannot run {cmd[0]}: {exc}") from exc


def _prove_copy_is_imported(python: str, copy: Path, env: dict[str, str]) -> None:
    """The copy's manager and the checkout's model-core, not an installed copy, are what get imported.

    ``-c`` puts the working directory first on ``sys.path``, as ``python -m pytest`` there does.
    """
    probe = _run([python, "-c", "import juniper_service_core.lifecycle.manager as m, juniper_model_core as c; print(m.__file__); print(c.__file__)"], cwd=copy, env=env)
    lines = probe.stdout.split()
    if probe.returncode != 0 or len(lines) != 2:
        raise SetupError(f"import probe failed in {copy}: {probe.stderr.strip()}")
    manager, model_core = (Path(line).resolve() for line in lines)
    if copy.resolve() not in manager.parents:
        raise SetupError(f"the manager imports from {manager}, not from the copy {copy}")
    if MODEL_CORE.resolve() not in model_core.parents:
        raise SetupError(f"juniper_model_core imports from {model_core}, not from {MODEL_CORE}")


def _run_suite(python: str, copy: Path, env: dict[str, str], log: Path) -> tuple[int, list[str], str]:
    """pytest's exit status (0 or 1), the failed test ids, and the summary line.

    Exit 5 (nothing collected) or 2 (a collection error) would otherwise read as "the mutant was
    killed" and make an expected-fail row pass vacuously. No ``-q`` here: the package's
    ``addopts`` already has one, and a second suppresses the summary line.
    """
    result = _run([python, "-m", "pytest", "-rf", "-p", "no:cacheprovider", "tests"], cwd=copy, env=env)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(result.stdout)
        fh.write(result.stderr)
    if result.returncode not in (0, 1):
        tail = "\n".join(result.stdout.splitlines()[-15:])
        raise SetupError(f"pytest exited {result.returncode} in {copy}\n{tail}")
    failed = [m.group(1) for m in map(_FAILED_LINE.match, result.stdout.splitlines()) if m]
    summary = next((line.strip("= ") for line in reversed(result.stdout.splitlines()) if _SUMMARY_LINE.match(line)), "")
    return result.returncode, failed, summary


def _check(args: argparse.Namespace) -> list[dict]:
    if shutil.which(args.python) is None:  # a path, or a name found on PATH, that can be executed
        raise SetupError(f"{args.python} is not an executable interpreter")
    if not args.main_manager.is_file():
        raise SetupError(f"{args.main_manager} is not a file")
    args.scratch.mkdir(parents=True, exist_ok=True)
    rows = []
    for mutant in [None, *MUTANTS]:
        mutant_id = "CONTROL" if mutant is None else mutant.mutant_id
        for suite in args.suites:
            work = args.scratch / f"{mutant_id}-{suite}"
            copy = _copy_package(work)
            try:
                if mutant is not None:
                    _apply(copy, mutant, args.main_manager)
                if suite == "old":
                    (copy / NEW_TEST_FILE).unlink()
                env = _env(copy, work)
                _prove_copy_is_imported(args.python, copy, env)
                rc, failed, summary = _run_suite(args.python, copy, env, work / "pytest.log")
            finally:
                shutil.rmtree(copy, ignore_errors=True)  # the log stays; see the module docstring
            expected_pass = mutant is None or suite == "old"
            missing = [] if expected_pass else [k for k in mutant.killers if k not in failed]
            ok = (rc == 0) == expected_pass and not missing
            rows.append(
                {
                    "mutant": mutant_id,
                    "targets": "unmutated" if mutant is None else mutant.targets,
                    "suite": suite,
                    "expected": "pass" if expected_pass else "fail",
                    "exit": rc,
                    "summary": summary,
                    "failed": failed,
                    "killers_missing": missing,
                    "verdict": "OK" if ok else "MISMATCH",
                }
            )
            print(f"{mutant_id}\t{suite}\texpected {rows[-1]['expected']}\texit {rc}\t{summary}\t{rows[-1]['verdict']}", flush=True)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", required=True, help="an interpreter with juniper-service-core's test dependencies")
    parser.add_argument("--scratch", required=True, type=Path, help="an empty-or-reusable scratch directory (the repo's tmp/, never the system temp dir)")
    parser.add_argument("--main-manager", required=True, type=Path, help="juniper_service_core/lifecycle/manager.py as it is on main (for fix-reverted)")
    parser.add_argument("--suites", default="new,old", type=lambda s: [p for p in s.split(",") if p], help="comma list from new,old (default: both)")
    parser.add_argument("--json-out", type=Path, help="also write every row, with its failed test ids, to this JSON file")
    args = parser.parse_args(argv)
    if not args.suites or set(args.suites) - {"new", "old"}:
        parser.error("--suites takes new, old or both")

    try:
        rows = _check(args)
    except SetupError as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return 2

    if args.json_out is not None:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
    mismatches = [row for row in rows if row["verdict"] != "OK"]
    for row in mismatches:
        print(f"MISMATCH {row['mutant']} [{row['suite']}]: exit {row['exit']}, killers missing {row['killers_missing']}", file=sys.stderr)
    print(f"RESULT: {len(rows) - len(mismatches)}/{len(rows)} rows as expected")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
