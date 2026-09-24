"""Lane A probe: load tests/test_service_fork_drift.py from a given juniper-ml tree,
report the ecosystem root it resolves, and record EVERY subtest outcome (including
successes, which the default TextTestResult does not print).

Usage: python3 probe_run.py <juniper-ml-root> [--force-local]
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

root = Path(sys.argv[1]).resolve()
if "--force-local" in sys.argv:
    os.environ["JUNIPER_DRIFT_TEST_FORCE_LOCAL"] = "1"
else:
    os.environ.pop("JUNIPER_DRIFT_TEST_FORCE_LOCAL", None)
os.environ.pop("GITHUB_ACTIONS", None)

test_file = root / "tests" / "test_service_fork_drift.py"
spec = importlib.util.spec_from_file_location("fork_drift_probe_mod", test_file)
mod = importlib.util.module_from_spec(spec)
sys.modules["fork_drift_probe_mod"] = mod
spec.loader.exec_module(mod)

print(f"test file        : {test_file}")
print(f"juniper_ml_root  : {Path(mod.__file__).resolve().parent.parent}")
print(f"ecosystem_root   : {mod._find_ecosystem_root(Path(mod.__file__).resolve().parent.parent)}")
print(f"_FORK_REPOS      : {mod._FORK_REPOS}")
print(f"_ROOT_ANCHOR     : {mod._ROOT_ANCHOR_REPOS}")
print(f"guards           : {[(g.guard_id, g.status, len(g.sites)) for g in mod.GUARDS]}")


class Recorder(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.rows = []

    def addSubTest(self, test, subtest, outcome):
        super().addSubTest(test, subtest, outcome)
        if outcome is None:
            status = "PASS"
            detail = ""
        elif issubclass(outcome[0], test.failureException):
            status = "FAIL"
            detail = str(outcome[1]).splitlines()[0][:200]
        else:
            status = "ERROR"
            detail = repr(outcome[1])[:200]
        self.rows.append((test.id().split(".")[-1], subtest._subDescription(), status, detail))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        name = test.id().split(".")[-1] if hasattr(test, "id") else str(test)
        self.rows.append((name, "", "SKIP", reason[:160]))

    def addSuccess(self, test):
        super().addSuccess(test)
        self.rows.append((test.id().split(".")[-1], "", "TEST-OK", ""))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.rows.append((test.id().split(".")[-1], "", "TEST-FAIL", str(err[1]).splitlines()[0][:200]))

    def addError(self, test, err):
        super().addError(test, err)
        self.rows.append((test.id().split(".")[-1], "", "TEST-ERROR", repr(err[1])[:200]))


suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
result = Recorder()
suite.run(result)
for row in result.rows:
    print(" | ".join(row))
print(f"testsRun={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)} wasSuccessful={result.wasSuccessful()}")
