"""
Pytest plugin: run canopy's lockfile-regen test as if on a non-Linux runner, to simulate CI's macOS leg on Linux.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy#792 (BSD base64 refuses `base64 -w0 FILE`); flood-3 record §6

Load with -p 2026-11-07_flood4_canopy_force_not_linux. FLOOD4_SIM_MODE selects:
  stand-in     -> the module's _on_linux() returns False (the probe decides whether the stand-in is used)
  no-stand-in  -> as above, and the probe always reports a working base64, so no stand-in is installed
                  (reproduces what the draft did on macOS)
Combined with a BSD-like base64 first on PATH, "stand-in" must pass and "no-stand-in" must fail.
"""

import os


def pytest_collection_modifyitems(session, config, items):
    mode = os.environ.get("FLOOD4_SIM_MODE", "")
    patched = set()
    for item in items:
        mod = getattr(item, "module", None)
        if mod is None or id(mod) in patched or not hasattr(mod, "_on_linux"):
            continue
        patched.add(id(mod))
        mod._on_linux = lambda: False
        if mode == "no-stand-in":
            mod._base64_runs_the_steps_form = lambda scratch: True
    config._flood4_patched = len(patched)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.write_line(f"FLOOD4-SIM mode={os.environ.get('FLOOD4_SIM_MODE', '')!r} patched_modules={getattr(config, '_flood4_patched', 0)}")
