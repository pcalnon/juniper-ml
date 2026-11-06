"""The juniper-ml#2210 ceiling is strict: equality is a refusal.

``check_per_run_timeout`` admits a suite only when ``per_run_timeout_seconds`` is
greater than every cell's worst-case driver budget. At equality the suite's
subprocess kill still lands before the driver writes ``manifest.json``, so the
comparison is ``>``, not ``>=`` (``util/experiments/run_suite.py``).

``tests/test_run_suite.py`` already refuses a timeout below the sum and admits
one a second above it. Those two results both survive a change of ``>`` to
``>=``. This file pins the boundary those tests skip: a timeout equal to the
sum, a zero budget (0 does not exceed 0), and a tie for the largest sum.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MODULE_PATH = _REPO_ROOT / "util" / "experiments" / "run_suite.py"
_spec = importlib.util.spec_from_file_location("run_suite_boundary", _MODULE_PATH)
run_suite = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_suite)


# The sums used by tests/test_run_suite.py::test_the_refusal_names_the_largest_cell.
_BUDGETS = {
    "c000-small": {"health_wait": 180.0, "drive": 60.0},  # 240
    "c001-large": {"health_wait": 180.0, "drive": 900.0},  # 1080
}


class PerRunTimeoutBoundaryTest(unittest.TestCase):
    def test_a_timeout_equal_to_the_largest_budget_is_refused(self) -> None:
        with self.assertRaises(run_suite.SuiteError) as caught:
            run_suite.check_per_run_timeout(1080.0, _BUDGETS)
        message = str(caught.exception)
        self.assertIn(
            "execution.per_run_timeout_seconds=1080 does not exceed the worst-case driver budget of 1 of 2 cell(s); the largest is c001-large at 1080s (health_wait 180 + drive 900).",
            message,
        )
        self.assertIn("Raise per_run_timeout_seconds above 1080", message)

    def test_a_timeout_one_second_above_the_largest_budget_is_admitted(self) -> None:
        self.assertIsNone(run_suite.check_per_run_timeout(1081.0, _BUDGETS))

    def test_a_zero_timeout_does_not_clear_a_zero_budget(self) -> None:
        """0 is a measured budget, not an absent one. It does not exceed itself."""
        with self.assertRaises(run_suite.SuiteError) as caught:
            run_suite.check_per_run_timeout(0.0, {"c000": {"drive": 0.0}})
        message = str(caught.exception)
        self.assertIn("execution.per_run_timeout_seconds=0 does not exceed the worst-case driver budget of 1 of 1 cell(s)", message)
        self.assertIn("the largest is c000 at 0s (drive 0)", message)
        self.assertIn("Raise per_run_timeout_seconds above 0", message)

    def test_cells_tied_for_the_largest_sum_are_all_counted_and_the_first_is_named(self) -> None:
        budgets = {
            "c000-first": {"drive": 50.0},
            "c001-second": {"drive": 50.0},
            "c002-under": {"drive": 10.0},
        }
        with self.assertRaises(run_suite.SuiteError) as caught:
            run_suite.check_per_run_timeout(50.0, budgets)
        message = str(caught.exception)
        self.assertIn("of 2 of 3 cell(s); the largest is c000-first at 50s (drive 50)", message)
        self.assertNotIn("c002-under", message)

    def test_an_undeclared_timeout_at_equality_names_the_default(self) -> None:
        with self.assertRaises(run_suite.SuiteError) as caught:
            run_suite.check_per_run_timeout(1080.0, _BUDGETS, declared=False)
        self.assertIn(
            "execution.per_run_timeout_seconds=1080 (the default: the suite sets none) does not exceed the worst-case driver budget of 1 of 2 cell(s)",
            str(caught.exception),
        )

    def test_an_empty_budget_map_is_not_a_refusal(self) -> None:
        self.assertIsNone(run_suite.check_per_run_timeout(0.0, {}))


if __name__ == "__main__":
    unittest.main()
