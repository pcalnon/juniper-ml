"""
Mutation check for ruling 23's "Lifecycle races beside N-2": each mutant of manager.py is killed by the tests it names.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — one-off verification (flood-4 session 14, builder r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 11, 19, 23);
         adapted from util/ad-hoc/2026-11-09_flood4r2_n2_mutation_check.py (juniper-ml#2557)

For each mutant, ``juniper-service-core`` is copied from ``--repo-root`` into ``--scratch`` and the copy's
``juniper_service_core/lifecycle/manager.py`` is mutated, by exact text substitutions (each refused unless its old
text occurs exactly once) or, for ``this-change-reverted``, by replacing the file with ``--main-manager``. The
checkout's own ``manager.py`` is never written: its sha256 is read before the first copy and after the last run.
The package's whole suite (the checkout's tests, copied), or the test paths ``--select`` names, then runs against the copy, with ``PYTHONPATH`` putting the
copy first and the checkout's ``juniper-model-core`` after it; each run first proves the copy is what gets imported.
The unmutated copy must PASS; every mutant must FAIL with every test named in its ``killers`` among the failures.

Mutants: this change reverted (main's manager.py); each changed site restored to main's behaviour (the load
refusal, the attach refusal, the load's teardown of a replay session, stop_replay's relabel); each placed where it
would be wrong (a refusal after the model is attached, the teardown before the snapshot has loaded); the control
mutant that drops stop_replay's relabel altogether; and eleven of the twelve mutants juniper-ml#2557's check runs (its
seven of the start refusal, all but its fix-reverted row, and the four of juniper-ml#2531's ownership guard),
re-expressed on the shared helper (``N2-`` rows), each with the killers #2557 named.

Each copy is removed after its run, and so is the run's pytest ``--basetemp`` (beside the copy); the run's log stays.

Exit: 0 when every row matches its expectation, 1 when a row does not, 2 on a setup error.
Usage: python3 <this file> --repo-root <juniper-ml checkout> --python <interpreter> --scratch <dir in a repo tmp/>
       --main-manager <main's lifecycle/manager.py> [--json-out FILE] [--only ID[,ID...]] [--select PATH[,PATH...]]
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

PACKAGE = "juniper-service-core"
MANAGER = "juniper_service_core/lifecycle/manager.py"

# ---- the tests (killers) ------------------------------------------------------------------------------------------
_L = "tests/test_lifecycle_stop_then_load.py::"
LOAD_REFUSED = tuple(_L + f"test_a_load_while_the_stopped_runs_fit_is_still_running_is_refused[{load}-{status}-{mon}]" for load, status, mon in (("load_snapshot", "INVESTIGATING", "investigating"), ("resume_from_snapshot", "RESUME_READY", "resume_ready"), ("start_replay", "REPLAYING", "replaying"), ("restore_for_retrain", "STOPPED", "stopped")))
ATTACH_REFUSED = _L + "test_attach_model_while_the_stopped_runs_fit_is_still_running_is_refused"
LOAD_AFTER_RESET = _L + "test_a_load_after_a_reset_is_refused_the_same_way"
RAISING_FIT = _L + "test_a_stopped_fit_that_raises_does_not_mark_a_load_failed"
IN_THE_SINK = _L + "test_a_load_while_an_event_is_inside_the_sink_is_refused"
LOAD_HTTP = tuple(_L + f"test_a_load_over_http_after_a_stop_is_a_409_until_the_stopped_fit_has_ended[{r}-{s}]" for r, s in (("restore", "INVESTIGATING"), ("resume", "RESUME_READY"), ("replay", "REPLAYING"), ("retrain", "STOPPED")))
LOAD_SETTLED = _L + "test_a_load_right_after_a_run_that_settled_itself_is_accepted_while_its_thread_exits"
LOAD_TESTS = (*LOAD_REFUSED, LOAD_AFTER_RESET, RAISING_FIT, IN_THE_SINK, *LOAD_HTTP)

_R = "tests/test_lifecycle_leftover_replay_session.py::"
SESSION_ENDS = tuple(_R + f"test_a_load_ends_the_replay_session_it_leaves[{load}-{status}]" for load, status in (("load_snapshot", "INVESTIGATING"), ("resume_from_snapshot", "RESUME_READY"), ("restore_for_retrain", "STOPPED")))
RUN_NOT_RESET = tuple(_R + f"test_a_replay_stop_after_a_load_cannot_reset_a_run_started_after_it[{load}]" for load in ("restore_for_retrain", "resume_from_snapshot"))
NO_FRAMES = _R + "test_a_session_left_by_a_load_pushes_no_replay_frame_into_a_run"
REPLAY_HTTP = _R + "test_a_replay_stop_over_http_after_a_retrain_is_a_409_and_the_run_keeps_running"
STOP_REPLAY_RUN = _R + "test_stop_replay_leaves_a_running_run_alone"
STOP_REPLAY_OUTSIDE = tuple(_R + f"test_stop_replay_outside_a_replay_leaves_the_machine_and_the_monitor_alone[{p}]" for p in ("load_snapshot-INVESTIGATING-investigating", "resume_from_snapshot-RESUME_READY-resume_ready", "None-COMPLETED-completed"))
FAILED_LOAD = _R + "test_a_load_that_fails_leaves_the_replay_session_alone"
ATTACH_KEEPS = _R + "test_attach_model_during_a_replay_keeps_the_session"
STOP_REPLAY_REPLAYING = _R + "test_stop_replay_from_a_replay_still_resets_and_relabels"
SESSION_TESTS = (*SESSION_ENDS, *RUN_NOT_RESET, NO_FRAMES, REPLAY_HTTP)
RELABEL_TESTS = (STOP_REPLAY_RUN, *STOP_REPLAY_OUTSIDE)

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

# ---- the text the mutants edit (as it stands with this change) ------------------------------------------------------
_CALL = "self._refuse_while_a_stopped_fit_runs()\n"
_HELPER_CONDITION = "        if previous is not None and previous.is_alive() and self._stop_event.is_set():\n"
_START_CALL = "            # outside is_active().\n            " + _CALL
_START_CALL_GONE = "            # outside is_active().\n"
_ATTACH_CHECK = '                raise RuntimeError("Cannot attach a model while training is active")\n'
_ATTACH_CALL = _ATTACH_CHECK + "            " + _CALL
_ATTACH_SET = "            self.model = model\n            self._last_result = None\n            self._last_error = None\n            self.monitor.reset()\n"
_LOAD_CHECK = '            raise RuntimeError("Cannot load a snapshot while training is active")\n'
_LOAD_CALL = _LOAD_CHECK + "        " + _CALL
_LOAD = "        model, sidecar = store.load(snapshot_id)  # raises SnapshotNotFoundError if absent\n"
_TEARDOWN = "        self._teardown_replay()\n"
_LOAD_SET = "        self.model = model\n        self._last_result = None\n"
_STOP_REPLAY_TAIL = '                self.state_machine.handle_command(LifecycleCommand.RESET)\n                self.monitor.set_run_context(status="stopped", phase="idle")\n            return self._status_dict()\n'
_STOP_REPLAY_TAIL_MAIN = '                self.state_machine.handle_command(LifecycleCommand.RESET)\n            self.monitor.set_run_context(status="stopped", phase="idle")\n            return self._status_dict()\n'
_STOP_REPLAY_TAIL_NONE = "                self.state_machine.handle_command(LifecycleCommand.RESET)\n            return self._status_dict()\n"
_CLEAR = "            self._stop_event.clear()\n"
_START_LOCK = '        with self._lock:\n            if self.model is None:\n                raise RuntimeError("No model attached")\n            if self.state_machine.is_active():\n                raise RuntimeError("Training already in progress")\n'
_SETTLE_GUARD = "                if not self._stop_event.is_set() and self._thread is threading.current_thread():\n"
_FAILURE_GUARD = "                if self._thread is threading.current_thread():\n                    self.state_machine.mark_failed(str(exc))\n"
_INTERRUPT_GUARD = '                if self._thread is threading.current_thread():\n                    self.monitor.set_run_context(status="stopped", phase="idle")\n'
_RESULT_UNDER_THE_GUARD = "                    self._last_result = result\n"


class SetupError(Exception):
    """The check could not run as designed; no verdict below it would mean anything."""


@dataclasses.dataclass(frozen=True)
class Mutant:
    mutant_id: str
    edits: tuple[tuple[str, str], ...]  # (old, new) applied in order; empty for this-change-reverted
    killers: tuple[str, ...]
    targets: str


MUTANTS = [
    Mutant("this-change-reverted", (), (*LOAD_TESTS, ATTACH_REFUSED, *SESSION_TESTS, *RELABEL_TESTS, *AFTER_A_LOAD), "the whole change (main's manager.py)"),
    Mutant("load-refusal-removed", ((_LOAD_CALL, _LOAD_CHECK),), (*LOAD_TESTS, *AFTER_A_LOAD), "main's behaviour at _load_snapshot_model: a load after a stop is accepted while that fit runs"),
    Mutant("attach-refusal-removed", ((_ATTACH_CALL, _ATTACH_CHECK),), (ATTACH_REFUSED,), "main's behaviour at attach_model"),
    Mutant("load-refusal-after-the-model-is-attached", ((_LOAD_CALL, _LOAD_CHECK), (_LOAD_SET, "        self.model = model\n        " + _CALL + "        self._last_result = None\n")), LOAD_REFUSED, "the load refusal comes before the load touches anything (here the model is replaced first)"),
    Mutant("attach-refusal-after-the-model-is-attached", ((_ATTACH_CALL, _ATTACH_CHECK), (_ATTACH_SET, "            self.model = model\n            " + _CALL + "            self._last_result = None\n            self._last_error = None\n            self.monitor.reset()\n")), (ATTACH_REFUSED,), "the attach refusal comes before the model is replaced"),
    Mutant("teardown-removed", ((_LOAD + _TEARDOWN, _LOAD),), SESSION_TESTS, "main's behaviour: a load leaves the replay session open"),
    Mutant("teardown-before-the-snapshot-has-loaded", ((_LOAD + _TEARDOWN, _TEARDOWN + _LOAD),), (FAILED_LOAD,), "a load that fails (no such snapshot) must leave the replay session alone"),
    Mutant("stop-replay-relabels-in-any-state", ((_STOP_REPLAY_TAIL, _STOP_REPLAY_TAIL_MAIN),), RELABEL_TESTS, "main's behaviour: stop_replay sets monitor.status 'stopped' whatever the machine reads"),
    Mutant("stop-replay-never-relabels", ((_STOP_REPLAY_TAIL, _STOP_REPLAY_TAIL_NONE),), (STOP_REPLAY_REPLAYING,), "control: from REPLAYING, stop_replay still relabels the monitor 'stopped'"),
    Mutant("N2-no-refusal", ((_START_CALL, _START_CALL_GONE),), RACE_TESTS, "#2557: the start refusal itself (the helper call in start_training)"),
    Mutant("N2-refusal-ignores-liveness", ((_HELPER_CONDITION, "        if previous is not None and self._stop_event.is_set():\n"),), AFTER_THE_STOPPED_FIT_ENDED, "#2557: the liveness half (now shared by the loads and attach_model)"),
    Mutant("N2-refusal-ignores-the-pending-stop", ((_HELPER_CONDITION, "        if previous is not None and previous.is_alive():\n"),), (SETTLED, STALE_RETURN_RUNNING, STALE_RETURN, STALE_RAISE, STALE_INTERRUPT, RESULT), "#2557: the pending-stop half"),
    Mutant("N2-refusal-after-the-dataset-write", ((_START_CALL, _START_CALL_GONE), (_CLEAR, "            " + _CALL + _CLEAR)), (REFUSED, UNDER_THE_LOCK), "#2557: the start refusal comes before the dataset fields are written"),
    Mutant("N2-refusal-after-the-stop-is-cleared", ((_START_CALL, _START_CALL_GONE), (_CLEAR, _CLEAR + "            " + _CALL)), RACE_TESTS, "#2557: the start refusal comes before the stop is cleared"),
    Mutant("N2-refusal-only-when-STOPPED", ((_HELPER_CONDITION, _HELPER_CONDITION.replace("self._stop_event.is_set():", "self._stop_event.is_set() and self.state_machine.is_stopped():")),), AFTER_A_LOAD, "#2557: the refusal does not read the machine's status"),
    Mutant("N2-check-before-the-lock", ((_START_CALL, _START_CALL_GONE), (_START_LOCK, "        " + _CALL + _START_LOCK)), (UNDER_THE_LOCK,), "#2557: the start refusal is decided under the manager lock"),
    Mutant("N2-completion-without-the-ownership-guard", ((_SETTLE_GUARD, "                if not self._stop_event.is_set():\n"),), (STALE_RETURN_RUNNING, STALE_RETURN), "#2531: the ownership guard on a completion"),
    Mutant("N2-failure-without-the-ownership-guard", ((_FAILURE_GUARD, _FAILURE_GUARD.replace("if self._thread is threading.current_thread():", "if self._thread is not None:")),), (STALE_RAISE,), "#2531: the ownership guard on a failure"),
    Mutant("N2-interrupt-without-the-ownership-guard", ((_INTERRUPT_GUARD, _INTERRUPT_GUARD.replace("if self._thread is threading.current_thread():", "if self._thread is not None:")),), (STALE_INTERRUPT,), "#2531: the ownership guard on an interrupt"),
    Mutant("N2-result-recorded-outside-the-guard", ((_RESULT_UNDER_THE_GUARD, "                self._last_result = result\n"),), (RESULT,), "#2531: only the settle that completes a run records its result"),
]

_FAILED_LINE = re.compile(r"^(?:FAILED|ERROR) (\S+?)(?: - .*)?$")
_SUMMARY_LINE = re.compile(r"^=* ?(?:\d+ (?:failed|passed|skipped|deselected|errors?|xfailed|xpassed|warnings?)(?:, )?)+ in [0-9.]+s")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_package(repo_root: Path, dest_root: Path) -> Path:
    dest = dest_root / PACKAGE
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(repo_root / PACKAGE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache", "build", "dist", ".coverage*"))
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


def _env(copy: Path, model_core: Path, work: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(copy), str(model_core)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    logs = work / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    env["JUNIPER_SERVICE_LOG_DIR"] = str(logs)
    return env


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)
    except OSError as exc:
        raise SetupError(f"cannot run {cmd[0]}: {exc}") from exc


def _prove_copy_is_imported(python: str, copy: Path, model_core: Path, env: dict[str, str]) -> None:
    probe = _run([python, "-c", "import juniper_service_core.lifecycle.manager as m, juniper_model_core as c; print(m.__file__); print(c.__file__)"], cwd=copy, env=env)
    lines = probe.stdout.split()
    if probe.returncode != 0 or len(lines) != 2:
        raise SetupError(f"import probe failed in {copy}: {probe.stderr.strip()}")
    manager, core = (Path(line).resolve() for line in lines)
    if copy.resolve() not in manager.parents:
        raise SetupError(f"the manager imports from {manager}, not from the copy {copy}")
    if model_core.resolve() not in core.parents:
        raise SetupError(f"juniper_model_core imports from {core}, not from {model_core}")


def _run_suite(python: str, copy: Path, env: dict[str, str], log: Path, select: list[str]) -> tuple[int, list[str], str]:
    basetemp = log.parent.resolve() / "basetemp"
    try:
        result = _run([python, "-m", "pytest", "-rfE", "-p", "no:cacheprovider", f"--basetemp={basetemp}", *select], cwd=copy, env=env)
    finally:
        shutil.rmtree(basetemp, ignore_errors=True)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(result.stdout)
        fh.write(result.stderr)
    if result.returncode not in (0, 1):
        tail = "\n".join(result.stdout.splitlines()[-15:])
        raise SetupError(f"pytest exited {result.returncode} in {copy}\n{tail}")
    failed = sorted({m.group(1) for m in map(_FAILED_LINE.match, result.stdout.splitlines()) if m})
    summary = next((line.strip("= ") for line in reversed(result.stdout.splitlines()) if _SUMMARY_LINE.match(line)), "")
    return result.returncode, failed, summary


def _check(args: argparse.Namespace) -> list[dict]:
    if shutil.which(args.python) is None:
        raise SetupError(f"{args.python} is not an executable interpreter")
    if not args.main_manager.is_file():
        raise SetupError(f"{args.main_manager} is not a file")
    repo_root = args.repo_root.resolve()
    model_core = repo_root / "juniper-model-core"
    args.scratch.mkdir(parents=True, exist_ok=True)
    checkout_manager = repo_root / PACKAGE / MANAGER
    before = _sha256(checkout_manager)
    wanted = None if not args.only else set(args.only.split(","))
    rows = []
    select = args.select.split(",") if args.select else ["tests"]
    for mutant in [None, *MUTANTS]:
        mutant_id = "CONTROL" if mutant is None else mutant.mutant_id
        if wanted is not None and mutant_id not in wanted:
            continue
        work = args.scratch / mutant_id
        copy = _copy_package(repo_root, work)
        try:
            if _sha256(copy / MANAGER) != before:
                raise SetupError(f"{mutant_id}: the copy's {MANAGER} differs from the checkout's before mutation")
            if mutant is not None:
                _apply(copy, mutant, args.main_manager)
            mutated = _sha256(copy / MANAGER)
            env = _env(copy, model_core, work)
            _prove_copy_is_imported(args.python, copy, model_core, env)
            rc, failed, summary = _run_suite(args.python, copy, env, work / "pytest.log", select)
        finally:
            shutil.rmtree(copy, ignore_errors=True)
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
                "killers": [] if mutant is None else list(mutant.killers),
                "killers_missing": missing,
                "verdict": "OK" if ok else "MISMATCH",
            }
        )
        print(f"{mutant_id}\texpected {rows[-1]['expected']}\texit {rc}\t{summary}\tfailed {len(failed)}\t{rows[-1]['verdict']}", flush=True)
    after = _sha256(checkout_manager)
    if after != before:
        raise SetupError(f"the checkout's {MANAGER} changed during the check ({before} -> {after})")
    rows.append({"mutant": "CHECKOUT", "targets": f"the checkout's {MANAGER}, never written", "sha256_before": before, "sha256_after": after, "verdict": "OK"})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--repo-root", required=True, type=Path, help="the juniper-ml checkout holding this change")
    parser.add_argument("--python", required=True, help="an interpreter with juniper-service-core's test dependencies")
    parser.add_argument("--scratch", required=True, type=Path, help="a scratch dir in a repo tmp/, never the system temp dir")
    parser.add_argument("--main-manager", required=True, type=Path, help="lifecycle/manager.py as it is on main")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--only", default="", help="comma-separated mutant ids (CONTROL included) to run; default all")
    parser.add_argument("--select", default="", help="comma-separated pytest paths relative to the package (default: tests)")
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
