"""Pin the symbol-loss WEAKENED arms at equality.

``classify_file`` flags a Python body only when both hold:

    head_lines <= WEAKEN_RATIO * base_lines     # 0.6, inclusive
    base_lines - head_lines >= WEAKEN_MIN_DELTA  # 4, inclusive

``test_symbol_loss_check.py`` guts a body far past both arms, or shrinks it by
one line. Neither case fails if ``<=`` becomes ``<`` or ``>=`` becomes ``>``,
so a gutted function that lands on the threshold would pass the sequence-safety
screen, and a one-line-tighter delta would fail ordinary edits.
"""

from __future__ import annotations

import unittest

import juniper_ci_tools.symbol_loss_check as slc


def _function(line_count: int) -> str:
    """A ``def kept`` whose source segment is exactly ``line_count`` lines."""
    if line_count < 2:
        raise ValueError(line_count)
    lines = ["def kept():"]
    for i in range(line_count - 2):
        lines.append(f"    v{i} = {i}")
    lines.append("    return 0")
    return "\n".join(lines) + "\n"


def _inventory(line_count: int) -> dict[str, slc.Sym]:
    syms = slc.py_symbols(_function(line_count))
    if syms is None:
        raise AssertionError(f"function of {line_count} lines did not parse")
    counted = syms["func:kept"].lines
    if counted != line_count:
        raise AssertionError(f"expected {line_count} lines, segment counted {counted}")
    return syms


def _finding(base_lines: int, head_lines: int) -> slc.Finding | None:
    findings = slc.classify_file("util/h.py", _inventory(base_lines), _inventory(head_lines), False)
    matched = [f for f in findings if f.symbol == "func:kept"]
    if len(matched) > 1:
        raise AssertionError(matched)
    return matched[0] if matched else None


class WeakenBoundaryTest(unittest.TestCase):
    def test_exact_ratio_and_exact_delta_is_weakened(self) -> None:
        # 6 == 0.6 * 10 and 10 - 6 == 4. Both arms are equalities.
        base, head = 10, 6
        self.assertEqual(head, slc.WEAKEN_RATIO * base)
        self.assertEqual(base - head, slc.WEAKEN_MIN_DELTA)
        finding = _finding(base, head)
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual((finding.verdict, finding.severity), ("WEAKENED", "FAIL"))
        self.assertEqual(finding.detail["base_lines"], base)
        self.assertEqual(finding.detail["head_lines"], head)

    def test_one_line_over_the_ratio_is_not_weakened(self) -> None:
        # 9 == 0.6 * 15 would weaken (delta 6). 10 is one line over that ratio
        # while the line delta (5) is still at least WEAKEN_MIN_DELTA.
        base, head = 15, 10
        self.assertGreater(head, slc.WEAKEN_RATIO * base)
        self.assertLessEqual(head - 1, slc.WEAKEN_RATIO * base)
        self.assertGreaterEqual(base - head, slc.WEAKEN_MIN_DELTA)
        self.assertIsNone(_finding(base, head))

    def test_delta_one_under_the_minimum_is_not_weakened(self) -> None:
        # 4 <= 0.6 * 7 (4.2), so the ratio arm still holds. The delta is 3.
        base, head = 7, 4
        self.assertLessEqual(head, slc.WEAKEN_RATIO * base)
        self.assertEqual(base - head, slc.WEAKEN_MIN_DELTA - 1)
        self.assertIsNone(_finding(base, head))

    def test_exact_delta_with_ratio_to_spare_is_weakened(self) -> None:
        # 3 < 0.6 * 7, so the ratio comparison is not the deciding arm.
        # The delta is exactly 4.
        base, head = 7, 3
        self.assertLess(head, slc.WEAKEN_RATIO * base)
        self.assertEqual(base - head, slc.WEAKEN_MIN_DELTA)
        finding = _finding(base, head)
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual((finding.verdict, finding.severity), ("WEAKENED", "FAIL"))
        self.assertEqual((finding.detail["base_lines"], finding.detail["head_lines"]), (base, head))


if __name__ == "__main__":
    unittest.main()
