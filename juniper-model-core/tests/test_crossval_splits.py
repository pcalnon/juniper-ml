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


# --- multi-entity ("panel") folds via groups= ---------------------------------------------------


def _panel(n_dates: int = 12, n_tickers: int = 2):
    """A panel where row r has date ``r // n_tickers`` and entity ``r % n_tickers`` (windows
    interleaved by date across entities). Returns ``(n_samples, order, groups)``."""
    order = np.repeat(np.arange(n_dates), n_tickers).astype(float)  # [0,0,1,1,2,2,...]
    groups = np.tile(np.arange(n_tickers), n_dates)  # [0,1,0,1,...]
    return n_dates * n_tickers, order, groups


def _signature(folds):
    return [(f.train_idx.tolist(), f.eval_idx.tolist()) for f in folds]


def test_groups_none_matches_omitted():
    # groups=None must be byte-identical to not passing groups at all (backward compatibility).
    assert _signature(walk_forward_folds(60, n_folds=3, embargo=2)) == _signature(
        walk_forward_folds(60, n_folds=3, embargo=2, groups=None)
    )


def test_groups_eval_is_pooled_across_entities():
    n, order, groups = _panel(12, 2)
    for f in walk_forward_folds(n, n_folds=3, order=order, groups=groups):
        assert set(groups[f.eval_idx].tolist()) == {0, 1}  # eval block spans both entities (pooled)


def test_groups_per_group_embargo_drops_each_entitys_latest_train():
    n, order, groups = _panel(12, 2)
    base = walk_forward_folds(n, n_folds=3, embargo=0, order=order, groups=groups)
    purged = walk_forward_folds(n, n_folds=3, embargo=1, order=order, groups=groups)
    for a, b in zip(base, purged, strict=True):
        assert set(a.eval_idx.tolist()) == set(b.eval_idx.tolist())  # same pooled eval block
        dropped = set(a.train_idx.tolist()) - set(b.train_idx.tolist())
        groups_with_train = {g for g in np.unique(groups) if (groups[a.train_idx] == g).any()}
        # embargo=1 drops exactly one window per entity that had any train windows...
        assert len(dropped) == len(groups_with_train)
        # ...and the dropped one is that entity's most-recent (by order) train window.
        for g in groups_with_train:
            g_train = a.train_idx[groups[a.train_idx] == g]
            assert g_train[np.argmax(order[g_train])] in dropped


def test_groups_per_group_leakage_guard():
    n, order, groups = _panel(12, 2)
    for f in walk_forward_folds(n, n_folds=3, embargo=1, order=order, groups=groups):
        for g in np.unique(groups):
            tr = f.train_idx[groups[f.train_idx] == g]
            ev = f.eval_idx[groups[f.eval_idx] == g]
            if tr.size and ev.size:
                # each entity's own train strictly precedes its own eval (no same-entity backflow)
                assert order[tr].max() < order[ev].min()


def test_groups_length_mismatch_raises():
    n, order, groups = _panel(12, 2)
    with pytest.raises(ValueError, match="groups length"):
        walk_forward_folds(n, n_folds=3, order=order, groups=groups[:-1])


def test_groups_determinism():
    n, order, groups = _panel(12, 2)
    assert _signature(walk_forward_folds(n, n_folds=3, embargo=1, order=order, groups=groups)) == _signature(
        walk_forward_folds(n, n_folds=3, embargo=1, order=order, groups=groups)
    )


def test_groups_embargo_skips_early_fold_but_keeps_later():
    # fold_size=4; embargo=2 fully purges fold 0's 4-window train (2 per entity), but fold 1's
    # 8-window candidate keeps 4 after the per-entity purge -> only the later fold survives.
    n, order, groups = _panel(6, 2)  # 12 windows
    folds = walk_forward_folds(n, n_folds=2, embargo=2, order=order, groups=groups)
    assert len(folds) == 1
    assert folds[0].train_idx.size == 4


def test_groups_min_train_skips_small_expanding_folds():
    # fold_size=6; expanding min_train=10 drops fold 0 (6 train rows); folds 1,2 (12,18) qualify.
    n, order, groups = _panel(12, 2)  # 24 windows
    folds = walk_forward_folds(n, n_folds=3, min_train=10, order=order, groups=groups)
    assert len(folds) == 2
    assert all(f.train_idx.size >= 10 for f in folds)
