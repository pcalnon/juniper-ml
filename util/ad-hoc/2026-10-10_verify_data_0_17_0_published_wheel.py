#!/usr/bin/env python3
"""
Probe a PUBLISHED juniper-data wheel for the W1.11 contract: equities_seq at 6.0.0 / regression.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — one-off (W1.11 post-publication check of juniper-data 0.17.0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W1.11: "PyPI 0.17.0 probe shows `regression`; wheel probe re-run"), juniper-data#437 (X8),
         util/ad-hoc/2026-09-10_verify_published_wheels.py (the pattern this follows)

Why this exists
---------------
X8 (juniper-data#437) relabelled ``equities_seq`` from ``classification`` to ``regression`` and
moved it from generator 5.0.0 to 6.0.0. It merged 22 minutes after v0.16.0 was cut, so 0.17.0 is
the first release that should carry it. A checkout is not a deployment, so this reads nothing
from a git tree: it refuses to run unless ``juniper_data`` was imported from an installed,
non-editable distribution of exactly the version asked for.

The arrays are unchanged by X8; only the stored meta and the ``dataset_id`` move. So the checks
are on the three things that do move:

1. the registry entry (``task_type``, ``version``) and the version ``GET /v1/generators`` serves;
2. the meta the dataset route builds from that ``task_type`` (``compute_shape_meta``), run on a
   synthetic sequence artifact that carries a one-hot ``y`` -- with a control showing the same
   arrays DO yield class counts under ``classification``, so the regression result is not vacuous;
3. the ``dataset_id`` prefix, which hashes the generator version, so a cached 5.0.0 artifact
   cannot answer a 6.0.0 request.

Run it against a fresh venv per version. The 0.16.0 run is the control: it must FAIL on the label.

    python3 -m venv <scratch>/v017 && <scratch>/v017/bin/pip install --only-binary=:all: 'juniper-data[api]==0.17.0'
    <scratch>/v017/bin/python -I util/ad-hoc/2026-10-10_verify_data_0_17_0_published_wheel.py --expect-version 0.17.0

Exit status: 0 when every check passes, 1 on the first failed check, 2 on a provenance refusal.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import sys
from pathlib import Path

import numpy as np

EXPECTED_SEQ_VERSION = "6.0.0"
EXPECTED_SEQ_TASK_TYPE = "regression"


def check_provenance(expect_version: str) -> None:
    """Refuse unless juniper_data comes from an installed, non-editable wheel of that version."""
    import juniper_data

    dist = importlib.metadata.distribution("juniper-data")
    module_path = Path(juniper_data.__file__).resolve()
    site_dirs = [Path(p).resolve() for p in sys.path if p.endswith("site-packages")]
    direct_url = dist.read_text("direct_url.json")
    print(f"  juniper-data {dist.version} from {module_path}")
    if dist.version != expect_version:
        print(f"REFUSED: installed juniper-data is {dist.version}, not {expect_version}")
        sys.exit(2)
    if not any(site in module_path.parents for site in site_dirs):
        print(f"REFUSED: juniper_data imported from {module_path}, outside every site-packages on sys.path")
        sys.exit(2)
    if direct_url is not None:
        print(f"REFUSED: juniper-data was installed from a URL or path, not an index: {json.loads(direct_url)}")
        sys.exit(2)
    print("  OK: an index-installed wheel, not a checkout")


def check_registry() -> dict:
    from juniper_data.api.routes.generators import GENERATOR_REGISTRY
    from juniper_data.generators.equities_seq import VERSION as SEQ_MODULE_VERSION

    seq = GENERATOR_REGISTRY["equities_seq"]
    flat = GENERATOR_REGISTRY["equities"]
    print(f"  equities_seq: version={seq['version']} task_type={seq['task_type']} time_unit={seq.get('time_unit')} (module VERSION={SEQ_MODULE_VERSION})")
    print(f"  equities:     version={flat['version']} task_type={flat['task_type']}")
    assert seq["task_type"] == EXPECTED_SEQ_TASK_TYPE, f"equities_seq task_type is {seq['task_type']!r}, expected {EXPECTED_SEQ_TASK_TYPE!r} (X8, juniper-data#437)"
    assert seq["version"] == EXPECTED_SEQ_VERSION == SEQ_MODULE_VERSION, f"equities_seq version is {seq['version']!r} (module {SEQ_MODULE_VERSION!r}), expected {EXPECTED_SEQ_VERSION!r}"
    assert seq.get("time_unit") == "calendar_days", seq.get("time_unit")
    # X8 moved the sequence variant only: flat equities stays a classifier at 5.0.0.
    assert flat["task_type"] == "classification" and flat["version"] == "5.0.0", flat
    # Decision 11 set a FLOOR: no generator below 3.0.0.
    below = {name: info["version"] for name, info in GENERATOR_REGISTRY.items() if int(info["version"].split(".")[0]) < 3}
    assert not below, f"generators below the decision-11 floor 3.0.0: {below}"
    print(f"  OK: equities_seq {EXPECTED_SEQ_VERSION} / {EXPECTED_SEQ_TASK_TYPE}; equities 5.0.0 / classification; {len(GENERATOR_REGISTRY)} generators all >= 3.0.0")
    return seq


def check_served_version() -> None:
    from juniper_data.api.routes.generators import list_generators

    served = {info.name: info.version for info in asyncio.run(list_generators())}
    print(f"  GET /v1/generators serves equities_seq at {served.get('equities_seq')}")
    assert served.get("equities_seq") == EXPECTED_SEQ_VERSION, served.get("equities_seq")
    print("  OK: the listing serves the registry's version")


def check_meta_dispatch(task_type: str) -> None:
    """The route's meta for a (W, L, F) artifact with a one-hot y and a y_reg rider, as equities_seq emits."""
    from juniper_data.core.meta import compute_shape_meta

    rng = np.random.default_rng(0)

    def part(n: int) -> dict[str, np.ndarray]:
        labels = rng.integers(0, 2, size=n)
        return {"X": rng.normal(size=(n, 5, 3)).astype(np.float32), "y": np.eye(2, dtype=np.float32)[labels], "y_reg": rng.normal(size=(n, 1)).astype(np.float32)}

    arrays: dict[str, np.ndarray] = {}
    for split, n in (("train", 8), ("val", 3), ("test", 4)):
        for key, value in part(n).items():
            arrays[f"{key}_{split}"] = value

    meta = compute_shape_meta(dict(arrays), task_type)
    control = compute_shape_meta(dict(arrays), "classification")
    print(f"  meta under {task_type!r}: n_classes={meta['n_classes']} class_distribution={meta['class_distribution']} n_features={meta['n_features']}")
    print(f"  control under 'classification': n_classes={control['n_classes']} class_distribution={control['class_distribution']}")
    # The control proves the fixture WOULD be counted as two classes if mislabelled, so None is the label's doing.
    assert control["n_classes"] == 2 and sum(control["class_distribution"].values()) == 15, control
    assert meta["n_classes"] is None and meta["class_distribution"] is None, meta
    assert meta["n_features"] == 3 and meta["n_samples"] == 15, meta
    print("  OK: n_classes / class_distribution null under the served label, populated under the control")


def check_dataset_id(seq_version: str) -> None:
    from juniper_data.core.dataset_id import generate_dataset_id

    params = {"tickers": ["AAPL"], "start_date": "2023-01-03", "end_date": "2024-06-03", "seed": 42}
    current = generate_dataset_id("equities_seq", seq_version, params)
    old = generate_dataset_id("equities_seq", "5.0.0", params)
    print(f"  dataset_id {current} (the same params at 5.0.0: {old})")
    assert current.startswith(f"equities_seq-{EXPECTED_SEQ_VERSION}-"), current
    assert current != old, "the id does not move with the generator version"
    print("  OK: the id carries 6.0.0, so a cached 5.0.0 artifact cannot answer it")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--expect-version", required=True, help="the juniper-data version that must be installed (e.g. 0.17.0)")
    args = parser.parse_args()

    print("[1/5] provenance")
    check_provenance(args.expect_version)
    steps = (
        ("[2/5] registry", check_registry),
        ("[3/5] served generator version", check_served_version),
    )
    seq = None
    try:
        for title, step in steps:
            print(title)
            result = step()
            if result is not None:
                seq = result
        print("[4/5] meta dispatch")
        check_meta_dispatch(seq["task_type"])
        print("[5/5] dataset_id")
        check_dataset_id(seq["version"])
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"PASS: juniper-data {args.expect_version} serves equities_seq at {EXPECTED_SEQ_VERSION} / {EXPECTED_SEQ_TASK_TYPE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
