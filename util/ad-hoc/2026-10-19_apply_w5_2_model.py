#!/usr/bin/env python3
"""Apply the W5.2 model half to a juniper-recurrence-model tree (exact-string edits).

Project: juniper-ml
Sub-Project: recurrence x equities (plan W5.2, model half; model 0.6.0)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc, single-use (kept for the record of exactly what the model PR changed)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (W5.2 row + Details);
         util/ad-hoc/2026-10-19_apply_w5_9_w5_8b_model.py (the pattern)

Usage:
    python3 util/ad-hoc/2026-10-19_apply_w5_2_model.py --root <juniper-recurrence checkout> [--check]

Edits (each an exact-string replacement that must match exactly once):

* ``juniper_recurrence_model/data.py`` -- ``SequenceData`` carries the per-window entity id
  (``ticker_code``) and end date (``window_end_date``) when the artifact has them; a composed
  ``trainval`` view (train | val, entity-major like ``full``) is the cross-validation pool that
  leaves ``test`` untouched; ``derive_full_split`` becomes a wrapper over ``derive_composed_split``.
* ``tests/test_sequence_data.py`` -- the view and the keys pinned.
* ``CHANGELOG.md`` -- ``[Unreleased]`` Added.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

EDITS: list[tuple[str, str, str]] = []


def edit(path: str, old: str, new: str) -> None:
    EDITS.append((path, old, new))


D = "juniper_recurrence_model/data.py"

edit(
    D,
    """__all__ = ["DEFAULT_TARGET", "TARGET_MODES", "SequenceData", "TargetMode", "derive_full_split", "load_sequence_npz", "sequence_data_from_arrays"]
""",
    """__all__ = ["DEFAULT_TARGET", "TARGET_MODES", "SequenceData", "TargetMode", "derive_composed_split", "derive_full_split", "load_sequence_npz", "sequence_data_from_arrays"]
""",
)

edit(
    D,
    """    ``X`` is ``(W, L, F)``; ``y`` is ``(W, output_dim)``; ``dt`` is ``(W, L)`` with
    ``dt[:, 0] == 0``. ``target_dt`` ``(W,)`` and ``seq_lengths`` ``(W,)`` are optional.
    \"\"\"

    X: np.ndarray
    y: np.ndarray
    dt: np.ndarray
    target_dt: np.ndarray | None = None
    seq_lengths: np.ndarray | None = None
""",
    """    ``X`` is ``(W, L, F)``; ``y`` is ``(W, output_dim)``; ``dt`` is ``(W, L)`` with
    ``dt[:, 0] == 0``. ``target_dt`` ``(W,)`` and ``seq_lengths`` ``(W,)`` are optional.

    ``ticker_code`` and ``window_end_date`` (both ``(W,)``, integer; plan W5.2, 0.6.0) are the
    per-window entity id and end date a panel artifact carries (``equities_seq`` emits both;
    the dates are ``YYYYMMDD`` integers, which sort chronologically as they are). They are
    **not** fit kwargs -- :meth:`fit_kwargs` leaves them out -- but the keys a caller hands to
    ``juniper_model_core.crossval.walk_forward_folds`` as ``groups`` / ``order`` so folds are
    cut on the global date with every entity's earlier windows in train and later ones in eval.
    \"\"\"

    X: np.ndarray
    y: np.ndarray
    dt: np.ndarray
    target_dt: np.ndarray | None = None
    seq_lengths: np.ndarray | None = None
    ticker_code: np.ndarray | None = None
    window_end_date: np.ndarray | None = None
""",
)

edit(
    D,
    """#: Partition suffixes that compose the whole dataset, in the order juniper-data laid them
#: down within each entity. Order is load-bearing -- see :func:`derive_full_split`.
_FULL_COMPONENT_SPLITS = ("train", "val", "test")
""",
    """#: Partition suffixes that compose the whole dataset, in the order juniper-data laid them
#: down within each entity. Order is load-bearing -- see :func:`derive_full_split`.
_FULL_COMPONENT_SPLITS = ("train", "val", "test")

#: The composed views a reader may ask for beyond the three partitions: ``full`` (train | val |
#: test) and, since 0.6.0 (plan W5.2), ``trainval`` (train | val) -- the cross-validation pool
#: that leaves the final ``test`` partition untouched for a single out-of-sample read (W5.3).
_COMPOSED_VIEWS: dict[str, tuple[str, ...]] = {"full": _FULL_COMPONENT_SPLITS, "trainval": ("train", "val")}

#: The per-window keys a panel artifact carries beside the data (W5.2): read into
#: :class:`SequenceData` when present, never required, never fit kwargs.
_WINDOW_KEYS = ("ticker_code", "window_end_date")
""",
)

edit(
    D,
    """    Keys already present in ``arrays`` are never overwritten: a legacy artifact that still
    ships ``*_full`` keeps the producer's own arrays, byte for byte.
    \"\"\"
    present = [s for s in _FULL_COMPONENT_SPLITS if f"X_{s}" in arrays]
    if not present:
        return arrays

    # Every base key available in ALL present partitions can be composed; one that is
    # missing from any of them cannot, and is skipped rather than half-built.
    base_keys = {key[: -len(f"_{present[0]}")] for key in arrays if key.endswith(f"_{present[0]}")}
    composable = sorted(base for base in base_keys if all(f"{base}_{s}" in arrays for s in present))

    derived: dict[str, np.ndarray] = {}
    for base in composable:
        if f"{base}_full" in arrays:
            continue  # the producer's own array wins
        derived[f"{base}_full"] = np.concatenate([np.asarray(arrays[f"{base}_{s}"]) for s in present], axis=0)

    if not derived:
        return arrays

    entity_parts = [np.asarray(arrays[f"{_ENTITY_KEY}_{s}"]).reshape(-1) for s in present] if all(f"{_ENTITY_KEY}_{s}" in arrays for s in present) else None
    if entity_parts is not None:
        order = np.argsort(np.concatenate(entity_parts), kind="stable")
        derived = {key: value[order] for key, value in derived.items()}

    return {**arrays, **derived}
""",
    """    Keys already present in ``arrays`` are never overwritten: a legacy artifact that still
    ships ``*_full`` keeps the producer's own arrays, byte for byte.
    \"\"\"
    return derive_composed_split(arrays, "full")


def derive_composed_split(arrays: dict[str, np.ndarray], view: str) -> dict[str, np.ndarray]:
    \"\"\"Return ``arrays`` plus a synthesized ``*_{view}`` family composed from its partitions.

    ``view`` is one of :data:`_COMPOSED_VIEWS`: ``"full"`` (train | val | test; see
    :func:`derive_full_split` for why the row order is a stable sort by ``ticker_code``, not a
    concatenation) or ``"trainval"`` (train | val; plan W5.2, 0.6.0) -- the cross-validation pool
    that excludes the final ``test`` partition, laid down the same entity-major way so a
    multi-ticker pool is exactly the ``full`` view with each ticker's ``test`` block removed.
    Partitions the artifact lacks are skipped (a two-way artifact's ``trainval`` is its train
    set); keys already present are never overwritten.
    \"\"\"
    if view not in _COMPOSED_VIEWS:
        raise ValueError(f"view must be one of {tuple(_COMPOSED_VIEWS)}; got {view!r}")
    present = [s for s in _COMPOSED_VIEWS[view] if f"X_{s}" in arrays]
    if not present:
        return arrays

    # Every base key available in ALL present partitions can be composed; one that is
    # missing from any of them cannot, and is skipped rather than half-built.
    base_keys = {key[: -len(f"_{present[0]}")] for key in arrays if key.endswith(f"_{present[0]}")}
    composable = sorted(base for base in base_keys if all(f"{base}_{s}" in arrays for s in present))

    derived: dict[str, np.ndarray] = {}
    for base in composable:
        if f"{base}_{view}" in arrays:
            continue  # the producer's own array wins
        derived[f"{base}_{view}"] = np.concatenate([np.asarray(arrays[f"{base}_{s}"]) for s in present], axis=0)

    if not derived:
        return arrays

    entity_parts = [np.asarray(arrays[f"{_ENTITY_KEY}_{s}"]).reshape(-1) for s in present] if all(f"{_ENTITY_KEY}_{s}" in arrays for s in present) else None
    if entity_parts is not None:
        order = np.argsort(np.concatenate(entity_parts), kind="stable")
        derived = {key: value[order] for key, value in derived.items()}

    return {**arrays, **derived}
""",
)

edit(
    D,
    """    ``split`` must be ``"train"`` / ``"val"`` / ``"test"`` / ``"full"`` -- the four the app's
    request schema admits; anything else is refused before the artifact is read.
    ``split="full"`` is served from the artifact's own ``*_full`` family when it has one, and
    otherwise from :func:`derive_full_split`. juniper-data stopped emitting that family in
    decision 11, so without the fallback every post-#369 artifact would fail this read --
    which is how ``POST /v1/crossval`` would break.
    \"\"\"
    if target not in TARGET_MODES:
        raise ValueError(f"target must be one of {TARGET_MODES}; got {target!r}")
    # The four splits the app's request schema admits (``SplitName``). Spelled as an inline literal
    # rather than derived from _FULL_COMPONENT_SPLITS: ``split`` reaches the target-fallback log lines,
    # and a comparison against a literal display is what static analysis (CodeQL
    # ``py/log-injection``) recognises as validating a caller-supplied string.
    if split not in ("train", "val", "test", "full"):
        raise ValueError(f"split must be one of 'train' / 'val' / 'test' / 'full'; got {split!r}")
    if split == "full" and f"X_{split}" not in arrays:
        arrays = derive_full_split(arrays)
""",
    """    ``split`` must be ``"train"`` / ``"val"`` / ``"test"`` / ``"full"`` / ``"trainval"`` -- the
    five the app's request schema admits; anything else is refused before the artifact is read.
    ``split="full"`` is served from the artifact's own ``*_full`` family when it has one, and
    otherwise from :func:`derive_full_split`. juniper-data stopped emitting that family in
    decision 11, so without the fallback every post-#369 artifact would fail this read --
    which is how ``POST /v1/crossval`` would break. ``split="trainval"`` (0.6.0, plan W5.2) is
    the composed train | val pool from :func:`derive_composed_split`: what cross-validation
    selects over, leaving ``test`` for a single out-of-sample read.

    ``ticker_code_{split}`` and ``window_end_date_{split}`` are read into the result when present
    (``(W,)``, integer dtype) and left ``None`` otherwise; they ride the composed views like every
    other per-window key, so a panel pool keeps each window's entity and date.
    \"\"\"
    if target not in TARGET_MODES:
        raise ValueError(f"target must be one of {TARGET_MODES}; got {target!r}")
    # The five splits the app's request schema admits (``SplitName``). Spelled as an inline literal
    # rather than derived from _COMPOSED_VIEWS: ``split`` reaches the target-fallback log lines,
    # and a comparison against a literal display is what static analysis (CodeQL
    # ``py/log-injection``) recognises as validating a caller-supplied string.
    if split not in ("train", "val", "test", "full", "trainval"):
        raise ValueError(f"split must be one of 'train' / 'val' / 'test' / 'full' / 'trainval'; got {split!r}")
    if split in _COMPOSED_VIEWS and f"X_{split}" not in arrays:
        arrays = derive_composed_split(arrays, split)
""",
)

edit(
    D,
    """    target_dt = _read_target_dt(arrays, split, n_windows)
    seq_lengths = _read_seq_lengths(arrays, split, n_windows, lookback)

    return SequenceData(X=X, y=y, dt=dt, target_dt=target_dt, seq_lengths=seq_lengths)
""",
    """    target_dt = _read_target_dt(arrays, split, n_windows)
    seq_lengths = _read_seq_lengths(arrays, split, n_windows, lookback)
    ticker_code = _read_window_key(arrays, "ticker_code", split, n_windows)
    window_end_date = _read_window_key(arrays, "window_end_date", split, n_windows)

    return SequenceData(X=X, y=y, dt=dt, target_dt=target_dt, seq_lengths=seq_lengths, ticker_code=ticker_code, window_end_date=window_end_date)


def _read_window_key(arrays: dict[str, np.ndarray], base: str, split: str, n_windows: int) -> np.ndarray | None:
    \"\"\"``{base}_{split}`` when present: ``(W,)`` of an integer dtype (W5.2; see :data:`_WINDOW_KEYS`).

    ``ticker_code`` is the entity id (an index into the artifact's ``ticker_vocab``) and
    ``window_end_date`` the window's last observed day as a ``YYYYMMDD`` integer. A ``(W, 1)``
    column or a float array is refused rather than reshaped or truncated: both are the keys the
    fold cut is made on, and a silent coercion there changes which windows share a fold.
    \"\"\"
    key = f"{base}_{split}"
    if key not in arrays:
        return None
    values = np.asarray(arrays[key])
    if values.shape != (n_windows,):
        raise ValueError(f"{key} shape {values.shape} != {(n_windows,)}")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError(f"{key} must be an integer dtype, got {values.dtype}")
    return values
""",
)

# CodeQL on the PR: ``_WINDOW_KEYS`` was declared and never read. Read the two keys through it.
edit(
    D,
    """    ticker_code = _read_window_key(arrays, "ticker_code", split, n_windows)
    window_end_date = _read_window_key(arrays, "window_end_date", split, n_windows)

    return SequenceData(X=X, y=y, dt=dt, target_dt=target_dt, seq_lengths=seq_lengths, ticker_code=ticker_code, window_end_date=window_end_date)
""",
    """    ticker_code, window_end_date = (_read_window_key(arrays, base, split, n_windows) for base in _WINDOW_KEYS)

    return SequenceData(X=X, y=y, dt=dt, target_dt=target_dt, seq_lengths=seq_lengths, ticker_code=ticker_code, window_end_date=window_end_date)
""",
)

# --- tests -------------------------------------------------------------------------------------

T = "tests/test_sequence_data.py"

edit(
    T,
    """from juniper_recurrence_model.data import DEFAULT_TARGET, TARGET_MODES, derive_full_split
""",
    """from juniper_recurrence_model.data import DEFAULT_TARGET, TARGET_MODES, derive_composed_split, derive_full_split
""",
)

edit(
    T,
    """class TestCrossvalReadSurvivesDecision11:
""",
    """class TestTrainvalViewAndWindowKeys:
    \"\"\"W5.2 (0.6.0): the ``trainval`` pool excludes ``test``; the entity / date keys ride every view.\"\"\"

    @staticmethod
    def _post_369_with_dates():
        \"\"\"The three-ticker artifact without its ``_full`` family, plus per-split ``window_end_date`` keys.\"\"\"
        artifact = {k: v for k, v in _three_ticker_artifact().items() if not k.endswith("_full")}
        # A YYYYMMDD-shaped date per window, unique per row, so the composed view's permutation of the
        # dates can be checked against the permutation of the rows (``X[:, 0, 0]`` is the row id).
        for split in ("train", "val", "test"):
            ids = artifact[f"X_{split}"][:, 0, 0].astype(np.int64)
            artifact[f"window_end_date_{split}"] = (20200101 + ids).astype(np.int32)
        return artifact

    def test_trainval_is_the_full_view_minus_every_tickers_test_block(self):
        artifact = _three_ticker_artifact()
        post_369 = {k: v for k, v in artifact.items() if not k.endswith("_full")}
        pool = sequence_data_from_arrays(post_369, "trainval")
        full = sequence_data_from_arrays(post_369, "full")
        test_ids = set(artifact["X_test"][:, 0, 0].tolist())
        expected = full.X[[i for i, row_id in enumerate(full.X[:, 0, 0].tolist()) if row_id not in test_ids]]
        assert pool.X.shape[0] == artifact["X_train"].shape[0] + artifact["X_val"].shape[0]
        assert np.array_equal(pool.X, expected)  # same entity-major order as ``full``, test rows removed
        assert not (set(pool.X[:, 0, 0].tolist()) & test_ids)
        assert np.array_equal(pool.y, full.y[[i for i, row_id in enumerate(full.X[:, 0, 0].tolist()) if row_id not in test_ids]])

    def test_window_keys_are_read_and_permuted_with_the_rows(self):
        artifact = self._post_369_with_dates()
        for view in ("trainval", "full"):
            data = sequence_data_from_arrays(artifact, view)
            assert data.ticker_code is not None and data.window_end_date is not None
            assert data.ticker_code.shape == (data.X.shape[0],) and data.window_end_date.shape == (data.X.shape[0],)
            # Each row's date is the one minted for that row id: the keys travelled with the rows.
            assert np.array_equal(data.window_end_date, (20200101 + data.X[:, 0, 0].astype(np.int64)).astype(np.int32))
            assert np.all(np.diff(data.ticker_code) >= 0)  # entity-major, as ``full`` is laid down

    def test_window_keys_are_none_when_the_artifact_lacks_them(self):
        arrays = _make_equities_seq_arrays(splits=("train", "val", "test"))
        data = sequence_data_from_arrays(arrays, "trainval")
        assert data.ticker_code is None and data.window_end_date is None
        assert "ticker_code" not in data.fit_kwargs() and "window_end_date" not in data.fit_kwargs()

    def test_window_keys_are_not_fit_kwargs(self):
        data = sequence_data_from_arrays(self._post_369_with_dates(), "train")
        assert set(data.fit_kwargs()) == {"dt"}
        assert data.ticker_code is not None and data.window_end_date is not None

    @pytest.mark.parametrize("bad", [np.zeros((3, 1), dtype=np.int32), np.zeros(3, dtype=np.float32), np.zeros(4, dtype=np.int32)])
    def test_a_mis_shaped_or_float_window_key_is_refused(self, bad):
        artifact = _assemble_like_juniper_data([_ticker_windows(10, (3, 2, 2))])
        artifact = {k: v for k, v in artifact.items() if not k.endswith("_full")}
        artifact["window_end_date_train"] = bad
        with pytest.raises(ValueError, match="window_end_date_train"):
            sequence_data_from_arrays(artifact, "train")

    def test_trainval_of_a_two_way_artifact_is_its_train_set(self):
        arrays = _make_equities_seq_arrays(splits=("train", "test"))
        data = sequence_data_from_arrays(arrays, "trainval")
        assert np.array_equal(data.X, np.asarray(arrays["X_train"]))

    def test_an_unknown_view_is_refused(self):
        with pytest.raises(ValueError, match="view must be one of"):
            derive_composed_split({}, "everything")
        with pytest.raises(ValueError, match="split must be one of"):
            sequence_data_from_arrays(_make_equities_seq_arrays(), "everything")

    def test_full_is_the_same_composition_as_before(self):
        post_369 = {k: v for k, v in _three_ticker_artifact().items() if not k.endswith("_full")}
        assert np.array_equal(derive_full_split(post_369)["X_full"], derive_composed_split(post_369, "full")["X_full"])


class TestCrossvalReadSurvivesDecision11:
""",
)

edit(
    T,
    """        \"\"\"The app's ``SplitName`` admits four splits; the reader refuses anything else up front, not as a missing key.\"\"\"
        with pytest.raises(ValueError, match=r"^split must be one of 'train' / 'val' / 'test' / 'full'; got "):
""",
    """        \"\"\"The app's ``SplitName`` admits five splits; the reader refuses anything else up front, not as a missing key.\"\"\"
        with pytest.raises(ValueError, match=r"^split must be one of 'train' / 'val' / 'test' / 'full' / 'trainval'; got "):
""",
)

edit(
    "README.md",
    """## Readout spectrum
""",
    """## Reading an artifact

`sequence_data_from_arrays` / `load_sequence_npz` read one split of a juniper-data sequence
artifact: `train`, `val`, `test`, or two composed views -- `full` (train | val | test) and, since
0.6.0, `trainval` (train | val), the cross-validation pool that leaves `test` for a single
out-of-sample read. Both views are laid down entity-major (every window of one ticker, then the
next), which is the order juniper-data wrote, not a plain concatenation. A panel artifact's
per-window `ticker_code` and `window_end_date` (a `YYYYMMDD` integer) come back on the
`SequenceData` as well; they are not fit kwargs but the `groups` / `order` keys for model-core's
`walk_forward_folds`, so folds are cut on the global date with every ticker's earlier windows in train.

## Readout spectrum
""",
)

# --- CHANGELOG ---------------------------------------------------------------------------------

edit(
    "CHANGELOG.md",
    """## [Unreleased]

## [0.5.0] - 2026-10-19
""",
    """## [Unreleased]

### Added

- **`SequenceData` carries `ticker_code` and `window_end_date`, and the reader serves a composed
  `trainval` view** (W5.2 of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`,
  the model half). `sequence_data_from_arrays` / `load_sequence_npz` read `ticker_code_{split}`
  (the entity id) and `window_end_date_{split}` (the window's last day, a `YYYYMMDD` integer) when
  the artifact has them -- `(W,)`, integer dtype, else refused -- into two new optional fields;
  they are not fit kwargs but the `groups` / `order` keys for
  `juniper_model_core.crossval.walk_forward_folds`, so a panel's folds can be cut on the global
  date with every ticker's earlier windows in train. `split="trainval"` composes train | val the
  way `full` composes train | val | test (`derive_composed_split`, of which `derive_full_split` is
  now the `"full"` case): the cross-validation pool that leaves the final `test` partition for a
  single out-of-sample read. `full` is unchanged, row for row.

## [0.5.0] - 2026-10-19
""",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True, help="juniper-recurrence checkout root (holds juniper-recurrence-model/)")
    parser.add_argument("--check", action="store_true", help="report each edit's state; write nothing")
    args = parser.parse_args()
    root = pathlib.Path(args.root) / "juniper-recurrence-model"
    pending = applied = 0
    failed = []
    for rel, old, new in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if text.count(new) == 1:  # an insertion edit keeps its anchor inside ``new``, so ``new`` present is the test
            applied += 1
            print(f"  = {rel}: already applied")
            continue
        count = text.count(old)
        if count != 1:
            failed.append((rel, count, old.splitlines()[0]))
            print(f"  ! {rel}: anchor matched {count} times: {old.splitlines()[0][:80]!r}")
            continue
        pending += 1
        if args.check:
            print(f"  ~ {rel}: WOULD apply: {old.splitlines()[0][:80]!r}")
        else:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            print(f"  + {rel}: applied: {old.splitlines()[0][:80]!r}")
    print(f"applied {applied}, pending {pending}, failed {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
