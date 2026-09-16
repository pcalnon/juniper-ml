#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.2)
Application: ad-hoc probe
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: establish whether juniper-cascor's THREE level-number tables agree, before P1.2
collapses them -- a swap is only behaviour-preserving if the tables it merges are equal.

The three:

  1. CANONICAL -- ``_PROJECT_LOG_LEVEL_NUMBER_*`` in ``cascor_constants/constants.py``, reaching
     ``logger.py`` as ``_LOGGER_LOG_LEVEL_NUMBERS_DICT`` through a three-step alias chain
     (``_PROJECT_… :571`` -> ``_LOG_CONFIG_… :1140`` -> ``_LOGGER_… :1209``). Imported at
     ``logger.py:93`` and used by the INSTANCE path (``self.log_level_numbers_dict``).
  2. DUPLICATE -- ``Logger._level_numbers``, hardcoded in the class body, used by the CLASS path
     (``_is_valid_level_number`` :383, ``_get_level_number`` :395, ``_get_level_name`` :404).
  3. CONTRADICTING -- ``profiling/logging_utils.py`` ``TRACE`` / ``VERBOSE``.

Note the shape: 1 and 2 are the same split P1.1 fixed for the configured LEVEL, one level up --
the class path and the instance path reading different objects that merely happen to agree.

Read-only.
"""
import os
import subprocess
import sys

CASCOR_SRC = os.environ.get("P12_CASCOR_SRC", "/home/pcalnon/Development/python/Juniper/juniper-cascor/src")

CHILD = r'''
import sys, types
sys.path.insert(0, "@@SRC@@")

# torch is STUBBED, and must be, as of 2026-09-12: the JuniperCascor1 conda env was moved from
# Python 3.13.13 to 3.14.7 while torch 2.11.0 remains installed only under
# lib/python3.13/site-packages, so `import torch` fails in that env and the 3.13 interpreter
# binary is gone. cascor_constants/constants.py imports constants_activation, whose ONLY use of
# torch is calling torch.nn.<Class>() constructors (16 sites) to build activation-function
# singletons. None of that touches a level NUMBER, so a stub cannot change the values this probe
# reads. It is declared loudly rather than hidden, because a probe that silently fakes a
# dependency is a probe you cannot trust about the thing it measures.
if "torch" not in sys.modules:
    try:
        import torch  # noqa: F401
        STUBBED = False
    except ModuleNotFoundError:
        _t = types.ModuleType("torch")
        _nn = types.ModuleType("torch.nn")
        class _Act:
            def __init__(self, *a, **k): pass
            def __call__(self, *a, **k): return None
        # Both levels need a catch-all: constants_activation reads torch.nn.<Class> (16 sites)
        # AND bare torch.<fn> such as torch.tanh.
        _nn.__getattr__ = lambda name: _Act
        _t.__getattr__ = lambda name: _Act
        _t.nn = _nn
        sys.modules["torch"] = _t
        sys.modules["torch.nn"] = _nn
        STUBBED = True
print("TORCH_STUBBED=" + repr(STUBBED))

from cascor_constants.constants import _LOGGER_LOG_LEVEL_NUMBERS_DICT as CANON
from log_config.logger.logger import Logger
DUP = Logger._level_numbers
print("CANON=" + repr(dict(sorted(CANON.items()))))
print("DUP=" + repr(dict(sorted(DUP.items()))))
print("EQUAL=" + repr(dict(CANON) == dict(DUP)))
try:
    from profiling import logging_utils as LU
    print("THIRD=" + repr({"TRACE": LU.TRACE, "VERBOSE": LU.VERBOSE}))
except Exception as exc:  # noqa: BLE001 -- reporting the failure is the point
    print("THIRD_ERR=" + repr(str(exc)))
'''


def main():
    env = {k: v for k, v in os.environ.items()
           if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    out = subprocess.run([sys.executable, "-c", CHILD.replace("@@SRC@@", CASCOR_SRC)],
                         capture_output=True, text=True, env=env, check=False)
    if out.returncode != 0:
        print("child failed:\n" + out.stderr[-1500:])
        return 2

    vals = {}
    for line in out.stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            vals[k] = v

    canon = eval(vals.get("CANON", "{}"))  # noqa: S307 -- our own child's repr
    dup = eval(vals.get("DUP", "{}"))  # noqa: S307
    third = eval(vals.get("THIRD", "{}")) if "THIRD" in vals else None

    if vals.get("TORCH_STUBBED") == "True":
        print("NOTE: torch was STUBBED -- it is unimportable in JuniperCascor1 since the env moved")
        print("      to Python 3.14 while torch 2.11.0 sits under lib/python3.13/site-packages.")
        print("      constants_activation uses torch only for torch.nn.<Class>() singletons, so")
        print("      no level NUMBER below depends on it.\n")

    print("1. CANONICAL  cascor_constants -> _LOGGER_LOG_LEVEL_NUMBERS_DICT (instance path)")
    print(f"   {canon}")
    print("2. DUPLICATE  Logger._level_numbers, hardcoded (class path)")
    print(f"   {dup}")
    print(f"\n   EQUAL? {canon == dup}")
    if canon != dup:
        keys = sorted(set(canon) | set(dup))
        print("   differences:")
        for k in keys:
            a, b = canon.get(k), dup.get(k)
            if a != b:
                print(f"     {k}: canonical={a!r} duplicate={b!r}")
        print("\n   => the swap is NOT behaviour-preserving; reconcile deliberately.")
    else:
        print("   => the duplicate agrees exactly, so deriving it from the canonical table")
        print("      changes no value. It removes the ability to DRIFT, which is the point.")

    print("\n3. CONTRADICTING  profiling/logging_utils.py")
    if third is None:
        print(f"   could not import: {vals.get('THIRD_ERR')}")
    else:
        print(f"   {third}")
        bad = {k: (third[k], canon.get(k)) for k in third if canon.get(k) != third[k]}
        if bad:
            print("   disagrees with canonical on:")
            for k, (got, want) in bad.items():
                print(f"     {k}: logging_utils={got!r}  canonical={want!r}")
            print("   Its comment claims it matches log_config's custom levels. It does not.")
        else:
            print("   agrees with canonical (the roadmap's claim would be stale)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
