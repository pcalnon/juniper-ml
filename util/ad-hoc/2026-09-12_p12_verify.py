#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.2)
Application: ad-hoc verification
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: verify P1.2 against the PATCHED logger -- one numeric level table, symbolic level
constants, and no third table -- before the change is pushed.

Set ``P12_TREE`` to a directory containing a patched ``src/`` (log_config + profiling packages
complete, or the import resolves to the real checkout and the probe silently measures the
UNPATCHED file -- which is exactly what happened on the first attempt).

torch is stubbed: JuniperCascor1 moved to Python 3.14 on 2026-09-12 while torch 2.11.0 remains
under lib/python3.13/site-packages, so it is unimportable there. constants_activation uses torch
only to build ``torch.nn.<Class>()`` singletons, so no level number depends on it.
"""
import os
import subprocess
import sys

TREE = os.environ.get("P12_TREE", "/tmp/claude-1000/p12")
CASCOR_SRC = os.environ.get("P12_CASCOR_SRC", "/home/pcalnon/Development/python/Juniper/juniper-cascor/src")

CHILD = r'''
import sys, types
_t = types.ModuleType("torch"); _nn = types.ModuleType("torch.nn")
class _A:
    def __init__(self, *a, **k): pass
    def __call__(self, *a, **k): return None
_nn.__getattr__ = lambda n: _A
_t.__getattr__ = lambda n: _A
_t.nn = _nn
sys.modules["torch"] = _t; sys.modules["torch.nn"] = _nn

sys.path.insert(0, "@@TREE@@/src")
sys.path.insert(1, "@@SRC@@")

from cascor_constants.constants import _LOGGER_LOG_LEVEL_NUMBERS_DICT as CANON
from log_config.logger.logger import Logger
import log_config.logger.logger as M
print("LOADED=" + M.__file__)
print("DERIVED_EQUAL=" + repr(dict(Logger._level_numbers) == dict(CANON)))
print("IS_COPY=" + repr(Logger._level_numbers is not CANON))
SYMS = ("TRACE", "VERBOSE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL")
got = {}
for n in SYMS:
    got[n] = getattr(Logger, n, "<MISSING>")
print("SYMS=" + repr(got))
print("SYMS_MATCH=" + repr(all(got[n] == CANON.get(n) for n in SYMS)))
# the name attributes must remain STRINGS -- P1.2(d)'s collision hazard
print("NAME_ATTRS=" + repr({"_level_trace": Logger._level_trace, "_level_verbose": Logger._level_verbose}))
# the resolution paths must still work
print("RESOLVE=" + repr({n: Logger._resolve_level_number(n) for n in SYMS}))
print("VALID_OK=" + repr(all(Logger.is_valid_level(n) for n in SYMS)))
print("VALID_JUNK=" + repr(Logger.is_valid_level("BANANA")))

import profiling.logging_utils as LU
import profiling.logging_utils
print("LU_FILE=" + profiling.logging_utils.__file__)
print("LU_HAS_TRACE=" + repr(hasattr(LU, "TRACE")))
print("LU_HAS_VERBOSE=" + repr(hasattr(LU, "VERBOSE")))
print("LU_CLASSES=" + repr(sorted(n for n in ("SampledLogger", "BatchLogger", "LogFrequencyTracker",
                                              "log_if_enabled", "log_timing") if hasattr(LU, n))))
'''


def main():
    env = {k: v for k, v in os.environ.items()
           if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    src = CHILD.replace("@@TREE@@", TREE).replace("@@SRC@@", CASCOR_SRC)
    out = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, env=env, check=False)
    if out.returncode != 0:
        print("child failed:\n" + out.stderr[-1800:])
        return 2

    v = {}
    for line in out.stdout.splitlines():
        if "=" in line:
            k, _, val = line.partition("=")
            v[k] = val

    loaded = v.get("LOADED", "")
    print(f"logger loaded from : {loaded}")
    if not loaded.startswith(TREE):
        print("  !! that is NOT the patched tree -- the probe would be measuring the unpatched file.")
        print("     (the staged tree needs its __init__.py files, or the package resolves elsewhere)")
        return 1
    print(f"logging_utils from : {v.get('LU_FILE')}")

    ok = True

    def check(label, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print(f"  [{'ok ' if good else 'FAIL'}] {label}: {got}")

    print("\nP1.2(b) -- the duplicate table is derived, not restated")
    check("Logger._level_numbers equals the canonical table", v.get("DERIVED_EQUAL"), "True")
    check("it is a copy, not an alias", v.get("IS_COPY"), "True")

    print("\nP1.2(d) -- symbolic level NUMBERS, no collision with the name strings")
    print(f"        {v.get('SYMS')}")
    check("every symbol matches the canonical table", v.get("SYMS_MATCH"), "True")
    print(f"        name attrs remain strings: {v.get('NAME_ATTRS')}")

    print("\n  resolution and validity still work")
    print(f"        {v.get('RESOLVE')}")
    check("every level resolves", v.get("VALID_OK"), "True")
    check("junk still rejected (P1.1(c) holds)", v.get("VALID_JUNK"), "False")

    print("\nP1.2(c) -- the third, contradicting table is gone")
    check("profiling.logging_utils has no TRACE", v.get("LU_HAS_TRACE"), "False")
    check("profiling.logging_utils has no VERBOSE", v.get("LU_HAS_VERBOSE"), "False")
    print(f"        its classes/helpers survive: {v.get('LU_CLASSES')}")

    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
