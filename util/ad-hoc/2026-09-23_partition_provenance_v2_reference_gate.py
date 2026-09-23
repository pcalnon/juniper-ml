#!/usr/bin/env python3
"""Reference gate and adversarial battery for the Decision 12 spec v2 (``partition_provenance``).

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-09-23
Status:      ad-hoc -- evidence for a specification, not a library
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md (v2, §4-§9, §14);
             util/ad-hoc/2026-09-22_partition_provenance_npz_roundtrip.py (v1's evidence);
             pcalnon/juniper-data#423

Why this exists
---------------
Review round 1 of the spec found its defects in gate logic that existed only as prose, so the
v1 script's 15 PASS results (encoding, digest, tamper detection) said nothing about them. This
script implements the v2 gate as written in the spec's §4-§9 and attacks it: one or more vectors
for each round-1 finding (B-1..B-7), the v1 tamper cases, and a truthful block for a REAL artifact
of every generator in juniper-data's registry. If a v2 rule cannot be implemented as written, or
a vector gets past it, this script is where that shows.

It is a reference, deliberately independent of any juniper-data or juniper-data-client
implementation: the digest, the canonical-JSON checks and the id re-derivation are re-written
here from the spec text. Where juniper-data code exists, the script cross-checks against it
(the golden vectors of v1, the real ``generate_dataset_id`` and ``external_dataset_id``).

Groups
------
V  digest: v1's nine golden vectors still hold under v2's exact dtype allowlist; refused dtypes;
   ``|b1`` normalisation (§6)
I  identity: the reference id re-derivation equals juniper-data's real ``generate_dataset_id`` for
   seeded params, and for UNSEEDED params once the nonce is exposed (§7.2, B-3); the store prefix
   rule equals the real ``external_dataset_id`` (B-7c)
R  real artifacts: every generator in ``GENERATOR_REGISTRY``, built offline with juniper-data#430's
   fleet builders, gets a truthful block, survives an ``allow_pickle=False`` NPZ round trip, and
   verifies (§5, §8)
B  one group of vectors per round-1 finding, B-1 to B-7
T  v1's tamper cases, re-run against the v2 gate
O  the legality override (conditional on OQ-2, §8.3)

Needs ``juniper_data`` from a checkout that carries juniper-data#430 (for the R group and part of
I); groups whose imports are unavailable SKIP. Exit code = number of FAILed checks.

Usage::

    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py \\
        --data-checkout /path/to/juniper-data  [--verbose]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import io
import json
import re
import sys
import tempfile
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np

# ---------------------------------------------------------------------------------------------
# The v2 gate, as the spec writes it
# ---------------------------------------------------------------------------------------------

BLOCK_KEY = "partition_provenance"
GATE_SCHEMA_VERSION = 1
KNOWN_SCHEMES = frozenset({"juniper-array-v1"})
SPLITS = ("train", "val", "test")
DIGEST_HEX = re.compile(r"[0-9a-f]{64}")
NONCE_HEX = re.compile(r"[0-9a-f]{8}")
SEMVER = re.compile(r"\d+\.\d+\.\d+")
# From the right: <optional store prefix>-<generator>-<X.Y.Z>-<16 hex>. Generator names hold no dash.
DATASET_ID = re.compile(r"(?:(?P<prefix>.+)-)?(?P<generator>[a-z0-9_]+)-(?P<version>\d+\.\d+\.\d+)-(?P<hash>[0-9a-f]{16})")

#: §6: the exact dtypes the scheme digests, after canonicalisation to little-endian. ``<U{n}`` (n >= 1)
#: is admitted separately. Everything else -- longdouble, float16, complex, datetime, int16, bytes,
#: object, structured, sub-array -- is outside the scheme.
ALLOWED_DTYPES = frozenset({"<f4", "<f8", "<i4", "<i8", "|u1", "|b1"})

METHODS = frozenset({"shuffled_carve", "ordered_carve", "temporal_rows_per_entity", "temporal_windows", "temporal_windows_per_entity"})
CARVES = frozenset({"shuffled_carve", "ordered_carve"})
PRE_CARVE_ORDERS = frozenset({"as_produced", "seeded_shuffle"})
SIZING_MODES = frozenset({"additive", "carve"})
FIT_SCOPES = frozenset({"none", "constant", "train", "non_train_fallback", "all_rows"})

#: §8: the client-side class map. An unknown generator gets the class-independent rules only.
CLASS_OF = {
    **dict.fromkeys(("spiral", "xor", "gaussian", "circles", "moon", "checkerboard"), "synthetic_tabular"),
    **dict.fromkeys(("mnist", "csv_import", "arc_agi"), "real_carve"),
    "equities": "temporal_rows",
    **dict.fromkeys(("multi_sine", "mackey_glass", "ar_p", "irregular_sine", "delay_product"), "temporal_windows"),
    "equities_seq": "temporal_entity_windows",
    **dict.fromkeys(("huggingface", "kaggle"), "external_store"),
}

#: §7.3 / §11.3 W11: the versions at which each generator FIRST emits the block, as PLANNED.
#: The published gate ships this table EMPTY and fills it only after the producer's release has
#: shipped (W11), so it records history rather than a plan. The battery exercises both.
PLANNED_FIRST_EMITTING = {
    **dict.fromkeys(("spiral", "xor", "gaussian", "circles", "moon", "checkerboard", "mnist", "csv_import", "multi_sine", "mackey_glass", "ar_p", "irregular_sine", "delay_product"), "3.1.0"),
    "arc_agi": "4.1.0",
    "equities": "5.1.0",
    "equities_seq": "5.1.0",
    "huggingface": "3.1.0",
    "kaggle": "3.1.0",
}

#: The integrity core (§7.1): frozen across schema versions. Changing any of these needs a new
#: digest scheme, which an older gate reports as unverifiable rather than misjudging.
CORE_FIELDS = ("generator", "generator_version", "dataset_id", "params", "id_nonce", "partitions", "unpartitioned", "digest")
LEGALITY_FIELDS = ("resolved_inputs", "seed", "strategy", "normaliser")


class DigestError(ValueError):
    """An array whose dtype the scheme does not cover."""


class ProvenanceRefused(ValueError):
    """The gate refuses the artifact. ``findings`` says why."""

    def __init__(self, findings: list[str]):
        super().__init__("; ".join(findings))
        self.findings = findings


@dataclass
class Report:
    status: str  # absent | verified | integrity_only | unverifiable | accepted_with_findings
    findings: list[str] = field(default_factory=list)
    block: dict[str, Any] | None = None


def _is_int(value: Any) -> bool:
    """Strict: ``bool`` is an ``int`` subclass in Python and must not pass as one (B-6)."""
    return type(value) is int


def canonical_json(obj: Any) -> str:
    """§4.1: exactly the form ``generate_dataset_id`` hashes (``json`` defaults otherwise)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def canonical_dtype(dtype: Any) -> np.dtype:
    dt = np.dtype(dtype)
    if dt.hasobject or dt.names is not None or dt.subdtype is not None:
        raise DigestError(f"dtype {dt} is outside juniper-array-v1 (object, structured or sub-array)")
    canon = dt.newbyteorder("<")
    if canon.kind == "U":
        if canon.itemsize == 0:
            raise DigestError("dtype <U0 is outside juniper-array-v1")
        return canon
    if canon.str not in ALLOWED_DTYPES:
        raise DigestError(f"dtype {canon.str} is outside juniper-array-v1 (allowed: {sorted(ALLOWED_DTYPES)} and <U{{n}})")
    return canon


def array_digest(array: Any) -> str:
    """§6. ``|b1`` elements are hashed as 0x00 / 0x01 whatever byte holds them."""
    arr = np.asarray(array)
    canon = canonical_dtype(arr.dtype)
    header = f"juniper-array-v1\n{canon.str}\n{','.join(str(int(d)) for d in arr.shape)}\n".encode("ascii")
    if canon.kind == "b":
        data = (np.ascontiguousarray(arr).view(np.uint8) != 0).astype(np.uint8).tobytes(order="C")
    else:
        data = np.ascontiguousarray(arr, dtype=canon).tobytes(order="C")
    return hashlib.sha256(header + data).hexdigest()


def store_prefix(generator: str, params: Mapping[str, Any]) -> str | None:
    """§7.2 / B-7(c): the stores' readable prefix is a function of their HASHED params."""
    if generator == "huggingface":
        name, config = params.get("dataset_name"), params.get("config_name")
        if not isinstance(name, str):
            raise ValueError("huggingface params carry no string dataset_name")
        return f"hf-{name}" + (f"-{config}" if config else "")
    if generator == "kaggle":
        ref = params.get("dataset_ref")
        if not isinstance(ref, str):
            raise ValueError("kaggle params carry no string dataset_ref")
        return f"kaggle-{ref.replace('/', '-')}"
    return None


def rederive_dataset_id(generator: str, version: str, params: Mapping[str, Any], id_nonce: str | None) -> str:
    """§7.2: the formula of ``juniper_data/core/dataset_id.py``, with the nonce SUPPLIED rather than drawn."""
    canonical: dict[str, Any] = {"generator": generator, "version": version, "params": dict(params)}
    if id_nonce is not None:
        canonical["_nonce"] = id_nonce
    hash16 = hashlib.sha256(canonical_json(canonical).encode("utf-8")).hexdigest()[:16]
    base = f"{generator}-{version}-{hash16}"
    prefix = store_prefix(generator, params)
    return f"{prefix}-{base}" if prefix else base


def _semver(text: str) -> tuple[int, int, int]:
    major, minor, patch_ = (int(part) for part in text.split("."))
    return major, minor, patch_


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ProvenanceRefused([f"G0: duplicate JSON key {key!r}"])
        seen[key] = value
    return seen


def _g0_decode(raw: Any) -> dict[str, Any]:
    """§4.1 and §9.3 G0. Raises ProvenanceRefused on anything malformed."""
    if not isinstance(raw, np.ndarray) or raw.ndim != 0 or raw.dtype.kind != "U":
        raise ProvenanceRefused([f"G0: {BLOCK_KEY} must be a 0-d <U array, got {getattr(raw, 'dtype', type(raw))} ndim={getattr(raw, 'ndim', '?')}"])
    text = str(raw.item())
    try:
        block = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ProvenanceRefused([f"G0: not JSON: {exc}"]) from exc
    if not isinstance(block, dict):
        raise ProvenanceRefused(["G0: the block is not a JSON object"])
    if canonical_json(block) != text:
        raise ProvenanceRefused(["G0: the text is not in canonical form (it differs from its own re-serialisation)"])

    findings: list[str] = []
    schema, reader = block.get("schema_version"), block.get("min_reader_version")
    if not (_is_int(schema) and schema >= 1):
        findings.append(f"G0: schema_version must be a positive int, got {schema!r}")
    if not (_is_int(reader) and reader >= 1 and (not _is_int(schema) or reader <= schema)):
        findings.append(f"G0: min_reader_version must be a positive int no greater than schema_version, got {reader!r}")
    for name in CORE_FIELDS:
        if name not in block:
            findings.append(f"G0: required core field {name!r} is missing")
    if findings:
        raise ProvenanceRefused(findings)

    if not (isinstance(block["generator"], str) and block["generator"]):
        findings.append("G0: generator must be a non-empty string")
    if not (isinstance(block["generator_version"], str) and SEMVER.fullmatch(block["generator_version"])):
        findings.append(f"G0: generator_version must be X.Y.Z, got {block['generator_version']!r}")
    if not (isinstance(block["dataset_id"], str) and block["dataset_id"]):
        findings.append("G0: dataset_id must be a non-empty string")
    if not isinstance(block["params"], dict):
        findings.append("G0: params must be an object")
    if block["id_nonce"] is not None and not isinstance(block["id_nonce"], str):
        findings.append("G0: id_nonce must be a string or null")
    if not isinstance(block["partitions"], dict) or not isinstance(block["unpartitioned"], dict):
        findings.append("G0: partitions and unpartitioned must be objects")
    digest = block["digest"]
    if not (isinstance(digest, dict) and digest.get("algorithm") == "sha256" and isinstance(digest.get("scheme"), str)):
        findings.append(f"G0: digest must be {{'algorithm': 'sha256', 'scheme': <string>}}, got {digest!r}")

    # The legality layer's shape is v1's to judge only when this gate may read the block at all.
    if _is_int(reader) and reader <= GATE_SCHEMA_VERSION:
        for name in LEGALITY_FIELDS:
            if name not in block:
                findings.append(f"G0: required field {name!r} is missing")
        if not findings:
            if not isinstance(block["resolved_inputs"], dict):
                findings.append("G0: resolved_inputs must be an object")
            if block["seed"] is not None and not _is_int(block["seed"]):
                findings.append(f"G0: seed must be an int or null, got {block['seed']!r}")
            strategy, normaliser = block["strategy"], block["normaliser"]
            if not (isinstance(strategy, dict) and isinstance(strategy.get("method"), str) and isinstance(strategy.get("pre_carve_order"), str) and "sizing_mode" in strategy and (strategy["sizing_mode"] is None or isinstance(strategy["sizing_mode"], str))):
                findings.append(f"G0: strategy must hold string method and pre_carve_order, and a string-or-null sizing_mode, got {strategy!r}")
            if not (isinstance(normaliser, dict) and isinstance(normaliser.get("fit_scope"), str) and isinstance(normaliser.get("stems"), list) and all(isinstance(s, str) for s in normaliser["stems"])):
                findings.append(f"G0: normaliser must hold a string fit_scope and a list of string stems, got {normaliser!r}")
    if findings:
        raise ProvenanceRefused(findings)
    return block


def _integrity(block: dict[str, Any], arrays: Mapping[str, Any], requested_id: str | None) -> list[str]:
    """§9.3 G1-G4. Every check runs; none stops the others."""
    findings: list[str] = []
    partitions, unpartitioned = block["partitions"], block["unpartitioned"]

    # G1 structure and coverage.
    if set(partitions) != set(SPLITS):
        findings.append(f"G1: partitions must be exactly {list(SPLITS)}, got {sorted(partitions)}")
    declared: dict[str, tuple[str | None, str]] = {}
    for split in SPLITS:
        part = partitions.get(split)
        if not (isinstance(part, dict) and set(part) == {"rows", "arrays"} and _is_int(part.get("rows")) and part["rows"] >= 0 and isinstance(part.get("arrays"), dict)):
            findings.append(f"G1: partitions.{split} must be {{'rows': <int >= 0>, 'arrays': {{...}}}}, got {part!r}")
            continue
        for stem in ("X", "y"):
            if stem not in part["arrays"]:
                findings.append(f"G1: partitions.{split} does not declare {stem}")
        for stem, digest in part["arrays"].items():
            key = f"{stem}_{split}"
            if not (isinstance(stem, str) and stem and isinstance(digest, str) and DIGEST_HEX.fullmatch(digest)):
                findings.append(f"G1: partitions.{split}.arrays[{stem!r}] is not a stem mapped to a 64-hex digest")
                continue
            if key in declared:
                findings.append(f"G1: {key} is declared twice")
            declared[key] = (split, digest)
    for key, digest in unpartitioned.items():
        if not (isinstance(digest, str) and DIGEST_HEX.fullmatch(digest)):
            findings.append(f"G1: unpartitioned[{key!r}] is not a 64-hex digest")
            continue
        if key == BLOCK_KEY or any(key.endswith(f"_{s}") for s in SPLITS):
            findings.append(f"G1: {key} cannot be unpartitioned (it is the block, or ends in a split suffix)")
        if key in declared:
            findings.append(f"G1: {key} is declared twice")
        declared[key] = (None, digest)
    present = set(arrays) - {BLOCK_KEY}
    for key in sorted(present - set(declared)):
        findings.append(f"G1: {key} is in the artifact but not declared")
    for key in sorted(set(declared) - present):
        findings.append(f"G1: {key} is declared but absent from the artifact")

    # G2 rank and counts, G3 digests.
    for key, (split, digest) in sorted(declared.items()):
        if key not in arrays:
            continue
        value = np.asarray(arrays[key])
        if split is not None:
            if value.ndim < 1:
                findings.append(f"G2: {key} is 0-d, so it has no rows to count")
            elif value.shape[0] != partitions[split]["rows"]:
                findings.append(f"G2: {key} has {value.shape[0]} rows, the block declares {partitions[split]['rows']}")
        try:
            if array_digest(value) != digest:
                findings.append(f"G3: {key} does not match its digest")
        except DigestError as exc:
            findings.append(f"G3: {key}: {exc}")

    # G4 identity, unconditional (B-3).
    generator, version, params, nonce = block["generator"], block["generator_version"], block["params"], block["id_nonce"]
    if requested_id is not None and block["dataset_id"] != requested_id:
        findings.append(f"G4: the artifact declares {block['dataset_id']}, the consumer requested {requested_id}")
    unseeded = params.get("seed") is None
    if unseeded and not (isinstance(nonce, str) and NONCE_HEX.fullmatch(nonce)):
        findings.append(f"G4: params has no seed, so id_nonce must be 8 lowercase hex characters, got {nonce!r}")
    elif not unseeded and nonce is not None:
        findings.append(f"G4: params carries a seed, so id_nonce must be null, got {nonce!r}")
    else:
        try:
            expected = rederive_dataset_id(generator, version, params, nonce)
        except ValueError as exc:
            findings.append(f"G4: cannot re-derive the id: {exc}")
        else:
            if block["dataset_id"] != expected:
                findings.append(f"G4: params, version and nonce hash to {expected}, not to the declared {block['dataset_id']}")
    return findings


def _legality(block: dict[str, Any]) -> list[str]:
    """§8.1 and §8.2 (G5)."""
    findings: list[str] = []
    strategy, normaliser, params = block["strategy"], block["normaliser"], block["params"]
    method, pre, sizing = strategy["method"], strategy["pre_carve_order"], strategy["sizing_mode"]
    fit, stems, seed, generator = normaliser["fit_scope"], normaliser["stems"], block["seed"], block["generator"]
    train_rows = block["partitions"]["train"]["rows"]
    declared_stems = {stem for split in SPLITS for stem in block["partitions"][split]["arrays"]}
    params_seed = params.get("seed")

    # L1 enums.
    if method not in METHODS:
        findings.append(f"L1: unknown method {method!r}")
    if pre not in PRE_CARVE_ORDERS:
        findings.append(f"L1: unknown pre_carve_order {pre!r}")
    if sizing is not None and sizing not in SIZING_MODES:
        findings.append(f"L1: unknown sizing_mode {sizing!r}")
    if fit not in FIT_SCOPES:
        findings.append(f"L1: unknown fit_scope {fit!r}")
    # L2 decision 7.
    if fit == "all_rows":
        findings.append("L2: fit_scope all_rows is a decision-7 leak")
    # L3 fallback needs an empty train.
    if fit == "non_train_fallback" and train_rows != 0:
        findings.append(f"L3: fit_scope non_train_fallback with {train_rows} train rows")
    # L4 stems.
    if (fit == "none") != (stems == []):
        findings.append(f"L4: fit_scope {fit!r} with stems {stems}")
    for stem in stems:
        if stem not in declared_stems:
            findings.append(f"L4: normalised stem {stem!r} is not a declared stem")
    # L5 seed binds to params (strict int).
    if _is_int(params_seed):
        if seed != params_seed or not _is_int(seed):
            findings.append(f"L5: seed {seed!r} differs from params.seed {params_seed!r}")
    elif seed is not None:
        findings.append(f"L5: params.seed is {params_seed!r}, so seed must be null, got {seed!r}")
    # L6 the carve's own permutation follows params.shuffle.
    if "shuffle" in params and method in CARVES:
        if not isinstance(params["shuffle"], bool):
            findings.append(f"L6: params.shuffle must be a bool, got {params['shuffle']!r}")
        elif (method == "shuffled_carve") != params["shuffle"]:
            findings.append(f"L6: method {method!r} contradicts params.shuffle={params['shuffle']}")
    # L7 sizing follows params.
    if "sizing_mode" in params and sizing != params["sizing_mode"]:
        findings.append(f"L7: sizing_mode {sizing!r} contradicts params.sizing_mode {params['sizing_mode']!r}")
    # L8 a seeded reordering needs a seed.
    if pre == "seeded_shuffle" and not _is_int(seed):
        findings.append("L8: pre_carve_order seeded_shuffle without an integer seed")

    # §8.2 class rows. Each: legal methods, sizing modes, seed rule, fit scopes, and the pre-carve
    # order as a function of the id-bound params (so it is DERIVED, not trusted).
    klass = CLASS_OF.get(generator)
    if klass is None:
        return findings
    int_seed = _is_int(params_seed)
    rows: dict[str, dict[str, Any]] = {
        "synthetic_tabular": {"methods": CARVES, "sizing": {"additive", "carve"}, "seed_null_ok": True, "fits": {"none"}, "pre": "as_produced"},
        "temporal_rows": {"methods": {"temporal_rows_per_entity"}, "sizing": {None}, "seed_null_ok": True, "fits": {"none", "train", "non_train_fallback"}, "pre": "as_produced"},
        "temporal_windows": {"methods": {"temporal_windows"}, "sizing": {None}, "seed_null_ok": False, "fits": {"none"}, "pre": "as_produced"},
        "temporal_entity_windows": {"methods": {"temporal_windows_per_entity"}, "sizing": {None}, "seed_null_ok": True, "fits": {"none", "train", "non_train_fallback"}, "pre": "as_produced"},
    }
    if klass == "real_carve":
        fits = {"mnist": {"none", "constant"}, "csv_import": {"none", "train", "non_train_fallback"}, "arc_agi": {"none"}}[generator]
        if generator == "mnist":
            expected_pre = "seeded_shuffle" if int_seed else "as_produced"
        elif generator == "arc_agi":
            expected_pre = "seeded_shuffle" if int_seed and params.get("n_tasks") is not None else "as_produced"
        else:
            expected_pre = "as_produced"
        row = {"methods": CARVES, "sizing": {"carve"}, "seed_null_ok": True, "fits": fits, "pre": expected_pre}
    elif klass == "external_store":
        fits = {"huggingface": {"none", "constant", "train"}, "kaggle": {"none", "train"}}[generator]
        row = {"methods": {"ordered_carve"}, "sizing": {"carve"}, "seed_null_ok": True, "fits": fits, "pre": "seeded_shuffle" if int_seed else "as_produced"}
    else:
        row = rows[klass]
    if method not in row["methods"]:
        findings.append(f"class {klass}: method {method!r} is not legal (legal: {sorted(row['methods'])})")
    if sizing not in row["sizing"]:
        findings.append(f"class {klass}: sizing_mode {sizing!r} is not legal")
    if seed is None and not row["seed_null_ok"]:
        findings.append(f"class {klass}: a null seed is not legal")
    if fit not in row["fits"]:
        findings.append(f"class {klass}: fit_scope {fit!r} is not legal for {generator} (legal: {sorted(row['fits'])})")
    if pre != row["pre"]:
        findings.append(f"class {klass}: pre_carve_order {pre!r}, but {generator}'s params imply {row['pre']!r}")
    if klass in ("temporal_rows", "temporal_entity_windows") and params.get("end_date") is None:
        end = block["resolved_inputs"].get("end_date")
        if not (isinstance(end, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", end)):
            findings.append(f"class {klass}: a null params.end_date requires resolved_inputs.end_date (YYYY-MM-DD), got {end!r}")
    return findings


def validate_partition_provenance(arrays: Mapping[str, Any], *, dataset_id: str | None = None, allow_illegal: bool = False, first_emitting: Mapping[str, str] | None = None) -> Report:
    """§9: the gate. Returns a Report, or raises ProvenanceRefused."""
    table = {} if first_emitting is None else first_emitting
    if BLOCK_KEY not in arrays:
        if dataset_id is not None:
            match = DATASET_ID.fullmatch(dataset_id)
            if match and match["generator"] in table and _semver(match["version"]) >= _semver(table[match["generator"]]):
                raise ProvenanceRefused([f"absent: {dataset_id} is at or above {match['generator']}'s first emitting version {table[match['generator']]}, so its block was stripped or the artifact substituted"])
        return Report("absent")
    block = _g0_decode(arrays[BLOCK_KEY])
    if block["digest"]["scheme"] not in KNOWN_SCHEMES:
        return Report("unverifiable", [f"digest scheme {block['digest']['scheme']!r} is unknown to this gate"], block)
    integrity = _integrity(block, arrays, dataset_id)
    if integrity:
        raise ProvenanceRefused(integrity)
    if block["min_reader_version"] > GATE_SCHEMA_VERSION:
        return Report("integrity_only", [f"min_reader_version {block['min_reader_version']} is above this gate's {GATE_SCHEMA_VERSION}; legality not judged"], block)
    legality = _legality(block)
    if legality:
        if allow_illegal:
            return Report("accepted_with_findings", legality, block)
        raise ProvenanceRefused(legality)
    return Report("verified", [], block)


# ---------------------------------------------------------------------------------------------
# A reference producer
# ---------------------------------------------------------------------------------------------


def _stem_split(key: str) -> tuple[str, str] | None:
    for split in SPLITS:
        if key.endswith(f"_{split}") and len(key) > len(split) + 1:
            return key[: -len(split) - 1], split
    return None


def build_block(arrays: Mapping[str, Any], *, generator: str, generator_version: str, params: dict[str, Any], id_nonce: str | None, method: str, pre_carve_order: str, sizing_mode: str | None, fit_scope: str, stems: list[str], resolved_inputs: dict[str, Any] | None = None, schema_version: int = 1, min_reader_version: int = 1) -> dict[str, Any]:
    """§4.4: counts and digests come from the arrays about to be written, never from bookkeeping."""
    partitions: dict[str, dict[str, Any]] = {s: {"rows": int(np.asarray(arrays[f"X_{s}"]).shape[0]), "arrays": {}} for s in SPLITS}
    unpartitioned: dict[str, str] = {}
    for key in sorted(arrays):
        if key == BLOCK_KEY:
            continue
        parsed = _stem_split(key)
        if parsed is None:
            unpartitioned[key] = array_digest(arrays[key])
        else:
            partitions[parsed[1]]["arrays"][parsed[0]] = array_digest(arrays[key])
    seed = params.get("seed")
    return {
        "schema_version": schema_version,
        "min_reader_version": min_reader_version,
        "generator": generator,
        "generator_version": generator_version,
        "dataset_id": rederive_dataset_id(generator, generator_version, params, id_nonce),
        "params": params,
        "id_nonce": id_nonce,
        "resolved_inputs": dict(resolved_inputs or {}),
        "seed": seed if _is_int(seed) else None,
        "strategy": {"method": method, "pre_carve_order": pre_carve_order, "sizing_mode": sizing_mode},
        "normaliser": {"fit_scope": fit_scope, "stems": stems},
        "partitions": partitions,
        "unpartitioned": unpartitioned,
        "digest": {"algorithm": "sha256", "scheme": "juniper-array-v1"},
    }


def stamp(arrays: Mapping[str, Any], block: dict[str, Any]) -> dict[str, np.ndarray]:
    stamped = {key: np.asarray(value) for key, value in arrays.items() if key != BLOCK_KEY}
    stamped[BLOCK_KEY] = np.array(canonical_json(block), dtype=np.str_)
    return stamped


def stamp_text(arrays: Mapping[str, Any], text: str) -> dict[str, np.ndarray]:
    stamped = {key: np.asarray(value) for key, value in arrays.items() if key != BLOCK_KEY}
    stamped[BLOCK_KEY] = np.array(text, dtype=np.str_)
    return stamped


def npz_round_trip(arrays: Mapping[str, Any]) -> dict[str, np.ndarray]:
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **{k: np.asarray(v) for k, v in arrays.items()})
    with np.load(io.BytesIO(buffer.getvalue()), allow_pickle=False) as npz:
        return {key: npz[key] for key in npz.files}


# ---------------------------------------------------------------------------------------------
# The battery
# ---------------------------------------------------------------------------------------------

RESULTS: list[tuple[str, str, str]] = []
VERBOSE = False


class Skip(Exception):
    pass


def record(status: str, check_id: str, detail: str) -> None:
    RESULTS.append((status, check_id, detail))
    if VERBOSE or status != "PASS":
        print(f"{status:4s} {check_id}: {detail}")
    else:
        print(f"{status:4s} {check_id}")


def check(check_id: str, fn: Callable[[], str]) -> None:
    try:
        detail = fn()
    except Skip as exc:
        record("SKIP", check_id, str(exc))
        return
    except Exception as exc:  # noqa: BLE001 - every failure is reported, none aborts the run
        record("FAIL", check_id, f"{type(exc).__name__}: {exc}")
        return
    record("PASS", check_id, detail or "")


def expect_refused(arrays: Mapping[str, Any], needle: str, **kwargs: Any) -> str:
    try:
        report = validate_partition_provenance(arrays, **kwargs)
    except ProvenanceRefused as exc:
        joined = " | ".join(exc.findings)
        assert needle in joined, f"refused, but no finding mentions {needle!r}: {joined}"
        return f"refused: {joined[:160]}"
    raise AssertionError(f"expected a refusal mentioning {needle!r}, got status {report.status} {report.findings}")


def expect_status(arrays: Mapping[str, Any], status: str, **kwargs: Any) -> str:
    report = validate_partition_provenance(arrays, **kwargs)
    assert report.status == status, f"expected {status}, got {report.status} {report.findings}"
    return f"{report.status} {report.findings[:1]}"


# --- a small synthetic artifact the B-group vectors mutate -------------------------------------


def toy_arrays() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(0)
    return {
        "X_train": rng.random((6, 2)).astype("<f4"),
        "y_train": np.eye(2, dtype="<f4")[[0, 1, 0, 1, 0, 1]],
        "X_val": rng.random((2, 2)).astype("<f4"),
        "y_val": np.eye(2, dtype="<f4")[[0, 1]],
        "X_test": rng.random((2, 2)).astype("<f4"),
        "y_test": np.eye(2, dtype="<f4")[[1, 0]],
    }


def toy_params(seed: Any = 7, shuffle: bool = True) -> dict[str, Any]:
    return {"n_points_per_spiral": 5, "noise": 0.1, "seed": seed, "shuffle": shuffle, "sizing_mode": "additive", "val_percent": 33.0}


def toy_block(arrays: Mapping[str, Any] | None = None, **overrides: Any) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    arrays = dict(toy_arrays() if arrays is None else arrays)
    params = overrides.pop("params", toy_params())
    fields: dict[str, Any] = {"generator": "spiral", "generator_version": "3.1.0", "params": params, "id_nonce": None, "method": "shuffled_carve" if params.get("shuffle") else "ordered_carve", "pre_carve_order": "as_produced", "sizing_mode": params.get("sizing_mode"), "fit_scope": "none", "stems": []}
    fields.update(overrides)
    block = build_block(arrays, **fields)
    return arrays, block


def mutated(block: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    clone = copy.deepcopy(block)
    edit(clone)
    return clone


# --- V: digest ---------------------------------------------------------------------------------

V1_GOLDEN = {
    "g1_empty_f4_0x2": (lambda: np.zeros((0, 2), dtype="<f4"), "5e67ae4f1967f08822c4b382bb0d123b3c859c20cea23bb0e3e4c805a3bc753b"),
    "g2_arange_f4_2x3": (lambda: np.arange(6, dtype="<f4").reshape(2, 3), "ec7f2a61261a10346a0e9ffea3e49795d9a1735ddecd8dab83c45d951ad413a2"),
    "g3_onehot_f4_3x2": (lambda: np.array([[1, 0], [0, 1], [1, 0]], dtype="<f4"), "fa7ecca04f364d7524e7306a784b8a7d8688a3b8292c100378ee27aa98e46dd3"),
    "g4_dates_i4": (lambda: np.array([20260922, 20260923], dtype="<i4"), "f0bcbbd287116e06af3f4a304aaaf1f36bf1a0a38a4614d600f6bb6e49652996"),
    "g5_mask_u1_2x3": (lambda: np.ones((2, 3), dtype="|u1"), "9294fb7ea8071edc6e670ffb7cc19c8c70209bff73f838c45659fd5842e8fb2a"),
    "g6_vocab_U4": (lambda: np.array(["AAPL", "MSFT"], dtype="<U4"), "4c5ebf265609a4cda4da5ef090e5f29bd68005223a5ad81aa6eb5dabbfde2c76"),
    "g7_seq_f4_2x3x1": (lambda: np.linspace(0, 1, 6, dtype="<f4").reshape(2, 3, 1), "14344b84e68d18df440c751373caf89cc9e5a396bbe7c3b62650850cbcdf6783"),
    "g8_bool": (lambda: np.array([True, False, True]), "20151a47ee82d897ad53febdfc5f803d4c9093ed018af3402d7bc6c77e801d3c"),
    "g9_f8_3x2": (lambda: np.arange(6, dtype="<f8").reshape(3, 2) / 7.0, "21aaf714507457e27a6d7eb587d61e098b434a533b05c3080de270a8f5358f15"),
}
V1_FINGERPRINT = "47fba46f786387baf2c1d6e06f7d5825306cd649554413e9dd4b0df1aa6c5733"


def v1_golden_vectors_hold() -> str:
    digests = {name: array_digest(make()) for name, (make, _) in V1_GOLDEN.items()}
    wrong = {name: got for name, got in digests.items() if got != V1_GOLDEN[name][1]}
    assert not wrong, f"v2 changed these v1 golden digests: {wrong}"
    fingerprint = hashlib.sha256(canonical_json(digests).encode("ascii")).hexdigest()
    assert fingerprint == V1_FINGERPRINT, f"fingerprint {fingerprint}"
    return f"all nine unchanged; fingerprint {fingerprint[:8]}...{fingerprint[-6:]}"


def v2_refused_dtypes() -> str:
    refused = {
        "longdouble": np.array([1.0], dtype=np.longdouble),
        "float16": np.array([1.0], dtype="<f2"),
        "complex64": np.array([1 + 2j], dtype="<c8"),
        "datetime64": np.array(["2026-09-23"], dtype="datetime64[D]"),
        "int16": np.array([1], dtype="<i2"),
        "uint32": np.array([1], dtype="<u4"),
        "bytes": np.array([b"abc"], dtype="S3"),
        "object": np.array(["a"], dtype=object),
        "structured": np.zeros(1, dtype=[("a", "<f4")]),
    }
    leaked = []
    for name, value in refused.items():
        try:
            array_digest(value)
        except DigestError:
            continue
        leaked.append(name)
    assert not leaked, f"digested although outside the allowlist: {leaked}"
    allowed = [np.zeros(1, dtype=d) for d in ("<f4", "<f8", "<i4", "<i8", "|u1", "|b1", ">f4", ">i8")] + [np.array(["x"], dtype="<U1"), np.array(["xy"], dtype=">U2")]
    for value in allowed:
        array_digest(value)
    return f"{len(refused)} dtypes refused (longdouble is {np.dtype(np.longdouble).str} here); 10 allowed forms digest, big-endian included"


def v3_bool_is_hashed_by_value() -> str:
    canonical = np.array([True, False, True])
    odd = np.frombuffer(bytes([2, 0, 1]), dtype=np.bool_)
    assert bool(np.array_equal(canonical, odd)), "the two arrays are not value-equal"
    assert odd.view(np.uint8).tolist() == [2, 0, 1], "numpy normalised the byte on its own"
    assert array_digest(odd) == array_digest(canonical), "a value-equal bool array digested differently"
    return "a True stored as byte 0x02 digests like a canonical True"


# --- I: identity against juniper-data ----------------------------------------------------------


def i1_seeded_ids_match_the_real_function(jd: Any) -> str:
    registry = importlib.import_module("juniper_data.api.routes.generators").GENERATOR_REGISTRY
    real = importlib.import_module("juniper_data.core.dataset_id").generate_dataset_id
    checked = 0
    for name, info in sorted(registry.items()):
        try:
            params = info["params_class"]().model_dump()
        except Exception:  # noqa: BLE001 - a params model that needs a required field
            continue
        if params.get("seed") is None:
            continue
        params = json.loads(canonical_json(params))
        assert real(name, info["version"], params) == rederive_dataset_id(name, info["version"], params, None), name
        checked += 1
    assert checked >= 10, f"only {checked} generators checked"
    return f"{checked} generators: the reference re-derivation equals generate_dataset_id for their default seeded params"


def i2_unseeded_ids_match_once_the_nonce_is_exposed(jd: Any) -> str:
    module = importlib.import_module("juniper_data.core.dataset_id")
    fixed = uuid.UUID("0123456789abcdef0123456789abcdef")
    params = {"n_points_per_spiral": 5, "seed": None}
    with patch.object(module.uuid, "uuid4", return_value=fixed):
        real = module.generate_dataset_id("spiral", "3.1.0", params)
    reference = rederive_dataset_id("spiral", "3.1.0", params, fixed.hex[:8])
    assert real == reference, f"{real} != {reference}"
    return f"with the nonce supplied, the unseeded id re-derives exactly ({real})"


def i3_store_prefix_rule_matches_external_dataset_id(jd: Any) -> str:
    external = importlib.import_module("juniper_data.storage.external_partition")
    cases = [
        ("huggingface", {"dataset_name": "mnist", "config_name": None, "split": "train", "n_samples": 100, "seed": 3, "normalize": True}, "hf-mnist"),
        ("huggingface", {"dataset_name": "glue", "config_name": "sst2", "split": "train", "n_samples": 50, "seed": None}, "hf-glue-sst2"),
        ("kaggle", {"dataset_ref": "owner/iris-data", "file_name": "iris.csv", "n_samples": 150, "seed": 11}, "kaggle-owner-iris-data"),
        ("kaggle", {"dataset_ref": "owner/iris-data", "file_name": "iris.csv", "n_samples": 150, "seed": None}, "kaggle-owner-iris-data"),
    ]
    for generator, params, prefix in cases:
        real = external.external_dataset_id(prefix, generator, params)
        hashed = dict(params)
        if hashed.get("seed") is None:
            hashed["seed"] = "unshuffled"
        assert rederive_dataset_id(generator, external.EXTERNAL_STORE_VERSION, hashed, None) == real, (generator, params)
    return f"{len(cases)} store ids (seeded, unseeded, with and without config_name, a slash in the ref) re-derive EXACTLY from the hashed params"


# --- R: real artifacts --------------------------------------------------------------------------


def _truthful_facts(name: str, params: dict[str, Any], arrays: Mapping[str, Any]) -> dict[str, Any]:
    klass = CLASS_OF[name]
    int_seed = _is_int(params.get("seed"))
    if klass in ("synthetic_tabular", "real_carve"):
        method = "shuffled_carve" if params.get("shuffle") else "ordered_carve"
        sizing = params.get("sizing_mode")
    else:
        method = {"temporal_rows": "temporal_rows_per_entity", "temporal_windows": "temporal_windows", "temporal_entity_windows": "temporal_windows_per_entity"}[klass]
        sizing = None
    pre = "as_produced"
    if name == "mnist" and int_seed:
        pre = "seeded_shuffle"
    if name == "arc_agi" and int_seed and params.get("n_tasks") is not None:
        pre = "seeded_shuffle"
    fit, stems = "none", []
    if name == "mnist" and params.get("normalize"):
        fit, stems = "constant", ["X"]
    if name in ("csv_import", "equities", "equities_seq") and params.get("normalize_features"):
        fit, stems = ("train" if name == "equities_seq" or np.asarray(arrays["X_train"]).shape[0] > 0 else "non_train_fallback"), ["X"]
    resolved = {}
    if klass in ("temporal_rows", "temporal_entity_windows") and params.get("end_date") is None:
        raise Skip(f"{name}: the builder left end_date null; the battery does not model the wall clock")
    return {"method": method, "pre_carve_order": pre, "sizing_mode": sizing, "fit_scope": fit, "stems": stems, "resolved_inputs": resolved}


def r_real_artifacts(jd: Any, fleet: Any, registry: Mapping[str, Any]) -> Callable[[], str]:
    def run() -> str:
        verified = []
        for name in sorted(registry):
            info = registry[name]
            generator_cls = info["generator"]
            original = generator_cls.__dict__["generate"]
            captured: dict[str, Any] = {}

            def capture(params: Any, *args: Any, _original: Any = original, _captured: dict[str, Any] = captured, **kwargs: Any) -> Any:
                _captured["params"] = params
                return _original.__func__(params, *args, **kwargs)

            generator_cls.generate = staticmethod(capture)
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    arrays = fleet._build(name, Path(tmp))
            finally:
                generator_cls.generate = original
            params = json.loads(canonical_json(captured["params"].model_dump()))
            nonce = uuid.uuid4().hex[:8] if params.get("seed") is None else None
            facts = _truthful_facts(name, params, arrays)
            block = build_block(arrays, generator=name, generator_version=info["version"], params=params, id_nonce=nonce, **facts)
            loaded = npz_round_trip(stamp(arrays, block))
            report = validate_partition_provenance(loaded, dataset_id=block["dataset_id"])
            assert report.status == "verified", f"{name}: {report.status} {report.findings}"
            verified.append(f"{name}({facts['method']},{facts['pre_carve_order']},{facts['fit_scope']})")
        assert len(verified) == len(registry) >= 16, f"{len(verified)} of {len(registry)}"
        return f"{len(verified)} real artifacts verified after an allow_pickle=False round trip: " + ", ".join(verified)

    return run


# --- B: one group per round-1 finding -------------------------------------------------------------


def b1_vectors() -> list[tuple[str, Callable[[], str]]]:
    def store_train_fit_verifies() -> str:
        params = {"dataset_name": "tab", "config_name": None, "split": "train", "n_samples": 10, "seed": 5, "normalize": True, "train_ratio": 0.6, "val_ratio": 0.2, "test_ratio": 0.2}
        arrays, block = toy_block(params=params, generator="huggingface", generator_version="3.1.0", method="ordered_carve", pre_carve_order="seeded_shuffle", sizing_mode="carve", fit_scope="train", stems=["X"])
        return expect_status(stamp(arrays, block), "verified", dataset_id=block["dataset_id"])

    def store_train_fit_needs_the_seeded_order_rule() -> str:
        params = {"dataset_name": "tab", "config_name": None, "split": "train", "n_samples": 10, "seed": 5, "normalize": True}
        arrays, block = toy_block(params=params, generator="huggingface", generator_version="3.1.0", method="ordered_carve", pre_carve_order="as_produced", sizing_mode="carve", fit_scope="train", stems=["X"])
        return expect_refused(stamp(arrays, block), "pre_carve_order")

    def mnist_unshuffled_but_seeded_is_labelled_truthfully() -> str:
        params = {"dataset": "mnist", "n_samples": 10, "seed": 7, "shuffle": False, "sizing_mode": "carve", "normalize": True}
        arrays, block = toy_block(params=params, generator="mnist", generator_version="3.1.0", method="ordered_carve", pre_carve_order="seeded_shuffle", sizing_mode="carve", fit_scope="constant", stems=["X"])
        return expect_status(stamp(arrays, block), "verified")

    def mnist_seeded_declared_as_produced_is_refused() -> str:
        params = {"dataset": "mnist", "n_samples": 10, "seed": 7, "shuffle": False, "sizing_mode": "carve", "normalize": True}
        arrays, block = toy_block(params=params, generator="mnist", generator_version="3.1.0", method="ordered_carve", pre_carve_order="as_produced", sizing_mode="carve", fit_scope="constant", stems=["X"])
        return expect_refused(stamp(arrays, block), "pre_carve_order")

    def arc_agi_sampled_tasks_are_a_seeded_shuffle() -> str:
        params = {"source": "local", "n_tasks": 2, "seed": 7, "shuffle": False, "sizing_mode": "carve"}
        arrays, block = toy_block(params=params, generator="arc_agi", generator_version="4.1.0", method="ordered_carve", pre_carve_order="seeded_shuffle", sizing_mode="carve", fit_scope="none", stems=[])
        good = expect_status(stamp(arrays, block), "verified")
        params_all = dict(params, n_tasks=None)
        arrays, block = toy_block(params=params_all, generator="arc_agi", generator_version="4.1.0", method="ordered_carve", pre_carve_order="seeded_shuffle", sizing_mode="carve", fit_scope="none", stems=[])
        bad = expect_refused(stamp(arrays, block), "pre_carve_order")
        return f"n_tasks+seed: {good}; all tasks: {bad}"

    def all_rows_is_refused() -> str:
        params = {"dataset_ref": "o/r", "file_name": "f.csv", "n_samples": 10, "seed": None, "normalize_features": True}
        hashed = dict(params, seed="unshuffled")
        arrays, block = toy_block(params=hashed, generator="kaggle", generator_version="3.1.0", method="ordered_carve", pre_carve_order="as_produced", sizing_mode="carve", fit_scope="all_rows", stems=["X"])
        return expect_refused(stamp(arrays, block), "L2")

    def windowed_train_fit_with_zero_train_windows_is_legal() -> str:
        """equities_seq fits on train FRAME rows but counts WINDOWS, so a train fit can coexist with 0 train windows.

        This pins a rule the spec deliberately does NOT have ("fit_scope train implies train rows > 0").
        """
        arrays = dict(toy_arrays())
        arrays["X_train"] = np.zeros((0, 2), dtype="<f4")
        arrays["y_train"] = np.zeros((0, 2), dtype="<f4")
        params = {"symbols": ["AAPL"], "start_date": "2008-01-01", "end_date": "2011-01-01", "seed": 42, "normalize_features": True, "lookback": 5}
        _, block = toy_block(arrays, params=params, generator="equities_seq", generator_version="5.1.0", method="temporal_windows_per_entity", pre_carve_order="as_produced", sizing_mode=None, fit_scope="train", stems=["X"])
        return expect_status(stamp(arrays, block), "verified")

    return [
        ("B1.a store fit_scope train verifies", store_train_fit_verifies),
        ("B1.b store pre-carve order is derived from the seed", store_train_fit_needs_the_seeded_order_rule),
        ("B1.c mnist shuffle=False seed=7 is ordered_carve + seeded_shuffle", mnist_unshuffled_but_seeded_is_labelled_truthfully),
        ("B1.d mnist seeded but declared as_produced is refused", mnist_seeded_declared_as_produced_is_refused),
        ("B1.e arc_agi seeded shuffle only with n_tasks", arc_agi_sampled_tasks_are_a_seeded_shuffle),
        ("B1.f all_rows is refused (L2)", all_rows_is_refused),
        ("B1.g a windowed train fit with 0 train windows is legal", windowed_train_fit_with_zero_train_windows_is_legal),
    ]


def b2_vectors() -> list[tuple[str, Callable[[], str]]]:
    arrays, block = toy_block()

    def string_version_is_malformed() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(schema_version="1"))), "schema_version")

    def bool_version_is_malformed() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(schema_version=True))), "schema_version")

    def newer_schema_readable_by_v1_verifies() -> str:
        return expect_status(stamp(arrays, mutated(block, lambda b: b.update(schema_version=2, new_field={"x": 1}))), "verified")

    def newer_schema_not_readable_by_v1_is_integrity_only() -> str:
        return expect_status(stamp(arrays, mutated(block, lambda b: b.update(schema_version=2, min_reader_version=2, strategy={"shape": "changed"}))), "integrity_only")

    def newer_schema_cannot_hide_a_corruption() -> str:
        corrupt = dict(arrays, X_val=np.asarray(arrays["X_val"]) + np.float32(1))
        return expect_refused(stamp(corrupt, mutated(block, lambda b: b.update(schema_version=9, min_reader_version=9))), "G3")

    def unknown_scheme_is_unverifiable() -> str:
        return expect_status(stamp(arrays, mutated(block, lambda b: b["digest"].update(scheme="juniper-array-v9"))), "unverifiable")

    def reader_above_schema_is_malformed() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(schema_version=2, min_reader_version=3))), "min_reader_version")

    def unknown_enum_at_a_readable_version_is_illegal() -> str:
        illegal = expect_refused(stamp(arrays, mutated(block, lambda b: b["strategy"].update(method="stratified_carve"))), "L1")
        deferred = expect_status(stamp(arrays, mutated(block, lambda b: (b["strategy"].update(method="stratified_carve"), b.update(schema_version=2, min_reader_version=2)))), "integrity_only")
        return f"min_reader 1: {illegal}; min_reader 2: {deferred}"

    return [
        ("B2.a schema_version '1' is malformed", string_version_is_malformed),
        ("B2.b schema_version true is malformed", bool_version_is_malformed),
        ("B2.c schema 2 / min_reader 1 verifies, unknown field ignored", newer_schema_readable_by_v1_verifies),
        ("B2.d schema 2 / min_reader 2 is integrity_only", newer_schema_not_readable_by_v1_is_integrity_only),
        ("B2.e a newer schema cannot hide a corrupted array", newer_schema_cannot_hide_a_corruption),
        ("B2.f an unknown digest scheme is unverifiable", unknown_scheme_is_unverifiable),
        ("B2.g min_reader_version above schema_version is malformed", reader_above_schema_is_malformed),
        ("B2.h an unknown enum is illegal when readable, deferred when not", unknown_enum_at_a_readable_version_is_illegal),
    ]


def b3_vectors() -> list[tuple[str, Callable[[], str]]]:
    unseeded = toy_params(seed=None)
    arrays, block = toy_block(params=unseeded, id_nonce="0a1b2c3d")

    def unseeded_artifact_is_bound() -> str:
        return expect_status(stamp(arrays, block), "verified", dataset_id=block["dataset_id"])

    def unseeded_params_edit_is_caught() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b["params"].update(noise=0.5))), "G4")

    def unseeded_without_a_nonce_is_refused() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(id_nonce=None))), "id_nonce")

    def seeded_with_a_nonce_is_refused() -> str:
        seeded_arrays, seeded = toy_block()
        return expect_refused(stamp(seeded_arrays, mutated(seeded, lambda b: b.update(id_nonce="0a1b2c3d"))), "id_nonce")

    def malformed_nonce_is_refused() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(id_nonce="XYZ"))), "id_nonce")

    return [("B3.a an unseeded artifact is id-bound through id_nonce", unseeded_artifact_is_bound), ("B3.b an edited unseeded params is caught", unseeded_params_edit_is_caught), ("B3.c unseeded without a nonce is refused", unseeded_without_a_nonce_is_refused), ("B3.d seeded with a nonce is refused", seeded_with_a_nonce_is_refused), ("B3.e a malformed nonce is refused", malformed_nonce_is_refused)]


def b4_vectors() -> list[tuple[str, Callable[[], str]]]:
    bare = toy_arrays()
    table = PLANNED_FIRST_EMITTING

    def stripped_block_is_refused() -> str:
        return expect_refused(bare, "stripped", dataset_id="spiral-3.1.0-0123456789abcdef", first_emitting=table)

    def legacy_id_is_absent() -> str:
        return expect_status(bare, "absent", dataset_id="spiral-3.0.0-0123456789abcdef", first_emitting=table)

    def no_requested_id_is_absent() -> str:
        return expect_status(bare, "absent", first_emitting=table)

    def unknown_generator_is_absent() -> str:
        return expect_status(bare, "absent", dataset_id="newgen-9.0.0-0123456789abcdef", first_emitting=table)

    def store_id_is_parsed_from_the_right() -> str:
        return expect_refused(bare, "stripped", dataset_id="hf-glue-sst2-huggingface-3.1.0-0123456789abcdef", first_emitting=table)

    def arc_agi_4_0_0_is_absent_not_refused() -> str:
        return expect_status(bare, "absent", dataset_id="arc_agi-4.0.0-0123456789abcdef", first_emitting=table)

    def empty_table_never_refuses() -> str:
        return expect_status(bare, "absent", dataset_id="spiral-9.9.9-0123456789abcdef")

    return [
        ("B4.a absent at/above the first emitting version is refused", stripped_block_is_refused),
        ("B4.b absent below it is tolerated", legacy_id_is_absent),
        ("B4.c absent with no requested id is tolerated", no_requested_id_is_absent),
        ("B4.d absent for an unknown generator is tolerated", unknown_generator_is_absent),
        ("B4.e a store id is parsed from the right", store_id_is_parsed_from_the_right),
        ("B4.f arc_agi 4.0.0 (W0) is below its first emitting 4.1.0", arc_agi_4_0_0_is_absent_not_refused),
        ("B4.g the table ships empty: no refusal before W11", empty_table_never_refuses),
    ]


def b5_vectors() -> list[tuple[str, Callable[[], str]]]:
    def longdouble_declared_is_refused() -> str:
        arrays = dict(toy_arrays(), extra=np.zeros(3, dtype="<f4"))
        _, block = toy_block(arrays)
        swapped = dict(arrays, extra=np.zeros(3, dtype=np.longdouble))
        return expect_refused(stamp(swapped, block), "G3")

    return [("B5.a a longdouble array is refused, not digested", longdouble_declared_is_refused)]


def b6_vectors() -> list[tuple[str, Callable[[], str]]]:
    arrays, block = toy_block()
    text = canonical_json(block)

    def duplicate_key_is_refused() -> str:
        doubled = text[:-1] + ',"seed":8}'
        return expect_refused(stamp_text(arrays, doubled), "duplicate")

    def non_canonical_text_is_refused() -> str:
        return expect_refused(stamp_text(arrays, json.dumps(block, sort_keys=True)), "canonical")

    def bool_seed_is_refused() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(seed=True))), "seed")

    def float_rows_are_refused() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b["partitions"]["test"].update(rows=2.0))), "G1")

    def bool_params_seed_does_not_pass_l5() -> str:
        params = toy_params(seed=True)
        bool_arrays, bool_block = toy_block(params=params)
        return expect_refused(stamp(bool_arrays, mutated(bool_block, lambda b: b.update(seed=1))), "L5")

    return [("B6.a a duplicate key is refused", duplicate_key_is_refused), ("B6.b non-canonical whitespace is refused", non_canonical_text_is_refused), ("B6.c seed true is refused", bool_seed_is_refused), ("B6.d rows 2.0 is refused", float_rows_are_refused), ("B6.e params.seed true does not bind seed 1", bool_params_seed_does_not_pass_l5)]


def b7_vectors() -> list[tuple[str, Callable[[], str]]]:
    def zero_d_train_is_a_finding_not_a_crash() -> str:
        arrays, block = toy_block()
        broken = dict(arrays, X_train=np.float32(1.0))
        return expect_refused(stamp(broken, block), "0-d")

    def a_derived_key_trips_coverage() -> str:
        arrays, block = toy_block()
        derived = dict(stamp(arrays, block), X_full=np.concatenate([arrays["X_train"], arrays["X_val"], arrays["X_test"]]))
        return expect_refused(derived, "X_full")

    def a_wrong_store_prefix_is_refused() -> str:
        params = {"dataset_name": "tab", "config_name": None, "n_samples": 10, "seed": 5, "normalize": False}
        arrays, block = toy_block(params=params, generator="huggingface", generator_version="3.1.0", method="ordered_carve", pre_carve_order="seeded_shuffle", sizing_mode="carve", fit_scope="none", stems=[])
        wrong = mutated(block, lambda b: b.update(dataset_id="hf-other-" + b["dataset_id"].split("-", 2)[2]))
        return expect_refused(stamp(arrays, wrong), "G4")

    def a_generator_id_with_a_prefix_is_refused() -> str:
        arrays, block = toy_block()
        return expect_refused(stamp(arrays, mutated(block, lambda b: b.update(dataset_id="evil-" + b["dataset_id"]))), "G4")

    return [("B7.a a 0-d X_train is a finding, not a crash", zero_d_train_is_a_finding_not_a_crash), ("B7.b a key added after loading trips G1", a_derived_key_trips_coverage), ("B7.c a store id with the wrong prefix is refused", a_wrong_store_prefix_is_refused), ("B7.c' a generator id with any prefix is refused", a_generator_id_with_a_prefix_is_refused)]


def t_vectors() -> list[tuple[str, Callable[[], str]]]:
    arrays, block = toy_block()
    stamped = stamp(arrays, block)

    def flipped_value() -> str:
        return expect_refused(dict(stamped, X_val=np.asarray(arrays["X_val"]) * np.float32(-1)), "G3")

    def dropped_row() -> str:
        return expect_refused(dict(stamped, X_test=np.asarray(arrays["X_test"])[:1]), "G2")

    def extra_key() -> str:
        return expect_refused(dict(stamped, sneaky=np.zeros(1, "<f4")), "G1")

    def edited_params() -> str:
        return expect_refused(stamp(arrays, mutated(block, lambda b: b["params"].update(noise=0.9))), "G4")

    def wrong_requested_id() -> str:
        return expect_refused(stamped, "requested", dataset_id="spiral-3.1.0-ffffffffffffffff")

    def the_untampered_artifact_verifies() -> str:
        return expect_status(npz_round_trip(stamped), "verified", dataset_id=block["dataset_id"])

    return [("T0 the untampered artifact verifies after a round trip", the_untampered_artifact_verifies), ("T1 a flipped value", flipped_value), ("T2 a dropped row", dropped_row), ("T3 an extra key", extra_key), ("T4 an edited params value", edited_params), ("T5 a wrong requested id", wrong_requested_id)]


def o_vectors() -> list[tuple[str, Callable[[], str]]]:
    arrays, block = toy_block()

    def illegal_with_override_is_accepted_with_findings() -> str:
        return expect_status(stamp(arrays, mutated(block, lambda b: b["normaliser"].update(fit_scope="all_rows", stems=["X"]))), "accepted_with_findings", allow_illegal=True)

    def integrity_is_never_overridable() -> str:
        corrupt = dict(arrays, X_val=np.asarray(arrays["X_val"]) + np.float32(1))
        return expect_refused(stamp(corrupt, block), "G3", allow_illegal=True)

    return [("O1 an illegal block with allow_illegal is accepted_with_findings", illegal_with_override_is_accepted_with_findings), ("O2 an integrity failure ignores allow_illegal", integrity_is_never_overridable)]


def main() -> int:
    global VERBOSE
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-checkout", type=Path, default=None, help="a juniper-data checkout carrying juniper-data#430 (enables groups I and R)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    VERBOSE = args.verbose

    print(f"python {sys.version.split()[0]}, numpy {np.__version__}")
    check("V1 v1's golden vectors hold under the v2 allowlist", v1_golden_vectors_hold)
    check("V2 dtypes outside the allowlist are refused", v2_refused_dtypes)
    check("V3 |b1 is hashed by value", v3_bool_is_hashed_by_value)

    jd = fleet = registry = None
    if args.data_checkout is not None:
        sys.path.insert(0, str(args.data_checkout.resolve()))
        try:
            jd = importlib.import_module("juniper_data")
            if not Path(jd.__file__).resolve().is_relative_to(args.data_checkout.resolve()):
                raise ImportError(f"juniper_data imported from {jd.__file__}, not from the checkout")
            registry = importlib.import_module("juniper_data.api.routes.generators").GENERATOR_REGISTRY
            fleet = importlib.import_module("juniper_data.tests.unit.test_artifacts_load_without_pickle")
        except ImportError as exc:
            print(f"SKIP groups I and R: {exc}")
            jd = None
    for check_id, fn in (("I1 seeded ids equal generate_dataset_id", i1_seeded_ids_match_the_real_function), ("I2 unseeded ids re-derive once the nonce is exposed", i2_unseeded_ids_match_once_the_nonce_is_exposed), ("I3 the store prefix rule equals external_dataset_id", i3_store_prefix_rule_matches_external_dataset_id)):
        if jd is None:
            record("SKIP", check_id, "juniper_data unavailable")
        else:
            check(check_id, lambda fn=fn: fn(jd))
    if jd is None or fleet is None:
        record("SKIP", "R1 every generator's real artifact verifies", "juniper_data or the #430 fleet builders unavailable")
    else:
        check("R1 every generator's real artifact verifies", r_real_artifacts(jd, fleet, registry))

    for group in (b1_vectors, b2_vectors, b3_vectors, b4_vectors, b5_vectors, b6_vectors, b7_vectors, t_vectors, o_vectors):
        for check_id, fn in group():
            check(check_id, fn)

    counts = {status: sum(1 for s, _, _ in RESULTS if s == status) for status in ("PASS", "FAIL", "SKIP")}
    print(f"\n{counts['PASS']} PASS, {counts['FAIL']} FAIL, {counts['SKIP']} SKIP")
    return counts["FAIL"]


if __name__ == "__main__":
    raise SystemExit(main())
