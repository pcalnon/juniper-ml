#!/usr/bin/env python3
"""
Mutation-check juniper-cascor's stop-then-start fix, and re-check the paused-fit fix's mutants, in hermetic copies.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 12; adapted from juniper-cascor
         util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py (juniper-cascor#753)

Each run copies the checkout's ``src/``, ``conf/`` and ``pyproject.toml`` into a fresh directory
under ``--scratch`` (never the system temp directory, and never a juniper-ml ``tmp/``: the copy
carries a ``[project]`` pyproject), applies one mutant there, and runs the detector with
``-m "unit and not slow"``. The checkout is never edited: its ``manager.py`` sha256 is recorded
before and after the campaign and must match. No ``__pycache__`` is copied and
``PYTHONDONTWRITEBYTECODE=1`` is set, so no stale ``.pyc`` can answer for a mutant. A one-function
plugin prints the ``__file__`` pytest resolved for ``api.lifecycle.manager``; a run that did not
import the mutated copy counts as NO-PROOF, never as a catch. Exit codes are read from the
subprocess, failures from the JUnit file.

Groups:
  main  -- the checkout with ``manager.py`` replaced by ``--main-ref``'s: which new tests fail on main.
  fix   -- the control (unmutated), then each of this fix's mutants S01..S13 against the new module.
  n1    -- juniper-cascor#753's own mutants (its script's MUTATIONS list, M01..M31; M00, the base
           revert, is skipped), each against #753's two test files plus the new module, and, with
           ``--n1-alone``, against #753's two files alone too.

Usage:
  2026-11-09_flood4r2_r17-cascor_mutants.py --tree <cascor checkout> --scratch <dir> --out <dir>
      [--main-ref origin/main] [--groups main,fix,n1] [--n1-alone] [--workers 4]
Exit: 0 when the controls are green, every fix mutant is caught, every n1 mutant is caught by the
extended detector, and the checkout's manager.py is unchanged; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 -- fixed-argv pytest and git runs
import sys
import tempfile
import xml.etree.ElementTree as ET  # nosec B405 -- parses the JUnit files these runs write
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MANAGER = "src/api/lifecycle/manager.py"
NEW_TESTS = "src/tests/unit/api/test_lifecycle_stop_then_start.py"
N1_TESTS = ("src/tests/unit/api/test_lifecycle_paused_fit_return.py", "src/tests/unit/api/test_lifecycle_state_machine.py")
N1_SCRIPT = "util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py"
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "logs", "reports")
PLUGIN = "_r17_mutant_provenance"
PLUGIN_SOURCE = """import sys


def pytest_sessionfinish(session, exitstatus):
    module = sys.modules.get("api.lifecycle.manager")
    print("\\nPROVENANCE " + str(getattr(module, "__file__", None)))
"""

_HELPER_BODY = "        if self._stop_event.is_set():\n            self._stop_event = threading.Event()\n        return self._stop_event\n"
_SWAP_SIGNAL = "                stop_event = self._stop_event_for_new_run_locked()\n                self._pause_event.set()\n"
_EPOCH_CHECKPOINT = "            # Was _output_training_callback (bound to network._output_epoch_callback).\n            self._check_for_interrupt(stop_event)\n"
_PHASE_CHECKPOINT = "            # CCN's coarse event types would otherwise drop (plan §3.3 — extend the payload).\n            self._check_for_interrupt(stop_event)\n"
_POST_FIT_CHECK = '            if stop_event.is_set():\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):\n'
_STOP_ORDER = "        self._stop_event.set()\n        transitioned = self.state_machine.handle_command(Command.STOP)\n"

# (id, description, [(old, new), ...] in manager.py) -- each ``old`` must occur exactly once.
FIX_MUTANTS = [
    ("S01", "a start clears the shared signal again (main's behaviour)", [(_HELPER_BODY, "        self._stop_event.clear()\n        return self._stop_event\n")]),
    ("S02", "every start gets a fresh signal, even when none was raised", [(_HELPER_BODY, "        self._stop_event = threading.Event()\n        return self._stop_event\n")]),
    ("S03", "a start never replaces a raised signal: the new run shares it", [(_HELPER_BODY, "        return self._stop_event\n")]),
    ("S04", "a run reads the newest signal as it enters, not the one it was accepted with", [("        stop_event = self._stop_event if stop_event is None else stop_event\n", "        stop_event = self._stop_event\n")]),
    ("S05", "the fit's sink reads the newest signal (on_event=self._handle_event)", [("on_event=lambda event: self._handle_event(event, stop_event)", "on_event=self._handle_event")]),
    ("S06", "_check_for_interrupt ignores the run's signal", [("        stop = self._stop_event if stop_event is None else stop_event\n", "        stop = self._stop_event\n")]),
    ("S07", "the epoch_end checkpoint reads the newest signal", [(_EPOCH_CHECKPOINT, _EPOCH_CHECKPOINT.replace("(stop_event)", "()"))]),
    ("S08", "the phase_change checkpoint reads the newest signal", [(_PHASE_CHECKPOINT, _PHASE_CHECKPOINT.replace("(stop_event)", "()"))]),
    ("S09", "the post-fit stop check reads the newest signal", [(_POST_FIT_CHECK, _POST_FIT_CHECK.replace("if stop_event.is_set():", "if self._stop_event.is_set():"))]),
    ("S10", "start_training submits the run without its signal", [("self._val_y, stop_event=stop_event, **fit_kwargs)", "self._val_y, **fit_kwargs)")]),
    ("S11", "the live swap clears the shared signal again", [(_SWAP_SIGNAL, "                self._stop_event.clear()\n                stop_event = self._stop_event\n                self._pause_event.set()\n")]),
    ("S12", "the live swap submits the run without its signal", [("                    self._val_y,\n                    stop_event=stop_event,\n                )", "                    self._val_y,\n                )")]),
    ("S13", "stop_training raises the signal after the FSM transition", [(_STOP_ORDER, "        transitioned = self.state_machine.handle_command(Command.STOP)\n        self._stop_event.set()\n")]),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _apply(sources: dict, edits: list) -> tuple:
    """Apply (file, old, new) edits in order; return (texts, error or None)."""
    texts = dict(sources)
    for relative, old, new in edits:
        count = texts[relative].count(old)
        if count != 1:
            return texts, f"anchor in {relative} occurs {count} times, expected 1: {old[:80]!r}"
        texts[relative] = texts[relative].replace(old, new)
    return texts, None


def _failures(junit: Path) -> tuple:
    if not junit.exists():
        return None, []
    root = ET.parse(junit).getroot()  # nosec B314 -- our own pytest output
    total, failing = 0, []
    for case in root.iter("testcase"):
        total += 1
        if case.find("failure") is not None or case.find("error") is not None:
            failing.append(f"{case.get('classname', '').rsplit('.', 1)[-1]}::{case.get('name')}")
    return total, failing


def _run(tree_root: Path, scratch: Path, out: Path, run_id: str, replacements: dict, tests: tuple) -> dict:
    """Build a hermetic copy with ``replacements`` (path -> text) and run ``tests`` there."""
    with tempfile.TemporaryDirectory(prefix=f"r17-{run_id}-", dir=scratch) as tmp:
        tree = Path(tmp)
        for name in ("src", "conf"):
            shutil.copytree(tree_root / name, tree / name, ignore=IGNORED)
        shutil.copy2(tree_root / "pyproject.toml", tree / "pyproject.toml")
        digests = {}
        for relative, text in replacements.items():
            (tree / relative).write_text(text, encoding="utf-8")
            digests[relative] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        (tree / "_plugins").mkdir()
        (tree / "_plugins" / f"{PLUGIN}.py").write_text(PLUGIN_SOURCE, encoding="utf-8")
        junit = out / f"{run_id}.xml"
        argv = [sys.executable, "-m", "pytest", "-m", "unit and not slow", *tests, "-p", "no:cacheprovider", "-p", PLUGIN, "-rf", "--timeout=120", f"--junitxml={junit}"]
        env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(tree / "_plugins")
        proc = subprocess.run(argv, cwd=tree, env=env, capture_output=True, text=True, timeout=1200, check=False)  # nosec B603 -- fixed argv
        expected = str(tree / MANAGER)
    (out / f"{run_id}.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    provenance = [line.split(" ", 1)[1] for line in proc.stdout.splitlines() if line.startswith("PROVENANCE ")]
    total, failing = _failures(junit)
    return {"id": run_id, "exit": proc.returncode, "tests": total, "failed": failing, "provenance_ok": provenance == [expected], "mutated_sha256": digests, "log": str(out / f"{run_id}.log")}


def _verdict(result: dict, expect_caught: bool) -> str:
    if not result["provenance_ok"]:
        return "NO-PROOF"
    if expect_caught:
        return "CAUGHT" if result["exit"] == 1 and result["failed"] else ("ERROR" if result["exit"] not in (0, 1) else "SURVIVED")
    return "GREEN" if result["exit"] == 0 else "RED"


def _load_n1_mutations(tree_root: Path) -> list:
    spec = importlib.util.spec_from_file_location("_n1_mutation_check", tree_root / N1_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.MUTATIONS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path, help="parent directory for the hermetic copies")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--groups", default="main,fix,n1")
    parser.add_argument("--n1-alone", action="store_true", help="also run each #753 mutant against #753's two test files alone")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    tree_root = args.tree.resolve()
    out = args.out.resolve()
    scratch = args.scratch.resolve()
    out.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    groups = set(args.groups.split(","))
    before = {MANAGER: _sha256(tree_root / MANAGER), "src/api/lifecycle/state_machine.py": _sha256(tree_root / "src/api/lifecycle/state_machine.py")}
    sources = {MANAGER: (tree_root / MANAGER).read_text(encoding="utf-8"), "src/api/lifecycle/state_machine.py": (tree_root / "src/api/lifecycle/state_machine.py").read_text(encoding="utf-8")}
    extended = (NEW_TESTS, *N1_TESTS)

    jobs = []  # (group, id, description, replacements, tests, expect_caught)
    if "main" in groups:
        blob = subprocess.run(["git", "-C", str(tree_root), "show", f"{args.main_ref}:{MANAGER}"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607 -- fixed argv
        jobs.append(("main", "main-new-tests", f"new module against {args.main_ref}'s manager.py", {MANAGER: blob}, (NEW_TESTS,), True))
    if "fix" in groups:
        jobs.append(("fix", "control-new", "control: unmutated, new module", {}, (NEW_TESTS,), False))
        for mutant_id, description, edits in FIX_MUTANTS:
            texts, error = _apply(sources, [(MANAGER, old, new) for old, new in edits])
            jobs.append(("fix", mutant_id, description, {MANAGER: texts[MANAGER]} if error is None else error, (NEW_TESTS,), True))
    if "n1" in groups:
        jobs.append(("n1", "control-extended", "control: unmutated, #753's two files plus the new module", {}, extended, False))
        if args.n1_alone:
            jobs.append(("n1", "control-n1-alone", "control: unmutated, #753's two files", {}, N1_TESTS, False))
        for index, (description, edits) in enumerate(_load_n1_mutations(tree_root), start=1):
            texts, error = _apply(sources, edits)
            replacements = {path: texts[path] for path in sources if texts[path] != sources[path]} if error is None else error
            jobs.append(("n1", f"M{index:02d}-extended", description, replacements, extended, True))
            if args.n1_alone:
                jobs.append(("n1", f"M{index:02d}-n1-alone", description, replacements, N1_TESTS, True))

    def _job(job: tuple) -> dict:
        group, run_id, description, replacements, tests, expect_caught = job
        if isinstance(replacements, str):
            return {"group": group, "id": run_id, "description": description, "verdict": "ANCHOR-ERROR", "error": replacements}
        result = _run(tree_root, scratch, out, run_id, replacements, tests)
        result.update({"group": group, "description": description, "tests_run": list(tests), "verdict": _verdict(result, expect_caught)})
        print(f"{result['verdict']:9} {run_id:22} {description}  [exit {result['exit']}; {len(result['failed'])} failed of {result['tests']}]", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        results = list(pool.map(_job, jobs))
    after = {path: _sha256(tree_root / path) for path in before}
    summary = {"tree": str(tree_root), "sha256_before": before, "sha256_after": after, "unchanged": before == after, "results": results}
    (out / "mutants.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    controls_ok = all(r["verdict"] == "GREEN" for r in results if r["id"].startswith("control"))
    fix_ok = all(r["verdict"] == "CAUGHT" for r in results if r["group"] == "fix" and not r["id"].startswith("control"))
    n1_ok = all(r["verdict"] == "CAUGHT" for r in results if r["group"] == "n1" and r["id"].endswith("-extended") and not r["id"].startswith("control"))
    print(f"controls green: {controls_ok}; fix mutants all caught: {fix_ok}; #753 mutants all caught (extended detector): {n1_ok}; checkout unchanged: {before == after}")
    return 0 if controls_ok and fix_ok and n1_ok and before == after else 1


if __name__ == "__main__":
    sys.exit(main())
