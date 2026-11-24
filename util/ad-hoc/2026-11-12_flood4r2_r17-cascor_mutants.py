#!/usr/bin/env python3
"""
Mutation-check juniper-cascor's stop-then-start fix in hermetic copies, verifying the checkout's bytes after every mutant.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 12; tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt sections 1
         and 2; a copy of util/ad-hoc/2026-11-11_flood4r2_r17-cascor_mutants.py (kept as it ran) with
         three changes: the six Sentry DSN variables are set to the empty string for every run, the
         checkout's guarded files are re-hashed after EVERY run and not only after the campaign,
         and a group that did not run is reported as not run, never as "all caught"

Each run copies the checkout's ``src/``, ``conf/`` and ``pyproject.toml`` into a fresh directory
under ``--scratch`` (never the system temp directory, and never a juniper-ml ``tmp/``: the copy
carries a ``[project]`` pyproject), applies one mutant there, and runs the detector with
``-m "unit and not slow"``. The checkout is never edited: the sha256 of its ``manager.py``,
``state_machine.py`` and the three test modules is recorded before the campaign and compared
again after every run; a run that finds a difference is reported CHECKOUT-CHANGED and fails the
campaign. No ``__pycache__`` is copied and ``PYTHONDONTWRITEBYTECODE=1`` is set, so no stale
``.pyc`` can answer for a mutant. A one-function plugin prints the ``__file__`` pytest resolved
for ``api.lifecycle.manager``; a run that did not import the mutated copy counts as NO-PROOF,
never as a catch. Exit codes are read from the subprocess, failures from the JUnit file.

Groups:
  main  -- the checkout with ``manager.py`` replaced by ``--main-ref``'s: which new tests fail on main.
  fix   -- the control (unmutated), then each of this fix's mutants S01..S17 against the new module.
  n1    -- juniper-cascor#753's own mutants (its script's MUTATIONS list, M01..M31; M00, the base
           revert, is skipped), each against #753's two test files plus the new module, and, with
           ``--n1-alone``, against #753's two files alone too.

Usage:
  2026-11-12_flood4r2_r17-cascor_mutants.py --tree <cascor checkout> --scratch <dir> --out <dir>
      [--main-ref origin/main] [--groups main,fix,n1] [--n1-alone] [--workers 4]
Exit: 0 when the controls are green, every mutant of each group that ran is caught (the n1 group
by the extended detector), and the checkout's guarded files are unchanged after every run;
1 otherwise.
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
STATE_MACHINE = "src/api/lifecycle/state_machine.py"
NEW_TESTS = "src/tests/unit/api/test_lifecycle_stop_then_start.py"
N1_TESTS = ("src/tests/unit/api/test_lifecycle_paused_fit_return.py", "src/tests/unit/api/test_lifecycle_state_machine.py")
N1_SCRIPT = "util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py"
# The checkout's files whose bytes are compared again after every run.
GUARDED = (MANAGER, STATE_MACHINE, NEW_TESTS, *N1_TESTS)
# No test run may reach Sentry: each of these is SET, to the empty string, for every run.
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
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
_ENTRY_CHECK = '        if stop.is_set():\n            raise TrainingInterrupted("stop_requested")\n'
_PAUSE_LOOP_CHECK = '            if stop.is_set():\n                raise TrainingInterrupted("stop_requested_during_pause")\n'
_START_KEEPS_SIGNAL = "            # must hold. The new run gets its own signal at the submit below.\n            self._pause_event.set()\n"

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
    ("S14", "the checkpoint's first stop read is the newest signal (its pause-loop read stays the run's)", [(_ENTRY_CHECK, _ENTRY_CHECK.replace("if stop.is_set():", "if self._stop_event.is_set():"))]),
    ("S15", "the checkpoint's pause-loop stop read is the newest signal (its first read stays the run's)", [(_PAUSE_LOOP_CHECK, _PAUSE_LOOP_CHECK.replace("if stop.is_set():", "if self._stop_event.is_set():"))]),
    ("S16", "the helper's test is inverted: a raised signal is shared, an unraised one replaced", [(_HELPER_BODY, _HELPER_BODY.replace("if self._stop_event.is_set():", "if not self._stop_event.is_set():"))]),
    ("S17", "start_training clears the shared signal where main did, before its params check", [(_START_KEEPS_SIGNAL, _START_KEEPS_SIGNAL.replace("            self._pause_event.set()\n", "            self._stop_event.clear()\n            self._pause_event.set()\n"))]),
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
        env.update({name: "" for name in SENTRY_DSN_NAMES})
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(tree / "_plugins")
        proc = subprocess.run(argv, cwd=tree, env=env, capture_output=True, text=True, timeout=1200, check=False)  # nosec B603 -- fixed argv
        expected = str(tree / MANAGER)
    (out / f"{run_id}.log").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    provenance = [line.split(" ", 1)[1] for line in proc.stdout.splitlines() if line.startswith("PROVENANCE ")]
    total, failing = _failures(junit)
    return {"id": run_id, "exit": proc.returncode, "tests": total, "failed": failing, "provenance_ok": provenance == [expected], "mutated_sha256": digests, "log": str(out / f"{run_id}.log")}


def _verdict(result: dict, expect_caught: bool) -> str:
    if not result["checkout_unchanged"]:
        return "CHECKOUT-CHANGED"
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
    before = {path: _sha256(tree_root / path) for path in GUARDED}
    sources = {MANAGER: (tree_root / MANAGER).read_text(encoding="utf-8"), STATE_MACHINE: (tree_root / STATE_MACHINE).read_text(encoding="utf-8")}
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
        # After EVERY run, not only after the campaign: the checkout's guarded bytes are as they were.
        result["checkout_unchanged"] = {path: _sha256(tree_root / path) for path in GUARDED} == before
        result.update({"group": group, "description": description, "tests_run": list(tests), "verdict": _verdict(result, expect_caught)})
        print(f"{result['verdict']:9} {run_id:22} {description}  [exit {result['exit']}; {len(result['failed'])} failed of {result['tests']}; checkout unchanged: {result['checkout_unchanged']}]", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        results = list(pool.map(_job, jobs))
    after = {path: _sha256(tree_root / path) for path in before}
    every_run_unchanged = all(r.get("checkout_unchanged", True) for r in results)
    summary = {"tree": str(tree_root), "groups": sorted(groups), "sha256_before": before, "sha256_after": after, "unchanged": before == after, "unchanged_after_every_run": every_run_unchanged, "results": results}
    (out / "mutants.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    controls = [r["verdict"] == "GREEN" for r in results if r["id"].startswith("control")]
    fix = [r["verdict"] == "CAUGHT" for r in results if r["group"] == "fix" and not r["id"].startswith("control")]
    n1 = [r["verdict"] == "CAUGHT" for r in results if r["group"] == "n1" and r["id"].endswith("-extended") and not r["id"].startswith("control")]
    main_runs = [r["verdict"] == "CAUGHT" for r in results if r["group"] == "main"]

    def _tally(verdicts: list) -> str:
        return f"{sum(verdicts)} of {len(verdicts)}" if verdicts else "not run"

    print(f"controls green: {_tally(controls)}; new tests failing on main: {_tally(main_runs)}; fix mutants caught: {_tally(fix)}; #753 mutants caught (extended detector): {_tally(n1)}; checkout unchanged after every run: {every_run_unchanged}; after the campaign: {before == after}")
    return 0 if all(controls) and all(fix) and all(n1) and all(main_runs) and every_run_unchanged and before == after else 1


if __name__ == "__main__":
    sys.exit(main())
