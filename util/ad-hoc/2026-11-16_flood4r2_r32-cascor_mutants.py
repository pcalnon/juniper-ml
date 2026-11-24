#!/usr/bin/env python3
"""
Mutation check for the r32 pause carrier after its fix-up: mutate a hermetic COPY of manager.py, one mutant at a time.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 round 2: the Overtoad's rulings of 2026-11-13 and 2026-11-16)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_flood4r2_r32-cascor_mutants.py (round 1, kept unedited); the r32 code lens's
         N04-N07 and N11

The carrier is never touched. ``--copy`` is a directory this script fills with the carrier's ``src/``,
``conf/`` and ``pyproject.toml`` (no ``__pycache__``). Each mutant is one or more exact, single-occurrence
replacements in the copy's ``src/api/lifecycle/manager.py``, applied together and restored byte for byte
in a ``finally:``, with the sha256 checked after every mutant. Stale ``__pycache__`` is deleted before each
run, and every run sets ``PYTHONDONTWRITEBYTECODE=1``, the six Sentry variables to "", a dead session bus,
and drops ``JUNIPER_CASCOR_LOG_DIR``. A control run on the unmutated copy must pass first.

Usage:
  2026-11-16_flood4r2_r32-cascor_mutants.py --carrier <fix worktree> --copy <fresh dir> --out <json file> [--only M01,M02]
Exit: 0 when the control passed, every mutant applied and was restored, and every mutant was killed; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- fixed-argv pytest runs
import sys
from pathlib import Path

MANAGER = Path("src/api/lifecycle/manager.py")
DETECTOR = (
    "src/tests/unit/api/test_lifecycle_pause_check_then_act.py",
    "src/tests/unit/api/test_lifecycle_stop_then_start.py",
    "src/tests/unit/api/test_lifecycle_paused_fit_return.py",
    "src/tests/unit/api/test_lifecycle_manager.py",
    "src/tests/unit/api/test_lifecycle_manager_coverage_ext.py",
)
SENTRY = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
NOT_ACTIVE = 'raise RuntimeError("Training is not active")'
NOT_PAUSED = 'raise RuntimeError("Training is not paused")'
PAUSE_CHECK = "            if not self.state_machine.is_started() or self._lifecycle_stop_event.is_set():"
START_OPEN = "preceded this open can close the gate after it.\n            with self._pause_lock:\n                self._pause_event.set()\n"
START_SUBMIT = "            self._training_future = self._executor.submit(self._run_training, self._train_x, self._train_y, self._val_x, self._val_y, stop_event=stop_event, **fit_kwargs)\n"
SWAP_OPEN = "its stop is raised (``_lifecycle_stop_event``).\n                with self._pause_lock:\n                    self._pause_event.set()\n"
SWAP_SUBMIT = "                    stop_event=stop_event,\n                )\n"
RECORD = "        # Recorded before the START below, so a pause that finds this run STARTED reads its signal.\n        self._lifecycle_stop_event = stop_event\n"
RESUME_ACT = f'            if not self.state_machine.handle_command(Command.RESUME):\n                {NOT_PAUSED}\n            self.training_state.update_state(status="Started")'

MUTANTS = (
    # Round 1's fifteen, re-anchored on the fixed-up text.
    ("M01", "pause_training takes a private lock (no exclusion)", [(f"        with self._pause_lock:\n{PAUSE_CHECK}", f"        with threading.Lock():\n{PAUSE_CHECK}")]),
    ("M02", "a refused PAUSE does not reopen the gate", [(f"            if not self.state_machine.handle_command(Command.PAUSE):\n                self._pause_event.set()\n                {NOT_ACTIVE}", f"            if not self.state_machine.handle_command(Command.PAUSE):\n                {NOT_ACTIVE}")]),
    ("M03", "a refused PAUSE still answers paused (the gate reopened)", [(f'                self._pause_event.set()\n                {NOT_ACTIVE}\n            self.training_state.update_state(status="Paused")', '                self._pause_event.set()\n            self.training_state.update_state(status="Paused")')]),
    ("M04", "PAUSE's answer is ignored again", [("            if not self.state_machine.handle_command(Command.PAUSE):", "            if not (self.state_machine.handle_command(Command.PAUSE) or True):")]),
    ("M05", "the Paused write moves outside the lock", [('            self.training_state.update_state(status="Paused")\n        self._broadcast_training_state(force=True)', '        self.training_state.update_state(status="Paused")\n        self._broadcast_training_state(force=True)')]),
    ("M06", "resume_training takes a private lock (no exclusion)", [("        with self._pause_lock:\n            if not self.state_machine.is_paused():", "        with threading.Lock():\n            if not self.state_machine.is_paused():")]),
    ("M07", "start_training opens the gate without the lock", [(START_OPEN, START_OPEN.replace("with self._pause_lock:", "with threading.Lock():"))]),
    ("M08", "the live swap opens the gate without the lock", [(SWAP_OPEN, SWAP_OPEN.replace("with self._pause_lock:", "with threading.Lock():"))]),
    ("M09", "the post-fit stop settle does not reopen the gate", [("                    # Every settle reopens the gate after its transition (see the docstring).\n                    self._pause_event.set()\n", "                    # Every settle reopens the gate after its transition (see the docstring).\n")]),
    ("M10", "the interrupted settle does not reopen the gate", [('                sm.handle_command(Command.STOP)\n                self._pause_event.set()\n                state.update_state(status="Stopped", phase="Idle")', '                sm.handle_command(Command.STOP)\n                state.update_state(status="Stopped", phase="Idle")')]),
    ("M11", "the failure settle does not reopen the gate", [("                sm.mark_failed(str(e))\n                self._pause_event.set()\n", "                sm.mark_failed(str(e))\n")]),
    ("M12", "the interrupted settle reopens before its transition", [('                sm.handle_command(Command.STOP)\n                self._pause_event.set()\n                state.update_state(status="Stopped", phase="Idle")', '                self._pause_event.set()\n                sm.handle_command(Command.STOP)\n                state.update_state(status="Stopped", phase="Idle")')]),
    ("M13", "the post-fit stop settle also reopens outside the ownership guard", [('            if stop_event.is_set():\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):', '            if stop_event.is_set():\n                self._pause_event.set()\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):')]),
    ("M14", "the interrupted settle also reopens outside the ownership guard", [('            if self._owns_lifecycle(run_token, "was interrupted"):', '            self._pause_event.set()\n            if self._owns_lifecycle(run_token, "was interrupted"):')]),
    ("M15", "the failure settle also reopens outside the ownership guard", [('            if self._owns_lifecycle(run_token, "failed"):', '            self._pause_event.set()\n            if self._owns_lifecycle(run_token, "failed"):')]),
    # The Overtoad's ruling of 2026-11-16, "Refuse it: 409": a pause is refused while the Overtoad's stop is raised.
    ("M16", "pause_training ignores the lifecycle owner's raised stop", [(PAUSE_CHECK, "            if not self.state_machine.is_started():")]),
    ("M17", "_run_training does not record its stop signal as the lifecycle's", [(RECORD, "")]),
    ("M18", "_run_training records its stop signal only after its START", [(RECORD, ""), ("        sm.handle_command(Command.START)\n", "        sm.handle_command(Command.START)\n        self._lifecycle_stop_event = stop_event\n")]),
    # "Wider fix + resume 409": a resume whose RESUME is refused is refused and writes nothing.
    ("M19", "resume_training ignores RESUME's answer again", [(RESUME_ACT, '            self.state_machine.handle_command(Command.RESUME)\n            self.training_state.update_state(status="Started")')]),
    ("M20", "a refused RESUME still writes Started before it is refused", [(RESUME_ACT, f'            accepted = self.state_machine.handle_command(Command.RESUME)\n            self.training_state.update_state(status="Started")\n            if not accepted:\n                {NOT_PAUSED}')]),
    ("M21", "a refused RESUME raises ValueError (a REST 400)", [(RESUME_ACT, RESUME_ACT.replace(NOT_PAUSED, 'raise ValueError("Training is not paused")'))]),
    # The code lens's surviving mutants, which its proposed tests (now folded in) target.
    ("N04", "start_training opens the gate after its submit", [(START_OPEN, "preceded this open can close the gate after it.\n"), (START_SUBMIT, START_SUBMIT + "            with self._pause_lock:\n                self._pause_event.set()\n")]),
    ("N05", "the live swap opens the gate after its submit", [(SWAP_OPEN, "its stop is raised (``_lifecycle_stop_event``).\n"), (SWAP_SUBMIT, SWAP_SUBMIT + "                with self._pause_lock:\n                    self._pause_event.set()\n")]),
    ("N06", "the post-fit stop settle reopens before its STOP", [("                    sm.handle_command(Command.STOP)\n                    # Every settle reopens the gate after its transition (see the docstring).\n                    self._pause_event.set()\n", "                    self._pause_event.set()\n                    sm.handle_command(Command.STOP)\n")]),
    ("N07", "the failure settle reopens before mark_failed", [("                sm.mark_failed(str(e))\n                self._pause_event.set()\n", "                self._pause_event.set()\n                sm.mark_failed(str(e))\n")]),
    ("N11", "a refused PAUSE raises ValueError (a REST 400)", [(f"                self._pause_event.set()\n                {NOT_ACTIVE}", '                self._pause_event.set()\n                raise ValueError("Training is not active")')]),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache(root: Path) -> None:
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _run(copy: Path, env: dict, label: str, out_dir: Path) -> dict:
    _clear_pycache(copy / "src")
    junit = out_dir / f"junit-{label}.xml"
    argv = [sys.executable, "-m", "pytest", *DETECTOR, "-p", "no:cacheprovider", "-m", "unit and not slow", "--timeout=60", "-q", "-rf", f"--junitxml={junit}"]
    done = subprocess.run(argv, cwd=copy, env=env, capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
    (out_dir / f"{label}.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    failed = [line.split(" ", 1)[1].split(" - ")[0] for line in done.stdout.splitlines() if line.startswith(("FAILED ", "ERROR "))]
    return {"exit": done.returncode, "failed": failed}


def _apply(text: str, edits: list) -> tuple:
    """Apply every (old, new) pair; return (new text, None) or (None, reason) when an old is not there exactly once."""
    for old, new in edits:
        count = text.count(old)
        if count != 1:
            return None, f"{count} occurrences of {old[:60]!r}"
        text = text.replace(old, new, 1)
    return text, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    only = {item for item in args.only.split(",") if item}
    carrier = args.carrier.resolve()
    copy = args.copy.resolve()
    if copy.exists():
        shutil.rmtree(copy)
    copy.mkdir(parents=True)
    shutil.copytree(carrier / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__", "reports"))
    shutil.copytree(carrier / "conf", copy / "conf", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(carrier / "pyproject.toml", copy / "pyproject.toml")
    out_dir = args.out.resolve().parent / (args.out.stem + "-runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = copy / MANAGER
    original = target.read_bytes()
    original_sha = _sha256(target)
    carrier_sha = _sha256(carrier / MANAGER)
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    env.update({name: "" for name in SENTRY})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    report = {"carrier_manager_sha256": carrier_sha, "copy_manager_sha256": original_sha, "detector": list(DETECTOR), "interpreter": sys.executable, "python": sys.version.split()[0], "mutants": []}
    report["control"] = _run(copy, env, "control", out_dir)
    ok = report["control"]["exit"] == 0
    print(json.dumps({"control_exit": report["control"]["exit"]}), flush=True)
    for mutant_id, what, edits in MUTANTS:
        if only and mutant_id not in only:
            continue
        entry = {"id": mutant_id, "what": what}
        mutated, reason = _apply(original.decode("utf-8"), edits)
        if mutated is None:
            entry.update({"result": "not applied", "reason": reason})
            report["mutants"].append(entry)
            ok = False
            print(json.dumps(entry), flush=True)
            continue
        try:
            target.write_text(mutated, encoding="utf-8")
            run = _run(copy, env, mutant_id, out_dir)
            entry.update({"result": "killed" if run["exit"] != 0 else "survived", "tests_failed": run["failed"]})
        finally:
            target.write_bytes(original)
        entry["restored_sha256_ok"] = _sha256(target) == original_sha
        ok = ok and entry["restored_sha256_ok"] and entry["result"] == "killed"
        report["mutants"].append(entry)
        print(json.dumps({k: entry[k] for k in ("id", "result", "restored_sha256_ok")} | {"n_failed": len(entry.get("tests_failed", []))}), flush=True)
    report["copy_manager_sha256_after"] = _sha256(target)
    report["carrier_manager_sha256_after"] = _sha256(carrier / MANAGER)
    report["carrier_untouched"] = report["carrier_manager_sha256_after"] == carrier_sha
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if ok and report["carrier_untouched"] else 1


if __name__ == "__main__":
    sys.exit(main())
