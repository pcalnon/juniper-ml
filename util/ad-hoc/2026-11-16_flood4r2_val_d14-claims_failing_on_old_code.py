"""
Run the D-14 juniper-ml carrier's new and updated service-core tests against OLD package code: the published
0.7.2 tag and the carrier's base (main at f181856f). Tests whether "Against 0.7.2's code ... fail" counts hold.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator MN2, claims lens, flood-4 session 9)
Created: 2026-11-16
Status: ad-hoc - investigation
Retire when: RETAINED - ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Cursor flood-4 disposition record (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)

Usage: python3 <this file>
Builds <scratch>/oldcode/<label>/ (package code from `git archive` of the ref, the carrier's three test files and its
fixture, and a pytest.ini copied from the carrier's [tool.pytest.ini_options]; no pyproject.toml, so no fixture project
sits under tmp/), then runs pytest with the JuniperCascor1 interpreter, the six Sentry variables set to "" and the dead
session bus. Read-only on the carrier.
"""

import json
import os
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
O = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "humming-stargazing-papert"
ML = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d"
SCRATCH = O / "tmp" / "flood4r2-val" / "d14-claims-lens" / "oldcode"
PYTHON = Path("/opt/miniforge3/envs/JuniperCascor1/bin/python3.14")
SENTRY = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
REFS = {"v072": "juniper-service-core-v0.7.2", "base": "f181856f4d0ab797b281e99d3547ab379b257dc8"}
TEST_FILES = ("tests/__init__.py", "tests/fixtures/ws_resume_answers.json", "tests/test_websocket_resume_answer_table.py", "tests/test_websocket_resume_continuity.py")
RULE_TESTS = (
    "test_a_last_seq_that_is_not_a_plain_integer_is_refused_as_malformed",
    "test_a_cursor_that_is_not_an_integer_is_malformed_before_its_server_instance_id_is_compared",
    "test_a_last_seq_above_the_last_seq_numbered_is_refused_out_of_range",
    "test_replay_since_and_the_catch_up_refuse_a_cursor_above_the_last_seq_numbered",
    "test_a_negative_last_seq_is_read_as_zero_whatever_the_buffer_holds",
    "test_a_negative_last_seq_is_out_of_range_once_seq_1_has_left_the_buffer_as_zero_is",
    "test_a_resume_frame_whose_data_is_not_an_object_is_refused_as_malformed",
)
CUT_TEST = "test_replay_since_returns_exactly_the_tail_after_every_cut_point"
PYTEST_INI = """[pytest]
minversion = 8.0
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = strict
addopts = -ra -q --strict-markers --strict-config -p no:dash -p no:playwright -p no:cacheprovider
filterwarnings = ignore::pytest.PytestUnraisableExceptionWarning
"""


def build(label, ref):
    root = SCRATCH / label
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    archive = SCRATCH / f"{label}.tar"
    subprocess.run(["git", "-C", str(O), "archive", "-o", str(archive), ref, "juniper-service-core/juniper_service_core"], check=True)
    with tarfile.open(archive) as tar:
        tar.extractall(root / "x", filter="data")
    shutil.move(str(root / "x" / "juniper-service-core" / "juniper_service_core"), str(root / "juniper_service_core"))
    shutil.rmtree(root / "x")
    archive.unlink()
    for rel in TEST_FILES:
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ML / "juniper-service-core" / rel, dest)
    (root / "pytest.ini").write_text(PYTEST_INI, encoding="utf-8")
    return root


def run(root, label):
    env = {**os.environ, **{name: "" for name in SENTRY}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus", "PYTHONDONTWRITEBYTECODE": "1"}
    junit = SCRATCH / f"{label}.junit.xml"
    log = SCRATCH / f"{label}.log"
    where = subprocess.run([str(PYTHON), "-c", "import juniper_service_core.websocket.manager as m; print(m.__file__)"], cwd=root, env=env, capture_output=True, text=True, check=False)
    cmd = [str(PYTHON), "-m", "pytest", "-c", "pytest.ini", "--rootdir", str(root), "-p", "no:randomly", "--timeout=120", f"--junitxml={junit}", "tests/test_websocket_resume_answer_table.py", "tests/test_websocket_resume_continuity.py"]
    with log.open("w", encoding="utf-8") as fh:
        fh.write(f"cmd: {cmd}\ncwd: {root}\n")
        fh.flush()
        proc = subprocess.run(cmd, cwd=root, env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=1200, check=False)
    groups = {"table": [0, 0], "cut": [0, 0], "rules22": [0, 0], "other_continuity": [0, 0]}
    if junit.is_file():
        for case in ET.parse(junit).getroot().iter("testcase"):
            failed = any(child.tag in ("failure", "error") for child in case)
            skipped = any(child.tag == "skipped" for child in case)
            name = case.get("name", "")
            classname = case.get("classname", "")
            base = name.split("[")[0]
            if "answer_table" in classname:
                key = "table"
            elif base == CUT_TEST:
                key = "cut"
            elif base in RULE_TESTS:
                key = "rules22"
            else:
                key = "other_continuity"
            if not skipped:
                groups[key][0 if not failed else 1] += 1
    return {"exit": proc.returncode, "imported_from": where.stdout.strip() or where.stderr.strip()[-300:], "groups_passed_failed": groups, "log": str(log), "junit": str(junit)}


def main():
    probe = subprocess.run([str(PYTHON), "-c", "import sys; print(sys.version.split()[0], sys.executable, sys.base_prefix)"], capture_output=True, text=True, check=True)
    results = {"interpreter": probe.stdout.strip()}
    labels = sys.argv[1:] or list(REFS)
    for label in labels:
        root = build(label, REFS[label])
        results[label] = {"ref": REFS[label], **run(root, label)}
        print(label, json.dumps(results[label]["groups_passed_failed"]), "exit", results[label]["exit"])
    (SCRATCH / "summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(results["interpreter"])


if __name__ == "__main__":
    main()
