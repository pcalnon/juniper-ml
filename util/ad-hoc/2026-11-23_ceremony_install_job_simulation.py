#!/usr/bin/env python3
# =============================================================================
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  util/ad-hoc
# File Name:    2026-11-23_ceremony_install_job_simulation.py
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
# Created:      2026-11-23
# Last Updated: 2026-11-23
#
# Status: ad-hoc -- investigation (one-artifact publish sweep, ruling 2 of 2026-11-16)
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
# Related: util/release_train/ceremony.py (classify_publish_run); juniper-ml#2592 (HALT_BUILD, the monitor's
#          dispatch runs); notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md v1.15.17
#          (section 5, the note on the one-artifact publish). Promoted from session e71d3e's scratch
#          ceremony_new_job_sim.py (2026-11-23), unchanged in substance.
#
# Description:
#   Ruling 2 of 2026-11-16 ("Yes, in this sweep (Recommended)") moves each publisher's TestPyPI install check into
#   its own job, "Verify the TestPyPI install", which PyPI's job then needs. Its option text claims: "The ceremony
#   already reads any job with 'TestPyPI' in its name, so a failure there reads HALT_TESTPYPI with no ceremony
#   change." This feeds six simulated publish runs that carry the new job through the checkout's own
#   classify_publish_run and requires each verdict:
#     - the install job failed, PyPI skipped            -> HALT_TESTPYPI
#     - the install job running                         -> IN_PROGRESS
#     - both TestPyPI-named jobs green, PyPI parked     -> PENDING_PYPI_APPROVAL (job-level, and run-level waiting)
#     - the TestPyPI upload failed, install job skipped -> HALT_TESTPYPI
#     - every job green                                 -> RELEASED
#   Read-only: it imports ceremony.py from this checkout and calls one pure function. No network, no gh, no writes.
#
# Usage:
#   python3 -I util/ad-hoc/2026-11-23_ceremony_install_job_simulation.py
#   Exit 0 = 6 of 6 as expected; 1 = any case differs.
# =============================================================================
"""Prove that the ceremony reads ruling 2's new 'Verify the TestPyPI install' job as a TestPyPI job."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CEREMONY = ROOT / "util" / "release_train" / "ceremony.py"

BUILD = "Build and Validate"
TESTPYPI = "Publish to TestPyPI"
INSTALL = "Verify the TestPyPI install"
PYPI = "Publish to PyPI"
REPUBLISH = "Republish the tested files (dispatch only)"


def load_ceremony():
    """Import ceremony.py by path, registered in sys.modules first (its dataclasses need the module there)."""
    sys.path.insert(0, str(CEREMONY.parent))
    spec = importlib.util.spec_from_file_location("ceremony", CEREMONY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ceremony"] = module
    spec.loader.exec_module(module)
    return module


def job(name: str, status: str, conclusion) -> dict:
    return {"name": name, "status": status, "conclusion": conclusion}


def cases() -> dict:
    """Label -> (run fields, jobs, the verdict ruling 2's option text implies)."""
    failed = {"status": "completed", "conclusion": "failure"}
    running = {"status": "in_progress", "conclusion": None}
    return {
        "install job FAILED, pypi skipped": (
            failed,
            [job(BUILD, "completed", "success"), job(TESTPYPI, "completed", "success"), job(INSTALL, "completed", "failure"), job(PYPI, "completed", "skipped"), job(REPUBLISH, "completed", "skipped")],
            "HALT_TESTPYPI",
        ),
        "install job running": (
            running,
            [job(BUILD, "completed", "success"), job(TESTPYPI, "completed", "success"), job(INSTALL, "in_progress", None), job(PYPI, "queued", None), job(REPUBLISH, "completed", "skipped")],
            "IN_PROGRESS",
        ),
        "both green, pypi parked (job-level)": (
            running,
            [job(BUILD, "completed", "success"), job(TESTPYPI, "completed", "success"), job(INSTALL, "completed", "success"), job(PYPI, "waiting", None), job(REPUBLISH, "completed", "skipped")],
            "PENDING_PYPI_APPROVAL",
        ),
        "both green, run waiting": (
            {"status": "waiting", "conclusion": None},
            [job(BUILD, "completed", "success"), job(TESTPYPI, "completed", "success"), job(INSTALL, "completed", "success"), job(PYPI, "waiting", None), job(REPUBLISH, "completed", "skipped")],
            "PENDING_PYPI_APPROVAL",
        ),
        "testpypi upload failed, install skipped": (
            failed,
            [job(BUILD, "completed", "success"), job(TESTPYPI, "completed", "failure"), job(INSTALL, "completed", "skipped"), job(PYPI, "completed", "skipped"), job(REPUBLISH, "completed", "skipped")],
            "HALT_TESTPYPI",
        ),
        "released": (
            {"status": "completed", "conclusion": "success"},
            [job(BUILD, "completed", "success"), job(TESTPYPI, "completed", "success"), job(INSTALL, "completed", "success"), job(PYPI, "completed", "success"), job(REPUBLISH, "completed", "skipped")],
            "RELEASED",
        ),
    }


def main() -> int:
    ceremony = load_ceremony()
    bad = 0
    table = cases()
    for label, (run, jobs, want) in table.items():
        got = ceremony.classify_publish_run(dict(run, jobs=jobs))
        bad += got != want
        print(f"{'OK  ' if got == want else 'FAIL'} {label}: {got} (want {want})")
    print(f"{len(table) - bad} of {len(table)} as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
