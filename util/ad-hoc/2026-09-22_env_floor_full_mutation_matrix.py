#!/usr/bin/env python3
"""2026-09-22_env_floor_full_mutation_matrix.py -- which of the 12 guard tests actually pin the fix?

Project: juniper-ml
Sub-Project: ad-hoc tooling (mutation check)
Application: ad-hoc verification
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

ml#2001's body and the 2026-09-11 handoff both claim *"5 + 2 mutation-checked against the
pre-fix code, the rest negative controls."* Those two figures came from **two separate
partial runs** -- 5 of the original 8 tests, then the 2 residual guards added later -- and
were added together without re-running the whole class against one baseline. That is the
same units-from-different-runs error the falsy-guard census taught (§2a of
`notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md`), applied to a
claim ABOUT rigour rather than to the population.

This runs **every** test in `MalformedOperatorInputGuardTest` against the module as it
stood immediately before ml#2001, so the split between "pins the fix" and "negative
control" is one measurement rather than an arithmetic guess.

HOW THE PRE-FIX MODULE IS LOADED

`tests/test_env_floor_drift_check.py` does `sys.path.insert(0, util/)` then
`import env_floor_drift_check`. That beats `PYTHONPATH`, so shadowing by path order
silently tests the CURRENT module and reports every test as a negative control. The
pre-fix source is therefore pre-seeded into `sys.modules` before the test module is
imported, and the binding is asserted before anything runs. See
`util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py`, whose first version made
exactly that mistake.

LIMITS

  * The baseline is `<merge-commit>^` for ml#2001 -- the tree before the guards landed. It
    is NOT a per-guard mutation: a test that fails here may fail because of any of the five
    sites, not the one it names. For per-guard attribution use the residual-pair script.
  * A test that passes here is a negative control *for this change*, not proof it is
    worthless -- it may pin behaviour an earlier PR established.

EXIT CODES

  * 0 -- ran and reported.
  * 2 -- the baseline blob or the seed could not be established, so nothing was measured.

Usage:
    python3 util/ad-hoc/2026-09-22_env_floor_full_mutation_matrix.py
    python3 util/ad-hoc/2026-09-22_env_floor_full_mutation_matrix.py --base <rev>
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import pathlib
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
MODULE = REPO / "util" / "env_floor_drift_check.py"
MODULE_REL = "util/env_floor_drift_check.py"
CLASS = "tests.test_env_floor_drift_check.MalformedOperatorInputGuardTest"
DEFAULT_BASE = "e6419175^"  # the commit before ml#2001 landed the guards


def main(argv: "list[str] | None" = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=DEFAULT_BASE, help=f"rev to take the pre-fix module from (default {DEFAULT_BASE})")
    args = p.parse_args(argv)

    proc = subprocess.run(["git", "show", f"{args.base}:{MODULE_REL}"], cwd=REPO, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"cannot read {args.base}:{MODULE_REL} -- nothing was measured", file=sys.stderr)
        return 2
    baseline = proc.stdout

    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location("env_floor_drift_check", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["env_floor_drift_check"] = module          # register BEFORE exec
    exec(compile(baseline, MODULE_REL, "exec"), module.__dict__)  # noqa: S102 - the point of the tool

    loader = unittest.defaultTestLoader
    suite = loader.loadTestsFromName(CLASS)

    def _flatten(s):
        """A TestSuite nests arbitrarily; a TestCase is not iterable. Walk, don't index."""
        for item in s:
            if isinstance(item, unittest.TestSuite):
                yield from _flatten(item)
            else:
                yield item

    names = [t._testMethodName for t in _flatten(suite)]
    if not names:
        print("loaded zero tests -- nothing was measured", file=sys.stderr)
        return 2

    test_mod = sys.modules.get("tests.test_env_floor_drift_check")
    if test_mod is None or test_mod.mod is not sys.modules["env_floor_drift_check"]:
        print("the test module did NOT bind to the baseline module -- nothing was measured", file=sys.stderr)
        return 2

    result = unittest.TextTestRunner(verbosity=0, stream=io.StringIO()).run(suite)
    broke = {c._testMethodName for c, _ in result.failures + result.errors}

    print(f"baseline: {args.base}  ({len(names)} tests in {CLASS.rsplit('.', 1)[1]})")
    print()
    for n in sorted(names):
        print(f"  {'PINS THE FIX ' if n in broke else 'control      '} {n}")
    print()
    print(f"pins the fix: {len(broke)}   negative controls: {len(names) - len(broke)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
