"""``screen_coverage`` must not call an unscreened ERROR row a pass.

``triage_batch`` writes ``gates: {}`` when one PR cannot be simulated (the ``ERROR``
row). On 2026-11-06 that was 56 of 57 open juniper-ml PRs: the scratch could not
see shallow ``origin/*`` heads. A missing, blank, or unknown status is ``absent``
and stays out of ``evaluated``. Mapping it to ``pass`` would report that flood as
screened fraction 1. ``unscreened`` stays the ``skip`` set. An empty verdict list
reports fraction 0 rather than dividing by zero.

The row shape is the one ``triage_batch`` builds. Production is unchanged.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from fleet_triage.predict_merge import PRECOMMIT_HOOKS, screen_coverage  # noqa: E402

_GATES = ("ast_symbol_screen", "docs_additions_only") + PRECOMMIT_HOOKS


def _error_row(pr: int) -> dict:
    """The dict ``triage_batch`` appends when ``simulate_merge`` raises."""
    return {
        "pr": pr,
        "branch": f"origin/cursor/pr-{pr}",
        "verdict": "ERROR",
        "error": "could not pin refs/fleet/branch -> abc in scratch clone: nonexistent object",
        "true_delta": [],
        "gates": {},
    }


def _screened(pr: int, status: str) -> dict:
    verdict = "MERGE-CLEAN" if status == "pass" else "CONFLICT"
    return {
        "pr": pr,
        "verdict": verdict,
        "gates": {
            "ast_symbol_screen": {"status": status},
            "docs_additions_only": {"status": status},
        },
    }


class ErrorRowScreenCoverageTest(unittest.TestCase):
    def _assert_absent(self, tally: dict, count: int) -> None:
        self.assertEqual(tally["absent"], count)
        self.assertEqual(tally["pass"], 0)
        self.assertEqual(tally["fail"], 0)
        self.assertEqual(tally["skip"], 0)
        self.assertEqual(tally["evaluated"], 0)
        self.assertEqual(tally["screened_fraction"], 0.0)

    def test_an_error_row_with_empty_gates_is_absent_on_every_gate(self) -> None:
        """The shallow-checkout flood's row is not a pass and is not ``unscreened``.

        ``unscreened`` is the ``skip`` set (a conflict). An ERROR row was never
        screened either, and the honest signal is ``absent`` with fraction 0.
        """
        cov = screen_coverage([_error_row(57), _error_row(56)])
        self.assertEqual(cov["unscreened"], [])
        self.assertEqual(cov["unscreened_count"], 0)
        self.assertEqual(tuple(cov["per_gate"]), _GATES)
        for gate, tally in cov["per_gate"].items():
            with self.subTest(gate=gate):
                self._assert_absent(tally, 2)

    def test_a_blank_or_unknown_status_stays_out_of_the_denominator(self) -> None:
        """Only the exact tokens ``pass`` / ``fail`` / ``skip`` enter ``evaluated``.

        ``None``, ``""``, ``"error"``, ``"PASS"`` and ``"skipped"`` are ``absent``.
        A neighbouring screen that really passed stays a pass, so one gate cannot
        launder the other.
        """
        cases = (None, "", "error", "PASS", "skipped")
        for status in cases:
            with self.subTest(status=repr(status)):
                verdict = {
                    "pr": 4,
                    "verdict": "ERROR",
                    "gates": {
                        "ast_symbol_screen": {"status": status},
                        "docs_additions_only": {"status": "pass"},
                    },
                }
                cov = screen_coverage([verdict])
                self._assert_absent(cov["per_gate"]["ast_symbol_screen"], 1)
                docs = cov["per_gate"]["docs_additions_only"]
                self.assertEqual(docs["pass"], 1)
                self.assertEqual(docs["absent"], 0)
                self.assertEqual(docs["evaluated"], 1)
                self.assertEqual(docs["screened_fraction"], 1.0)
                self.assertEqual(cov["unscreened"], [])

    def test_a_mixed_batch_excludes_the_error_row_from_the_denominator(self) -> None:
        """One pass, one ERROR, one conflict: evaluated is 1 of 3, and the conflict is named once."""
        cov = screen_coverage([_screened(7, "pass"), _error_row(8), _screened(9, "skip")])
        for gate in ("ast_symbol_screen", "docs_additions_only"):
            tally = cov["per_gate"][gate]
            with self.subTest(gate=gate):
                self.assertEqual(tally["pass"], 1)
                self.assertEqual(tally["skip"], 1)
                self.assertEqual(tally["fail"], 0)
                self.assertEqual(tally["absent"], 1)
                self.assertEqual(tally["evaluated"], 1)
                self.assertEqual(tally["screened_fraction"], 0.333)
        self.assertEqual(cov["unscreened"], [9])
        self.assertEqual(cov["unscreened_count"], 1)

    def test_an_empty_verdict_list_reports_zero_instead_of_dividing(self) -> None:
        """``--batch`` with no open PR still builds ``screen_coverage``."""
        cov = screen_coverage([])
        self.assertEqual(cov["unscreened"], [])
        self.assertEqual(cov["unscreened_count"], 0)
        self.assertEqual(tuple(cov["per_gate"]), _GATES)
        for gate, tally in cov["per_gate"].items():
            with self.subTest(gate=gate):
                self._assert_absent(tally, 0)


if __name__ == "__main__":
    unittest.main()
