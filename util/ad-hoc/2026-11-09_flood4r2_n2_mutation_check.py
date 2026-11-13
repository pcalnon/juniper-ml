#!/usr/bin/env python3
"""Stop-then-start race mutation check: each mutant of the start refusal is killed by a named test.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Status:      ad-hoc -- one-off verification
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     §8, ruling 11 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
             (juniper-service-core's stop-then-start race);
             juniper-service-core/tests/test_lifecycle_stop_then_start.py; adapted from
             util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py (juniper-ml#2531)

For each mutant, ``juniper-service-core`` is copied into ``--scratch`` and
``juniper_service_core/lifecycle/manager.py`` in the copy is mutated: by exact text substitutions
(each refused unless its old text occurs exactly once), or, for ``fix-reverted``, by replacing the
whole file with ``--main-manager`` (``main``'s manager, so the fix reverted). The checkout's own
``manager.py`` is never written; its sha256 is read before the first copy and after the last run,
and a difference is a setup error. The package's whole suite (this tree's tests) then runs
against the copy, with ``PYTHONPATH`` putting the copy ahead of any installed one and the
checkout's ``juniper-model-core`` behind it. Each run first proves the copy is what gets imported.
An unmutated copy runs first and must PASS; every mutant must FAIL, with every test named in its
``killers`` among the failures. Twelve mutants: the fix reverted; the refusal removed; each half of
its condition dropped; the refusal made to depend on the machine reading ``STOPPED``; the check
moved before the lock is taken, after the dataset write, or after the stop is cleared; and four
mutants of the ownership guard and result recording that juniper-ml#2531 added.

Each copy is removed once its run is over, and so is the run's pytest ``--basetemp``, which is put
beside the copy; the run's ``pytest.log`` stays in ``--scratch``. Left in a checkout's ``tmp/``, a
copy's ``pyproject.toml``, or one of the fixture projects the suite builds under its basetemp,
would be picked up by juniper-ml's ``tests/test_release_train_registry.py``, which walks ``tmp/``
too. ``TMPDIR`` is left as the session set it.

Exit status: 0 when every row matches its expectation, 1 when a row does not, 2 on a usage or
setup error (an interpreter that will not run, a mutant's text not found exactly once, the copy
not the module imported, pytest exiting with anything but 0 or 1, the checkout's file changed).

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_n2_mutation_check.py --python <interpreter> \\
        --scratch <a scratch dir in the repo's tmp> --main-manager <main's lifecycle/manager.py> [--json-out <file>]
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
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

_N = "tests/test_lifecycle_stop_then_start.py::"
REFUSED = _N + "test_a_start_while_the_stopped_runs_fit_is_still_running_is_refused"
SEES_STOP = _N + "test_the_stopped_fit_still_sees_its_stop_and_none_of_its_later_events_lands"
HTTP = _N + "test_stop_then_start_over_http_is_a_409_until_the_stopped_fit_has_ended"
PAUSE_GATE = _N + "test_a_stopped_fit_cannot_be_released_by_a_later_paused_completion"
UNWINDING = _N + "test_a_start_while_the_stopped_fit_is_still_unwinding_is_refused"
EVENTLESS = _N + "test_a_stopped_eventless_fit_holds_a_start_back_until_it_returns"
RESET = _N + "test_a_reset_then_start_is_refused_the_same_way"
SETTLED = _N + "test_a_start_right_after_a_run_settled_itself_is_accepted_while_its_thread_exits"
AFTER_A_LOAD = tuple(_N + f"test_a_start_after_a_snapshot_load_is_refused_while_the_stopped_fit_is_still_running[{load}-{status}]" for load, status in (("resume_from_snapshot", "RESUME_READY"), ("load_snapshot", "INVESTIGATING"), ("start_replay", "REPLAYING")))
UNDER_THE_LOCK = _N + "test_a_stop_that_lands_while_a_start_waits_for_the_lock_still_refuses_that_start"
RACE_TESTS = (REFUSED, SEES_STOP, HTTP, PAUSE_GATE, UNWINDING, EVENTLESS, RESET, *AFTER_A_LOAD, UNDER_THE_LOCK)
AFTER_THE_STOPPED_FIT_ENDED = (SEES_STOP, HTTP, PAUSE_GATE, UNWINDING, EVENTLESS, RESET, UNDER_THE_LOCK)

_O = "tests/test_lifecycle_paused_fit_return.py::"
STALE_RETURN_RUNNING = _O + "test_a_stopped_runs_fit_that_returns_leaves_a_newer_running_run_alone"
STALE_RETURN = _O + "test_a_stopped_runs_fit_that_returns_leaves_a_newer_paused_run_alone"
STALE_RAISE = _O + "test_a_stopped_runs_fit_that_raises_leaves_a_newer_paused_run_alone"
STALE_INTERRUPT = _O + "test_a_stopped_runs_interrupt_leaves_a_newer_runs_monitor_alone"
RESULT = _O + "test_only_the_run_that_completes_records_its_result"

_REFUSAL = '            if previous is not None and previous.is_alive() and self._stop_event.is_set():\n                raise RuntimeError("The stopped run\'s fit is still running (a stop takes effect at its next event)")\n'
_CONDITION = "            if previous is not None and previous.is_alive() and self._stop_event.is_set():\n"
_CLEAR = "            self._stop_event.clear()\n"
_PREVIOUS = "            previous = self._thread\n"
_START_LOCK = '        with self._lock:\n            if self.model is None:\n                raise RuntimeError("No model attached")\n            if self.state_machine.is_active():\n                raise RuntimeError("Training already in progress")\n'
_CHECK_BEFORE_THE_LOCK = "".join(line[4:] for line in (_PREVIOUS + _REFUSAL).splitlines(keepends=True))
_SETTLE_GUARD = "                if not self._stop_event.is_set() and self._thread is threading.current_thread():\n"
_FAILURE_GUARD = "                if self._thread is threading.current_thread():\n                    self.state_machine.mark_failed(str(exc))\n"
_INTERRUPT_GUARD = '                if self._thread is threading.current_thread():\n                    self.monitor.set_run_context(status="stopped", phase="idle")\n'
_RESULT_UNDER_THE_GUARD = "                    self._last_result = result\n"


class SetupError(Exception):
    """The check could not run as designed; no verdict below it would mean anything."""


@dataclasses.dataclass(frozen=True)
class Mutant:
    mutant_id: str
    edits: tuple[tuple[str, str], ...]  # (old, new) pairs applied to manager.py, in order; empty for fix-reverted
    killers: tuple[str, ...]  # tests that must be among the failures
    targets: str


MUTANTS = [
    Mutant("fix-reverted", (), RACE_TESTS, "the whole fix (main's manager.py)"),
    Mutant("no-refusal", ((_REFUSAL, ""),), RACE_TESTS, "the start refusal itself"),
    Mutant("refusal-ignores-liveness", ((_CONDITION, "            if previous is not None and self._stop_event.is_set():\n"),), AFTER_THE_STOPPED_FIT_ENDED, "the liveness half: a stop with no live fit behind it must not block every later start"),
    Mutant("refusal-ignores-the-pending-stop", ((_CONDITION, "            if previous is not None and previous.is_alive():\n"),), (SETTLED, STALE_RETURN_RUNNING, STALE_RETURN, STALE_RAISE, STALE_INTERRUPT, RESULT), "the pending-stop half: a run that settled itself must not hold a start back while its thread exits"),
    Mutant("refusal-after-the-dataset-write", ((_REFUSAL, ""), (_CLEAR, _REFUSAL + _CLEAR)), (REFUSED, UNDER_THE_LOCK), "the refusal comes before the start touches anything (the dataset fields)"),
    Mutant("refusal-after-the-stop-is-cleared", ((_REFUSAL, ""), (_CLEAR, _CLEAR + _REFUSAL)), RACE_TESTS, "the refusal comes before the stop is cleared"),
    Mutant("refusal-only-when-STOPPED", ((_CONDITION, _CONDITION.replace("self._stop_event.is_set():", "self._stop_event.is_set() and self.state_machine.is_stopped():")),), AFTER_A_LOAD, "the refusal does not depend on the machine's status: after a stop, a snapshot load leaves RESUME_READY, INVESTIGATING or REPLAYING with the stopped fit still running"),
    Mutant("check-before-the-lock", ((_PREVIOUS + _REFUSAL, ""), (_START_LOCK, _CHECK_BEFORE_THE_LOCK + _START_LOCK)), (UNDER_THE_LOCK,), "the refusal is decided under the manager lock: a stop that lands while the start waits for the lock is seen"),
    Mutant("completion-without-the-ownership-guard", ((_SETTLE_GUARD, "                if not self._stop_event.is_set():\n"),), (STALE_RETURN_RUNNING, STALE_RETURN), "kept: the ownership guard on a completion, still pinned by the adapted tests"),
    Mutant("failure-without-the-ownership-guard", ((_FAILURE_GUARD, _FAILURE_GUARD.replace("if self._thread is threading.current_thread():", "if self._thread is not None:")),), (STALE_RAISE,), "kept: the ownership guard on a failure"),
    Mutant("interrupt-without-the-ownership-guard", ((_INTERRUPT_GUARD, _INTERRUPT_GUARD.replace("if self._thread is threading.current_thread():", "if self._thread is not None:")),), (STALE_INTERRUPT,), "kept: the ownership guard on an interrupt"),
    Mutant("result-recorded-outside-the-guard", ((_RESULT_UNDER_THE_GUARD, "                self._last_result = result\n"),), (RESULT,), "kept: only the settle that completes a run records its result"),
]

_FAILED_LINE = re.compile(r"^FAILED (\S+?)(?: - .*)?$")
_SUMMARY_LINE = re.compile(r"^=* ?(?:\d+ (?:failed|passed|skipped|deselected|errors?|xfailed|xpassed|warnings?)(?:, )?)+ in [0-9.]+s")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    """The copy's manager and the checkout's model-core, not an installed copy, are what get imported."""
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
    killed" and make an expected-fail row pass vacuously.
    """
    basetemp = log.parent.resolve() / "basetemp"  # absolute: pytest runs with the copy as its working directory
    try:
        result = _run([python, "-m", "pytest", "-rf", "-p", "no:cacheprovider", f"--basetemp={basetemp}", "tests"], cwd=copy, env=env)
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)  # the suite's fixture projects must not stay under a checkout's tmp/
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
    if shutil.which(args.python) is None:
        raise SetupError(f"{args.python} is not an executable interpreter")
    if not args.main_manager.is_file():
        raise SetupError(f"{args.main_manager} is not a file")
    args.scratch.mkdir(parents=True, exist_ok=True)
    checkout_manager = REPO_ROOT / PACKAGE / MANAGER
    before = _sha256(checkout_manager)
    rows = []
    for mutant in [None, *MUTANTS]:
        mutant_id = "CONTROL" if mutant is None else mutant.mutant_id
        work = args.scratch / mutant_id
        copy = _copy_package(work)
        try:
            if _sha256(copy / MANAGER) != before:
                raise SetupError(f"{mutant_id}: the copy's {MANAGER} differs from the checkout's before mutation")
            if mutant is not None:
                _apply(copy, mutant, args.main_manager)
            mutated = _sha256(copy / MANAGER)
            env = _env(copy, work)
            _prove_copy_is_imported(args.python, copy, env)
            rc, failed, summary = _run_suite(args.python, copy, env, work / "pytest.log")
        finally:
            shutil.rmtree(copy, ignore_errors=True)  # the log stays; see the module docstring
        expected_pass = mutant is None
        missing = [] if expected_pass else [k for k in mutant.killers if k not in failed]
        ok = (rc == 0) == expected_pass and not missing
        rows.append(
            {
                "mutant": mutant_id,
                "targets": "unmutated" if mutant is None else mutant.targets,
                "manager_sha256": mutated,
                "expected": "pass" if expected_pass else "fail",
                "exit": rc,
                "summary": summary,
                "failed": failed,
                "killers_missing": missing,
                "verdict": "OK" if ok else "MISMATCH",
            }
        )
        print(f"{mutant_id}\texpected {rows[-1]['expected']}\texit {rc}\t{summary}\t{rows[-1]['verdict']}", flush=True)
    after = _sha256(checkout_manager)
    if after != before:
        raise SetupError(f"the checkout's {MANAGER} changed during the check ({before} -> {after})")
    rows.append({"mutant": "CHECKOUT", "targets": f"the checkout's {MANAGER}, never written", "sha256_before": before, "sha256_after": after, "verdict": "OK"})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", required=True, help="an interpreter with juniper-service-core's test dependencies")
    parser.add_argument("--scratch", required=True, type=Path, help="an empty-or-reusable scratch directory (the repo's tmp/, never the system temp dir)")
    parser.add_argument("--main-manager", required=True, type=Path, help="juniper_service_core/lifecycle/manager.py as it is on main (for fix-reverted)")
    parser.add_argument("--json-out", type=Path, help="also write every row, with its failed test ids, to this JSON file")
    args = parser.parse_args(argv)

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
        print(f"MISMATCH {row['mutant']}: exit {row['exit']}, killers missing {row['killers_missing']}", file=sys.stderr)
    print(f"RESULT: {len(rows) - len(mismatches)}/{len(rows)} rows as expected")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
