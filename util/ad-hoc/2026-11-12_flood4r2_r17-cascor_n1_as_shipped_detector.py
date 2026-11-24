#!/usr/bin/env python3
"""
Run juniper-cascor's paused-fit mutation check on a tree with the detector it shipped with (its first two test files).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/r17-cascor-code-lens-s5/findings.json F1; juniper-cascor
         util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py (juniper-cascor#753), whose
         ``TESTS`` tuple the stop-then-start carrier extends with its own test module

The carrier's copy of that script names three test files. This runs the SAME script, loaded from
``--tree``, with ``TESTS`` cut back to the first ``--keep`` entries (2: the detector as
juniper-cascor#753 shipped it), so the "before" figure of the detector change is measured on the
carrier's final source bytes without editing any file of the carrier. Nothing else of the script
is changed: its mutants, its hermetic copies, its provenance plugin and its exit code are its own.
The six Sentry DSN variables are set to the empty string and ``JUNIPER_CASCOR_LOG_DIR`` is
dropped before the script runs (it copies ``os.environ`` for every pytest it starts). The sha256
of the script and of the files it mutates or runs is printed before and after.

Usage:
  2026-11-12_flood4r2_r17-cascor_n1_as_shipped_detector.py --tree <cascor checkout> --base <ref> [--keep 2]
Exit: the script's own exit code (0 when its control is green and every mutation is caught).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import sys
from pathlib import Path

SCRIPT = "util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py"
WATCHED = (SCRIPT, "src/api/lifecycle/manager.py", "src/api/lifecycle/state_machine.py")
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def _digests(tree: Path, paths: tuple) -> dict:
    return {relative: hashlib.sha256((tree / relative).read_bytes()).hexdigest() for relative in paths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="the juniper-cascor checkout whose script and source are used")
    parser.add_argument("--base", required=True, help="the ref whose manager.py and state_machine.py the script's M00 restores")
    parser.add_argument("--keep", type=int, default=2, help="how many leading TESTS entries to keep (2 = as juniper-cascor#753 shipped)")
    args = parser.parse_args()
    tree = args.tree.resolve()

    os.environ.pop("JUNIPER_CASCOR_LOG_DIR", None)
    os.environ.update({name: "" for name in SENTRY_DSN_NAMES})

    spec = importlib.util.spec_from_file_location("_paused_fit_wedge_mutation_check", tree / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    kept = tuple(module.TESTS[: args.keep])
    print(f"script: {tree / SCRIPT}")
    print(f"TESTS in the script: {list(module.TESTS)}")
    print(f"TESTS used for this run: {list(kept)}")
    module.TESTS = kept
    watched = WATCHED + kept
    before = _digests(tree, watched)
    for relative, digest in before.items():
        print(f"sha256 before  {digest}  {relative}")
    sys.stdout.flush()

    sys.argv = [str(tree / SCRIPT), "--base", args.base]
    code = module.main()

    after = _digests(tree, watched)
    print(f"checkout unchanged: {after == before}")
    print(f"script exit: {code}")
    return code if after == before else 1


if __name__ == "__main__":
    sys.exit(main())
