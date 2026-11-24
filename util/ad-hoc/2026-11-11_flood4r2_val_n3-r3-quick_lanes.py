"""
Run the wider WebSocket-bearing test lanes for the N-3 round-3 quick validation, on the carrier copy and on clean main.

The six WebSocket unit files are covered by the mutants helper. This one casts a wider net, because a test OUTSIDE those
six that pinned the old answer to a negative cursor or a non-object ``data`` would fail only here:

  api-unit         every unit test under src/tests/unit/api (CI's marker selection, at most 4 xdist workers)
  api-integration  every quick integration test under src/tests/integration/api (serial, as CI runs it)

each in COPY (origin/main 9f632eac + the carrier's 11 files) and in MAIN (pristine 9f632eac). Fresh bytecode prefix and
basetemp per run under the validator's scratch directory; ``JUNIPER_CASCOR_LOG_DIR`` removed from the environment.
The report lists, per lane, the counts on each side and every test that fails on one side only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses (N-3 round 3)
"""

import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
WORKTREES = JUNIPER / "worktrees"
TREES = {
    "carrier": WORKTREES / "juniper-cascor--val--n3-r3-quick--20261111-1958--9f632eac",
    "main": WORKTREES / "juniper-cascor--val--n3-r3-quick-main--20261111-1958--9f632eac",
}
OUT = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert" / "tmp" / "flood4r2-val" / "n3-r3-quick-s5" / "lanes"
PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
LANES = {
    "api-unit": ["-m", "unit and not slow", "src/tests/unit/api", "--timeout=60", "-n", "4"],
    "api-integration": ["--integration", "-m", "integration and not slow", "src/tests/integration/api", "--timeout=60"],
}


def run(label: str, tree: Path, pytest_args: list) -> dict:
    pyc = OUT / f"pycache-{label}"
    basetemp = OUT / f"basetemp-{label}"
    for stale in (pyc, basetemp):
        if stale.exists():
            shutil.rmtree(stale)
    pyc.mkdir(parents=True)
    junit = OUT / f"junit-{label}.xml"
    if junit.exists():
        junit.unlink()
    env = dict(os.environ)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(pyc)
    cmd = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", f"--junitxml={junit}", f"--basetemp={basetemp}", *pytest_args]
    t0 = time.monotonic()
    with open(OUT / f"{label}.log", "w", encoding="utf-8") as log:
        log.write("$ (cwd " + str(tree) + ") env -u JUNIPER_CASCOR_LOG_DIR " + " ".join(cmd) + "\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=tree, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    cases = list(ET.parse(junit).getroot().iter("testcase")) if junit.exists() else []
    failed = sorted(f"{c.get('classname')}::{c.get('name')}" for c in cases if c.find("failure") is not None or c.find("error") is not None)
    skipped = sum(1 for c in cases if c.find("skipped") is not None)
    return {"exit_status": rc, "seconds": round(time.monotonic() - t0, 1), "tests": len(cases), "failed": len(failed), "skipped": skipped, "passed": len(cases) - len(failed) - skipped, "failed_ids": failed}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for lane, pytest_args in LANES.items():
        results[lane] = {}
        for side, tree in TREES.items():
            results[lane][side] = run(f"{lane}-{side}", tree, pytest_args)
            (OUT / "lanes.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
        carrier, main_side = results[lane]["carrier"], results[lane]["main"]
        only_carrier = sorted(set(carrier["failed_ids"]) - set(main_side["failed_ids"]))
        only_main = sorted(set(main_side["failed_ids"]) - set(carrier["failed_ids"]))
        results[lane]["fails_on_the_carrier_only"] = only_carrier
        results[lane]["fails_on_main_only"] = only_main
        (OUT / "lanes.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
        for side in TREES:
            rec = results[lane][side]
            print(f"{lane} {side}: {rec['tests']} tests, {rec['passed']} passed, {rec['failed']} failed, {rec['skipped']} skipped, exit {rec['exit_status']}, {rec['seconds']} s", flush=True)
        print(f"{lane}: fails on the carrier only {only_carrier}; fails on main only {only_main}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
