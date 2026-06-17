"""Tests for index-based walk-forward fold generation (`juniper_model_core.crossval.splits`).

Covers expanding vs rolling fold counts and train growth, the leakage guard (no eval-before-train,
embargo gap respected), chronological ``order`` enforcement, ``min_train``, and the input-validation
error paths.
"""

import numpy as np
import pytest

from juniper_model_core.crossval import Fold, walk_forward_folds


def test_expanding_counts_growth_and_eval_blocks():
    folds = walk_forward_folds(100, n_folds=4)  # fold_size = 100 // 5 = 20
    assert len(folds) == 4
    assert all(isinstance(f, Fold) for f in folds)
    train_sizes = [len(f.train_idx) for f in folds]
    # expanding: train strictly grows each fold (20, 40, 60, 80)
    assert train_sizes == [20, 40, 60, 80]
    # equal-size eval blocks
    assert all(len(f.eval_idx) == 20 for f in folds)
    # no eval before train (identity order: positions are the indices)
    for f in folds:
        assert f.train_idx.max() < f.eval_idx.min()


def test_rolling_uses_fixed_window():
    folds = walk_forward_folds(100, n_folds=4, scheme="rolling")  # window defaults to fold_size=20
    assert [len(f.train_idx) for f in folds] == [20, 20, 20, 20]


def test_rolling_window_length_from_min_train():
    folds = walk_forward_folds(120, n_folds=4, scheme="rolling", min_train=30)  # fold_size=24, window=30
    for f in folds:
        assert len(f.train_idx) <= 30
    # later folds reach the full window
    assert max(len(f.train_idx) for f in folds) == 30


def test_expanding_min_train_skips_small_folds():
    # fold_size = 100//5 = 20; first fold would train on 20 rows. Require >= 50 -> folds 0,1 dropped.
    folds = walk_forward_folds(100, n_folds=4, min_train=50)
    assert all(len(f.train_idx) >= 50 for f in folds)
    assert len(folds) == 2  # only folds with train_end in {60, 80} qualify


def test_embargo_shrinks_train_and_opens_a_gap():
    base = walk_forward_folds(100, n_folds=4)
    embargoed = walk_forward_folds(100, n_folds=4, embargo=5)
    for f0, f5 in zip(base, embargoed, strict=True):
        assert len(f5.train_idx) == len(f0.train_idx) - 5
        assert f5.eval_idx.min() - f5.train_idx.max() > 5  # embargo gap present


def test_order_enforces_chronology_and_returns_original_indices():
    n = 60
    # order key reversed: original row 0 is the *latest* timestamp, row n-1 the earliest.
    order = np.arange(n)[::-1].astype(float)
    folds = walk_forward_folds(n, n_folds=3, order=order)
    for f in folds:
        # returned indices reference original positions; under the order key, all train timestamps
        # precede all eval timestamps.
        assert order[f.train_idx].max() < order[f.eval_idx].min()
        # the returned indices are original positions, not the sorted ranks
        assert f.train_idx.max() <= n - 1 and f.eval_idx.max() <= n - 1


def test_leakage_guard_with_order_and_embargo():
    n = 80
    order = np.linspace(0.0, 1.0, n)
    folds = walk_forward_folds(n, n_folds=4, embargo=3, order=order)
    for f in folds:
        assert order[f.train_idx].max() < order[f.eval_idx].min()


def test_validation_errors():
    with pytest.raises(ValueError, match="n_samples"):
        walk_forward_folds(1, n_folds=2)
    with pytest.raises(ValueError, match="n_folds"):
        walk_forward_folds(100, n_folds=0)
    with pytest.raises(ValueError, match="embargo"):
        walk_forward_folds(100, n_folds=4, embargo=-1)
    with pytest.raises(ValueError, match="scheme"):
        walk_forward_folds(100, n_folds=4, scheme="bogus")
    with pytest.raises(ValueError, match="not enough samples"):
        walk_forward_folds(3, n_folds=10)
    with pytest.raises(ValueError, match="order length"):
        walk_forward_folds(100, n_folds=4, order=np.arange(50))


def test_no_valid_folds_raises():
    # huge embargo wipes out every training block
    with pytest.raises(ValueError, match="no valid folds"):
        walk_forward_folds(30, n_folds=2, embargo=100)
