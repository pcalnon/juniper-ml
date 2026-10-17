#!/usr/bin/env python3
"""
Probe a PUBLISHED juniper-data-client wheel for the W1.4 validator: the four rules 0.6.0 adds.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-17
Status: ad-hoc — one-off (W1.13 post-publication check of juniper-data-client 0.6.0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W1.13: "PyPI/GHCR probes for all four"; W1.4: the validator gaps, findings F-P3 / F-S3),
         util/ad-hoc/2026-10-10_verify_data_0_17_0_published_wheel.py (the pattern this follows)

Why this exists
---------------
juniper-data-client 0.6.0 closes the W1.4 gaps in ``validate_npz_contract``: ``dt_*`` must be
finite, ``target_dt_*`` must be ``(W,)``, finite and non-negative, ``seq_lengths_*`` must be
``(W,)``, integer and in ``[1, L]``, and ``X_*`` / ``y_*`` / ``y_reg_*`` must be ``float32``, on
the 2-D path too. juniper-recurrence 0.6.0 and juniper-canopy 0.9.0 lock this release so that
their images validate with it. A checkout is not a deployment, so this reads nothing from a git
tree: it refuses to run unless ``juniper_data_client`` was imported from an installed,
non-editable distribution of exactly the version asked for.

1. a conforming three-partition sequence artifact passes, and so does a big-endian ``>f4`` one
   (the dtype rule compares the scalar type), so a refusal below is the rule's and not a broken
   fixture's;
2. each W1.4 rule refuses its own mutation with ``JuniperDataContractError`` (also a
   ``ValueError``), and the message names the key.

Run it against a fresh venv per version. The 0.5.0 run is the control: it must FAIL at step 2,
because 0.5.0 accepts every mutation.

    python3 -m venv <scratch>/dc060 && <scratch>/dc060/bin/pip install --only-binary=:all: 'juniper-data-client==0.6.0'
    <scratch>/dc060/bin/python -I util/ad-hoc/2026-10-17_verify_data_client_0_6_0_published_wheel.py --expect-version 0.6.0

Exit status: 0 when every check passes, 1 on the first failed check, 2 on a provenance refusal.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np

N_WINDOWS = {"train": 8, "val": 3, "test": 4}
LOOKBACK = 5
N_FEATURES = 2


def check_provenance(expect_version: str) -> None:
    """Refuse unless juniper_data_client comes from an installed, non-editable wheel of that version."""
    import juniper_data_client

    dist = importlib.metadata.distribution("juniper-data-client")
    module_path = Path(juniper_data_client.__file__).resolve()
    site_dirs = [Path(p).resolve() for p in sys.path if p.endswith("site-packages")]
    direct_url = dist.read_text("direct_url.json")
    print(f"  juniper-data-client {dist.version} (__version__ {juniper_data_client.__version__}) from {module_path}")
    if dist.version != expect_version or juniper_data_client.__version__ != expect_version:
        print(f"REFUSED: installed juniper-data-client is {dist.version} / {juniper_data_client.__version__}, not {expect_version}")
        sys.exit(2)
    if not any(site in module_path.parents for site in site_dirs):
        print(f"REFUSED: juniper_data_client imported from {module_path}, outside every site-packages on sys.path")
        sys.exit(2)
    if direct_url is not None:
        print(f"REFUSED: juniper-data-client was installed from a URL or path, not an index: {json.loads(direct_url)}")
        sys.exit(2)
    print("  OK: an index-installed wheel, not a checkout")


def conforming_sequence() -> dict[str, np.ndarray]:
    """A contract-valid three-partition 3-D artifact, shaped as equities_seq emits one."""
    rng = np.random.default_rng(0)
    arrays: dict[str, np.ndarray] = {}
    for split, n in N_WINDOWS.items():
        dt = np.zeros((n, LOOKBACK), dtype=np.float32)
        dt[:, 1:] = rng.uniform(0.5, 3.0, size=(n, LOOKBACK - 1))
        arrays[f"X_{split}"] = rng.normal(size=(n, LOOKBACK, N_FEATURES)).astype(np.float32)
        arrays[f"y_reg_{split}"] = rng.normal(size=(n,)).astype(np.float32)
        arrays[f"dt_{split}"] = dt
        arrays[f"target_dt_{split}"] = rng.uniform(1.0, 3.0, size=(n,)).astype(np.float32)
        arrays[f"seq_lengths_{split}"] = np.full((n,), LOOKBACK, dtype=np.int64)
    return arrays


def conforming_tabular() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(1)
    return {f"{stem}_{split}": rng.normal(size=(n, N_FEATURES) if stem == "X" else (n,)).astype(np.float32) for split, n in N_WINDOWS.items() for stem in ("X", "y_reg")}


def mutated(base: Callable[[], dict[str, np.ndarray]], key: str, change: Callable[[np.ndarray], np.ndarray]) -> dict[str, np.ndarray]:
    arrays = base()
    arrays[key] = change(arrays[key])
    return arrays


def _set(index: tuple, value: float) -> Callable[[np.ndarray], np.ndarray]:
    def change(array: np.ndarray) -> np.ndarray:
        out = array.copy()
        out[index] = value
        return out

    return change


# (description, artifact, the key the refusal must name, a phrase the refusal must carry)
MUTATIONS = [
    ("dt_* finite: +inf", lambda: mutated(conforming_sequence, "dt_train", _set((0, 2), np.inf)), "dt_train", "non-finite"),
    ("dt_* finite: NaN", lambda: mutated(conforming_sequence, "dt_val", _set((1, 3), np.nan)), "dt_val", "non-finite"),
    ("dt_* finite: -inf reported as non-finite, not as a negative gap", lambda: mutated(conforming_sequence, "dt_test", _set((0, 1), -np.inf)), "dt_test", "non-finite"),
    ("target_dt_* shape (W,)", lambda: mutated(conforming_sequence, "target_dt_train", lambda a: a.reshape(-1, 1)), "target_dt_train", "shape"),
    ("target_dt_* finite", lambda: mutated(conforming_sequence, "target_dt_val", _set((0,), np.inf)), "target_dt_val", "non-finite"),
    ("target_dt_* >= 0", lambda: mutated(conforming_sequence, "target_dt_test", _set((2,), -1.0)), "target_dt_test", "negative horizons"),
    ("seq_lengths_* integer", lambda: mutated(conforming_sequence, "seq_lengths_train", lambda a: a.astype(np.float32)), "seq_lengths_train", "integer dtype"),
    ("seq_lengths_* >= 1", lambda: mutated(conforming_sequence, "seq_lengths_val", _set((0,), 0)), "seq_lengths_val", "below 1"),
    ("seq_lengths_* <= L", lambda: mutated(conforming_sequence, "seq_lengths_test", _set((1,), LOOKBACK + 1)), "seq_lengths_test", "above the window length"),
    ("X_* float32", lambda: mutated(conforming_sequence, "X_train", lambda a: a.astype(np.float64)), "X_train", "float32"),
    ("y_reg_* float32", lambda: mutated(conforming_sequence, "y_reg_val", lambda a: a.astype(np.float64)), "y_reg_val", "float32"),
    ("X_* float32 on the 2-D (tabular) path too", lambda: mutated(conforming_tabular, "X_test", lambda a: a.astype(np.float64)), "X_test", "float32"),
]


def check_conforming() -> None:
    from juniper_data_client import validate_npz_contract

    kind = validate_npz_contract(conforming_sequence())
    big_endian = mutated(conforming_sequence, "X_train", lambda a: a.astype(">f4"))
    kind_be = validate_npz_contract(big_endian)
    kind_tab = validate_npz_contract(conforming_tabular())
    print(f"  conforming sequence -> {kind}; big-endian >f4 X -> {kind_be}; conforming tabular -> {kind_tab}")
    assert kind == kind_be == "sequence" and kind_tab == "tabular", (kind, kind_be, kind_tab)
    print("  OK: the fixtures conform, so each refusal below is its rule's")


def check_rules() -> None:
    from juniper_data_client import JuniperDataClientError, JuniperDataContractError, validate_npz_contract

    for description, build, key, phrase in MUTATIONS:
        try:
            validate_npz_contract(build())
        except JuniperDataContractError as exc:
            message = str(exc)
            assert isinstance(exc, ValueError) and isinstance(exc, JuniperDataClientError), type(exc).__mro__
            assert key in message and phrase in message, f"{description}: refused, but the message does not name {key!r} / {phrase!r}: {message!r}"
            print(f"  OK  {description}: {message}")
        else:
            raise AssertionError(f"{description}: ACCEPTED -- the rule is absent from this wheel")
    print(f"  OK: all {len(MUTATIONS)} W1.4 mutations refused, each naming its key")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--expect-version", required=True, help="the juniper-data-client version that must be installed (e.g. 0.6.0)")
    args = parser.parse_args()

    print("[1/3] provenance")
    check_provenance(args.expect_version)
    try:
        print("[2/3] conforming artifacts")
        check_conforming()
        print("[3/3] the W1.4 rules")
        check_rules()
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"PASS: juniper-data-client {args.expect_version} enforces the W1.4 validator rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
