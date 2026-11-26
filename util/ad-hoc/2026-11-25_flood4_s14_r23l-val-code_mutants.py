"""
Mutation check of carrier r23l's lifecycle/manager.py: does the suite kill each mutant of the fix?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23l-val-code: independent validation of carrier r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 19, 23);
         juniper-ml#2557 (N-2)

Each row copies the whole juniper-service-core directory (package, tests, pyproject.toml) to its own scratch
directory, applies exact (old, new) replacements to the copy's lifecycle/manager.py (each ``old`` must occur
exactly once), and runs the chosen test files there with the venv's ``pytest`` script, cwd and PYTHONPATH both
the copy, so the package the tests import is the copy (each row records the file it resolved and its sha256).
The source directory is only read: its manager.py sha256 is recorded before and after. ``main`` swaps in a
given manager.py (main's) instead of mutating. Up to ``--jobs`` rows run at once (at most 4).

Usage: python <this file> --source-dir <clone>/juniper-service-core --python <venv>/bin/python --scratch DIR
       --json-out FILE [--main-manager FILE] [--tests tests/a.py,tests/b.py | --whole-suite] [--only m1,m2] [--jobs N]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MANAGER = Path("juniper_service_core/lifecycle/manager.py")
LOAD_GUARD = '            raise RuntimeError("Cannot load a snapshot while training is active")\n'
ATTACH_GUARD = '            raise RuntimeError("Cannot attach a model while training is active")\n'
CALL = "        self._refuse_while_a_stopped_fit_runs()\n"
LOAD = "        model, sidecar = store.load(snapshot_id)  # raises SnapshotNotFoundError if absent\n"
TEARDOWN = "        self._teardown_replay()\n"
COND = "if previous is not None and previous.is_alive() and self._stop_event.is_set():"
START_HEAD = '        with self._lock:\n            if self.model is None:\n                raise RuntimeError("No model attached")\n            if self.state_machine.is_active():\n                raise RuntimeError("Training already in progress")\n'

# name -> (what it does, expectation, [(old, new), ...])
MUTANTS: dict[str, tuple[str, str, list[tuple[str, str]]]] = {
    "m01-load-refusal-removed": ("main's behaviour for the four loads", "killed", [(LOAD_GUARD + CALL, LOAD_GUARD)]),
    "m02-attach-refusal-removed": ("main's behaviour for attach_model", "killed", [(ATTACH_GUARD + "    " + CALL, ATTACH_GUARD)]),
    "m03-start-refusal-removed": ("N-2's own site dropped", "killed", [("    " + CALL + "            self._train_x, self._train_y = X, y\n", "            self._train_x, self._train_y = X, y\n")]),
    "m04-teardown-removed": ("main's behaviour: a load leaves the session", "killed", [(LOAD + TEARDOWN, LOAD)]),
    "m05-teardown-before-store-load": ("a load that fails (unknown id) ends the session", "killed", [(CALL + LOAD + TEARDOWN, CALL + TEARDOWN + LOAD)]),
    "m06-teardown-before-the-refusals": ("a refused or failed load ends the session", "killed", [("        store = self._require_snapshots()\n        if self.state_machine.is_active():\n", "        store = self._require_snapshots()\n" + TEARDOWN + "        if self.state_machine.is_active():\n")]),
    "m07-load-refusal-after-store-load": ("in the window an unknown id answers 404, not the documented 409", "killed?", [(CALL + LOAD, LOAD + CALL)]),
    "m08-stop-replay-relabels-in-any-state": (
        "main's behaviour for stop_replay's relabel",
        "killed",
        [('                self.state_machine.handle_command(LifecycleCommand.RESET)\n                self.monitor.set_run_context(status="stopped", phase="idle")\n            return self._status_dict()\n\n    def get_replay_state', '                self.state_machine.handle_command(LifecycleCommand.RESET)\n            self.monitor.set_run_context(status="stopped", phase="idle")\n            return self._status_dict()\n\n    def get_replay_state')],
    ),
    "m09-stop-replay-resets-in-any-state": ("stop_replay resets and relabels whatever the machine reads", "killed", [("            self._teardown_replay()\n            if self.state_machine.is_replaying():\n                self.state_machine.handle_command(LifecycleCommand.RESET)\n                self.monitor", "            self._teardown_replay()\n            if True:\n                self.state_machine.handle_command(LifecycleCommand.RESET)\n                self.monitor")]),
    "m10-helper-ignores-liveness": ("a dead thread with its stop set holds everything back", "killed", [(COND, "if previous is not None and self._stop_event.is_set():")]),
    "m11-helper-ignores-the-stop": ("any live thread holds everything back, settled or not", "killed", [(COND, "if previous is not None and previous.is_alive():")]),
    "m12-helper-alive-or-stop": ("and -> or", "killed", [(COND, "if previous is not None and (previous.is_alive() or self._stop_event.is_set()):")]),
    "m13-helper-only-when-STOPPED": ("refusal limited to a machine reading STOPPED", "killed", [(COND, "if previous is not None and previous.is_alive() and self._stop_event.is_set() and self.state_machine.is_stopped():")]),
    "m14-teardown-drops-without-stopping": ("the session is dropped but its daemon keeps running", "killed", [(LOAD + TEARDOWN, LOAD + "        self._replay_session = None\n")]),
    "m15-start-replay-second-teardown-removed": ("start_replay's own teardown (now redundant) dropped", "equivalent", [("            sidecar = self._load_snapshot_model(snapshot_id)\n            self._teardown_replay()\n", "            sidecar = self._load_snapshot_model(snapshot_id)\n")]),
    "m16-attach-refusal-after-the-model-is-set": ("attach replaces the model, then refuses", "killed", [("    " + CALL + "            self.model = model\n", "            self.model = model\n    " + CALL)]),
    "m17-load-refusal-after-the-model-is-set": ("a load attaches the snapshot's model and ends the session, then refuses", "killed", [(CALL + LOAD + TEARDOWN + "        self.model = model\n", LOAD + TEARDOWN + "        self.model = model\n" + CALL)]),
    "m18-start-check-outside-the-lock": ("N-2's check moved before the lock (check-then-act)", "survives-known", [(START_HEAD, CALL + START_HEAD), ("    " + CALL + "            self._train_x, self._train_y = X, y\n", "            self._train_x, self._train_y = X, y\n")]),
    "m19-load-snapshot-unlocked": ("load_snapshot's body runs without the manager lock", "survives-known", [('        with self._lock:\n            sidecar = self._load_snapshot_model(snapshot_id)\n            self.monitor.restore(sidecar.get("history", []), status="investigating", phase="idle")\n', '        if True:\n            sidecar = self._load_snapshot_model(snapshot_id)\n            self.monitor.restore(sidecar.get("history", []), status="investigating", phase="idle")\n')]),
    "m20-load-refusal-before-the-active-check": ("the stopped-fit check precedes is_active() in the load core", "equivalent?", [('        store = self._require_snapshots()\n        if self.state_machine.is_active():\n            raise RuntimeError("Cannot load a snapshot while training is active")\n' + CALL, "        store = self._require_snapshots()\n" + CALL + '        if self.state_machine.is_active():\n            raise RuntimeError("Cannot load a snapshot while training is active")\n')]),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_row(name: str, args: argparse.Namespace, tests: list[str]) -> dict:
    row_dir = Path(args.scratch) / name
    if row_dir.exists():
        shutil.rmtree(row_dir)
    shutil.copytree(args.source_dir, row_dir, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.egg-info", "build", "dist"))
    target = row_dir / MANAGER
    text = target.read_text(encoding="utf-8")
    applied = []
    if name == "control":
        what, expect = "the carrier's manager.py, unmutated", "passes"
    elif name == "main":
        shutil.copyfile(args.main_manager, target)
        what, expect = "main's manager.py with the carrier's tests", "fails"
    else:
        what, expect, pairs = MUTANTS[name]
        for old, new in pairs:
            count = text.count(old)
            if count != 1:
                return {"name": name, "error": f"old text occurs {count} times", "old": old}
            text = text.replace(old, new)
            applied.append({"old": old, "new": new})
        target.write_text(text, encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(row_dir)
    env.pop("PYTHONSAFEPATH", None)
    resolved = subprocess.run([args.python, "-c", "import hashlib, juniper_service_core.lifecycle.manager as m; print(m.__file__); print(hashlib.sha256(open(m.__file__, 'rb').read()).hexdigest())"], cwd=row_dir, env=env, capture_output=True, text=True, check=False)
    pytest = str(Path(args.python).with_name("pytest"))
    junit = row_dir / "junit.xml"
    cmd = [pytest, "-p", "no:cacheprovider", f"--junitxml={junit}", f"--basetemp={row_dir / 'basetemp'}", *tests]
    proc = subprocess.run(cmd, cwd=row_dir, env=env, capture_output=True, text=True, check=False, timeout=1800)
    (row_dir / "pytest.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    failed, passed, errors = [], 0, []
    if junit.is_file():
        for case in ET.parse(junit).getroot().iter("testcase"):
            ident = f"{case.get('classname')}::{case.get('name')}"
            if case.find("failure") is not None:
                failed.append(ident)
            elif case.find("error") is not None:
                errors.append(ident)
            elif case.find("skipped") is None:
                passed += 1
    summary = re.findall(r"=+ (.*?) in [0-9.]+s", proc.stdout)
    return {
        "name": name,
        "what": what,
        "expect": expect,
        "applied": applied,
        "manager_sha256": sha(target),
        "resolved": resolved.stdout.split(),
        "exit": proc.returncode,
        "summary": summary[-1] if summary else proc.stdout[-300:],
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "killed": bool(failed or errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--main-manager")
    parser.add_argument("--tests", default="tests/test_lifecycle_stop_then_start.py,tests/test_lifecycle_stop_then_load.py,tests/test_lifecycle_leftover_replay_session.py,tests/test_lifecycle_paused_fit_return.py")
    parser.add_argument("--whole-suite", action="store_true")
    parser.add_argument("--only", default="")
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    jobs = max(1, min(args.jobs, 4))
    tests = ["tests"] if args.whole_suite else args.tests.split(",")
    names = ["control"] + (["main"] if args.main_manager else []) + list(MUTANTS)
    if args.only:
        names = [n for n in names if n in set(args.only.split(","))]
    source_manager = Path(args.source_dir) / MANAGER
    before = sha(source_manager)
    Path(args.scratch).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        rows = list(pool.map(lambda n: run_row(n, args, tests), names))
    after = sha(source_manager)
    out = {"python": args.python, "tests": tests, "source_manager_sha256_before": before, "source_manager_sha256_after": after, "rows": rows}
    Path(args.json_out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    for row in rows:
        if "error" in row:
            print(f"{row['name']:44} ERROR {row['error']}")
            continue
        print(f"{row['name']:44} expect={row['expect']:15} killed={row['killed']!s:5} failed={len(row['failed']):3} errors={len(row['errors'])} passed={row['passed']:4} resolved={row['resolved'][0] if row['resolved'] else '?'}")
    print(f"source manager.py sha256 before {before} after {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
