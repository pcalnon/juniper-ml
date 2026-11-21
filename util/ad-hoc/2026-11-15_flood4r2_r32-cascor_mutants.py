#!/usr/bin/env python3
"""
Mutation check for the r32 pause carrier: mutate a hermetic COPY of the fix's manager.py, one change at a time.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (Cursor flood-4 round 2: the Overtoad's ruling of 2026-11-13, "Fix it + document")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor carrier r32-pause-fix (pause_training's check-then-act, and the gate a settle leaves closed)

The carrier is never touched. ``--copy`` is a directory this script fills with the carrier's ``src/``,
``conf/`` and ``pyproject.toml`` (no ``__pycache__``); each mutant is one exact, single-occurrence
replacement in the copy's ``src/api/lifecycle/manager.py``, which is restored byte for byte in a
``finally:`` and checked by sha256 after every mutant. Stale ``__pycache__`` is deleted before each run,
and every run sets ``PYTHONDONTWRITEBYTECODE=1``, the six Sentry variables to "" and drops
``JUNIPER_CASCOR_LOG_DIR``. A control run on the unmutated copy must pass first.

Usage:
  2026-11-15_flood4r2_r32-cascor_mutants.py --carrier <fix worktree> --copy <fresh dir> --out <json file>
Exit: 0 when the control passed, every mutant was restored, and every mutant was killed; 1 otherwise.
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

MUTANTS = (
    ("M01", "pause_training takes a private lock (no exclusion)", '        with self._pause_lock:\n            if not self.state_machine.is_started():', '        with threading.Lock():\n            if not self.state_machine.is_started():'),
    ("M02", "a refused PAUSE does not reopen the gate", f"            if not self.state_machine.handle_command(Command.PAUSE):\n                self._pause_event.set()\n                {NOT_ACTIVE}", f"            if not self.state_machine.handle_command(Command.PAUSE):\n                {NOT_ACTIVE}"),
    ("M03", "a refused PAUSE still answers paused (the gate reopened)", f'                self._pause_event.set()\n                {NOT_ACTIVE}\n            self.training_state.update_state(status="Paused")', '                self._pause_event.set()\n            self.training_state.update_state(status="Paused")'),
    ("M04", "PAUSE's answer is ignored again", "            if not self.state_machine.handle_command(Command.PAUSE):", "            if not (self.state_machine.handle_command(Command.PAUSE) or True):"),
    ("M05", "the Paused write moves outside the lock", '            self.training_state.update_state(status="Paused")\n        self._broadcast_training_state(force=True)', '        self.training_state.update_state(status="Paused")\n        self._broadcast_training_state(force=True)'),
    ("M06", "resume_training takes a private lock (no exclusion)", "        with self._pause_lock:\n            if not self.state_machine.is_paused():", "        with threading.Lock():\n            if not self.state_machine.is_paused():"),
    ("M07", "start_training opens the gate without the lock", "none can straddle the submit.\n            with self._pause_lock:\n                self._pause_event.set()", "none can straddle the submit.\n            with threading.Lock():\n                self._pause_event.set()"),
    ("M08", "the live swap opens the gate without the lock", "no pause straddles this submit.\n                with self._pause_lock:\n                    self._pause_event.set()", "no pause straddles this submit.\n                with threading.Lock():\n                    self._pause_event.set()"),
    ("M09", "the post-fit stop settle does not reopen the gate", "                    # Every settle reopens the gate after its transition (see the docstring).\n                    self._pause_event.set()\n", "                    # Every settle reopens the gate after its transition (see the docstring).\n"),
    ("M10", "the interrupted settle does not reopen the gate", '                sm.handle_command(Command.STOP)\n                self._pause_event.set()\n                state.update_state(status="Stopped", phase="Idle")', '                sm.handle_command(Command.STOP)\n                state.update_state(status="Stopped", phase="Idle")'),
    ("M11", "the failure settle does not reopen the gate", "                sm.mark_failed(str(e))\n                self._pause_event.set()\n", "                sm.mark_failed(str(e))\n"),
    ("M12", "the interrupted settle reopens before its transition", '                sm.handle_command(Command.STOP)\n                self._pause_event.set()\n                state.update_state(status="Stopped", phase="Idle")', '                self._pause_event.set()\n                sm.handle_command(Command.STOP)\n                state.update_state(status="Stopped", phase="Idle")'),
    ("M13", "the post-fit stop settle also reopens outside the Overtoadship guard", '            if stop_event.is_set():\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):', '            if stop_event.is_set():\n                self._pause_event.set()\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):'),
    ("M14", "the interrupted settle also reopens outside the Overtoadship guard", '            if self._owns_lifecycle(run_token, "was interrupted"):', '            self._pause_event.set()\n            if self._owns_lifecycle(run_token, "was interrupted"):'),
    ("M15", "the failure settle also reopens outside the Overtoadship guard", '            if self._owns_lifecycle(run_token, "failed"):', '            self._pause_event.set()\n            if self._owns_lifecycle(run_token, "failed"):'),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache(root: Path) -> None:
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _run(copy: Path, env: dict, label: str, out_dir: Path) -> dict:
    _clear_pycache(copy / "src")
    junit = out_dir / f"junit-{label}.xml"
    argv = [sys.executable, "-m", "pytest", *DETECTOR, "-p", "no:cacheprovider", "-m", "unit and not slow", "--timeout=60", "-q", f"--junitxml={junit}"]
    done = subprocess.run(argv, cwd=copy, env=env, capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
    (out_dir / f"{label}.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    failed = [line.split(" ", 1)[1].split(" - ")[0] for line in done.stdout.splitlines() if line.startswith(("FAILED ", "ERROR "))]
    summary = [line for line in done.stdout.splitlines() if " passed" in line or " failed" in line]
    return {"exit": done.returncode, "failed": failed, "summary": summary[-1] if summary else ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    carrier = args.carrier.resolve()
    copy = args.copy.resolve()
    if copy.exists():
        shutil.rmtree(copy)
    copy.mkdir(parents=True)
    shutil.copytree(carrier / "src", copy / "src", ignore=shutil.ignore_patterns("__pycache__", "reports"))
    shutil.copytree(carrier / "conf", copy / "conf", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(carrier / "pyproject.toml", copy / "pyproject.toml")
    out_dir = args.out.resolve().parent / "mutant-runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = copy / MANAGER
    original = target.read_bytes()
    original_sha = _sha256(target)
    carrier_sha = _sha256(carrier / MANAGER)
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    env.update({name: "" for name in SENTRY})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    report = {"carrier_manager_sha256": carrier_sha, "copy_manager_sha256": original_sha, "detector": list(DETECTOR), "interpreter": sys.executable, "python": sys.version.split()[0], "mutants": []}
    report["control"] = _run(copy, env, "control", out_dir)
    ok = report["control"]["exit"] == 0
    for mutant_id, what, old, new in MUTANTS:
        text = original.decode("utf-8")
        entry = {"id": mutant_id, "what": what}
        count = text.count(old)
        if count != 1:
            entry.update({"result": "not applied", "reason": f"{count} occurrences of the target text"})
            report["mutants"].append(entry)
            ok = False
            continue
        try:
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            run = _run(copy, env, mutant_id, out_dir)
            entry.update({"result": "killed" if run["exit"] != 0 else "survived", "tests_failed": run["failed"], "summary": run["summary"]})
        finally:
            target.write_bytes(original)
        entry["restored_sha256_ok"] = _sha256(target) == original_sha
        ok = ok and entry["restored_sha256_ok"] and entry["result"] == "killed"
        report["mutants"].append(entry)
        print(json.dumps({k: entry[k] for k in ("id", "result", "restored_sha256_ok")} | {"n_failed": len(entry.get("tests_failed", []))}), flush=True)
    report["carrier_manager_sha256_after"] = _sha256(carrier / MANAGER)
    report["carrier_untouched"] = report["carrier_manager_sha256_after"] == carrier_sha
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if ok and report["carrier_untouched"] else 1


if __name__ == "__main__":
    sys.exit(main())
