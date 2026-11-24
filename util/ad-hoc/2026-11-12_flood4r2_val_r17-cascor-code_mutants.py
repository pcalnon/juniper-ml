"""
Validator's own mutants of the cascor stop-then-start fix: each undoes one part of it and must be caught by the new test module.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, ruling 17 cascor stop-then-start, code lens)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17, "cascor: stop-then-start")

Usage: <JuniperCascor1 python> <this> <carrier copy tree> <main tree> <work dir> <out.json>

Hermetic: every run copies <carrier copy>/src, conf and pyproject.toml into a fresh directory under
<work dir>, applies ONE mutant's edits to the copy's src/api/lifecycle/manager.py, and runs the new
test module there with bytecode writing off, so the validator's tree is never edited and no stale
``.pyc`` can answer for a mutant. Each edit's anchor must occur exactly once. A run counts only when
the provenance plugin shows pytest imported the copy's manager.py. The unmutated copy runs first as
the control (must be green); M00 swaps in <main tree>'s manager.py whole (the fix reverted) and runs
without ``-x`` so the number of new tests that fail on main is counted. The sha256 of the validator
tree's manager.py is recorded before and after the campaign and must not move.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CARRIER = Path(sys.argv[1]).resolve()
MAIN = Path(sys.argv[2]).resolve()
WORK = Path(sys.argv[3]).resolve()
OUT = Path(sys.argv[4]).resolve()
MANAGER = "src/api/lifecycle/manager.py"
TEST = "src/tests/unit/api/test_lifecycle_stop_then_start.py"
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "logs", "reports")
PLUGIN_SOURCE = 'import sys\n\n\ndef pytest_sessionfinish(session, exitstatus):\n    module = sys.modules.get("api.lifecycle.manager")\n    print("\\nPROVENANCE " + str(getattr(module, "__file__", None)))\n'

_HELPER = "        if self._stop_event.is_set():\n            self._stop_event = threading.Event()\n        return self._stop_event\n"
_CHECK_HEAD = '        stop = self._stop_event if stop_event is None else stop_event\n        if stop.is_set():\n            raise TrainingInterrupted("stop_requested")\n'
_PAUSE_LOOP = '            self._pause_event.wait(timeout=0.5)\n            if stop.is_set():\n                raise TrainingInterrupted("stop_requested_during_pause")\n'
_EPOCH_CP = "            # Was _output_training_callback (bound to network._output_epoch_callback).\n            self._check_for_interrupt(stop_event)\n"
_PHASE_CP = "            # CCN's coarse event types would otherwise drop (plan §3.3 — extend the payload).\n            self._check_for_interrupt(stop_event)\n"
_RUN_BIND = "        stop_event = self._stop_event if stop_event is None else stop_event\n\n        # cascor#582: clear the previous run's final score BEFORE this one starts."
_SINK = "on_event=lambda event: self._handle_event(event, stop_event), **kwargs)"
_START_SUBMIT = "self._val_x, self._val_y, stop_event=stop_event, **fit_kwargs)"
_SWAP_PICK = "                stop_event = self._stop_event_for_new_run_locked()\n                self._pause_event.set()\n"
_SWAP_SUBMIT = "                    self._val_y,\n                    stop_event=stop_event,\n                )\n"
_STOP_ORDER = "        self._stop_event.set()\n        transitioned = self.state_machine.handle_command(Command.STOP)\n"
_START_NOCLEAR = "            # must hold. The new run gets its own signal at the submit below.\n            self._pause_event.set()\n"
_POSTFIT = '            if stop_event.is_set():\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):\n'

MUTANTS = [
    ("V01", "helper never replaces a raised signal (the new run shares the raised one)", [(_HELPER, "        return self._stop_event\n")]),
    ("V02", "helper clears the raised signal in place (main's behaviour, moved)", [(_HELPER, "        if self._stop_event.is_set():\n            self._stop_event.clear()\n        return self._stop_event\n")]),
    ("V03", "helper gives EVERY start a fresh signal", [(_HELPER, "        self._stop_event = threading.Event()\n        return self._stop_event\n")]),
    ("V04", "helper returns a fresh signal but does not store it as the newest", [(_HELPER, "        if self._stop_event.is_set():\n            return threading.Event()\n        return self._stop_event\n")]),
    ("V05", "_check_for_interrupt ignores the run's signal at its first check", [(_CHECK_HEAD, '        stop = self._stop_event if stop_event is None else stop_event\n        if self._stop_event.is_set():\n            raise TrainingInterrupted("stop_requested")\n')]),
    ("V06", "_check_for_interrupt's pause loop reads the newest signal", [(_PAUSE_LOOP, '            self._pause_event.wait(timeout=0.5)\n            if self._stop_event.is_set():\n                raise TrainingInterrupted("stop_requested_during_pause")\n')]),
    ("V07", "epoch_end checkpoint does not pass the run's signal", [(_EPOCH_CP, "            # Was _output_training_callback (bound to network._output_epoch_callback).\n            self._check_for_interrupt()\n")]),
    ("V08", "phase_change checkpoint does not pass the run's signal", [(_PHASE_CP, "            # CCN's coarse event types would otherwise drop (plan §3.3 — extend the payload).\n            self._check_for_interrupt()\n")]),
    ("V09", "_run_training reads the newest signal as it enters", [(_RUN_BIND, "        stop_event = self._stop_event\n\n        # cascor#582: clear the previous run's final score BEFORE this one starts.")]),
    ("V10", "the fit's sink is not bound to the run's signal", [(_SINK, "on_event=self._handle_event, **kwargs)")]),
    ("V11", "start_training submits without the run's signal", [(_START_SUBMIT, "self._val_x, self._val_y, **fit_kwargs)")]),
    ("V12", "swap_dataset_live clears the signal again before it submits", [(_SWAP_PICK, "                self._stop_event.clear()\n                stop_event = self._stop_event\n                self._pause_event.set()\n")]),
    ("V13", "swap_dataset_live submits without the run's signal", [(_SWAP_SUBMIT, "                    self._val_y,\n                )\n")]),
    ("V14", "stop_training raises the signal AFTER its FSM transition", [(_STOP_ORDER, "        transitioned = self.state_machine.handle_command(Command.STOP)\n        self._stop_event.set()\n")]),
    ("V15", "start_training clears the signal again where main did", [(_START_NOCLEAR, "            # must hold. The new run gets its own signal at the submit below.\n            self._stop_event.clear()\n            self._pause_event.set()\n")]),
    ("V16", "the post-fit stop check reads the newest signal", [(_POSTFIT, '            if self._stop_event.is_set():\n                if self._owns_lifecycle(run_token, "returned with a stop requested"):\n')]),
    ("V17", "start_training submits a signal no stop can raise (a fresh one nobody stores)", [(_START_SUBMIT, "self._val_x, self._val_y, stop_event=threading.Event(), **fit_kwargs)")]),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(label: str, manager_text: str, stop_at_first: bool) -> dict:
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=WORK, prefix=f"{label}-") as tmp:
        tree = Path(tmp)
        for name in ("src", "conf"):
            shutil.copytree(CARRIER / name, tree / name, ignore=IGNORED)
        shutil.copy2(CARRIER / "pyproject.toml", tree / "pyproject.toml")
        (tree / MANAGER).write_text(manager_text)
        plugins = tree / "_plugins"
        plugins.mkdir()
        (plugins / "_r17val_mutant_provenance.py").write_text(PLUGIN_SOURCE)
        for rel in ("logs", "src/logs", "src/tests/reports"):
            (tree / rel).mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env.pop("JUNIPER_CASCOR_LOG_DIR", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(plugins)
        argv = [sys.executable, "-m", "pytest", "-m", "unit and not slow", TEST, "-p", "no:cacheprovider", "-p", "_r17val_mutant_provenance", "-rf", "--timeout=120"]
        if stop_at_first:
            argv.append("-x")
        proc = subprocess.run(argv, cwd=tree, env=env, capture_output=True, text=True, timeout=1500, check=False)
        text = proc.stdout + proc.stderr
        provenance = [line.split(" ", 1)[1] for line in text.splitlines() if line.startswith("PROVENANCE ")]
        provenance_ok = bool(provenance) and all(Path(p).resolve() == (tree / MANAGER).resolve() for p in provenance)
        failed = sorted(line.split(" ", 1)[1].split(" - ")[0] for line in text.splitlines() if line.startswith("FAILED "))
        summary = [line for line in text.splitlines() if " passed" in line or " failed" in line or " error" in line][-1:]
        return {"exit": proc.returncode, "provenance_ok": provenance_ok, "failed": failed, "summary": summary}


def main() -> int:
    carrier_text = (CARRIER / MANAGER).read_text()
    sha_before = _sha(CARRIER / MANAGER)
    results = {"carrier_manager_sha256_before": sha_before, "runs": []}
    control = _run("control", carrier_text, stop_at_first=False)
    control["id"], control["what"] = "CONTROL", "unmutated carrier manager.py"
    control["verdict"] = "GREEN" if control["exit"] == 0 and control["provenance_ok"] else "CONTROL-NOT-GREEN"
    results["runs"].append(control)
    print(f"CONTROL {control['verdict']} {control['summary']}", flush=True)
    reverted = _run("M00", (MAIN / MANAGER).read_text(), stop_at_first=False)
    reverted["id"], reverted["what"] = "M00", "main's manager.py swapped in whole (the fix reverted)"
    reverted["verdict"] = "CAUGHT" if reverted["exit"] == 1 and reverted["provenance_ok"] and reverted["failed"] else "NOT-CAUGHT-OR-ERROR"
    results["runs"].append(reverted)
    print(f"M00 {reverted['verdict']} failed={len(reverted['failed'])} {reverted['summary']}", flush=True)
    for mutant_id, what, edits in MUTANTS:
        text = carrier_text
        anchors_ok = True
        for old, new in edits:
            if text.count(old) != 1:
                anchors_ok = False
                break
            text = text.replace(old, new)
        if not anchors_ok:
            entry = {"id": mutant_id, "what": what, "verdict": "ANCHOR-ERROR"}
        else:
            entry = _run(mutant_id, text, stop_at_first=True)
            entry["id"], entry["what"] = mutant_id, what
            if not entry["provenance_ok"] or entry["exit"] not in (0, 1):
                entry["verdict"] = "ERROR"
            else:
                entry["verdict"] = "CAUGHT" if entry["exit"] == 1 and entry["failed"] else "SURVIVED"
        results["runs"].append(entry)
        print(f"{mutant_id} {entry['verdict']} {entry.get('failed', [])[:1]} -- {what}", flush=True)
        with open(OUT, "w") as fh:
            json.dump(results, fh, indent=2)
    results["carrier_manager_sha256_after"] = _sha(CARRIER / MANAGER)
    results["carrier_manager_unchanged"] = results["carrier_manager_sha256_after"] == sha_before
    with open(OUT, "w") as fh:
        json.dump(results, fh, indent=2)
    verdicts = [run["verdict"] for run in results["runs"]]
    print(f"SUMMARY caught={verdicts.count('CAUGHT')} survived={verdicts.count('SURVIVED')} errors={sum(v in ('ERROR', 'ANCHOR-ERROR', 'CONTROL-NOT-GREEN', 'NOT-CAUGHT-OR-ERROR') for v in verdicts)} unchanged={results['carrier_manager_unchanged']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
