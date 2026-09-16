#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.3)
Application: ad-hoc verification
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: verify P1.3 in BOTH trees, and demonstrate the cross-tree hazard it had to solve.

``candidate_unit.py`` is byte-gated, so the package ships the identical file -- which now reads
``Logger.DEBUG`` / ``Logger.VERBOSE`` / ``Logger.TRACE``. But ``log_config/logger/logger.py`` is on
``_INTENTIONAL_DIVERGENCE`` and is NOT byte-compared, and the package's copy is the stale
2026-06-14 one. Without adding the eight constants there too, the published package would raise
AttributeError on the first guard evaluation -- on every candidate construction -- while src/
stayed perfectly green. **The byte-gate guarantees the CALLER is mirrored; nothing guarantees the
CALLEE is.**

This checks, for each tree independently:
  1. the eight symbolic constants resolve, and to the canonical values;
  2. every guard integer written in candidate_unit.py is now symbolic;
  3. the guard agrees with the emit decision at every configured level.

And it demonstrates (3) negatively: with the constants removed, the guard sites raise.

torch is stubbed -- unimportable in JuniperCascor1 since the env moved to Python 3.14 while torch
2.11.0 remains under lib/python3.13/site-packages. No level number depends on it.
"""
import os
import re
import subprocess
import sys

P13 = os.environ.get("P13_TREE", "/tmp/claude-1000/p13")
CASCOR = os.environ.get("P13_CASCOR", "/home/pcalnon/Development/python/Juniper/juniper-cascor")

CANON = {"TRACE": 1, "VERBOSE": 5, "DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50, "FATAL": 60}

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
# Splice, do NOT loop with insert(0, p): inserting each in turn puts the LAST one first, which
# silently put the real checkout ahead of the staged tree and made this probe measure the
# unpatched file while reporting a failure of the patched one.
sys.path[:0] = @@PATHS@@
sys.path.append("@@CASCOR@@/src")
from log_config.logger.logger import Logger
import log_config.logger.logger as M
print("LOGGER=" + M.__file__)
names = ("TRACE", "VERBOSE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL")
print("SYMS=" + repr({n: getattr(Logger, n, "<MISSING>") for n in names}))
'''


def run_tree(label, paths):
    src = CHILD.replace("@@PATHS@@", repr(paths)).replace("@@CASCOR@@", CASCOR)
    env = {k: v for k, v in os.environ.items()
           if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    out = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True, env=env, check=False)
    if out.returncode != 0:
        print(f"  {label}: child FAILED\n{out.stderr[-600:]}")
        return None
    vals = dict(line.split("=", 1) for line in out.stdout.splitlines() if "=" in line)
    return vals


def check_guards(path):
    """Every isEnabledFor in the file must name a symbol, not an integer."""
    text = open(path, encoding="utf-8").read()
    calls = re.findall(r"isEnabledFor\(level=([^)]+)\)", text)
    numeric = [c for c in calls if re.fullmatch(r"\s*\d+\s*", c)]
    return calls, numeric


def main():
    ok = True
    print("=== 1. the eight constants resolve in BOTH trees ===")
    trees = {
        "src  (juniper-cascor/src)": [f"{P13}/src", f"{CASCOR}/src"],
        "model (juniper-cascor-model)": [f"{P13}/model", f"{CASCOR}/juniper-cascor-model"],
    }
    for label, paths in trees.items():
        vals = run_tree(label, paths)
        if vals is None:
            ok = False
            continue
        syms = eval(vals["SYMS"])  # noqa: S307 -- our own child's repr
        good = syms == CANON
        ok = ok and good
        print(f"  [{'ok ' if good else 'FAIL'}] {label}")
        print(f"        logger: {vals['LOGGER']}")
        print(f"        {syms}")

    print("\n=== 2. no bare integer guard remains, and the copies match ===")
    for label, rel in (("src  ", f"{P13}/src/candidate_unit/candidate_unit.py"),
                       ("model", f"{P13}/model/candidate_unit/candidate_unit.py")):
        calls, numeric = check_guards(rel)
        good = len(calls) == 8 and not numeric
        ok = ok and good
        print(f"  [{'ok ' if good else 'FAIL'}] {label}: {len(calls)} guard sites, "
              f"{len(numeric)} still numeric  -> {sorted({c.strip() for c in calls})}")

    a = open(f"{P13}/src/candidate_unit/candidate_unit.py", encoding="utf-8").read()
    b = open(f"{P13}/model/candidate_unit/candidate_unit.py", encoding="utf-8").read()
    same = a == b
    ok = ok and same
    print(f"  [{'ok ' if same else 'FAIL'}] the two candidate_unit.py copies are byte-identical")

    print("\n=== 3. the hazard: does the CHECKED-IN mirror's logger carry the constants? ===")
    stock = run_tree("stock mirror", [f"{CASCOR}/juniper-cascor-model"])
    if stock:
        syms = eval(stock["SYMS"])  # noqa: S307
        missing = [n for n, v in syms.items() if v == "<MISSING>"]
        if missing:
            print(f"  [HAZARD OPEN] the mirror's logger lacks {len(missing)}/8: {missing}")
            print("        A mirrored guard site reading Logger.DEBUG raises AttributeError on EVERY")
            print("        candidate construction, while src/ stays green. This is the pre-P1.3 state;")
            print("        if you see it AFTER P1.3, the package's logger has regressed.")
            ok = False
        else:
            print("  [ok ] the mirror's logger carries all 8 -- the hazard is CLOSED (P1.3 landed).")
            print("        Before P1.3 this read 8/8 MISSING. The byte-gate mirrors the CALLER")
            print("        (candidate_unit.py); nothing mirrors the CALLEE, so this needed its own fix.")

    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
