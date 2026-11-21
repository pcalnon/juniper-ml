#!/usr/bin/env python3
"""
Validator mutation run on the r32 pause fix: mutants beyond the builder's fifteen, in the validator's own copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (Cursor flood-4 round 2, validator LN1, code lens on the r32 pause fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor carrier r32-pause-fix; builder's 2026-11-15_flood4r2_r32-cascor_mutants.py (M01-M15)

``--tree`` is the validator's own juniper-cascor worktree holding the carrier's files (never the
carrier). Each mutant is a list of exact replacements, each of whose target text must occur exactly
once in ``src/api/lifecycle/manager.py``; the file is restored byte for byte in a ``finally:`` and
checked by sha256 after every mutant. ``__pycache__`` under ``src/`` is deleted before each run, and
every run sets ``PYTHONDONTWRITEBYTECODE=1``, the six Sentry variables to "" and drops
``JUNIPER_CASCOR_LOG_DIR``. The detector is one pytest run over the unit files and the integration
files that touch the pause gate. A control run on the unmutated tree must pass first.

Usage:
  2026-11-15_flood4r2_val_r32-fix-code_mutants.py --tree <own worktree> --out <json file>
Exit: 0 when the control passed and every mutant was restored; the kill count is in the JSON.
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
    "src/tests/unit/api/test_training_route_coverage.py",
    "src/tests/unit/test_remaining_coverage_deep.py",
    "src/tests/integration/api/test_lifecycle_event_invariants.py",
    "src/tests/integration/api/test_pause_stop_actually_interrupts.py",
)
SENTRY = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
NOT_ACTIVE = 'raise RuntimeError("Training is not active")'
START_OPEN = "none can straddle the submit.\n            with self._pause_lock:\n                self._pause_event.set()\n"
SWAP_OPEN = "no pause straddles this submit.\n                with self._pause_lock:\n                    self._pause_event.set()\n"
START_SUBMIT = "stop_event=stop_event, **fit_kwargs)\n"
SWAP_SUBMIT = "                    self._val_y,\n                    stop_event=stop_event,\n                )\n"
CHECK_IN_LOCK = f"        with self._pause_lock:\n            if not self.state_machine.is_started():\n                {NOT_ACTIVE}\n            self._pause_event.clear()\n"
REFUSE = f"                self._pause_event.set()\n                {NOT_ACTIVE}\n            self.training_state.update_state(status=\"Paused\")"
STOP_SETTLE = "                    sm.handle_command(Command.STOP)\n                    # Every settle reopens the gate after its transition (see the docstring).\n                    self._pause_event.set()\n"
COMPLETION_REOPEN = "                    # accepted in between would clear it again and leave it closed.\n                    self._pause_event.set()\n"

MUTANTS = (
    ("N01", "pause's FSM check moves outside the lock (clear + PAUSE stay inside)", ((CHECK_IN_LOCK, f"        if not self.state_machine.is_started():\n            {NOT_ACTIVE}\n        with self._pause_lock:\n            self._pause_event.clear()\n"),)),
    ("N02", "start_training no longer opens the gate", ((START_OPEN, "none can straddle the submit.\n            with self._pause_lock:\n                pass\n"),)),
    ("N03", "the swap's step 12 no longer opens the gate", ((SWAP_OPEN, "no pause straddles this submit.\n                with self._pause_lock:\n                    pass\n"),)),
    ("N04", "start_training opens the gate after its submit, not before", ((START_OPEN, "none can straddle the submit.\n"), (START_SUBMIT, START_SUBMIT + "            with self._pause_lock:\n                self._pause_event.set()\n"))),
    ("N05", "the swap opens the gate after its submit, not before", ((SWAP_OPEN, "no pause straddles this submit.\n"), (SWAP_SUBMIT, SWAP_SUBMIT + "                with self._pause_lock:\n                    self._pause_event.set()\n"))),
    ("N06", "the post-fit stop settle reopens before its STOP", ((STOP_SETTLE, "                    self._pause_event.set()\n                    sm.handle_command(Command.STOP)\n"),)),
    ("N07", "the failure settle reopens before mark_failed", (("                sm.mark_failed(str(e))\n                self._pause_event.set()\n", "                self._pause_event.set()\n                sm.mark_failed(str(e))\n"),)),
    ("N08", "pause writes Paused before its PAUSE", ((f"            self._pause_event.clear()\n            if not self.state_machine.handle_command(Command.PAUSE):\n{REFUSE}", f"            self._pause_event.clear()\n            self.training_state.update_state(status=\"Paused\")\n            if not self.state_machine.handle_command(Command.PAUSE):\n                self._pause_event.set()\n                {NOT_ACTIVE}"),)),
    ("N09", "the completion settle no longer reopens the gate", ((COMPLETION_REOPEN, "                    # accepted in between would clear it again and leave it closed.\n"),)),
    ("N10", "pause clears the gate before its FSM check (a refused check leaves it closed)", ((CHECK_IN_LOCK, f"        with self._pause_lock:\n            self._pause_event.clear()\n            if not self.state_machine.is_started():\n                {NOT_ACTIVE}\n"),)),
    ("N11", "a refused PAUSE raises ValueError (REST no longer maps it to 409)", ((REFUSE, f"                self._pause_event.set()\n                raise ValueError(\"Training is not active\")\n            self.training_state.update_state(status=\"Paused\")"),)),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache(root: Path) -> None:
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _run(tree: Path, env: dict, label: str, out_dir: Path, detector: tuple) -> dict:
    _clear_pycache(tree / "src")
    junit = out_dir / f"junit-{label}.xml"
    argv = [sys.executable, "-m", "pytest", "--integration", "-m", "(unit or integration) and not slow", *detector, "-p", "no:cacheprovider", "--timeout=60", "-q", f"--junitxml={junit}"]
    done = subprocess.run(argv, cwd=tree, env=env, capture_output=True, text=True, check=False, timeout=1200)  # nosec B603 -- fixed argv
    (out_dir / f"{label}.log").write_text(done.stdout + done.stderr, encoding="utf-8")
    failed = [line.split(" ", 1)[1].split(" - ")[0] for line in done.stdout.splitlines() if line.startswith(("FAILED ", "ERROR "))]
    summary = [line for line in done.stdout.splitlines() if " passed" in line or " failed" in line]
    return {"exit": done.returncode, "failed": failed, "summary": summary[-1] if summary else ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", nargs="*", default=None, help="mutant ids to run (default: all)")
    parser.add_argument("--detector", nargs="*", default=None, help="tree-relative test files (default: DETECTOR)")
    args = parser.parse_args()
    tree = args.tree.resolve()
    detector = tuple(args.detector) if args.detector else DETECTOR
    out_dir = args.out.resolve().parent / f"mutant-runs-{args.out.stem}"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = tree / MANAGER
    original = target.read_bytes()
    original_sha = _sha256(target)
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    env.update({name: "" for name in SENTRY})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    report = {"tree": str(tree), "manager_sha256_before": original_sha, "detector": list(detector), "interpreter": sys.executable, "python": sys.version.split()[0], "mutants": []}
    report["control"] = _run(tree, env, "control", out_dir, detector)
    print(json.dumps({"control": report["control"]["summary"], "exit": report["control"]["exit"]}), flush=True)
    restored_all = True
    for mutant_id, what, edits in MUTANTS:
        if args.only and mutant_id not in args.only:
            continue
        text = original.decode("utf-8")
        entry = {"id": mutant_id, "what": what}
        counts = [text.count(old) for old, _new in edits]
        if any(count != 1 for count in counts):
            entry.update({"result": "not applied", "reason": f"target occurrences {counts}"})
            report["mutants"].append(entry)
            print(json.dumps({"id": mutant_id, "result": "not applied", "counts": counts}), flush=True)
            continue
        mutated = text
        for old, new in edits:
            mutated = mutated.replace(old, new, 1)
        try:
            target.write_text(mutated, encoding="utf-8")
            run = _run(tree, env, mutant_id, out_dir, detector)
            entry.update({"result": "killed" if run["exit"] != 0 else "survived", "tests_failed": run["failed"], "summary": run["summary"]})
        finally:
            target.write_bytes(original)
        entry["restored_sha256_ok"] = _sha256(target) == original_sha
        restored_all = restored_all and entry["restored_sha256_ok"]
        report["mutants"].append(entry)
        print(json.dumps({k: entry[k] for k in ("id", "result", "restored_sha256_ok")} | {"n_failed": len(entry.get("tests_failed", []))}), flush=True)
    report["manager_sha256_after"] = _sha256(target)
    report["restored_all"] = restored_all and report["manager_sha256_after"] == original_sha
    report["killed"] = sum(1 for m in report["mutants"] if m.get("result") == "killed")
    report["survived"] = [m["id"] for m in report["mutants"] if m.get("result") == "survived"]
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["control"]["exit"] == 0 and report["restored_all"] else 1


if __name__ == "__main__":
    sys.exit(main())
