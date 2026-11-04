"""Edges of ``AnomalyDetector`` the happy-path suite does not reach.

The existing checks send a score well past each threshold, three identical
floats, and a window of distinct scores. They do not pin the strict bounds, a
score whose magnitude is small but negative, or the duplicate rule itself:
the whole window must print as one value to six decimals, and an older
different score keeps a repeated run from looking stuck until that score ages
out of the window.
"""

from __future__ import annotations

import re

from juniper_service_core.workers import AnomalyDetector

_DUPLICATE = re.compile(r"duplicate_scores: 1/3 unique \(hash=[0-9a-f]{8}\)\Z")


def _kinds(anomalies: list[str]) -> set[str]:
    return {item.split(":", 1)[0] for item in anomalies}


def test_thresholds_are_strict_and_a_negative_score_uses_its_magnitude() -> None:
    """A value sitting on the bound is clean. Just past it is not.

    ``score < threshold`` without ``abs`` would call every negative score stale,
    including -0.5, and would still miss nothing at the positive bound. ``>=``
    on the perfect score, or ``<=`` on the stale score, would flag the bound.
    """
    det = AnomalyDetector()

    assert det.check_result("duration-bound", score=0.5, training_duration=0.1, task_id="t") == []
    assert det.check_result("perfect-bound", score=0.999, training_duration=1.0, task_id="t") == []
    assert det.check_result("stale-bound", score=0.001, training_duration=1.0, task_id="t") == []
    assert det.check_result("stale-negative-bound", score=-0.001, training_duration=1.0, task_id="t") == []
    assert det.check_result("large-negative", score=-0.5, training_duration=1.0, task_id="t") == []

    assert _kinds(det.check_result("fast", score=0.5, training_duration=0.099, task_id="t")) == {"suspiciously_fast"}
    assert _kinds(det.check_result("perfect", score=0.9990001, training_duration=1.0, task_id="t")) == {"perfect_score"}
    assert _kinds(det.check_result("stale", score=0.000999, training_duration=1.0, task_id="t")) == {"stale_score"}
    assert _kinds(det.check_result("stale-negative", score=-0.0005, training_duration=1.0, task_id="t")) == {"stale_score"}


def test_one_result_can_carry_both_a_fast_time_and_a_perfect_score() -> None:
    det = AnomalyDetector()
    assert _kinds(det.check_result("w", score=1.0, training_duration=0.0, task_id="t")) == {"suspiciously_fast", "perfect_score"}


def test_two_identical_scores_are_not_a_duplicate_and_the_third_is() -> None:
    det = AnomalyDetector()
    assert det.check_result("w", score=0.42, training_duration=1.0, task_id="t0") == []
    assert "duplicate_scores" not in _kinds(det.check_result("w", score=0.42, training_duration=1.0, task_id="t1"))
    third = det.check_result("w", score=0.42, training_duration=1.0, task_id="t2")
    assert any(_DUPLICATE.fullmatch(item) for item in third)


def test_float_noise_that_prints_to_the_same_six_decimals_is_one_score() -> None:
    """Exact equality would miss a stuck worker whose scores differ past the sixth decimal."""
    scores = (0.42, 0.4200004, 0.4199995)
    assert {f"{score:.6f}" for score in scores} == {"0.420000"}
    det = AnomalyDetector()
    last: list[str] = []
    for index, score in enumerate(scores):
        last = det.check_result("w", score=score, training_duration=1.0, task_id=f"t{index}")
        if index < 2:
            assert "duplicate_scores" not in _kinds(last)
    assert any(_DUPLICATE.fullmatch(item) for item in last)


def test_a_difference_at_the_sixth_decimal_is_not_a_duplicate() -> None:
    """A coarser format (five decimals) would call these one score."""
    assert f"{0.4200006:.6f}" == "0.420001"
    det = AnomalyDetector()
    last: list[str] = []
    for index, score in enumerate((0.42, 0.42, 0.4200006)):
        last = det.check_result("w", score=score, training_duration=1.0, task_id=f"t{index}")
    assert "duplicate_scores" not in _kinds(last)


def test_an_older_different_score_blocks_the_flag_until_it_ages_out() -> None:
    """The window is what is compared. The discarded prefix must not keep a stuck worker clean."""
    det = AnomalyDetector(duplicate_window=3)
    for index, score in enumerate((0.10, 0.50, 0.50)):
        assert "duplicate_scores" not in _kinds(det.check_result("w", score=score, training_duration=1.0, task_id=f"t{index}"))
    aged = det.check_result("w", score=0.50, training_duration=1.0, task_id="t3")
    assert any(_DUPLICATE.fullmatch(item) for item in aged)
    assert det.get_worker_stats("w")["total_results"] == 3


def test_a_later_different_score_clears_the_duplicate() -> None:
    det = AnomalyDetector(duplicate_window=3)
    for index in range(3):
        det.check_result("w", score=0.50, training_duration=1.0, task_id=f"t{index}")
    assert det.check_result("w", score=0.11, training_duration=1.0, task_id="t3") == []


def test_workers_do_not_share_a_window() -> None:
    det = AnomalyDetector()
    for index in range(3):
        det.check_result("w1", score=0.42, training_duration=1.0, task_id=f"t{index}")
    assert det.check_result("w2", score=0.42, training_duration=1.0, task_id="t0") == []
