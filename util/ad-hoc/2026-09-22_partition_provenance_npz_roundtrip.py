#!/usr/bin/env python3
"""Round-trip and digest-determinism probe for Decision 12's ``partition_provenance`` encoding.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md; pcalnon/juniper-data#423

What it verifies
----------------
The spec stores the block as canonical JSON inside the NPZ, under the key
``partition_provenance``, as a 0-d fixed-width unicode (``<U``) array. It digests every
partition array with a self-describing SHA-256 scheme (``juniper-array-v1``). Consumers load
with ``allow_pickle=False``: numpy's default, which juniper-data-client's
``download_artifact_npz`` relies on. So the encoding must survive that. Check groups:

E  encoding round trip (savez and savez_compressed, eager all-key read, allow_pickle=False),
   the uint8 alternative, and three hazards: numpy-2 StringDType, ``<U`` trailing-NUL
   stripping, and object arrays (the shape of arc_agi's ``task_ids``);
D  the digest: two independent implementations agree; invariance under memory layout,
   byte order and NPZ round trip; sensitivity to shape, dtype and value; golden vectors;
C  the existing ``DatasetMeta.checksum`` precondition (np.savez is byte-deterministic) and
   that it is not a hash of the served (compressed) bytes;
J  canonical-JSON text stability, and dataset-id re-derivation from JSON-round-tripped params
   against the REAL ``generate_dataset_id`` (needs ``juniper_data`` importable);
P  a producer + gate prototype over a REAL spiral artifact with tamper detection, and the REAL
   arc_agi generator's object-dtype ``task_ids`` (needs ``juniper_data`` importable);
L  the REAL ``JuniperDataClient.download_artifact_npz`` over those bytes (needs
   ``juniper_data_client``; the network is never touched).

Groups whose imports are unavailable SKIP, so the script runs anywhere numpy is installed.
Exit code = number of FAILed checks.

Usage::

    /opt/miniforge3/envs/JuniperData/bin/python -s util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py
    <any-python-with-numpy> util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py --vectors-only
    <producer-python> <this script> --write-payload SCRATCH_DIR     # then, under another numpy:
    <consumer-python> <this script> --read-payload SCRATCH_DIR/spiral.npz
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import io
import json
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import numpy as np

BLOCK_KEY = "partition_provenance"
DIGEST_SCHEME = "juniper-array-v1"
SPLITS = ("train", "val", "test")
ALLOWED_KINDS = frozenset("biufU")
FIT_SCOPES = ("none", "constant", "train", "non_train_fallback", "all_rows")
METHODS = ("shuffled_carve", "ordered_carve", "temporal_rows_per_entity", "temporal_windows", "temporal_windows_per_entity")

RESULTS: list[tuple[str, str, str]] = []
PAYLOADS: dict[str, bytes] = {}


class SkipCheck(Exception):
    """Raised inside a check whose prerequisites are unavailable in this interpreter."""


def record(status: str, check_id: str, detail: str) -> None:
    RESULTS.append((status, check_id, detail))
    print(f"{status:4s} {check_id}: {detail}")


def check(check_id: str, fn: Callable[[], str]) -> None:
    try:
        detail = fn()
    except SkipCheck as exc:
        record("SKIP", check_id, str(exc))
        return
    except Exception as exc:  # noqa: BLE001 - every failure is reported, none aborts the run
        record("FAIL", check_id, f"{type(exc).__name__}: {exc}")
        return
    status, _, text = (detail or "").partition("|") if (detail or "").startswith("INFO|") else ("PASS", "", detail or "")
    record(status, check_id, text)


# --- digest: implementation A (numpy canonicalisation) ------------------------------


def canonical_dtype(dtype: Any) -> np.dtype:
    dt = np.dtype(dtype)
    if dt.hasobject or dt.names is not None or dt.subdtype is not None or dt.kind not in ALLOWED_KINDS:
        raise ValueError(f"dtype {dt!r} is outside {DIGEST_SCHEME} (allowed kinds: b i u f U)")
    return dt.newbyteorder("<")


def digest_a(array: Any) -> str:
    arr = np.asarray(array)
    canon = canonical_dtype(arr.dtype)
    header = f"{DIGEST_SCHEME}\n{canon.str}\n{','.join(str(int(d)) for d in arr.shape)}\n".encode("ascii")
    data = np.ascontiguousarray(arr, dtype=canon).tobytes(order="C")
    return hashlib.sha256(header + data).hexdigest()


# --- digest: implementation B (struct packing, no numpy byte-order or layout API) ---

_STRUCT_CODES = {("f", 4): "f", ("f", 8): "d", ("i", 1): "b", ("i", 2): "h", ("i", 4): "i", ("i", 8): "q", ("u", 1): "B", ("u", 2): "H", ("u", 4): "I", ("u", 8): "Q", ("b", 1): "?"}


def _flatten(obj: Any):
    if isinstance(obj, list):
        for item in obj:
            yield from _flatten(item)
    else:
        yield obj


def digest_b(array: Any) -> str:
    arr = np.asarray(array)
    kind, size = arr.dtype.kind, arr.dtype.itemsize
    dtype_str = f"<U{size // 4}" if kind == "U" else (f"|{kind}1" if size == 1 else f"<{kind}{size}")
    values = list(_flatten(arr.tolist()))  # logical C order whatever the memory layout
    if kind == "U":
        data = b"".join(v.encode("utf-32-le").ljust(size, b"\x00") for v in values)
    else:
        data = struct.pack("<" + _STRUCT_CODES[(kind, size)] * len(values), *values)
    header = f"{DIGEST_SCHEME}\n{dtype_str}\n{','.join(str(d) for d in arr.shape)}\n".encode("ascii")
    return hashlib.sha256(header + data).hexdigest()


def golden_battery() -> dict[str, np.ndarray]:
    return {
        "g1_empty_f4_0x2": np.zeros((0, 2), dtype="<f4"),
        "g2_arange_f4_2x3": np.arange(6, dtype="<f4").reshape(2, 3),
        "g3_onehot_f4_3x2": np.array([[1, 0], [0, 1], [1, 0]], dtype="<f4"),
        "g4_dates_i4": np.array([20260922, 20260923], dtype="<i4"),
        "g5_mask_u1_2x3": np.ones((2, 3), dtype="|u1"),
        "g6_vocab_U4": np.array(["AAPL", "MSFT"], dtype="<U4"),
        "g7_seq_f4_2x3x1": np.linspace(0, 1, 6, dtype="<f4").reshape(2, 3, 1),
        "g8_bool": np.array([True, False, True]),
        "g9_f8_3x2": np.arange(6, dtype="<f8").reshape(3, 2) / 7.0,
    }


# --- encoding -----------------------------------------------------------------------


def canonical_json(obj: Any) -> str:
    """The JSON form generate_dataset_id already uses (juniper_data/core/dataset_id.py:57)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def encode_block(block: dict[str, Any]) -> np.ndarray:
    return np.array(canonical_json(block), dtype=np.str_)


def decode_block(raw: np.ndarray) -> dict[str, Any]:
    if raw.dtype.kind != "U" or raw.ndim != 0:
        raise ValueError(f"{BLOCK_KEY} must be a 0-d unicode array, got dtype={raw.dtype} ndim={raw.ndim}")
    return json.loads(str(raw.item()))


def save_npz(arrays: dict[str, np.ndarray], compressed: bool) -> bytes:
    buf = io.BytesIO()
    (np.savez_compressed if compressed else np.savez)(buf, **arrays)
    return buf.getvalue()


def load_like_the_client(payload: bytes) -> dict[str, np.ndarray]:
    """Mirror of juniper-data-client client.py:679-680: eager, every key, numpy's default allow_pickle."""
    with np.load(io.BytesIO(payload), allow_pickle=False) as npz_file:
        return {key: np.asarray(npz_file[key]) for key in npz_file.files}


# --- prototype producer + gate --------------------------------------------------------


def stem_and_split(key: str) -> tuple[str | None, str | None]:
    for split in SPLITS:
        suffix = f"_{split}"
        if key.endswith(suffix) and len(key) > len(suffix):
            return key[: -len(suffix)], split
    return None, None


def rederive_dataset_id(generator: str, version: str, params: dict[str, Any]) -> str:
    """The formula of juniper_data/core/dataset_id.py:46-61, without the seedless nonce."""
    digest = hashlib.sha256(canonical_json({"generator": generator, "version": version, "params": params}).encode("utf-8")).hexdigest()
    return f"{generator}-{version}-{digest[:16]}"


def build_block(*, generator: str, version: str, dataset_id: str, params: dict[str, Any], method: str, sizing_mode: str | None, fit_scope: str, fit_stems: list[str], arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    partitions: dict[str, dict[str, Any]] = {s: {"rows": int(arrays[f"X_{s}"].shape[0]), "arrays": {}} for s in SPLITS}
    unpartitioned: dict[str, str] = {}
    for key in sorted(arrays):
        if key == BLOCK_KEY:
            continue
        stem, split = stem_and_split(key)
        if split is None:
            unpartitioned[key] = digest_a(arrays[key])
        else:
            partitions[split]["arrays"][stem] = digest_a(arrays[key])
    return {
        "schema_version": 1,
        "generator": generator,
        "generator_version": version,
        "dataset_id": dataset_id,
        "params": params,
        "resolved_inputs": {},
        "seed": params.get("seed"),
        "strategy": {"method": method, "sizing_mode": sizing_mode},
        "normaliser": {"fit_scope": fit_scope, "stems": fit_stems},
        "partitions": partitions,
        "unpartitioned": unpartitioned,
        "digest": {"algorithm": "sha256", "scheme": DIGEST_SCHEME},
    }


def gate(arrays: dict[str, np.ndarray], expected_dataset_id: str | None = None) -> tuple[str, list[str]]:
    if BLOCK_KEY not in arrays:
        return "absent", []
    try:
        block = decode_block(arrays[BLOCK_KEY])
    except (ValueError, json.JSONDecodeError) as exc:
        return "refused", [f"malformed block: {exc}"]
    if block.get("schema_version") != 1:
        return "unverifiable", [f"schema_version {block.get('schema_version')!r} is not understood"]
    findings: list[str] = []
    declared_keys = {BLOCK_KEY} | set(block["unpartitioned"]) | {f"{stem}_{s}" for s in SPLITS for stem in block["partitions"][s]["arrays"]}
    for key in sorted(set(arrays) ^ declared_keys):
        findings.append(f"coverage: {key} is {'undeclared' if key in arrays else 'declared but absent'}")
    for s in SPLITS:
        part = block["partitions"][s]
        for stem, declared in part["arrays"].items():
            key = f"{stem}_{s}"
            if key not in arrays:
                continue
            if arrays[key].shape[0] != part["rows"]:
                findings.append(f"count: {key} has {arrays[key].shape[0]} rows, block declares {part['rows']}")
            if digest_a(arrays[key]) != declared:
                findings.append(f"digest: {key}")
    for key, declared in block["unpartitioned"].items():
        if key in arrays and digest_a(arrays[key]) != declared:
            findings.append(f"digest: {key}")
    if block["seed"] is not None:
        suffix = rederive_dataset_id(block["generator"], block["generator_version"], block["params"])
        if not block["dataset_id"].endswith(suffix):
            findings.append(f"identity: params/version do not hash to {block['dataset_id']} (re-derived {suffix})")
    if expected_dataset_id is not None and block["dataset_id"] != expected_dataset_id:
        findings.append(f"identity: artifact declares {block['dataset_id']}, consumer requested {expected_dataset_id}")
    strategy, params = block["strategy"], block["params"]
    if strategy["method"] not in METHODS:
        findings.append(f"legality: unknown method {strategy['method']!r}")
    if "shuffle" in params and (strategy["method"] == "shuffled_carve") != bool(params["shuffle"]):
        findings.append("legality: method contradicts params.shuffle")
    if "sizing_mode" in params and strategy["sizing_mode"] != params["sizing_mode"]:
        findings.append("legality: sizing_mode contradicts params.sizing_mode")
    fit = block["normaliser"]["fit_scope"]
    if fit not in FIT_SCOPES or fit == "all_rows" or (fit == "non_train_fallback" and block["partitions"]["train"]["rows"] != 0):
        findings.append(f"legality: fit_scope {fit!r} with train rows {block['partitions']['train']['rows']}")
    return ("refused" if findings else "verified"), findings


# --- checks ---------------------------------------------------------------------------


def sample_block() -> dict[str, Any]:
    params = {"n_spirals": 2, "noise": 0.1, "seed": 42, "val_percent": 40.0, "tiny": 1e-8, "third": 1 / 3, "flag": True, "nothing": None, "nested": [1, [2.5, "x"]], "note": "unicode survives: Δt µ"}
    return {"schema_version": 1, "generator": "spiral", "generator_version": "3.1.0", "params": params, "seed": 42}


def e0_default() -> str:
    default = inspect.signature(np.load).parameters["allow_pickle"].default
    assert default is False, f"np.load allow_pickle default is {default!r}"
    return f"numpy {np.__version__}: np.load(allow_pickle=...) defaults to False"


def e1_roundtrip() -> str:
    block = sample_block()
    raw = encode_block(block)
    assert raw.dtype.kind == "U" and raw.ndim == 0, f"encoded as {raw.dtype} ndim={raw.ndim}"
    arrays = {"X_train": np.ones((3, 2), "<f4"), "y_train": np.eye(3, 2, dtype="<f4"), BLOCK_KEY: raw}
    for compressed in (False, True):
        loaded = load_like_the_client(save_npz(arrays, compressed))
        got = loaded[BLOCK_KEY]
        assert got.dtype == raw.dtype and got.ndim == 0, f"loaded as {got.dtype} ndim={got.ndim}"
        assert decode_block(got) == block, "decoded block differs"
        assert str(got.item()) == canonical_json(block), "canonical text differs"
    return f"0-d {raw.dtype} survives savez + savez_compressed + eager allow_pickle=False load; {len(canonical_json(block))} chars"


def e2_uint8() -> str:
    text = canonical_json(sample_block())
    as_u = np.array(text, dtype=np.str_)
    as_b = np.frombuffer(text.encode("utf-8"), dtype=np.uint8)
    loaded = load_like_the_client(save_npz({"b": as_b}, compressed=True))
    assert loaded["b"].tobytes().decode("utf-8") == text
    return f"INFO|uint8 alternative also round-trips; nbytes <U={as_u.nbytes} vs uint8={as_b.nbytes} (4x, ASCII text)"


def e3_inference() -> str:
    raw = np.array("abc")
    assert raw.dtype.kind == "U", f"np.array('abc') inferred {raw.dtype}"
    return f"np.array(str) infers {raw.dtype} (fixed-width), not StringDType"


def e4_stringdtype() -> str:
    string_dtype = getattr(getattr(np, "dtypes", None), "StringDType", None)
    if string_dtype is None:
        raise SkipCheck("numpy has no StringDType")
    raw = np.array("abc", dtype=string_dtype())
    try:
        payload = save_npz({"s": raw}, compressed=False)
    except Exception as exc:  # noqa: BLE001
        return f"INFO|StringDType cannot even be saved: {type(exc).__name__}: {exc}"
    try:
        load_like_the_client(payload)
    except ValueError as exc:
        return f"INFO|StringDType saves but an allow_pickle=False load raises ValueError: {exc}"
    return "INFO|StringDType survived allow_pickle=False in this numpy"


def e5_nul() -> str:
    loaded = load_like_the_client(save_npz({"s": np.array("ab\x00")}, compressed=False))
    stripped = str(loaded["s"].item())
    escaped = json.dumps("ab\x00")
    assert stripped == "ab", f"expected trailing NUL stripped, got {stripped!r}"
    assert "\x00" not in escaped, "json.dumps emitted a raw NUL"
    return f"<U strips a trailing NUL ('ab\\x00' -> {stripped!r}); json.dumps escapes it as {escaped}, so canonical JSON never carries one"


def e6_object() -> str:
    payload = save_npz({"X_train": np.ones((2, 2), "<f4"), "task_ids": np.array(["t1", "t2"], dtype=object)}, compressed=True)
    try:
        load_like_the_client(payload)
    except ValueError as exc:
        return f"an object array saves (pickled) but an eager allow_pickle=False load raises: {exc}"
    raise AssertionError("object array loaded without pickle")


def d1_agree() -> str:
    battery = golden_battery()
    for name, arr in battery.items():
        assert digest_a(arr) == digest_b(arr), f"{name}: implementations disagree"
    nan = np.array([np.nan, 1.0], dtype="<f4")
    nan_agree = digest_a(nan) == digest_b(nan)
    return f"implementations A and B agree on all {len(battery)} golden arrays; canonical-NaN case agrees: {nan_agree}"


def d2_invariance() -> str:
    battery = golden_battery()
    variants = 0
    for name, arr in battery.items():
        expected = digest_a(arr)
        forms = [np.asfortranarray(arr)]
        if arr.dtype.kind in "fiu" and arr.dtype.itemsize > 1:
            forms.append(arr.astype(arr.dtype.newbyteorder(">")))
        for form in forms:
            assert digest_a(form) == expected, f"{name}: layout/byte-order variant changed the digest"
            assert digest_b(form) == expected, f"{name}: implementation B disagrees on a variant"
            variants += 1
        for compressed in (False, True):
            stored = {"a": forms[-1]}
            assert digest_a(load_like_the_client(save_npz(stored, compressed))["a"]) == expected, f"{name}: NPZ round trip changed the digest"
            variants += 1
    wide = np.arange(12, dtype="<f4").reshape(3, 4)
    assert digest_a(wide[:, ::2]) == digest_a(np.array(wide[:, ::2])), "non-contiguous view differs from its copy"
    return f"{variants} variants (Fortran order, big-endian, savez, savez_compressed) plus a strided view all reproduce the digest"


def d3_sensitivity() -> str:
    base = np.arange(6, dtype="<f4").reshape(2, 3)
    changed = base.copy()
    changed[1, 2] = 5.5
    pairs = {"reshape (same bytes)": base.reshape(3, 2), "reinterpret dtype (same bytes)": base.view("<i4"), "one element": changed}
    for label, other in pairs.items():
        assert digest_a(other) != digest_a(base), f"{label} did not change the digest"
    zero, negzero = np.array([0.0], "<f4"), np.array([-0.0], "<f4")
    assert digest_a(zero) != digest_a(negzero)
    return "shape, dtype and a single value each change the digest; +0.0 and -0.0 differ (byte-level, not value-level)"


def d4_vectors() -> tuple[dict[str, str], str]:
    vectors = {name: digest_a(arr) for name, arr in golden_battery().items()}
    return vectors, hashlib.sha256(canonical_json(vectors).encode("ascii")).hexdigest()


def c1_checksum() -> str:
    arrays = {"X_train": np.arange(6, dtype="<f4").reshape(3, 2), "y_train": np.eye(3, 2, dtype="<f4"), BLOCK_KEY: encode_block(sample_block())}
    ordered = {k: arrays[k] for k in sorted(arrays)}
    first, second = save_npz(ordered, False), save_npz(ordered, False)
    assert first == second, "np.savez is not byte-deterministic"
    served = save_npz(arrays, True)
    assert hashlib.sha256(first).hexdigest() != hashlib.sha256(served).hexdigest()
    rebuilt = save_npz(dict(sorted(load_like_the_client(served).items())), False)
    return f"INFO|np.savez byte-deterministic; checksum-of-savez != sha256(savez_compressed served bytes); re-serialising the loaded arrays reproduces the checksum under this numpy: {rebuilt == first}"


def j1_json_stable() -> str:
    params = {"a": 0.1, "b": 1e-8, "c": 1 / 3, "d": 2**53 + 1, "e": float("inf"), "f": -0.0, "g": None, "h": [1, (2, 3)], "i": True, "j": "Δ"}
    text = canonical_json(params)
    assert canonical_json(json.loads(text)) == text, "canonical JSON text is not stable through loads/dumps"
    return f"canonical JSON text survives loads->dumps unchanged (floats, 2**53+1, Infinity, -0.0, tuple, non-ASCII): {text}"


def _juniper_data() -> Any:
    try:
        import juniper_data.api.routes.generators as registry_module  # noqa: F401 - breaks the #316 import cycle first
        from juniper_data.core.dataset_id import generate_dataset_id
    except ImportError as exc:
        raise SkipCheck(f"juniper_data not importable: {exc}") from exc
    return registry_module, generate_dataset_id


def j2_rederive() -> str:
    registry_module, generate_dataset_id = _juniper_data()
    matched, skipped = [], []
    for name, info in registry_module.GENERATOR_REGISTRY.items():
        params_cls, gen_cls = info["params_class"], info["generator"]
        try:
            params = params_cls()
        except Exception:  # noqa: BLE001 - csv_import needs a path; the hash does not care whether it exists
            params = params_cls(file_path="rows.csv")
        binder = getattr(gen_cls, "bind_deployment_defaults", None)
        if callable(binder):
            params = binder(params)
        dumped = params.model_dump()
        if dumped.get("seed") is None:
            skipped.append(name)
            continue
        real = generate_dataset_id(name, info["version"], dumped)
        through_block = json.loads(canonical_json(dumped))
        assert rederive_dataset_id(name, info["version"], through_block) == real, f"{name}: re-derived id differs from generate_dataset_id"
        matched.append(name)
    return f"{len(matched)} generators' default params re-derive their real dataset_id after a JSON round trip; seedless (nonce, not derivable): {skipped or 'none'}"


def p1_spiral() -> str:
    _, generate_dataset_id = _juniper_data()
    from juniper_data.core.artifacts import compute_checksum
    from juniper_data.generators.spiral import VERSION, SpiralGenerator, SpiralParams

    params = SpiralParams(n_points_per_spiral=50, seed=7)
    dumped = params.model_dump()
    arrays = SpiralGenerator.generate(params)
    dataset_id = generate_dataset_id("spiral", VERSION, dumped)
    without = save_npz(dict(arrays), compressed=True)
    block = build_block(generator="spiral", version=VERSION, dataset_id=dataset_id, params=json.loads(canonical_json(dumped)), method="shuffled_carve" if params.shuffle else "ordered_carve", sizing_mode=params.sizing_mode, fit_scope="none", fit_stems=[], arrays=arrays)
    arrays[BLOCK_KEY] = encode_block(block)
    compute_checksum(arrays)  # the route's own checksum call accepts the block (datasets.py:300)
    PAYLOADS["spiral"] = save_npz(arrays, compressed=True)  # local_fs.py:211 writes savez_compressed
    loaded = load_like_the_client(PAYLOADS["spiral"])
    status, findings = gate(loaded, expected_dataset_id=dataset_id)
    assert status == "verified", f"{status}: {findings}"
    rows = {s: block["partitions"][s]["rows"] for s in SPLITS}
    return f"real spiral artifact {dataset_id} verified; rows {rows}; block {len(canonical_json(block))} chars; stored NPZ {len(without)} -> {len(PAYLOADS['spiral'])} bytes"


def p2_tamper() -> str:
    if "spiral" not in PAYLOADS:
        raise SkipCheck("P1 produced no payload")
    base = load_like_the_client(PAYLOADS["spiral"])
    outcomes = {}
    flipped = {k: v.copy() for k, v in base.items()}
    flipped["X_val"][0, 0] += 1.0
    outcomes["value flip in X_val"] = gate(flipped)
    dropped = dict(base, X_test=base["X_test"][:-1], y_test=base["y_test"][:-1])
    outcomes["row dropped from test"] = gate(dropped)
    extra = dict(base, X_extra_train=base["X_train"])
    outcomes["undeclared key"] = gate(extra)
    lied = decode_block(base[BLOCK_KEY])
    lied["params"]["noise"] = 0.5
    outcomes["block params edited"] = gate(dict(base, **{BLOCK_KEY: encode_block(lied)}))
    outcomes["wrong id requested"] = gate(base, expected_dataset_id="spiral-3.0.0-0000000000000000")
    for label, (status, findings) in outcomes.items():
        assert status == "refused" and findings, f"{label}: gate said {status}"
    return "; ".join(f"{label} -> {findings[0]}" for label, (_, findings) in outcomes.items())


def p3_arc_agi() -> str:
    _juniper_data()
    from juniper_data.generators.arc_agi import ArcAgiGenerator, ArcAgiParams

    with tempfile.TemporaryDirectory() as tmp:
        training = Path(tmp) / "training"
        training.mkdir()
        for index in range(3):
            pairs = [{"input": [[index, 1], [2, 3]], "output": [[3, 2], [1, index]]} for _ in range(3)]
            (training / f"task{index}.json").write_text(json.dumps({"train": pairs, "test": pairs[:1]}), encoding="utf-8")
        result = ArcAgiGenerator.generate(ArcAgiParams(source="local", local_path=tmp, subset="training", seed=42))
    dtype = result["task_ids"].dtype
    assert dtype == object, f"task_ids dtype is {dtype}"
    PAYLOADS["arc_agi"] = save_npz(result, compressed=True)
    try:
        load_like_the_client(PAYLOADS["arc_agi"])
    except ValueError as exc:
        return f"real ArcAgiGenerator emits task_ids dtype={dtype}; the stored artifact fails an allow_pickle=False load: {exc}"
    raise AssertionError("arc_agi artifact loaded without pickle")


def _client() -> Any:
    try:
        from juniper_data_client import JuniperDataClient
    except ImportError as exc:
        raise SkipCheck(f"juniper_data_client not importable: {exc}") from exc
    return JuniperDataClient


def _real_download(payload: bytes) -> dict[str, np.ndarray]:
    client = _client()(base_url="http://127.0.0.1:9")
    client.download_artifact_bytes = lambda dataset_id: payload  # shadow the HTTP call; the load path is the real one
    try:
        return client.download_artifact_npz("probe")
    finally:
        client.close()


def l1_client_block() -> str:
    payload = PAYLOADS.get("spiral") or save_npz({"X_train": np.ones((2, 2), "<f4"), BLOCK_KEY: encode_block(sample_block())}, compressed=True)
    arrays = _real_download(payload)
    block = decode_block(arrays[BLOCK_KEY])
    source = "real spiral" if "spiral" in PAYLOADS else "synthetic"
    return f"real download_artifact_npz returns the block ({source} payload) as {arrays[BLOCK_KEY].dtype}; schema_version={block['schema_version']}"


def l2_client_object() -> str:
    payload = PAYLOADS.get("arc_agi") or save_npz({"X_train": np.ones((2, 2), "<f4"), "task_ids": np.array(["a", "b"], dtype=object)}, compressed=True)
    source = "real arc_agi" if "arc_agi" in PAYLOADS else "synthetic"
    try:
        _real_download(payload)
    except ValueError as exc:
        return f"real download_artifact_npz raises on the {source} payload: {exc}"
    raise AssertionError("client loaded an object array")


def read_payload(path: str) -> int:
    """Load an NPZ written by ANOTHER interpreter (e.g. a numpy-2 producer) the client's way, then gate it."""
    arrays = load_like_the_client(Path(path).read_bytes())
    status, findings = gate(arrays)
    print(f"READ {path}: python {sys.version.split()[0]} numpy {np.__version__} -> gate {status}; findings={findings}")
    return 0 if status == "verified" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vectors-only", action="store_true", help="print only the golden digest vectors and their fingerprint")
    parser.add_argument("--write-payload", metavar="DIR", help="after the checks, write the produced NPZ payloads into DIR (scratch space)")
    parser.add_argument("--read-payload", metavar="FILE", help="only load FILE like the client and run the prototype gate on it")
    args = parser.parse_args()
    if args.read_payload:
        return read_payload(args.read_payload)
    vectors, fingerprint = d4_vectors()
    print(f"python {sys.version.split()[0]}  numpy {np.__version__}")
    if not args.vectors_only:
        for check_id, fn in (("E0", e0_default), ("E1", e1_roundtrip), ("E2", e2_uint8), ("E3", e3_inference), ("E4", e4_stringdtype), ("E5", e5_nul), ("E6", e6_object), ("D1", d1_agree), ("D2", d2_invariance), ("D3", d3_sensitivity), ("C1", c1_checksum), ("J1", j1_json_stable), ("J2", j2_rederive), ("P1", p1_spiral), ("P2", p2_tamper), ("P3", p3_arc_agi), ("L1", l1_client_block), ("L2", l2_client_object)):
            check(check_id, fn)
    for name, value in vectors.items():
        print(f"VECTOR {name} {value}")
    print(f"VECTOR-FINGERPRINT {fingerprint}")
    if args.write_payload:
        for name, payload in PAYLOADS.items():
            target = Path(args.write_payload) / f"{name}.npz"
            target.write_bytes(payload)
            print(f"WROTE {target} ({len(payload)} bytes)")
    failed = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    print(f"SUMMARY pass={sum(1 for s, _, _ in RESULTS if s == 'PASS')} info={sum(1 for s, _, _ in RESULTS if s == 'INFO')} skip={sum(1 for s, _, _ in RESULTS if s == 'SKIP')} fail={failed}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
