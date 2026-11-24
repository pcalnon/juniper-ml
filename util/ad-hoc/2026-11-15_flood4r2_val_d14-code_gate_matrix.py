"""
Drive juniper-ml's resume-table drift gate in every sibling state and environment, from synthetic ecosystem roots.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --source <juniper-ml tree holding the gate and the table> --scratch <dir> --out <json>
Builds one synthetic ecosystem root per sibling state under --scratch (the "sibling absent" root is nested more
than six levels deep, so the gate's upward walk cannot reach a real juniper-cascor), copies the gate module and
the juniper-ml copy of the table into each, and runs `python3 -m unittest -v tests/test_ws_resume_answer_table_drift.py`
there under four environments. Records the module's exit and the cross-repository test's own outcome.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

GATE = "tests/test_ws_resume_answer_table_drift.py"
ML_COPY = "juniper-service-core/tests/fixtures/ws_resume_answers.json"
CASCOR_COPY = "src/tests/fixtures/ws_resume_answers.json"
ENVS = {
    "local-default": {},
    "actions-true": {"GITHUB_ACTIONS": "true"},
    "force-local-1": {"JUNIPER_DRIFT_TEST_FORCE_LOCAL": "1"},
    "actions-false": {"GITHUB_ACTIONS": "false"},
}
EXPECTED_COMPARED = {"sibling-absent": "skipped", "copy-absent": "FAIL", "copies-equal": "ok", "row-edited": "FAIL", "bytes-differ": "FAIL"}
CROSS = re.compile(r"test_juniper_cascors_copy_is_byte_identical_to_this_one .*? \.\.\. (ok|FAIL|ERROR|skipped)", re.DOTALL)


def edited_row(text: str) -> str:
    table = json.loads(text)
    table["frames"][7]["answers"]["fresh"]["handshake"] = ["resume_ok(replayed_count=1)"]
    return json.dumps(table, indent=2) + "\n"


def build(scratch: Path, state: str, table: str, gate: str) -> Path:
    base = scratch / state
    if base.exists():
        shutil.rmtree(base)
    ml_root = (base / "a" / "b" / "c" / "d" / "e" / "f" / "g" / "juniper-ml") if state == "sibling-absent" else (base / "juniper-ml")
    (ml_root / "tests").mkdir(parents=True)
    (ml_root / ML_COPY).parent.mkdir(parents=True)
    (ml_root / GATE).write_text(gate, encoding="utf-8")
    (ml_root / ML_COPY).write_text(table, encoding="utf-8")
    if state != "sibling-absent":
        cascor = base / "juniper-cascor"
        cascor.mkdir()
        sibling_text = {"copy-absent": None, "copies-equal": table, "row-edited": edited_row(table), "bytes-differ": table.rstrip("\n")}[state]
        if sibling_text is not None:
            (cascor / CASCOR_COPY).parent.mkdir(parents=True)
            (cascor / CASCOR_COPY).write_text(sibling_text, encoding="utf-8")
    return ml_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    table = (args.source / ML_COPY).read_text(encoding="utf-8")
    gate = (args.source / GATE).read_text(encoding="utf-8")
    base_env = {key: value for key, value in os.environ.items() if key not in ("GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL")}
    rows, wrong = [], 0
    for state, compared in EXPECTED_COMPARED.items():
        ml_root = build(args.scratch, state, table, gate)
        for env_name, extra in ENVS.items():
            proc = subprocess.run([sys.executable, "-m", "unittest", "-v", GATE], cwd=str(ml_root), env={**base_env, **extra}, capture_output=True, text=True, timeout=120, check=False)
            match = CROSS.search(proc.stderr)
            outcome = match.group(1) if match else "not-found"
            expected = compared if env_name in ("actions-true", "force-local-1") else "skipped"
            ok = outcome == expected and (proc.returncode == 0) == (expected != "FAIL")
            wrong += not ok
            ran = re.search(r"Ran (\d+) tests?", proc.stderr)
            rows.append({"state": state, "env": env_name, "exit": proc.returncode, "cross_repo_test": outcome, "expected": expected, "ran": int(ran.group(1)) if ran else None, "as_expected": ok})
            print(f"{state:15} {env_name:14} exit={proc.returncode} cross={outcome:8} expected={expected:8} ran={rows[-1]['ran']} {'OK' if ok else 'UNEXPECTED'}")
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
        handle.write("\n")
    print(f"unexpected outcomes: {wrong} of {len(rows)}")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
