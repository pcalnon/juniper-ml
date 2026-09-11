#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.1)
Application: ad-hoc verification
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: run P1.1's new regression suite against BOTH the patched and the unpatched logger,
to establish that it actually detects the defect.

A test that passes against the fix proves nothing on its own -- it must FAIL against the
code the fix replaces. This runs the identical test file against two trees:

  p11      -- log_config with P1.1 applied      -> expect PASS
  p11base  -- log_config exactly as cascor ships -> expect FAIL

Both trees are scratch copies; neither repository is modified.
"""
import os
import subprocess
import sys

#: Directory holding the two scratch trees ``p11`` (patched) and ``p11base`` (as-shipped), each
#: laid out as ``<tree>/log_config/...`` plus ``<tree>/tests/unit/<TEST_REL>``. Required: the
#: original default was this session's scratchpad, which exists for no one else, and a runner
#: pointed at a missing tree reports pytest's collection error as if it were the defect.
SCRATCH = os.environ.get("P11_SCRATCH")
CASCOR_SRC = os.environ.get("P11_CASCOR_SRC", "/home/pcalnon/Development/python/Juniper/juniper-cascor/src")
TEST_REL = "tests/unit/test_logger_level_state_reconciliation.py"


def run(tree):
    root = os.path.join(SCRATCH, tree)
    env = {k: v for k, v in os.environ.items()
           if k not in ("CASCOR_LOG_LEVEL", "JUNIPER_CASCOR_LOG_LEVEL")}
    env["PYTHONPATH"] = os.pathsep.join([root, CASCOR_SRC])
    logdir = os.path.join(SCRATCH, f"{tree}-logs")
    os.makedirs(logdir, exist_ok=True)
    env["JUNIPER_CASCOR_LOG_DIR"] = logdir  # trap 1: never share a log dir
    out = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(root, TEST_REL), "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True, text=True, env=env, cwd=root, check=False,
    )
    return out.returncode, out.stdout + out.stderr


def main():
    if not SCRATCH:
        print("P11_SCRATCH is not set. Point it at a directory containing both trees:")
        print("  <P11_SCRATCH>/p11/      -- log_config with P1.1 applied  + tests/unit/<suite>")
        print("  <P11_SCRATCH>/p11base/  -- log_config as cascor ships it + tests/unit/<suite>")
        return 2
    for tree in ("p11", "p11base"):
        missing = [p for p in (os.path.join(SCRATCH, tree, "log_config"),
                               os.path.join(SCRATCH, tree, TEST_REL)) if not os.path.exists(p)]
        if missing:
            print(f"tree {tree!r} is incomplete; missing: {missing}")
            print("Refusing to run: a collection error would be indistinguishable from the defect.")
            return 2

    results = {}
    for tree, expect, label in (("p11", 0, "PATCHED — P1.1 applied"),
                                ("p11base", 1, "BASELINE — cascor as it ships")):
        rc, text = run(tree)
        results[tree] = rc
        print(f"########## {label}  (exit {rc}, expected {'0' if expect == 0 else 'non-zero'}) ##########")
        tail = [ln for ln in text.strip().splitlines() if ln.strip()]
        print("\n".join(tail[-14:]))
        print()

    ok = results["p11"] == 0 and results["p11base"] != 0
    print("=" * 76)
    if ok:
        print("PASS: the suite passes on the fix and FAILS on the code the fix replaces.")
        print("      It is therefore capable of detecting the defect, not merely of agreeing")
        print("      with the implementation it was written against.")
    else:
        if results["p11"] != 0:
            print("FAIL: the suite does not pass against the patched logger.")
        if results["p11base"] == 0:
            print("FAIL: the suite PASSES against the unpatched logger -- it cannot detect the")
            print("      defect and is a vacuous guard. Do not ship it.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
