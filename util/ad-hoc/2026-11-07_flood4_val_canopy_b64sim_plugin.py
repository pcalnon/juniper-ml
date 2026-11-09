#!/usr/bin/env python3
"""
pytest plugin: run canopy's lockfile-regen test as the macOS leg would see it, and report which base64 ran.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#792 (carried with a macOS base64 fix); flood-4 validation brief

Controlled by environment variables (all optional):
  VAL_PREPEND_PATH     a directory put FIRST on PATH at configure time (a simulated BSD base64 lives there)
  VAL_SIM_PLATFORM     e.g. "darwin": sys.platform is monkeypatched for the lockfile module's tests only,
                       so the module's own _on_linux() answers as it would on the macOS runner
  VAL_DISABLE_STANDIN  "1": the module's probe is monkeypatched to report success, so no stand-in is
                       installed ("without the stand-in path")
  VAL_B64_REPORT       a file; after each lockfile test one line names which base64 the test's bin/ held:
                       STAND-IN (the module's _GNU_BASE64_STAND_IN), TEST-STUB (a case's own stub) or
                       REAL (nothing in bin/: the PATH's base64 ran)
Nothing in the test file is modified.
"""

from __future__ import annotations

import os
import sys

import pytest

LOCK_MODULE = "test_lockfile_regen_empty_payload"


def pytest_configure(config):  # noqa: ARG001 - pytest hook signature
    prepend = os.environ.get("VAL_PREPEND_PATH")
    if prepend:
        os.environ["PATH"] = prepend + os.pathsep + os.environ.get("PATH", "")


@pytest.fixture(autouse=True)
def _val_b64sim(request, monkeypatch, tmp_path):
    module = request.module
    if not getattr(module, "__name__", "").endswith(LOCK_MODULE):
        yield
        return
    sim = os.environ.get("VAL_SIM_PLATFORM")
    if sim:
        monkeypatch.setattr(sys, "platform", sim)
    if os.environ.get("VAL_DISABLE_STANDIN") == "1":
        assert hasattr(module, "_base64_runs_the_steps_form"), "module has no probe to disable"
        monkeypatch.setattr(module, "_base64_runs_the_steps_form", lambda scratch: True)
    yield
    report = os.environ.get("VAL_B64_REPORT")
    if report:
        stub = tmp_path / "bin" / "base64"
        standin = getattr(module, "_GNU_BASE64_STAND_IN", None)
        if stub.is_file():
            kind = "STAND-IN" if standin is not None and stub.read_text(encoding="utf-8") == standin else "TEST-STUB"
        elif (tmp_path / "bin").is_dir():
            kind = "REAL"
        else:
            kind = "NO-RUN"
        with open(report, "a", encoding="utf-8") as handle:
            handle.write(f"{kind}\tplatform={sys.platform}\t{request.node.nodeid}\n")
