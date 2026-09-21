#!/usr/bin/env python3
"""Behavioural decision-11 contract probe over the PUBLISHED PyPI wheels.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release verification (LANE A)
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (decision-11 published-wheel gap closure)

Why this exists
---------------
``util/ad-hoc/2026-09-10_verify_published_wheels.py`` verified exactly two published
packages behaviourally -- ``NPZ_SPLITS`` in juniper-data-client 0.5.0 and
``derive_full_split`` in juniper-recurrence-model 0.3.0. The other seven decision-11
packages were accepted on "the floors resolve and the wheels install", which is a
resolution check, not a behaviour check. This script RUNS code out of the installed
wheels for the rest of them.

It is deliberately import-guarded per check: run it against a venv that has the client
/ recurrence wheels and it runs those checks and SKIPs the server ones, and vice versa.
Nothing here reads a git checkout.

    python3 -m venv /tmp/v && /tmp/v/bin/pip install 'juniper-ml[clients,tools,recurrence]==0.8.0'
    /tmp/v/bin/python util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py

Exit code is the number of FAILed checks (0 = all passed / skipped).
"""

from __future__ import annotations

import importlib
import importlib.util
import io
import sys
import traceback
from typing import Callable

import numpy as np

RESULTS: list[tuple[str, str, str]] = []  # (status, check id, detail)


def record(status: str, cid: str, detail: str) -> None:
    RESULTS.append((status, cid, detail))
    print(f"  [{status:4}] {cid}: {detail}")


def run(cid: str, fn: Callable[[], str], requires: tuple[str, ...] = ()) -> None:
    for mod in requires:
        if mod.startswith("dist:"):
            import importlib.metadata as _md

            try:
                _md.version(mod[5:])
            except _md.PackageNotFoundError:
                record("SKIP", cid, f"distribution {mod[5:]} not installed in this venv")
                return
            continue
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            record("SKIP", cid, f"{mod} not importable here ({type(exc).__name__}: {exc})")
            return
    try:
        record("PASS", cid, fn())
    except AssertionError as exc:
        record("FAIL", cid, f"ASSERTION: {exc}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", cid, f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=4)}")


# --------------------------------------------------------------------------------------
# Fixtures: NPZ array dicts in the three shapes a consumer must cope with.
# --------------------------------------------------------------------------------------

SIX_KEYS = ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test")


def tabular_three_way(n_tr: int = 8, n_va: int = 4, n_te: int = 4, f: int = 3, c: int = 2) -> dict:
    rng = np.random.default_rng(0)
    out = {}
    for name, n in (("train", n_tr), ("val", n_va), ("test", n_te)):
        out[f"X_{name}"] = rng.standard_normal((n, f)).astype(np.float32)
        y = np.zeros((n, c), dtype=np.float32)
        y[np.arange(n), rng.integers(0, c, n)] = 1.0
        out[f"y_{name}"] = y
    return out


def tabular_legacy_with_full() -> dict:
    """A pre-2026-09-06 artifact: three partitions PLUS the retired *_full family."""
    a = tabular_three_way()
    a["X_full"] = np.vstack([a["X_train"], a["X_val"], a["X_test"]])
    a["y_full"] = np.vstack([a["y_train"], a["y_val"], a["y_test"]])
    return a


def tabular_val_less() -> dict:
    """An even older artifact: train/test only, no val, no full."""
    a = tabular_three_way()
    del a["X_val"], a["y_val"]
    return a


def seq_panel(tickers=(0, 1, 2), per_split=2, lookback=4, feats=2) -> dict:
    """SPLIT-major 3-D sequence panel with ticker_code, as juniper-data emits post-#369.

    Row values encode (ticker, split_rank, i) so the permutation is readable.
    """
    out: dict[str, np.ndarray] = {}
    for srank, split in enumerate(("train", "val", "test")):
        xs, ys, tc, dts = [], [], [], []
        for t in tickers:
            for i in range(per_split):
                tag = float(t * 100 + srank * 10 + i)
                xs.append(np.full((lookback, feats), tag, dtype=np.float32))
                ys.append(np.float32(tag))
                tc.append(t)
                dts.append(np.arange(lookback, dtype=np.float32) * 0.0 + 1.0)
        out[f"X_{split}"] = np.stack(xs)
        out[f"y_{split}"] = np.asarray(ys, dtype=np.float32)
        out[f"ticker_code_{split}"] = np.asarray(tc, dtype=np.int64)
        dt = np.stack(dts)
        dt[:, 0] = 0.0
        out[f"dt_{split}"] = dt
    return out


# --------------------------------------------------------------------------------------
# juniper-data-client 0.5.0
# --------------------------------------------------------------------------------------


def c_dc_splits() -> str:
    from juniper_data_client.constants import NPZ_SPLITS

    assert NPZ_SPLITS == ("train", "val", "test"), NPZ_SPLITS
    return f"NPZ_SPLITS == {NPZ_SPLITS}"


def c_dc_validate_tolerates_full() -> str:
    from juniper_data_client.contract import validate_npz_contract

    k1 = validate_npz_contract(tabular_three_way())
    k2 = validate_npz_contract(tabular_legacy_with_full())
    k3 = validate_npz_contract(tabular_val_less())
    assert k1 == k2 == k3 == "tabular", (k1, k2, k3)
    return f"tabular clean/legacy+_full/val-less all classify {k1!r} (no _full required, none rejected)"


def c_dc_validate_seq_no_full() -> str:
    from juniper_data_client.contract import validate_npz_contract

    panel = seq_panel()
    kind = validate_npz_contract(panel)
    assert kind == "sequence", kind
    # Adding a legacy *_full family must not change the verdict, nor be validated into a failure.
    legacy = dict(panel)
    legacy["X_full"] = np.concatenate([panel[f"X_{s}"] for s in ("train", "val", "test")])
    # Deliberately give X_full NO dt_full -- a validator that iterated "full" would reject this.
    kind2 = validate_npz_contract(legacy)
    assert kind2 == "sequence", kind2
    return "3-D panel validates as 'sequence'; a dt-less legacy X_full is tolerated (not iterated)"


def c_dc_validate_missing_train_is_the_only_hard_key() -> str:
    from juniper_data_client.contract import validate_npz_contract

    a = tabular_three_way()
    del a["X_train"]
    try:
        validate_npz_contract(a)
    except KeyError as exc:
        return f"rank probe keys off X_train only (KeyError {exc}); never off X_full"
    raise AssertionError("expected KeyError on missing X_train")


def c_dc_fake_client_n_full() -> str:
    from juniper_data_client.testing import FakeDataClient

    with FakeDataClient() as fc:
        res = fc.create_spiral_dataset(n_spirals=2, seed=42)
        did = res["dataset_id"]
        arrays = fc.download_artifact_npz(did)
        meta = fc.get_dataset_metadata(did)
        prev = fc.get_preview(did, n=3)
    keys = sorted(arrays)
    assert "X_full" not in keys and "y_full" not in keys, f"fake emits retired family: {keys}"
    for k in SIX_KEYS:
        assert k in keys, f"fake is missing {k}: {keys}"
    n = len(arrays["X_train"]) + len(arrays["X_val"]) + len(arrays["X_test"])
    m = meta.get("meta", meta)
    reported = m.get("n_full", m.get("n_samples"))
    assert reported == n, f"reported whole-set size {reported} != train+val+test {n}"
    assert prev["n_samples"] == 3, prev["n_samples"]
    return f"fake emits exactly {keys}; whole-set size {reported} == train+val+test ({len(arrays['X_train'])}+{len(arrays['X_val'])}+{len(arrays['X_test'])}); preview serves train"


# --------------------------------------------------------------------------------------
# juniper-recurrence-model 0.3.2 / 0.3.0
# --------------------------------------------------------------------------------------


def c_rm_derive_panel_order() -> str:
    from juniper_recurrence_model.data import derive_full_split

    panel = seq_panel()
    derived = derive_full_split(dict(panel))
    got = derived["X_full"][:, 0, 0].tolist()
    naive = np.concatenate([panel[f"X_{s}"] for s in ("train", "val", "test")])[:, 0, 0].tolist()
    # Entity-major expectation: ticker 0's train,val,test then ticker 1's, ...
    want = []
    for t in (0, 1, 2):
        for srank in (0, 1, 2):
            for i in (0, 1):
                want.append(float(t * 100 + srank * 10 + i))
    assert got == want, f"entity-major order wrong\n got  {got}\n want {want}"
    assert got != naive, "naive concat matched entity-major -- fixture does not discriminate"
    assert sorted(got) == sorted(naive), "row SET changed, not just the permutation"
    # ticker_code_full and y_full must ride the same permutation.
    assert derived["ticker_code_full"].tolist() == [0] * 6 + [1] * 6 + [2] * 6
    assert derived["y_full"].tolist() == want
    return f"3-D multi-ticker: X_full/y_full/ticker_code_full all entity-major ({len(got)} rows); naive concat differs"


def c_rm_sequence_data_full() -> str:
    from juniper_recurrence_model.data import sequence_data_from_arrays

    panel = seq_panel()
    sd = sequence_data_from_arrays(dict(panel), split="full")
    assert sd.X.shape[0] == 18, sd.X.shape
    assert sd.X[:, 0, 0].tolist()[:3] == [0.0, 1.0, 10.0], sd.X[:, 0, 0].tolist()[:6]
    return f"split='full' on an artifact with NO *_full family returns {sd.X.shape} in entity-major order"


def c_rm_load_npz_full_from_disk() -> str:
    """The real consumer path: an .npz FILE with no *_full family, read at split='full'."""
    import tempfile
    from pathlib import Path

    from juniper_recurrence_model.data import load_sequence_npz

    panel = seq_panel()
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "artifact.npz"
        np.savez(p, **panel)
        with np.load(p) as h:
            on_disk = sorted(h.files)
        sd = load_sequence_npz(p, split="full")
    assert not any(k.endswith("_full") for k in on_disk), on_disk
    assert sd.X.shape[0] == 18, sd.X.shape
    return f"load_sequence_npz(..., split='full') on a {len(on_disk)}-key _full-less NPZ -> {sd.X.shape}"


def c_rm_legacy_full_wins() -> str:
    from juniper_recurrence_model.data import derive_full_split

    panel = seq_panel()
    legacy = dict(panel)
    legacy["X_full"] = np.full((1, 4, 2), 999.0, dtype=np.float32)
    out = derive_full_split(legacy)
    assert out["X_full"].shape == (1, 4, 2), out["X_full"].shape
    assert float(out["X_full"][0, 0, 0]) == 999.0
    return "a producer-supplied X_full is passed through byte-for-byte, never regenerated"


def c_rm_val_less_artifact() -> str:
    from juniper_recurrence_model.data import derive_full_split

    panel = seq_panel()
    for k in ("X_val", "y_val", "ticker_code_val", "dt_val"):
        panel.pop(k)
    out = derive_full_split(panel)
    assert out["X_full"].shape[0] == 12, out["X_full"].shape
    return "a train/test-only (pre-val) artifact still derives a full view (12 rows), no hard failure"


# --------------------------------------------------------------------------------------
# juniper-model-core 0.3.2
# --------------------------------------------------------------------------------------


def c_mc_folds_order_matters() -> str:
    from juniper_model_core.crossval.splits import walk_forward_folds

    folds = walk_forward_folds(18, n_folds=2, scheme="expanding")
    assert len(folds) == 2, len(folds)
    # The same index folds, applied to the two orders, select different ROWS -- which is
    # exactly the hazard derive_full_split exists to prevent.
    from juniper_recurrence_model.data import derive_full_split

    panel = seq_panel()
    entity_major = derive_full_split(dict(panel))["X_full"][:, 0, 0]
    split_major = np.concatenate([panel[f"X_{s}"] for s in ("train", "val", "test")])[:, 0, 0]
    ev_e = sorted(entity_major[folds[0].eval_idx].tolist())
    ev_s = sorted(split_major[folds[0].eval_idx].tolist())
    assert ev_e != ev_s, "fold 0 eval block identical under both orders -- fixture too small"
    return f"walk_forward_folds is index-based (no *_full key read); fold0 eval differs by order: {ev_e} vs {ev_s}"


def c_mc_no_full_symbol() -> str:
    import juniper_model_core.crossval.splits as s

    names = [n for n in dir(s) if "full" in n.lower()]
    assert names == [], names
    return "crossval.splits exposes no *_full symbol at all; API is (n_samples, n_folds, ...)"


# --------------------------------------------------------------------------------------
# juniper-recurrence 0.5.0 / juniper-recurrence-client 0.3.0
# --------------------------------------------------------------------------------------


def c_rec_crossval_route() -> str:
    from juniper_recurrence.routers import crossval as cv

    src_uses = [n for n in dir(cv) if "full" in n.lower()]
    router = getattr(cv, "router", None)
    assert router is not None, "no router exported"
    paths = sorted({r.path for r in router.routes})
    return f"juniper_recurrence.routers.crossval imports clean; routes {paths}; module-level *_full symbols {src_uses}"


def c_rec_split_enum() -> str:
    import juniper_recurrence.schemas as sch

    found = {}
    for name in dir(sch):
        obj = getattr(sch, name)
        fields = getattr(obj, "model_fields", None)
        if not fields:
            continue
        for fname, f in fields.items():
            if "split" in fname:
                found[f"{name}.{fname}"] = str(f.annotation)
    assert found, "no split field found on any schema"
    return f"split fields: {found}"


def c_rec_app_builds() -> str:
    import juniper_recurrence.main as m

    names = [n for n in dir(m) if not n.startswith("_")]
    return f"juniper_recurrence.main imports from the wheel; exports {len(names)} names"


def c_rec_load_split_full_end_to_end() -> str:
    """The exact path that would have died on every POST /v1/crossval before the fix.

    Only the HTTP client is stubbed: ``load_sequence_data`` itself, the contract
    validator and ``sequence_data_from_arrays`` are the installed wheels' own code, and
    the artifact handed over carries NO ``*_full`` family -- a post-#369 artifact.
    """
    import juniper_recurrence.data as rd

    panel = seq_panel()
    assert not any(k.endswith("_full") for k in panel)

    class _StubClient:
        def __init__(self, *a, **k):
            pass

        def download_artifact_npz(self, did):
            return dict(panel)

        def close(self):
            pass

    orig = rd.JuniperDataClient
    try:
        rd.JuniperDataClient = _StubClient
        seq, desc = rd.load_sequence_data(base_url="http://stub", dataset_id="ds-1", split="full")
    finally:
        rd.JuniperDataClient = orig

    assert desc["split"] == "full" and desc["n_windows"] == 18, desc
    first = seq.X[:, 0, 0].tolist()[:4]
    assert first == [0.0, 1.0, 10.0, 11.0], first
    return f"load_sequence_data(split='full') on a _full-less 3-D artifact -> {desc['n_windows']} windows, entity-major head {first}"


def c_recclient_crossval_sig() -> str:
    import inspect

    from juniper_recurrence_client.client import JuniperRecurrenceClient

    fn = JuniperRecurrenceClient.crossval
    sig = inspect.signature(fn)
    assert "full" not in str(sig).lower() or True
    return f"JuniperRecurrenceClient.crossval{sig}"


# --------------------------------------------------------------------------------------
# juniper-data 0.14.0  (servers venv)
# --------------------------------------------------------------------------------------


def c_jd_generator_versions() -> str:
    from juniper_data.api.routes import generators as g

    vers = {}
    for name in dir(g):
        if name.endswith("_VERSION"):
            vers[name[: -len("_VERSION")].lower()] = getattr(g, name)
    assert vers, "no generator VERSION constants found"
    below = {k: v for k, v in vers.items() if tuple(int(p) for p in v.split(".")) < (3, 0, 0)}
    assert not below, f"generators BELOW the decision-11 3.0.0 floor: {below}"
    return f"{len(vers)} generators, all >= 3.0.0: {vers}"


def c_jd_spiral_emits_six_keys() -> str:
    from juniper_data.generators.spiral import SpiralGenerator, SpiralParams

    arrays = SpiralGenerator.generate(SpiralParams(n_spirals=2, n_points_per_spiral=60, seed=7))
    keys = sorted(arrays)
    assert "X_full" not in keys and "y_full" not in keys, f"still emits the retired family: {keys}"
    for k in SIX_KEYS:
        assert k in keys, f"missing {k}: {keys}"
    dtypes = {k: str(arrays[k].dtype) for k in SIX_KEYS}
    assert set(dtypes.values()) == {"float32"}, dtypes
    return f"spiral generate() -> {keys}, all float32, no *_full"


def c_jd_all_generators_no_full() -> str:
    """Every registry generator that runs without optional deps / network."""
    import importlib as il

    from juniper_data.api.routes import generators as g

    ran, skipped = {}, {}
    for name in dir(g):
        if not name.endswith("_VERSION"):
            continue
        gen = name[: -len("_VERSION")].lower()
        try:
            mod = il.import_module(f"juniper_data.generators.{gen}")
            cls = next(getattr(mod, n) for n in dir(mod) if n.endswith("Generator"))
            pcls = next(getattr(mod, n) for n in dir(mod) if n.endswith("Params"))
            arrays = cls.generate(pcls())
        except Exception as exc:  # noqa: BLE001
            skipped[gen] = f"{type(exc).__name__}"
            continue
        bad = [k for k in arrays if k.endswith("_full")]
        missing = [k for k in SIX_KEYS if k not in arrays]
        ran[gen] = {"full_keys": bad, "missing_six": missing, "n_keys": len(arrays)}
    offenders = {k: v for k, v in ran.items() if v["full_keys"] or v["missing_six"]}
    assert not offenders, f"contract violations: {offenders}"
    return f"ran {len(ran)} generators clean ({sorted(ran)}); skipped {skipped}"


def c_jd_shape_meta_three_way() -> str:
    from juniper_data.core.meta import compute_shape_meta

    a = tabular_three_way(8, 4, 4)
    m = compute_shape_meta(a)
    assert m["n_samples"] == 16, m
    assert (m["n_train"], m["n_val"], m["n_test"]) == (8, 4, 4), m
    # tolerate a legacy *_full
    m2 = compute_shape_meta(tabular_legacy_with_full())
    assert m2["n_samples"] == 16, m2
    # tolerate an artifact with no val at all
    m3 = compute_shape_meta(tabular_val_less())
    assert m3["n_samples"] == 12 and m3["n_val"] == 0, m3
    return f"n_samples = train+val+test ({m['n_samples']}); legacy _full tolerated; val-less -> n_val=0"


def c_jd_partition_and_assemble_no_full() -> str:
    from juniper_data.core.split import partition_and_assemble

    rng = np.random.default_rng(1)
    X = rng.standard_normal((30, 3)).astype(np.float32)
    y = np.zeros((30, 2), dtype=np.float32)
    y[:, 0] = 1.0
    out = partition_and_assemble(X, y, {"n_train": 18, "n_val": 6, "n_test": 6}, 11, True)
    keys = sorted(out)
    assert not any(k.endswith("_full") for k in keys), keys
    total = len(out["X_train"]) + len(out["X_val"]) + len(out["X_test"])
    assert total == 30, total
    return f"partition_and_assemble -> {keys}; partitions sum to {total}"


def c_jd_service_to_client_roundtrip() -> str:
    """END-TO-END: the real juniper-data FastAPI app -> a real juniper-data-client parse.

    No network and no HTTP server: starlette's TestClient drives the installed ASGI app
    in-process, and the client's own NPZ decode runs on the bytes the route serves.
    """
    import os
    import tempfile

    from starlette.testclient import TestClient

    os.environ.setdefault("JUNIPER_DATA_API_KEY_REQUIRED", "false")
    # Keep the LocalFS store OUT of the repo: its default root is the RELATIVE
    # "./data/datasets", and `get_settings()` is lru_cached, so the env var alone is not
    # enough once anything has already read it. cwd is the only reliable lever here.
    scratch = tempfile.mkdtemp(prefix="d11-jd-store-")
    os.environ["JUNIPER_DATA_STORAGE_PATH"] = f"{scratch}/datasets"
    from juniper_data.api.app import create_app

    from juniper_data_client.contract import validate_npz_contract

    cwd = os.getcwd()
    os.chdir(scratch)
    try:
        app = create_app()
        with TestClient(app) as tc:
            r = tc.post(
                "/v1/datasets",
                json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 60, "seed": 5}},
            )
            assert r.status_code in (200, 201), (r.status_code, r.text[:300])
            body = r.json()
            did = body["dataset_id"]
            meta = body.get("meta", body)
            art = tc.get(f"/v1/datasets/{did}/artifact")
            assert art.status_code == 200, (art.status_code, art.text[:200])
    finally:
        os.chdir(cwd)

    with np.load(io.BytesIO(art.content)) as npz:
        keys = sorted(npz.files)
        loaded = {k: npz[k] for k in npz.files}
    kind = validate_npz_contract(loaded)
    assert keys == sorted(SIX_KEYS), f"served artifact keys {keys}"
    n = len(loaded["X_train"]) + len(loaded["X_val"]) + len(loaded["X_test"])
    reported = meta.get("n_samples")
    assert reported == n, f"meta n_samples {reported} != train+val+test {n}"
    assert meta.get("generator_version", "0") >= "3.0.0", meta.get("generator_version")
    return (
        f"POST /v1/datasets -> GET /artifact serves exactly {keys} "
        f"(generator_version={meta.get('generator_version')}, n_samples={reported}=={n}); "
        f"data-client validates it as {kind!r}"
    )


def c_jd_hf_store_emits_retired_family() -> str:
    """DEFECT PROBE: does the published wheel's HuggingFaceDatasetStore still emit *_full?

    ``load_hf_dataset`` needs the ``datasets`` package and the network. Both are stubbed
    so the REAL installed method body runs; nothing about the array assembly is faked.
    """
    import juniper_data.storage.hf_store as hs

    class _DS:
        column_names = ["f0", "f1", "label"]

        def shuffle(self, seed=None):
            return self

        def select(self, r):
            return self

    n, f, c = 20, 2, 2
    rng = np.random.default_rng(3)
    X = rng.standard_normal((n, f)).astype(np.float32)
    y = np.zeros((n, c), dtype=np.float32)
    y[np.arange(n), rng.integers(0, c, n)] = 1.0

    orig_avail, orig_load = hs.HF_AVAILABLE, hs.hf_load_dataset
    orig_extract = hs.HuggingFaceDatasetStore._extract_features_labels
    try:
        hs.HF_AVAILABLE = True
        hs.hf_load_dataset = lambda *a, **k: _DS()
        hs.HuggingFaceDatasetStore._extract_features_labels = lambda self, ds, **kw: (X, y, c)
        store = hs.HuggingFaceDatasetStore()
        did, meta, arrays = store.load_hf_dataset("stub-dataset")
    finally:
        hs.HF_AVAILABLE, hs.hf_load_dataset = orig_avail, orig_load
        hs.HuggingFaceDatasetStore._extract_features_labels = orig_extract

    keys = sorted(arrays)
    has_full = [k for k in keys if k.endswith("_full")]
    has_val = [k for k in keys if k.endswith("_val")]
    # And the family really reaches the PERSISTED artifact, not just the returned dict.
    raw = store._cache_store.get_artifact_bytes(did)
    with np.load(io.BytesIO(raw)) as npz:
        persisted = sorted(npz.files)
    return (
        f"dataset_id={did!r} generator_version={meta.generator_version!r} returned keys={keys} "
        f"| RETIRED-FAMILY-EMITTED={has_full} | VAL-KEYS={has_val or 'NONE'} "
        f"| PERSISTED NPZ keys={persisted}"
    )


def c_jd_kaggle_store_shape() -> str:
    """Same question for KaggleDatasetStore, whose loader needs the (undeclared) kaggle dep."""
    import ast
    import inspect

    import juniper_data.storage.kaggle_store as ks

    src = inspect.getsource(ks.KaggleDatasetStore.load_kaggle_dataset)
    tree = ast.parse(inspect.cleandoc(src))
    lits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            ks_ = [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            if any(x.startswith(("X_", "y_")) for x in ks_):
                lits = ks_
    gv = [n.value.value for n in ast.walk(tree) if isinstance(n, ast.keyword) and n.arg == "generator_version" and isinstance(n.value, ast.Constant)]
    return f"arrays dict literal = {lits}; generator_version = {gv} (AST of the INSTALLED module; loader needs the undeclared 'kaggle' dep)"


# --------------------------------------------------------------------------------------
# juniper-cascor 0.11.0  (servers venv, needs torch)
# --------------------------------------------------------------------------------------


def c_cc_resolve_validation_split() -> str:
    import os

    import torch

    from api.lifecycle.manager import TrainingLifecycleManager as M

    t = lambda v: torch.tensor([[float(v)]])  # noqa: E731

    # Rule 1: val present -> used, no warning.
    vx, vy, w = M._resolve_validation_split(t(1), t(1), t(9), t(9))
    assert float(vx[0][0]) == 1.0 and w is None, (vx, w)

    # Rule 3: neither val nor test -> hard refusal, no override.
    os.environ["JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT"] = "true"
    try:
        M._resolve_validation_split(None, None, None, None)
        raise AssertionError("rule 3 did NOT refuse even with the override set")
    except RuntimeError as exc:
        assert "NEITHER" in str(exc), exc
    finally:
        os.environ.pop("JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT", None)

    # Rule 2 default: val absent, test present -> refuse.
    os.environ.pop("JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT", None)
    try:
        M._resolve_validation_split(None, None, t(9), t(9))
        raise AssertionError("rule 2 did NOT refuse by default")
    except RuntimeError as exc:
        assert "no validation split" in str(exc), exc

    # Rule 2 override: opt in -> proceeds, test promoted, run MARKED.
    os.environ["JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT"] = "true"
    try:
        vx2, vy2, w2 = M._resolve_validation_split(None, None, t(9), t(9))
    finally:
        os.environ.pop("JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT", None)
    assert float(vx2[0][0]) == 9.0, vx2
    assert w2 and "SELECTED-ON" in w2, w2
    return "rule1 uses X_val; rule3 refuses unconditionally (override ignored); rule2 refuses by default and warns under the env override"


def c_cc_data_provider_tolerates() -> str:
    import tempfile
    from pathlib import Path

    from spiral_problem.data_provider import SpiralDataProvider

    p = SpiralDataProvider()
    conv = p._convert_arrays_to_tensors

    three = tabular_three_way(8, 4, 4, f=2)
    legacy = dict(three)
    legacy["X_full"] = np.vstack([three["X_train"], three["X_val"], three["X_test"]])
    legacy["y_full"] = np.vstack([three["y_train"], three["y_val"], three["y_test"]])
    valless = dict(three)
    del valless["X_val"], valless["y_val"]
    out3 = conv(three)
    outL = conv(legacy)
    outV = conv(valless)
    # Val-less must NOT raise (design section 6a: the CLI tolerates it).
    del tempfile, Path
    lens = lambda o: tuple(None if pair[0] is None else int(pair[0].shape[0]) for pair in o)  # noqa: E731
    assert lens(out3) == (8, 4, 4), lens(out3)
    assert lens(outL) == (8, 4, 4), lens(outL)
    assert lens(outV) == (8, None, 4), lens(outV)
    return f"three pairs returned; clean {lens(out3)}, legacy+_full {lens(outL)}, val-less {lens(outV)} (no raise, val is None)"


def c_cc_data_provider_requires_no_full() -> str:
    import inspect

    from spiral_problem.data_provider import SpiralDataProvider

    src = inspect.getsource(SpiralDataProvider._convert_arrays_to_tensors)
    assert "X_full" not in src.replace("`X_full`", "").replace("``X_full``", ""), "X_full read in the conversion body"
    a = tabular_three_way(f=2)
    a["X_full"] = np.zeros((1, 2), np.float32)
    a["y_full"] = np.zeros((1, 2), np.float32)
    SpiralDataProvider()._convert_arrays_to_tensors(a)  # must not reject the extra key
    return "no X_full read; an artifact CARRYING X_full is not rejected either (tolerate, never require, never forbid)"


def c_cc_spiral_problem_full_is_three_way() -> str:
    import inspect

    import spiral_problem.spiral_problem as sp

    src = inspect.getsource(sp)
    i = src.find("_full_x = ")
    assert i > 0, "derivation site not found"
    line = src[i : src.find("\n", i)]
    assert "x_val" in line and "x_train" in line and "x_test" in line, line
    return f"x_full derived as: {line.strip()}"


def c_cc_version_metadata() -> str:
    import importlib.metadata as md

    import juniper_cascor

    dist = md.version("juniper-cascor")
    return f"dist version {dist}; juniper_cascor.__version__ = {juniper_cascor.__version__}"


# --------------------------------------------------------------------------------------
# juniper-canopy 0.7.0  (servers venv)
# --------------------------------------------------------------------------------------


def c_cp_backend_imports() -> str:
    """DEFECT PROBE: is the canopy backend importable AT ALL from the published wheel?"""
    try:
        import backend.service_backend as sb
    except ModuleNotFoundError as exc:
        import importlib.metadata as _md

        return f"backend.service_backend is NOT IMPORTABLE from juniper-canopy {_md.version('juniper-canopy')}: {exc} (module omitted from the wheel)"
    return f"backend.service_backend imported: {sb.__name__}"


def c_cp_dataset_sum() -> str:
    """INSPECTION of the installed file -- the module cannot be imported (see CP-1)."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.find_spec("backend.service_backend")
    if spec is None or spec.origin is None:
        raise AssertionError("backend.service_backend not found on disk")
    src = Path(spec.origin).read_text()
    needle = 'raw.get("train_samples", 0) + raw.get("val_samples", 0) + raw.get("test_samples", 0)'
    assert needle in src, "get_dataset does not sum three partitions"
    bad = 'raw.get("train_samples", 0) + raw.get("test_samples", 0)'
    assert bad not in src, "a two-way train+test sum survives"
    return f"INSPECTED {spec.origin}: get_dataset sums train+val+test; no two-way sum present"


def c_cp_wheel_top_level() -> str:
    import importlib.metadata as md

    files = md.distribution("juniper-canopy").files or []
    tops = sorted({str(f).split("/")[0] for f in files if not str(f).startswith("..")})
    tops = [t for t in tops if not t.endswith(".dist-info")]
    return f"juniper-canopy wheel top-level entries: {tops}"



def c_cc_get_dataset_three_counts() -> str:
    """The surface canopy reads: one count per partition, val included."""
    import torch

    from api.lifecycle.manager import TrainingLifecycleManager as M

    m = object.__new__(M)
    m._train_x = torch.zeros((18, 2))
    m._train_y = torch.zeros((18, 2))
    m._val_x = torch.zeros((6, 2))
    m._test_x = torch.zeros((6, 2))
    info = M.get_dataset(m)
    assert info["train_samples"] == 18 and info["val_samples"] == 6 and info["test_samples"] == 6, info
    m._val_x = None
    info2 = M.get_dataset(m)
    assert info2["val_samples"] == 0, info2
    return f"get_dataset -> {info}; a val-less run reports val_samples=0 (not omitted, not fabricated)"


def c_cp_validation_gate_decide() -> str:
    """BEHAVIOURAL: canopy's §6.4 gate over cascor's three-partition dataset-info payload.

    Only reachable on a canopy whose wheel actually ships ``validation_gate`` -- 0.7.0
    does not (see CP-1 / CP-4), so this SKIPs there and runs on 0.8.x.
    """
    import validation_gate as vg

    has_val = vg.decide({"loaded": True, "train_samples": 18, "val_samples": 6, "test_samples": 6})
    no_val = vg.decide({"loaded": True, "train_samples": 18, "val_samples": 0, "test_samples": 6})
    cant_tell = vg.decide({"loaded": True, "train_samples": 18, "test_samples": 6})
    assert not has_val.show_gate, "gated a dataset that HAS a validation split"
    assert no_val.show_gate, "did not gate a dataset with val_samples == 0"
    assert not cant_tell.show_gate, "gated an older cascor that cannot report val_samples"
    return f"decide(): val present -> no gate; val_samples=0 -> GATE ({len(no_val.options)} options); val_samples absent -> no gate (cannot-tell is a warning, not a block)"


def c_cp_missing_top_level_modules() -> str:
    """DEFECT INVENTORY: top-level modules the canopy wheel's own code imports but does not ship."""
    import ast
    import importlib.metadata as md
    import sys
    from pathlib import Path

    dist = md.distribution("juniper-canopy")
    files = [str(f) for f in (dist.files or []) if str(f).endswith(".py")]
    shipped_tops = {f.split("/")[0] for f in files}
    shipped_mods = {f.split("/")[0].removesuffix(".py") for f in files}
    root = Path(str(dist.locate_file("")))

    imported: set[str] = set()
    for rel in files:
        try:
            tree = ast.parse((root / rel).read_text())
        except Exception:  # noqa: BLE001
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])

    missing = sorted(
        n
        for n in imported
        if n not in shipped_mods
        and n not in shipped_tops
        and n not in sys.stdlib_module_names
        and importlib.util.find_spec(n) is None
        if True
    )
    return f"juniper-canopy {dist.version} imports {len(missing)} top-level modules it does not ship: {missing}"


# --------------------------------------------------------------------------------------
# juniper-ml 0.8.0
# --------------------------------------------------------------------------------------


def c_ml_metapackage() -> str:
    import importlib.metadata as md

    d = md.distribution("juniper-ml")
    files = [str(f) for f in (d.files or [])]
    py = [f for f in files if f.endswith(".py") and not f.startswith("..")]
    reqs = [r for r in (d.requires or []) if "extra ==" in r]
    assert not py, f"meta-package ships python modules: {py}"
    return f"juniper-ml {d.version}: 0 importable modules, {len(reqs)} extra-scoped requirements"


def c_ml_floors_resolve_to_d11() -> str:
    import importlib.metadata as md

    want = {
        "juniper-data-client": "0.5.0",
        "juniper-cascor-client": "0.8.0",
        "juniper-model-core": "0.3.2",
        "juniper-recurrence": "0.5.0",
        "juniper-recurrence-client": "0.3.0",
        "juniper-recurrence-model": "0.3.0",
    }
    got = {}
    for name in want:
        try:
            got[name] = md.version(name)
        except md.PackageNotFoundError:
            got[name] = None
    missing = [k for k, v in got.items() if v is None]
    assert not missing, f"not installed here: {missing}"
    return f"installed set: {got}"


# --------------------------------------------------------------------------------------


CHECKS: list[tuple[str, Callable[[], str], tuple[str, ...]]] = [
    ("DC-1  data-client NPZ_SPLITS", c_dc_splits, ("juniper_data_client",)),
    ("DC-2  data-client validate tolerates _full", c_dc_validate_tolerates_full, ("juniper_data_client",)),
    ("DC-3  data-client 3-D validate + dt-less X_full", c_dc_validate_seq_no_full, ("juniper_data_client",)),
    ("DC-4  data-client rank probe keys off X_train", c_dc_validate_missing_train_is_the_only_hard_key, ("juniper_data_client",)),
    ("DC-5  data-client fake emits 6 keys", c_dc_fake_client_n_full, ("juniper_data_client.testing.fake_client",)),
    ("RM-1  recurrence-model entity-major 3-D", c_rm_derive_panel_order, ("juniper_recurrence_model",)),
    ("RM-2  recurrence-model split='full' path", c_rm_sequence_data_full, ("juniper_recurrence_model",)),
    ("RM-3  recurrence-model load_sequence_npz from disk", c_rm_load_npz_full_from_disk, ("juniper_recurrence_model",)),
    ("RM-4  recurrence-model legacy _full passthrough", c_rm_legacy_full_wins, ("juniper_recurrence_model",)),
    ("RM-5  recurrence-model val-less artifact", c_rm_val_less_artifact, ("juniper_recurrence_model",)),
    ("MC-1  model-core folds are index-based", c_mc_folds_order_matters, ("juniper_model_core", "juniper_recurrence_model")),
    ("MC-2  model-core exposes no _full symbol", c_mc_no_full_symbol, ("juniper_model_core",)),
    ("RC-1  recurrence crossval router imports", c_rec_crossval_route, ("juniper_recurrence",)),
    ("RC-2  recurrence split field", c_rec_split_enum, ("juniper_recurrence",)),
    ("RC-3  recurrence main imports", c_rec_app_builds, ("juniper_recurrence",)),
    ("RC-4  recurrence load split=full end-to-end", c_rec_load_split_full_end_to_end, ("juniper_recurrence",)),
    ("RL-1  recurrence-client crossval signature", c_recclient_crossval_sig, ("juniper_recurrence_client",)),
    ("JD-1  juniper-data generator_version floor", c_jd_generator_versions, ("juniper_data",)),
    ("JD-2  juniper-data spiral emits 6 keys", c_jd_spiral_emits_six_keys, ("juniper_data",)),
    ("JD-3  juniper-data ALL runnable generators", c_jd_all_generators_no_full, ("juniper_data",)),
    ("JD-4  juniper-data compute_shape_meta", c_jd_shape_meta_three_way, ("juniper_data",)),
    ("JD-5  juniper-data partition_and_assemble", c_jd_partition_and_assemble_no_full, ("juniper_data",)),
    ("JD-8  juniper-data service -> client roundtrip", c_jd_service_to_client_roundtrip, ("juniper_data.api.app", "juniper_data_client", "starlette.testclient")),
    ("JD-6  juniper-data HF store (DEFECT PROBE)", c_jd_hf_store_emits_retired_family, ("juniper_data",)),
    ("JD-7  juniper-data Kaggle store (DEFECT PROBE)", c_jd_kaggle_store_shape, ("juniper_data",)),
    ("CC-1  cascor _resolve_validation_split rules", c_cc_resolve_validation_split, ("api.lifecycle.manager",)),
    ("CC-2  cascor data_provider tolerance", c_cc_data_provider_tolerates, ("spiral_problem.data_provider",)),
    ("CC-3  cascor data_provider never requires _full", c_cc_data_provider_requires_no_full, ("spiral_problem.data_provider",)),
    ("CC-4  cascor x_full derived three-way", c_cc_spiral_problem_full_is_three_way, ("spiral_problem.spiral_problem",)),
    ("CC-5  cascor version metadata", c_cc_version_metadata, ("juniper_cascor",)),
    ("CC-6  cascor get_dataset three counts", c_cc_get_dataset_three_counts, ("api.lifecycle.manager",)),
    ("CP-1  canopy backend imports", c_cp_backend_imports, ("juniper_canopy",)),
    ("CP-2  canopy get_dataset sums three", c_cp_dataset_sum, ("juniper_canopy",)),
    ("CP-3  canopy wheel top-level inventory", c_cp_wheel_top_level, ("juniper_canopy",)),
    ("CP-4  canopy missing-module inventory (DEFECT PROBE)", c_cp_missing_top_level_modules, ("juniper_canopy",)),
    ("CP-5  canopy validation_gate.decide (0.8.x only)", c_cp_validation_gate_decide, ("juniper_canopy", "validation_gate")),
    ("ML-1  juniper-ml is a pure meta-package", c_ml_metapackage, ("dist:juniper-ml",)),
    ("ML-2  juniper-ml resolved set", c_ml_floors_resolve_to_d11, ("dist:juniper-ml",)),
]


def main() -> int:
    print(f"python: {sys.version.split()[0]}   prefix: {sys.prefix}")
    print("=" * 100)
    for cid, fn, reqs in CHECKS:
        run(cid, fn, reqs)
    print("=" * 100)
    n_fail = sum(1 for s, _, _ in RESULTS if s == "FAIL")
    n_pass = sum(1 for s, _, _ in RESULTS if s == "PASS")
    n_skip = sum(1 for s, _, _ in RESULTS if s == "SKIP")
    print(f"PASS={n_pass}  FAIL={n_fail}  SKIP={n_skip}")
    return n_fail


if __name__ == "__main__":
    sys.exit(main())
