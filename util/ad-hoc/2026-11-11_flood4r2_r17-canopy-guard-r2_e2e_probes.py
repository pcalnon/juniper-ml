"""
End-to-end probes of the round-2 guard fixes: real xfail tests (F2) and a thread a test left running (F1).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --carrier <carrier worktree> --probe <probe worktree> --out <dir> --python <label>=<interpreter> [--python ...]

The unit tests in src/tests/unit/test_unit_lane_network_guard.py pin flag() and the report hook on synthetic reports.
These probes run whole tests through pytest instead, in a PROBE worktree (never the carrier): two probe modules are
written into its src/tests/unit/, run through 2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py, and deleted.

  xfail   three tests that swallow a refused connect and are an expected failure (marked and failing, marked and
          passing, imperative pytest.xfail). With the carrier's conftest.py pytest must exit 1 with three junit
          failures. With F2's edit removed from the probe's conftest.py (restored afterwards, sha256 checked) the
          same run exits 0 with none: the defect the validator's F2 describes.
  thread  test_a starts a daemon thread that connects 0.8 s later and passes; test_b only sleeps. test_b must
          fail, and its message must name the thread and must not say "this test connected" (F1).

No probe can reach a listener: each module replaces the guard's pass-through with a no-op for its duration, and the
fence refuses a service port at the C level besides. <dir>/e2e_probes.json records every run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import xml.etree.ElementTree as ET  # nosec B405 - our own pytest junit output
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_LANE = HERE / "2026-11-11_flood4r2_r17-canopy-guard-r2_run_lane.py"
CONFTEST = "src/tests/conftest.py"
XFAIL_PROBE = "src/tests/unit/test_zz_r2_probe_xfail.py"
THREAD_PROBE = "src/tests/unit/test_zz_r2_probe_left_running_thread.py"
F2_EDIT = '        if hasattr(report, "wasxfail"):\n            del report.wasxfail  # an xfail marker must not turn the guard\'s failure back into a skip (exit 0, junit "skipped")\n'

XFAIL_SOURCE = '''"""Round-2 probe, NOT part of the carrier: xfail tests that swallow a refused connect."""

import contextlib
import socket

import pytest


@pytest.fixture(autouse=True)
def _no_real_connect(service_port_guard, monkeypatch):
    monkeypatch.setattr(service_port_guard, "real_connect", lambda sock, address: None)
    monkeypatch.setattr(service_port_guard, "real_connect_ex", lambda sock, address: 0)


def _swallowed_refused_connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, contextlib.suppress(OSError):
        sock.connect(("127.0.0.1", 8055))


@pytest.mark.xfail(reason="probe: an expected failure that also makes a refused connect")
def test_xfail_marked_and_failing():
    _swallowed_refused_connect()
    raise AssertionError("the expected failure")


@pytest.mark.xfail(reason="probe: marked xfail but passing, after a refused connect")
def test_xfail_marked_and_passing():
    _swallowed_refused_connect()


def test_imperative_xfail():
    _swallowed_refused_connect()
    pytest.xfail("probe: imperative xfail after a refused connect")
'''

THREAD_SOURCE = '''"""Round-2 probe, NOT part of the carrier: a thread one test leaves running connects during the next."""

import contextlib
import socket
import threading
import time

import pytest


@pytest.fixture(scope="module", autouse=True)
def _no_real_connect(service_port_guard):
    saved = (service_port_guard.real_connect, service_port_guard.real_connect_ex)
    service_port_guard.real_connect = lambda sock, address: None
    service_port_guard.real_connect_ex = lambda sock, address: 0
    yield
    service_port_guard.real_connect, service_port_guard.real_connect_ex = saved


def test_a_leaves_a_thread_running():
    def later():
        time.sleep(0.8)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, contextlib.suppress(OSError):
            sock.connect(("127.0.0.1", 8055))

    threading.Thread(target=later, name="r2-probe-left-running", daemon=True).start()


def test_b_only_sleeps():
    time.sleep(2.0)
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_pycache(probe: Path) -> None:
    for cache in list((probe / "src" / "tests").rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)


def run(probe: Path, python: str, label: str, out: Path, path: str) -> dict:
    clear_pycache(probe)
    subprocess.run([sys.executable, str(RUN_LANE), "--tree", str(probe), "--python", python, "--label", label, "--out", str(out), "--mode", "files", "--paths", path], check=True, capture_output=True)  # nosec B603 - fixed argv
    summary = json.loads((out / f"{label}.summary.json").read_text(encoding="utf-8"))
    cases = {}
    for case in ET.parse(out / f"{label}.junit.xml").getroot().iter("testcase"):  # nosec B314 - our own pytest junit output
        kinds = {child.tag for child in case}
        text = " ".join((child.get("message") or "") + " " + (child.text or "") for child in case)
        cases[case.get("name")] = {"result": next((kind for kind in ("failure", "error", "skipped") if kind in kinds), "passed"), "text": " ".join(text.split())[:700]}
    return {"label": label, "versions": summary["versions"], "exit": summary["exit"], "junit": {key: summary["junit"].get(key) for key in ("tests", "failures", "errors", "skipped")}, "cases": cases, "guarded_port_connects_at_c_level": summary["guarded_port_connects_past_the_guard"], "log": str(out / f"{label}.log")}


def main() -> int:
    parser = argparse.ArgumentParser(description="End-to-end probes of the round-2 guard fixes.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True, action="append", help="<label>=<interpreter>")
    args = parser.parse_args()
    carrier, probe, out = args.carrier.resolve(), args.probe.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = (carrier / CONFTEST).read_text(encoding="utf-8")
    pristine = sha256(carrier / CONFTEST)
    if sha256(probe / CONFTEST) != pristine or original.count(F2_EDIT) != 1:
        raise SystemExit("[e2e] the probe's conftest.py differs from the carrier's, or F2's edit is not there exactly once")
    (probe / XFAIL_PROBE).write_text(XFAIL_SOURCE, encoding="utf-8")
    (probe / THREAD_PROBE).write_text(THREAD_SOURCE, encoding="utf-8")
    record: dict = {"carrier_conftest_sha256": pristine, "runs": [], "verdicts": {}}
    try:
        for tag, python in [entry.split("=", 1) for entry in args.python]:
            with_fix = run(probe, python, f"e2e-xfail-with-f2-{tag}", out, XFAIL_PROBE)
            (probe / CONFTEST).write_text(original.replace(F2_EDIT, ""), encoding="utf-8")
            without_fix = run(probe, python, f"e2e-xfail-without-f2-{tag}", out, XFAIL_PROBE)
            shutil.copyfile(carrier / CONFTEST, probe / CONFTEST)
            thread = run(probe, python, f"e2e-thread-{tag}", out, THREAD_PROBE)
            record["runs"] += [with_fix, without_fix, thread]
            blamed = thread["cases"].get("test_b_only_sleeps", {})
            record["verdicts"][tag] = {
                "xfail_with_f2_exit_1_and_3_failures": with_fix["exit"] == 1 and with_fix["junit"]["failures"] == "3",
                "xfail_without_f2_exit_0_and_0_failures": without_fix["exit"] == 0 and without_fix["junit"]["failures"] == "0",
                "thread_test_a_passes": thread["cases"].get("test_a_leaves_a_thread_running", {}).get("result") == "passed",
                "thread_test_b_fails_naming_the_thread": blamed.get("result") == "failure" and "127.0.0.1:8055 (thread r2-probe-left-running)" in blamed.get("text", "") and "was refused while this test ran" in blamed.get("text", ""),
                "thread_message_does_not_blame_test_b": "this test connected" not in blamed.get("text", ""),
                "conftest_restored": sha256(probe / CONFTEST) == pristine,
            }
            print(f"[e2e] {tag}: {record['verdicts'][tag]}")
    finally:
        shutil.copyfile(carrier / CONFTEST, probe / CONFTEST)
        (probe / XFAIL_PROBE).unlink(missing_ok=True)
        (probe / THREAD_PROBE).unlink(missing_ok=True)
        clear_pycache(probe)
    record["probe_conftest_sha256_after"] = sha256(probe / CONFTEST)
    record["probe_files_removed"] = not (probe / XFAIL_PROBE).exists() and not (probe / THREAD_PROBE).exists()
    (out / "e2e_probes.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    good = all(all(verdict.values()) for verdict in record["verdicts"].values()) and record["probe_conftest_sha256_after"] == pristine and record["probe_files_removed"]
    print(f"[e2e] all verdicts true: {good}; record {out / 'e2e_probes.json'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
