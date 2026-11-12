"""
Mutation check of the n1 round-2 carrier's state-machine lock and settle, in a validator worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, n1 r2 code lens)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 11, cascor paused-fit wedge)

Usage: python3 <this> <mutant-worktree> <out-dir> [--only ID,ID] [--wide ID,ID] [--explore ID=SCENARIO[+inner],...]

For each mutant: restore the worktree's two lifecycle files from the carrier, apply the mutant's
edits (each old string must occur exactly once), delete those modules' cached bytecode, and run the
detector (the carrier's new test module plus the state-machine suite) with bytecode writes off.
``--wide`` also runs every API unit test for the named mutants; ``--explore`` runs the interleaving
explorer (2026-11-09_flood4r2_val_n1-r2-code_interleavings.py) against the mutated tree. The
provenance plugin records the sha256 of the source pytest imported, which must equal the mutated
file's. The worktree's two files are restored from the carrier at the end. The carrier is read only.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses the validator's own pytest output
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
ORCH = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
PLUGINS = ORCH / "tmp" / "flood4r2-val" / "n1-r2-code-lens" / "plugins"
EXPLORER = ORCH / "util" / "ad-hoc" / "2026-11-09_flood4r2_val_n1-r2-code_interleavings.py"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
SM = "src/api/lifecycle/state_machine.py"
MGR = "src/api/lifecycle/manager.py"
DETECTOR = ["src/tests/unit/api/test_lifecycle_paused_fit_return.py", "src/tests/unit/api/test_lifecycle_state_machine.py"]


def _unlock(*names):
    return [(SM, f"    @_atomic\n    def {name}(", f"    def {name}(") for name in names]


_SETTLE_GATE = "                    sm.mark_completed()\n                    # Reopen the gate a pause cleared. After the transition, not before: a pause\n                    # accepted in between would clear it again and leave it closed.\n                    self._pause_event.set()\n"

MUTANTS = {
    "CTRL": ("control: the carrier unchanged", []),
    "V01": ("mark_failed is not atomic", _unlock("mark_failed")),
    "V02": ("set_phase is not atomic", _unlock("set_phase")),
    "V03": ("get_state_summary is not atomic", _unlock("get_state_summary")),
    "V04": ("save_candidate_state and get_candidate_state are not atomic", _unlock("save_candidate_state", "get_candidate_state")),
    "V05": ("mark_resume_ready is not atomic", _unlock("mark_resume_ready")),
    "V06": ("mark_investigating is not atomic", _unlock("mark_investigating")),
    "V07": ("mark_replaying is not atomic", _unlock("mark_replaying")),
    "V08": ("the lock is a non-reentrant Lock, not an RLock", [(SM, "        self._lock = threading.RLock()\n", "        self._lock = threading.Lock()\n")]),
    "V09": ("minimal lock: only handle_command and mark_completed are atomic", _unlock("set_phase", "save_candidate_state", "get_candidate_state", "mark_failed", "mark_resume_ready", "mark_investigating", "mark_replaying", "get_state_summary")),
    "V10": ("the settle does not reopen the pause gate", [(MGR, _SETTLE_GATE, "                    sm.mark_completed()\n")]),
    "V11": ("the settle reopens the pause gate before mark_completed", [(MGR, _SETTLE_GATE, "                    self._pause_event.set()\n                    sm.mark_completed()\n")]),
    "V12": ("the state machine takes no lock", [(SM, "        with self._lock:\n            return method(self, *args, **kwargs)\n", "        return method(self, *args, **kwargs)\n")]),
    "V13": ("mark_completed accepts STARTED only again", [(SM, "        if self._status in (TrainingStatus.STARTED, TrainingStatus.PAUSED):\n            prev = \"Paused\" if", "        if self._status in (TrainingStatus.STARTED,):\n            prev = \"Paused\" if")]),
}


def _sha(path: Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def _restore(tree: Path) -> None:
    for rel in (SM, MGR):
        with open(CARRIER / rel, "rb") as src, open(tree / rel, "wb") as dst:
            dst.write(src.read())


def _drop_bytecode(tree: Path) -> None:
    cache = tree / "src" / "api" / "lifecycle" / "__pycache__"
    if cache.is_dir():
        for pyc in cache.glob("*.pyc"):
            if pyc.name.startswith(("state_machine.", "manager.")):
                pyc.unlink()


def _apply(tree: Path, edits) -> None:
    for rel, old, new in edits:
        path = tree / rel
        with open(path) as fh:
            text = fh.read()
        if text.count(old) != 1:
            raise SystemExit(f"edit for {rel} matches {text.count(old)} times, not once: {old[:80]!r}")
        with open(path, "w") as fh:
            fh.write(text.replace(old, new))


def _env(prov: Path) -> dict:
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONPATH"] = os.pathsep.join([str(PLUGINS)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["N1R2_PROVENANCE_OUT"] = str(prov)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _failed(xml_path: Path) -> list:
    if not xml_path.exists():
        return ["<no junit: collection or startup failure>"]
    root = ET.parse(xml_path).getroot()  # nosec B314 - the validator's own pytest output
    out = []
    for case in root.iter("testcase"):
        if any(child.tag in ("failure", "error") for child in case):
            out.append(f"{case.get('classname').rsplit('.', 1)[-1]}::{case.get('name')}")
    return out


def _count(xml_path: Path) -> int:
    if not xml_path.exists():
        return 0
    return sum(1 for _ in ET.parse(xml_path).getroot().iter("testcase"))  # nosec B314


def _pytest(tree: Path, out: Path, tag: str, targets) -> dict:
    xml = out / f"{tag}.xml"
    prov = out / f"{tag}.provenance.txt"
    if prov.exists():
        prov.unlink()
    cmd = [PYTHON, "-m", "pytest", *targets, "-m", "unit and not slow", "--timeout=60", "-q", "-p", "no:cacheprovider", "-p", "n1r2_provenance", f"--junitxml={xml}"]
    with open(out / f"{tag}.log", "w") as log:
        proc = subprocess.run(cmd, cwd=tree, env=_env(prov), stdout=log, stderr=subprocess.STDOUT, check=False)
    provenance = prov.read_text().strip() if prov.exists() else ""
    return {"exit": proc.returncode, "tests": _count(xml), "failed": _failed(xml), "provenance": provenance}


def _explore(tree: Path, out: Path, tag: str, scenario: str, inner: bool) -> dict:
    cmd = [PYTHON, str(EXPLORER), "--src", str(tree / "src"), "--scenario", scenario, "--sample", "300", "--out", str(out / f"{tag}_explore")]
    if inner:
        cmd.append("--inner")
    env = _env(out / f"{tag}_explore.provenance.txt")
    with open(out / f"{tag}_explore.log", "w") as log:
        subprocess.run(cmd, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    summary_path = out / f"{tag}_explore" / "summary.json"
    if not summary_path.exists():
        return {"error": "explorer wrote no summary"}
    with open(summary_path) as fh:
        summaries = json.load(fh)
    return {s["scenario"] + ("+inner" if s["inner_yield"] else ""): {k: s[k] for k in ("schedules", "invalid", "wedged", "blocked_steps", "stuck", "status_diverges", "sm_has_lock")} for s in summaries}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tree")
    parser.add_argument("out")
    parser.add_argument("--only", default="")
    parser.add_argument("--wide", default="")
    parser.add_argument("--explore", default="", help="ID=scenario[+inner] items, comma-separated")
    args = parser.parse_args()
    tree, out = Path(args.tree).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    only = [m for m in args.only.split(",") if m] or list(MUTANTS)
    wide = {m for m in args.wide.split(",") if m}
    explore = {}
    for item in [i for i in args.explore.split(",") if i]:
        mid, scen = item.split("=", 1)
        explore.setdefault(mid, []).append(scen)
    results = []
    try:
        for mid in only:
            desc, edits = MUTANTS[mid]
            _restore(tree)
            _apply(tree, edits)
            _drop_bytecode(tree)
            record = {"id": mid, "mutant": desc, "sm_sha": _sha(tree / SM), "mgr_sha": _sha(tree / MGR)}
            record["detector"] = _pytest(tree, out, f"{mid}_detector", DETECTOR)
            if mid in wide:
                _drop_bytecode(tree)
                record["wide_api_unit"] = _pytest(tree, out, f"{mid}_wide", ["src/tests/unit/api"])
            for scen in explore.get(mid, []):
                name, _, flag = scen.partition("+")
                _drop_bytecode(tree)
                record.setdefault("explore", {}).update(_explore(tree, out, f"{mid}_{name}{'_inner' if flag else ''}", name, flag == "inner"))
            prov = record["detector"]["provenance"]
            record["provenance_ok"] = f"sha={record['sm_sha']}" in prov and f"sha={record['mgr_sha']}" in prov and str(tree) in prov
            det = record["detector"]
            verdict = "control" if mid == "CTRL" else ("CAUGHT" if det["failed"] else "SURVIVED")
            record["verdict"] = verdict
            print(f"{mid} {verdict:8s} {desc}  [detector exit {det['exit']}; {len(det['failed'])} of {det['tests']} failed; provenance_ok={record['provenance_ok']}]" + (f" wide: {len(record['wide_api_unit']['failed'])} of {record['wide_api_unit']['tests']} failed" if "wide_api_unit" in record else "") + (f" explore: {record['explore']}" if "explore" in record else ""), flush=True)
            results.append(record)
    finally:
        _restore(tree)
        _drop_bytecode(tree)
    with open(out / "mutants.json", "w") as fh:
        json.dump(results, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
