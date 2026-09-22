#!/usr/bin/env python3
"""2026-09-22_env_floor_residual_mutation_check.py -- prove the residual-guard tests FAIL pre-fix.

Project: juniper-ml
Sub-Project: ad-hoc tooling (mutation check)
Application: ad-hoc verification
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

Adversarial validation of the 2026-09-22 `env_floor_drift_check.py` falsy-guard fix found two
residuals the first pass missed, both in `_load_ecosystem_envs` and both breaking the SAME
documented contract (*"empty on any failure … or malformed"*) by routes the first fix did not
close:

  1. `UnicodeDecodeError` is a `ValueError`, not an `OSError`, so a non-UTF-8 ecosystem.yaml
     escaped `except (OSError, yaml.YAMLError)`.
  2. A YAML KEY need not be a string. `NO:` parses as the boolean `False` (the "Norway
     problem") and `3:` as an int; both reached `site_packages_for_env`, where
     `conda_dir / "envs" / env_name` raises `TypeError` on a non-str.

A test that passes after a fix proves nothing on its own -- it must be shown to FAIL without
it, or "no longer fires" is indistinguishable from "never fired". This reverts the two guards
in a SCRATCHPAD COPY of the module (the repo tree is never modified) and asserts each new test
fails against it.

HOW THE REVERTED MODULE IS ACTUALLY LOADED -- and why the obvious way does not work

`tests/test_env_floor_drift_check.py` opens with the house idiom::

    UTIL_DIR = Path(__file__).resolve().parents[1] / "util"
    sys.path.insert(0, str(UTIL_DIR))
    import env_floor_drift_check as mod

`insert(0, ...)` puts the REAL `util/` ahead of anything on `PYTHONPATH`, so shadowing by
path order silently imports the unmutated module and every test passes -- a mutation check
that measured nothing and reports the fix as unnecessary. The first version of this script
did exactly that. The module is therefore pre-seeded into `sys.modules` under its own name
BEFORE the test module is imported, which `import` honours regardless of `sys.path`.

LIMITS

  * It checks the two RESIDUAL guards only. The first-pass guards (`_mapping` at the three
    original sites) are mutation-checked by their own tests failing at HEAD, recorded in the
    PR body.
  * A revert that fails to apply exits 2 rather than reporting a pass, because a mutation
    check that silently mutated nothing reports the un-mutated code as proof.
  * It asserts the seed took effect before running anything; a seed that did not bind is a
    measurement failure (exit 2), not a clean run.

EXIT CODES

  * 0 -- every targeted test failed against the reverted module (the fix is load-bearing).
  * 1 -- a test PASSED against the reverted module, i.e. it does not pin what it claims.
  * 2 -- the revert could not be applied, so nothing was measured.

Usage:
    python3 util/ad-hoc/2026-09-22_env_floor_residual_mutation_check.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
MODULE = REPO / "util" / "env_floor_drift_check.py"

REVERTS = (
    ("except (OSError, UnicodeDecodeError, yaml.YAMLError):", "except (OSError, yaml.YAMLError):"),
    ("        if not isinstance(env_name, str):\n            continue\n", ""),
)

TARGETS = (
    "test_load_ecosystem_envs_degrades_on_non_utf8_bytes",
    "test_load_ecosystem_envs_skips_a_non_string_env_name",
)

CLASS = "tests.test_env_floor_drift_check.MalformedOperatorInputGuardTest"


def _seed_reverted_module() -> int:
    """Build the reverted module and bind it in sys.modules under its import name."""
    mutated = MODULE.read_text(encoding="utf-8")
    for present, replacement in REVERTS:
        if present not in mutated:
            print(f"revert anchor not found, nothing was measured: {present!r}", file=sys.stderr)
            return 2
        mutated = mutated.replace(present, replacement)

    spec = importlib.util.spec_from_file_location("env_floor_drift_check", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register BEFORE exec so the test module's `import env_floor_drift_check` binds to this
    # object rather than re-importing the real file from util/.
    sys.modules["env_floor_drift_check"] = module
    exec(compile(mutated, str(MODULE), "exec"), module.__dict__)  # noqa: S102 - the point of the tool
    return 0


def main() -> int:
    sys.path.insert(0, str(REPO))
    rc = _seed_reverted_module()
    if rc:
        return rc

    suite = unittest.defaultTestLoader.loadTestsFromNames([f"{CLASS}.{t}" for t in TARGETS])

    # The seed is only meaningful if the TEST module bound to it. tests/… does
    # `sys.path.insert(0, util/)` then `import env_floor_drift_check`, which returns the
    # sys.modules entry -- but if anything imported the real module first, this check fails
    # loudly instead of reporting an unmutated run as proof.
    test_mod = sys.modules["tests.test_env_floor_drift_check"]
    if test_mod.mod is not sys.modules["env_floor_drift_check"]:
        print("the test module did NOT bind to the reverted module -- nothing was measured", file=sys.stderr)
        return 2

    result = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(suite)
    broke = len(result.failures) + len(result.errors)
    for case, _tb in result.failures + result.errors:
        print(f"FAILS (good)  {case._testMethodName}")
    passed = [t for t in TARGETS if not any(t == c._testMethodName for c, _ in result.failures + result.errors)]
    for name in passed:
        print(f"PASSES (BAD)  {name}")

    if broke != len(TARGETS):
        print(f"\n{len(TARGETS) - broke} test(s) passed against the REVERTED module -- they do not pin the fix.", file=sys.stderr)
        return 1
    print(f"\nall {len(TARGETS)} residual-guard test(s) fail without the fix -- the guards are load-bearing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
