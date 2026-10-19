#!/usr/bin/env python3
"""W5.2's owed bench half: the equities rows pool ``trainval`` and cut folds on the global date per entity; a multi-ticker row.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (the juniper-recurrence bench PR for W5.2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W5.2 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         ("Bench gains a multi-ticker row"; "Owed: the bench's multi-ticker row");
         util/ad-hoc/2026-10-19_apply_w5_2_model.py (model 0.6.0: the composed ``trainval`` view and the window keys);
         util/ad-hoc/2026-10-19_apply_w5_2_service.py (the route's folding, which this mirrors)

Why this exists
---------------
``bench/run_benchmark.py`` still cut row-index folds (``walk_forward_folds(n, embargo=_EMBARGO)``) over the ``full``
view, and ``bench/datasets.py`` loaded ``y_reg_full``. On a multi-ticker request that view is entity-major, so a
row-index cut puts ticker A's 2021 in train and ticker B's 2015 in eval (F-P7), and the last fold evaluates the
``test`` partition the plan reserves (W5.3). The service fixed this in juniper-recurrence#215; the bench mirrors it:

- ``Dataset`` carries ``order`` (``window_end_date``), ``groups`` (``ticker_code``) and the row's own ``embargo``;
- ``equities_seq`` loads the composed ``trainval`` view (juniper-recurrence-model 0.6.0's ``derive_composed_split``),
  reads the two keys when the artifact carries them, and sets ``embargo`` to the look-back;
- ``run_dataset`` passes ``order`` / ``groups`` / the row's embargo to model-core and records a ``folding`` block;
- a new informational row ``equities_seq_panel`` (``AAPL`` + ``MSFT``) sits beside the single-ticker row;
- Band 2b and the report's per-dataset header cover both equities rows.

Runs against a tree laid out like the juniper-recurrence repo root (the scratch copy), never the owner's checkout.
Each edit asserts its exact old text and must match exactly once; "new present once" counts as applied. The
CHANGELOG entry goes first under ``[Unreleased]`` -> ``### Changed`` (created when absent), so it applies on
``main`` before or after juniper-recurrence#215 lands.

Usage
-----
    python3 util/ad-hoc/2026-10-19_apply_w5_2_bench_multi_ticker.py --root <scratch juniper-recurrence tree> [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

# --------------------------------------------------------------------------------------------- bench/datasets.py
_DS_DOC_OLD = """returning the full ordered window set + the per-step Δt. Uses the ``*_full`` arrays (every
window, chronologically ordered) so the walk-forward CV does its own splitting.

Generator output (verified): ``X_full (n,T,F)``, ``y_full (n,output_dim)``, ``dt_full (n,T)``,
``target_dt_full (n,)`` (+ ``observed_mask_full``, ``*_train`` / ``*_test`` splits we ignore).
For ``equities_seq`` the regression target is ``y_reg_full`` (next-day close), not the one-hot
``y_full`` direction label.
"""
_DS_DOC_NEW = """returning one ordered window set + the per-step Δt so the walk-forward CV does its own splitting.
The synthetic rows use the composed ``full`` view (every window); the equities rows use the
composed ``trainval`` view (train | val, entity-major -- plan W5.2), so the final ``test``
partition is never in a fold, and carry the per-window keys the folds are cut on.

Generator output (verified): ``X_{split} (n,T,F)``, ``y_{split} (n,output_dim)``, ``dt_{split} (n,T)``,
``target_dt_{split} (n,)`` (+ ``observed_mask_{split}``) for ``train`` / ``val`` / ``test``; the composed
views are derived by juniper-recurrence-model (``derive_composed_split``, 0.6.0). For ``equities_seq``
the regression target is ``y_reg_{split}`` (the stationary next-day log-return), not the one-hot
``y_{split}`` direction label, and the artifact also carries ``window_end_date_{split}`` (``YYYYMMDD``
integers) and ``ticker_code_{split}``.
"""

_DS_REG_DOC_OLD = """``delay_product`` capacity dataset (design §8a), the ``ar_p`` linear floor (plan W-5), and a
real-data irregular-Δt sanity check (``equities_seq``).
\"\"\""""
_DS_REG_DOC_NEW = """``delay_product`` capacity dataset (design §8a), the ``ar_p`` linear floor (plan W-5), and two
real-data irregular-Δt sanity checks (``equities_seq``, one ticker; ``equities_seq_panel``, two
tickers whose folds are cut on the global date per entity -- plan W5.2).
\"\"\""""

_DS_CLASS_OLD = """    dt: np.ndarray  # (n, T) real per-step gaps (dt[:, 0] == 0)
    target_dt: np.ndarray  # (n,) irregular forecast horizon
"""
_DS_CLASS_NEW = """    dt: np.ndarray  # (n, T) real per-step gaps (dt[:, 0] == 0)
    target_dt: np.ndarray  # (n,) irregular forecast horizon
    # W5.2 (juniper-recurrence-model 0.6.0): the per-window keys a panel's folds are cut on, and the
    # row's own embargo. ``order`` is ``window_end_date`` (``YYYYMMDD`` ints) and ``groups`` is
    # ``ticker_code``; both ``None`` for a synthetic series, whose folds stay row-index folds.
    # ``embargo`` is in windows; ``None`` means the harness default (``run_benchmark._EMBARGO``). The
    # equities rows set it to the look-back -- the gap that keeps an eval window's history clear of
    # every train window's -- as ``POST /v1/crossval`` does by default since juniper-recurrence 0.8.0.
    order: np.ndarray | None = None
    groups: np.ndarray | None = None
    embargo: int | None = None
"""

_DS_FULL_OLD = '''def _full(out: dict[str, np.ndarray], key: str) -> np.ndarray:
    """Read one array from the whole-dataset view, deriving it on first use.

    Decision 11 (juniper-data#369) retired the ``*_full`` family from the NPZ contract,
    so the generators below emit only ``train`` / ``val`` / ``test`` and this used to be
    a bare ``KeyError`` on every dataset.

    ``derive_full_split`` rebuilds the view ENTITY-major, stable-sorting on
    ``ticker_code`` when the artifact carries one. That is load-bearing for
    ``equities_seq``: juniper-data laid its ``_full`` down entity-major while the
    partitions are split-major, so a plain ``np.concatenate`` would hold the same rows in
    a DIFFERENT order for any multi-ticker request, and walk-forward CV slices by row
    index -- a change to what the benchmark measures, not a refactor. A legacy artifact
    that still ships ``*_full`` keeps the producer's own arrays, byte for byte.

    The derived keys are merged back into ``out`` so the reconstruction runs once per
    dataset rather than once per call.
    """
    full_key = f"{key}_full"
    if full_key not in out:
        from juniper_recurrence_model.data import derive_full_split

        out.update(derive_full_split(out))
    if full_key not in out:
        available = ", ".join(sorted(out)) or "<empty>"
        raise KeyError(
            f"{full_key!r} could not be derived; generator emitted: {available}"
        )
    return np.asarray(out[full_key])
'''
_DS_FULL_NEW = '''def _full(out: dict[str, np.ndarray], key: str) -> np.ndarray:
    """Read one array from the whole-dataset view, deriving it on first use.

    Decision 11 (juniper-data#369) retired the ``*_full`` family from the NPZ contract,
    so the generators below emit only ``train`` / ``val`` / ``test`` and this used to be
    a bare ``KeyError`` on every dataset. The ``"full"`` case of :func:`_composed`.
    """
    return _composed(out, key, "full")


def _composed(out: dict[str, np.ndarray], key: str, view: str) -> np.ndarray:
    """Read one array from a composed view -- ``"full"`` (train | val | test) or ``"trainval"`` (train | val) -- deriving the view on first use.

    ``derive_composed_split`` (juniper-recurrence-model 0.6.0) rebuilds either view ENTITY-major,
    stable-sorting on ``ticker_code`` when the artifact carries one. That is load-bearing for
    the equities rows: juniper-data laid its retired ``_full`` down entity-major while the
    partitions are split-major, so a plain ``np.concatenate`` would hold the same rows in a
    DIFFERENT order for any multi-ticker request, and model-core's folds slice by row index
    unless given ``order`` / ``groups`` -- a change to what the benchmark measures, not a
    refactor. A legacy artifact that still ships ``*_full`` keeps the producer's own arrays,
    byte for byte. ``trainval`` (plan W5.2) is the cross-validation pool: the final ``test``
    partition is never in a fold.

    The derived keys are merged back into ``out`` so the reconstruction runs once per
    dataset rather than once per call.
    """
    view_key = f"{key}_{view}"
    if view_key not in out:
        from juniper_recurrence_model.data import derive_composed_split

        out.update(derive_composed_split(out, view))
    if view_key not in out:
        available = ", ".join(sorted(out)) or "<empty>"
        raise KeyError(
            f"{view_key!r} could not be derived; generator emitted: {available}"
        )
    return np.asarray(out[view_key])
'''

_DS_EQ_SIG_OLD = '''    lookback: int = 32,
    regression_target: str = "log_return",
) -> Dataset:
    """Real irregular-Δt sequences from one equity's daily history (calendar gaps = genuine Δt).

    Uses a **single ticker** so the concatenated window set is one chronological series (clean
    walk-forward CV — no cross-ticker interleaving). The regression target ``y_reg`` is the
'''
_DS_EQ_SIG_NEW = '''    lookback: int = 32,
    regression_target: str = "log_return",
    name: str = "equities_seq",
) -> Dataset:
    """Real irregular-Δt sequences from equities' daily history (calendar gaps = genuine Δt).

    The default is a **single ticker** (one chronological series); ``equities_seq_panel`` passes
    two. Either way the window set is the composed ``trainval`` pool -- the final ``test``
    partition is never in a fold (plan W5.2) -- and the dataset carries the per-window
    ``window_end_date`` / ``ticker_code`` keys plus ``embargo = lookback``, so ``run_dataset``
    cuts a panel's folds on the global date with a per-entity embargo of one look-back (the
    route's own rule since juniper-recurrence 0.8.0) instead of by row index over an
    entity-major pool. The regression target ``y_reg`` is the
'''

_DS_EQ_BODY_OLD = '''    return Dataset(
        "equities_seq",
        "irregular",
        _full(out, "X"),
        _full(out, "y_reg"),
        _full(out, "dt"),
        _full(out, "target_dt"),
    )
'''
_DS_EQ_BODY_NEW = '''    pool = "trainval"
    has_keys = all(
        f"{key}_{split}" in out
        for key in ("window_end_date", "ticker_code")
        for split in ("train", "val")
    )
    return Dataset(
        name,
        "irregular",
        _composed(out, "X", pool),
        _composed(out, "y_reg", pool),
        _composed(out, "dt", pool),
        _composed(out, "target_dt", pool),
        order=_composed(out, "window_end_date", pool) if has_keys else None,
        groups=_composed(out, "ticker_code", pool) if has_keys else None,
        embargo=int(lookback),
    )
'''

_DS_REG_OLD = '''    "delay_product": delay_product,
    "equities_seq": equities_seq,
}
'''
_DS_REG_NEW = '''    "delay_product": delay_product,
    "equities_seq": equities_seq,
    # W5.2: the multi-ticker row. Two entities whose windows interleave in time; the folds are cut on
    # the global date per entity (see run_dataset), which a row-index cut over the entity-major pool
    # would get wrong (ticker A's 2021 in train, ticker B's 2015 in eval). Informational, like the
    # single-ticker row; needs the [bench-equities] extra and network at generation time.
    "equities_seq_panel": partial(
        equities_seq, symbols=("AAPL", "MSFT"), name="equities_seq_panel"
    ),
}
'''

# ----------------------------------------------------------------------------------------- bench/run_benchmark.py
_RB_EMBARGO_OLD = "_N_FOLDS = 5\n_EMBARGO = 2\n"
_RB_EMBARGO_NEW = (
    "_N_FOLDS = 5\n"
    "# The synthetic rows' embargo (in windows). A dataset that carries its own `embargo` -- the equities rows set\n"
    "# it to the look-back (plan W5.2) -- overrides this in run_dataset.\n"
    "_EMBARGO = 2\n"
)

_RB_FOLDS_OLD = "    folds = walk_forward_folds(ds.X.shape[0], n_folds=_N_FOLDS, embargo=_EMBARGO)\n"
_RB_FOLDS_NEW = (
    "    # W5.2: a panel's folds are cut on the global date per entity (model-core's `order=` / `groups=`,\n"
    "    # the seam the service's crossval route uses), with the row's own embargo -- the equities rows: one\n"
    "    # look-back. A row-index cut over an entity-major pool would put ticker A's 2021 in train and ticker\n"
    "    # B's 2015 in eval. A keyless synthetic series keeps its row-index folds and the harness embargo.\n"
    "    embargo = _EMBARGO if ds.embargo is None else int(ds.embargo)\n"
    "    folds = walk_forward_folds(\n"
    "        ds.X.shape[0],\n"
    "        n_folds=_N_FOLDS,\n"
    "        embargo=embargo,\n"
    "        order=ds.order,\n"
    "        groups=ds.groups,\n"
    "    )\n"
    "    folding = {\n"
    '        "embargo": embargo,\n'
    '        "ordered": ds.order is not None,\n'
    '        "grouped": ds.groups is not None,\n'
    '        "n_entities": int(np.unique(ds.groups).shape[0])\n'
    "        if ds.groups is not None\n"
    "        else 1,\n"
    '        "n_folds": len(folds),\n'
    "    }\n"
)

_RB_RETURN_OLD = '''        "n_windows": int(ds.X.shape[0]),
        "theta": theta,
        "models": {**models, **sweep},
    }
'''
_RB_RETURN_NEW = '''        "n_windows": int(ds.X.shape[0]),
        "theta": theta,
        "folding": folding,
        "models": {**models, **sweep},
    }
'''

_RB_2B_OLD = '        if name == "equities_seq" and rkey in results[name]["models"]:\n'
_RB_2B_NEW = '        if name.startswith("equities_seq") and rkey in results[name]["models"]:\n'

_RB_HEADER_OLD = '''        lines.append(
            f"### `{name}` ({res['grid']}-Δt, n_windows={res['n_windows']}, θ={res['theta']:.3f}, {_N_FOLDS} folds)"
        )
'''
_RB_HEADER_NEW = '''        folding = res.get("folding") or {}
        extra = f", embargo={folding['embargo']}" if "embargo" in folding else ""
        if folding.get("grouped"):
            extra += f", {folding['n_entities']} entities, folds cut on the date"
        lines.append(
            f"### `{name}` ({res['grid']}-Δt, n_windows={res['n_windows']}, θ={res['theta']:.3f}, {_N_FOLDS} folds{extra})"
        )
'''

# ---------------------------------------------------------------------------------------- bench/test_bench_smoke.py
_TEST_MARKER = "def test_equities_dataset_pools_trainval_and_cuts_folds_on_the_date"
_TESTS = '''

# --- W5.2: the trainval pool, the window keys, and date-cut folds per entity ---------------------------------


def _panel_arrays(n_per: int = 30, lookback: int = 4) -> dict:
    """Two tickers x three partitions with the W5.2 keys -- the shape juniper-data's equities_seq emits.

    Each partition holds ticker 0's windows then ticker 1's (split-major outside, entity blocks inside).
    ``window_end_date`` is a ``YYYYMMDD``-style integer that rises with the window; the splits sit in
    successive years so ``test`` is recognisable by its dates.
    """
    rng = np.random.default_rng(0)
    out: dict = {}
    for split, n in (("train", n_per), ("val", n_per // 2), ("test", n_per // 3)):
        parts: dict = {
            k: []
            for k in ("X", "y_reg", "dt", "target_dt", "ticker_code", "window_end_date")
        }
        base = {"train": 20200101, "val": 20210101, "test": 20220101}[split]
        for code in (0, 1):
            parts["X"].append(rng.standard_normal((n, lookback, 2)).astype(np.float32))
            parts["y_reg"].append(rng.standard_normal((n, 1)).astype(np.float32))
            dt = np.ones((n, lookback), dtype=np.float32)
            dt[:, 0] = 0.0
            parts["dt"].append(dt)
            parts["target_dt"].append(np.ones(n, dtype=np.float32))
            parts["ticker_code"].append(np.full(n, code, dtype=np.int64))
            parts["window_end_date"].append(base + np.arange(n, dtype=np.int64))
        for key, chunks in parts.items():
            out[f"{key}_{split}"] = np.concatenate(chunks, axis=0)
    return out


def test_trainval_view_excludes_test_and_carries_the_window_keys():
    out = _panel_arrays()
    arrays = dict(out)
    X = datasets._composed(arrays, "X", "trainval")
    assert X.shape[0] == out["X_train"].shape[0] + out["X_val"].shape[0]
    groups = datasets._composed(arrays, "ticker_code", "trainval")
    order = datasets._composed(arrays, "window_end_date", "trainval")
    assert sorted(set(groups.tolist())) == [0, 1]
    assert np.all(np.diff(groups) >= 0), "the composed view is entity-major"
    assert order.max() < 20220101, "no test window in the pool"
    # The full view is still the three partitions, and _full is its "full" case.
    assert datasets._full(dict(out), "X").shape[0] == sum(
        out[f"X_{s}"].shape[0] for s in ("train", "val", "test")
    )


def test_equities_dataset_pools_trainval_and_cuts_folds_on_the_date(monkeypatch):
    """``equities_seq`` loads the trainval pool with the keys and embargo = look-back; model-core then cuts
    every fold on one global date with the per-entity embargo (no network: the generator is stubbed)."""
    import juniper_data.generators.equities_seq as eq

    out = _panel_arrays(n_per=30, lookback=4)
    monkeypatch.setattr(
        eq.EquitiesSeqGenerator, "generate", staticmethod(lambda params: dict(out))
    )
    ds = datasets.equities_seq(
        symbols=("AAPL", "MSFT"), lookback=4, name="equities_seq_panel"
    )
    assert ds.name == "equities_seq_panel" and ds.grid == "irregular"
    assert ds.embargo == 4
    assert ds.X.shape[0] == 2 * (30 + 15), "train + val of both tickers; test excluded"
    assert ds.order is not None and ds.groups is not None
    folds = walk_forward_folds(
        ds.X.shape[0], n_folds=3, embargo=ds.embargo, order=ds.order, groups=ds.groups
    )
    assert folds, "the panel yields folds"
    for fold in folds:
        train, ev = np.asarray(fold.train_idx), np.asarray(fold.eval_idx)
        cut = int(ds.order[ev].min())
        assert ds.order[train].max() < cut, (
            "every train window precedes every eval window on the global date"
        )
        for code in (0, 1):
            before = np.sort(ds.order[(ds.groups == code) & (ds.order < cut)])
            kept = np.sort(ds.order[train[ds.groups[train] == code]])
            assert np.array_equal(
                kept, before[: max(0, before.shape[0] - ds.embargo)]
            ), "the last `embargo` windows of each entity before the cut are dropped"


def test_run_dataset_passes_the_keys_and_the_row_embargo_to_model_core(monkeypatch):
    from bench import run_benchmark

    captured: dict = {}
    real = run_benchmark.walk_forward_folds

    def spy(n, **kwargs):
        captured.clear()
        captured.update(kwargs)
        return real(n, **kwargs)

    monkeypatch.setattr(run_benchmark, "walk_forward_folds", spy)
    monkeypatch.setattr(run_benchmark, "_TORCH_AVAILABLE", False)
    out = _panel_arrays(n_per=60, lookback=4)
    arrays = dict(out)
    ds = datasets.Dataset(
        "panel",
        "irregular",
        datasets._composed(arrays, "X", "trainval"),
        datasets._composed(arrays, "y_reg", "trainval"),
        datasets._composed(arrays, "dt", "trainval"),
        datasets._composed(arrays, "target_dt", "trainval"),
        order=datasets._composed(arrays, "window_end_date", "trainval"),
        groups=datasets._composed(arrays, "ticker_code", "trainval"),
        embargo=4,
    )
    result = run_benchmark.run_dataset(ds)
    assert (
        captured["embargo"] == 4
        and captured["order"] is ds.order
        and captured["groups"] is ds.groups
    )
    assert result["folding"] == {
        "embargo": 4,
        "ordered": True,
        "grouped": True,
        "n_entities": 2,
        "n_folds": run_benchmark._N_FOLDS,
    }
    # The synthetic path is unchanged: row-index folds, the harness embargo.
    run_benchmark.run_dataset(datasets.irregular_sine(n_steps=240, lookback=12, seed=0))
    assert (
        captured["embargo"] == run_benchmark._EMBARGO
        and captured["order"] is None
        and captured["groups"] is None
    )


def test_panel_row_is_a_registered_extension_and_band_2b_covers_it():
    from bench import run_benchmark

    assert "equities_seq_panel" in datasets.DATASETS
    assert "equities_seq_panel" not in datasets.PRIMARY_DATASETS
    assert datasets.DATASETS["equities_seq_panel"].keywords == {
        "symbols": ("AAPL", "MSFT"),
        "name": "equities_seq_panel",
    }
    var = f"lmu_var_d{run_benchmark._HEADLINE_D}"
    rkey = f"lmu_var_d{run_benchmark._HEADLINE_D}_ridge{run_benchmark._RIDGE_VARIANT}"
    row = {
        "mean": {"rmse": 0.02, "r2": -0.1},
        "std": {"rmse": 0.001, "r2": 0.03},
        "n_folds": 5,
    }
    models = {
        var: row,
        f"lmu_fixed_d{run_benchmark._HEADLINE_D}": row,
        "naive_persistence": row,
        "linear_ridge": row,
        rkey: row,
    }
    bands = run_benchmark.evaluate_bands(
        {"equities_seq_panel": {"grid": "irregular", "models": models}}
    )
    assert any(
        b["band"].startswith("2b — equities_seq_panel") and not b["primary"]
        for b in bands
    )
'''

# ------------------------------------------------------------------------------------- juniper-recurrence/CHANGELOG.md
_CL_MARKER = "**The bench's equities rows pool `trainval` and cut a panel's folds on the global date per entity"
_CL_ENTRY = f"""- {_CL_MARKER}; a multi-ticker row `equities_seq_panel` joins the single-ticker one** (W5.2 of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, the owed
  bench half; `bench/` is not part of the published distribution). `bench/run_benchmark.py` cut row-index folds
  (`walk_forward_folds(n, embargo=2)`) over the composed `full` view, so on a multi-ticker request -- an
  entity-major pool -- ticker A's 2021 landed in train beside ticker B's 2015 in eval, and the last fold
  evaluated the `test` partition the plan reserves (F-P7 / W5.3). `bench/datasets.py`'s `Dataset` now carries
  `order` (`window_end_date`), `groups` (`ticker_code`) and the row's own `embargo`; `equities_seq` loads the
  composed `trainval` view (juniper-recurrence-model 0.6.0's `derive_composed_split`; `_full` is its `"full"`
  case) with those keys and `embargo = lookback`; `run_dataset` passes `order` / `groups` / the row's embargo
  to model-core -- the seam `POST /v1/crossval` uses -- and records a `folding` block (`embargo`, `ordered`,
  `grouped`, `n_entities`, `n_folds`) that the report's per-dataset header prints. The synthetic rows are
  unchanged (row-index folds, embargo 2). The new informational row `equities_seq_panel` (`AAPL` + `MSFT`)
  sits beside `equities_seq`; Band 2b covers both. Four bench tests pin the pool, the keys, the per-entity
  embargo on the date-cut folds, the `run_dataset` seam and the registry (the generator is stubbed; no
  network). Needs juniper-recurrence-model >= 0.6.0, the app's own floor since 0.8.0.

"""


def _replace_once(path: Path, old: str, new: str, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    # "new present once" is the applied test -- NOT "old absent": an insertion edit's new text contains
    # its anchor, so the old text is still present after the edit and a second run would apply it again.
    if text.count(new) == 1:
        print(f"  = {path.name} [{old.strip().splitlines()[0][:50]}]: already applied")
        return False
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: {path}: expected exactly one occurrence of {old.strip().splitlines()[0][:60]!r}, found {text.count(old)}")
    if check:
        print(f"  ~ {path.name} [{old.strip().splitlines()[0][:50]}]: WOULD rewrite")
        return True
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  + {path.name} [{old.strip().splitlines()[0][:50]}]: rewrote")
    return True


def _append_tests(path: Path, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if _TEST_MARKER in text:
        print("  = test_bench_smoke.py: W5.2 tests already present")
        return False
    if check:
        print("  ~ test_bench_smoke.py: WOULD append the four W5.2 tests")
        return True
    path.write_text(text.rstrip("\n") + "\n" + _TESTS, encoding="utf-8")
    print("  + test_bench_smoke.py: appended the four W5.2 tests")
    return True


def _insert_changelog(path: Path, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if _CL_MARKER in text:
        print("  = CHANGELOG.md: entry already present")
        return False
    start = text.index("## [Unreleased]\n")
    end = text.index("\n## [", start + 1)
    section = text[start:end]
    if "\n### Changed\n\n" in section:
        anchor = section.index("\n### Changed\n\n") + len("\n### Changed\n\n")
        new_section = section[:anchor] + _CL_ENTRY + section[anchor:]
        how = "first under the existing '### Changed'"
    else:
        head = "## [Unreleased]\n\n"
        new_section = head + "### Changed\n\n" + _CL_ENTRY.rstrip("\n") + "\n" + section[len(head):] if section.startswith(head) else section.rstrip("\n") + "\n\n### Changed\n\n" + _CL_ENTRY.rstrip("\n") + "\n"
        how = "as a new '### Changed' heading"
    if check:
        print(f"  ~ CHANGELOG.md: WOULD add the entry {how}")
        return True
    path.write_text(text[:start] + new_section + text[end:], encoding="utf-8")
    print(f"  + CHANGELOG.md: added the entry {how}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path, help="scratch tree laid out like the juniper-recurrence repo root")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    root = args.root.resolve()
    ds, rb = root / "bench" / "datasets.py", root / "bench" / "run_benchmark.py"

    changed = False
    for path, old, new in (
        (ds, _DS_DOC_OLD, _DS_DOC_NEW),
        (ds, _DS_REG_DOC_OLD, _DS_REG_DOC_NEW),
        (ds, _DS_CLASS_OLD, _DS_CLASS_NEW),
        (ds, _DS_FULL_OLD, _DS_FULL_NEW),
        (ds, _DS_EQ_SIG_OLD, _DS_EQ_SIG_NEW),
        (ds, _DS_EQ_BODY_OLD, _DS_EQ_BODY_NEW),
        (ds, _DS_REG_OLD, _DS_REG_NEW),
        (rb, _RB_EMBARGO_OLD, _RB_EMBARGO_NEW),
        (rb, _RB_FOLDS_OLD, _RB_FOLDS_NEW),
        (rb, _RB_RETURN_OLD, _RB_RETURN_NEW),
        (rb, _RB_2B_OLD, _RB_2B_NEW),
        (rb, _RB_HEADER_OLD, _RB_HEADER_NEW),
    ):
        changed |= _replace_once(path, old, new, args.check)
    changed |= _append_tests(root / "bench" / "test_bench_smoke.py", args.check)
    changed |= _insert_changelog(root / "juniper-recurrence" / "CHANGELOG.md", args.check)
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
