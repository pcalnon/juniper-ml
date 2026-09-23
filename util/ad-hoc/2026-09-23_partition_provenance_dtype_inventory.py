#!/usr/bin/env python3
"""Inventory every dtype that juniper-data's generators put into an artifact today.

Project:       Juniper
Sub-Project:   juniper-ml (ad-hoc evidence for the Decision 12 spec v2)
Application:   util/ad-hoc
Author:        Paul Calnon
Version:       0.1.0
License:       MIT License
Created:       2026-09-23
Status:        ad-hoc, single-purpose

Why
---
Review round 1 of ``notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md``
(§14 B-5) found that the ``juniper-array-v1`` digest admitted dtype KINDS (``f`` included
``longdouble``, whose padding bytes are unspecified) and proposed an exact allowlist: the
dtypes a generator emits today. This script measures that set instead of guessing it.

How
---
It reuses the offline builders of juniper-data's fleet guard,
``juniper_data/tests/unit/test_artifacts_load_without_pickle.py`` (juniper-data#430), so every
generator in ``GENERATOR_REGISTRY`` is built exactly as that test builds it: default params, or an
offline source for mnist / csv_import / arc_agi / equities / equities_seq, then the create
route's reserved-channel pops. For each generator it records every key's canonical
little-endian dtype string and rank.

Usage
-----
    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-23_partition_provenance_dtype_inventory.py \\
        --data-checkout /path/to/a/juniper-data/checkout/carrying/#430 [--json OUT.json]

Exit 0 on success; 2 if the checkout does not carry the fleet guard.

Limits
------
The two external stores (``hf_store``, ``kaggle_store``) are not built here: they need a Hub or
Kaggle source. Their dtypes are read from their code and stated separately in the spec.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-checkout", required=True, type=Path, help="a juniper-data checkout that carries tests/unit/test_artifacts_load_without_pickle.py")
    parser.add_argument("--json", type=Path, default=None, help="also write the inventory as JSON here")
    args = parser.parse_args()

    checkout = args.data_checkout.resolve()
    guard = checkout / "juniper_data" / "tests" / "unit" / "test_artifacts_load_without_pickle.py"
    if not guard.exists():
        print(f"ERROR: {guard} does not exist -- this checkout does not carry juniper-data#430's fleet guard", file=sys.stderr)
        return 2
    sys.path.insert(0, str(checkout))

    import numpy as np

    juniper_data = importlib.import_module("juniper_data")
    if not Path(juniper_data.__file__).resolve().is_relative_to(checkout):
        print(f"ERROR: imported juniper_data from {juniper_data.__file__}, not from {checkout}", file=sys.stderr)
        return 2
    fleet = importlib.import_module("juniper_data.tests.unit.test_artifacts_load_without_pickle")
    registry = importlib.import_module("juniper_data.api.routes.generators").GENERATOR_REGISTRY

    per_generator: dict[str, dict[str, dict[str, object]]] = {}
    by_dtype: dict[str, set[str]] = defaultdict(set)
    for name in sorted(registry):
        with tempfile.TemporaryDirectory() as tmp:
            arrays = fleet._build(name, Path(tmp))
        entry: dict[str, dict[str, object]] = {}
        for key in sorted(arrays):
            value = np.asarray(arrays[key])
            canon = value.dtype.newbyteorder("<") if value.dtype.byteorder not in ("|", "=") else value.dtype
            dtype_str = canon.str if value.dtype.kind != "U" else "<U{n}"
            entry[key] = {"dtype": value.dtype.str, "canonical": dtype_str, "ndim": value.ndim, "shape": list(value.shape)}
            by_dtype[dtype_str].add(f"{name}:{key}")
        per_generator[name] = entry

    print(f"numpy {np.__version__}; juniper_data from {juniper_data.__file__}")
    print(f"{len(per_generator)} generators built\n")
    print("| canonical dtype | emitted by (generator:key) |")
    print("| --- | --- |")
    for dtype_str in sorted(by_dtype):
        members = sorted(by_dtype[dtype_str])
        print(f"| `{dtype_str}` | {len(members)} keys: {', '.join(members)} |")
    print()
    for name, entry in per_generator.items():
        ranks = sorted({int(v["ndim"]) for v in entry.values()})
        zero_d = [k for k, v in entry.items() if v["ndim"] == 0]
        print(f"{name}: {len(entry)} keys, ranks {ranks}, 0-d keys {zero_d or 'none'}")

    if args.json is not None:
        args.json.write_text(json.dumps({"numpy": np.__version__, "generators": per_generator, "by_dtype": {k: sorted(v) for k, v in by_dtype.items()}}, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
