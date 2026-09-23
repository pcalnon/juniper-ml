#!/usr/bin/env python3
"""Re-check every file:line citation in the Decision 12 spec v2 at the SHAs it is pinned to.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-09-23
Status:      ad-hoc -- evidence for a specification
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md (its header lists the pins)

Why
---
A line number is not a durable citation, and a blanket "every file:line was re-probed" claim turns
one stale anchor into a falsified header. So each citation in the spec gets a (repo, path, lines,
token) row here: the token must appear inside the cited lines AT THE PINNED SHA. A second pass
scans the spec text for every ``name.ext:NN`` citation and fails if one has no row, so the table
cannot silently cover less than the document.

Usage
-----
    python3 util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py            # verify
    python3 util/ad-hoc/2026-09-23_partition_provenance_v2_citation_check.py --dump     # print the cited lines

Reads blobs with ``git show <sha>:<path>`` from the checkouts under ECOSYSTEM (below), so each pinned
SHA must be present in that checkout's object store (a ``git fetch`` is enough). Exit code = number
of failures.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - read-only git show against local checkouts
from pathlib import Path

ECOSYSTEM = Path("/home/pcalnon/Development/python/Juniper")
HERE = Path(__file__).resolve().parents[2]
SPEC = HERE / "notes" / "JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md"

#: repo key -> (checkout directory, pinned sha). Must match the spec's "Grounded at" list.
PINS = {
    "data": (ECOSYSTEM / "juniper-data", "90ad035e4aa7dde5303899b43038cc8835ec88aa"),
    "client": (ECOSYSTEM / "juniper-data-client", "9bc8870a18"),
    "cascor": (ECOSYSTEM / "juniper-cascor", "f7a6d57347"),
    "canopy": (ECOSYSTEM / "juniper-canopy", "894a2cc789"),
    "recurrence": (ECOSYSTEM / "juniper-recurrence", "9b24025358"),
    "ml": (HERE, "c2bcb96c"),
}

D = "juniper_data"
G = f"{D}/generators"
S = f"{D}/storage"
C = "juniper_data_client"

# (spec citation as written, repo, full path, first line, last line, token that must appear in those lines)
ROWS: list[tuple[str, str, str, int, int, str]] = [
    # juniper-data: route, core, storage
    ("juniper_data/storage/local_fs.py:261", "data", f"{S}/local_fs.py", 261, 261, "DatasetMeta(**meta_dict)"),
    ("storage/local_fs.py:211", "data", f"{S}/local_fs.py", 211, 211, "np.savez_compressed"),
    ("juniper_data/api/routes/datasets.py:146-154", "data", f"{D}/api/routes/datasets.py", 146, 154, "generate_dataset_id("),
    ("datasets.py:146-154", "data", f"{D}/api/routes/datasets.py", 146, 154, "bind_deployment_defaults"),
    ("datasets.py:150-154", "data", f"{D}/api/routes/datasets.py", 150, 154, "params=params.model_dump()"),
    ("datasets.py:150", "data", f"{D}/api/routes/datasets.py", 150, 150, "dataset_id = generate_dataset_id("),
    ("datasets.py:287-298", "data", f"{D}/api/routes/datasets.py", 287, 298, "pop_scaling_meta"),
    ("datasets.py:298", "data", f"{D}/api/routes/datasets.py", 298, 298, "pop_data_quality_meta"),
    (":300 (after datasets.py)", "data", f"{D}/api/routes/datasets.py", 300, 300, "compute_checksum(arrays)"),
    (":355 (after datasets.py)", "data", f"{D}/api/routes/datasets.py", 355, 355, "store.save_versioned"),
    ("api/routes/generators.py:45", "data", f"{D}/api/routes/generators.py", 45, 45, "GENERATOR_REGISTRY"),
    ("core/split.py:43", "data", f"{D}/core/split.py", 43, 43, "permutation"),
    (":211 (after core/split.py)", "data", f"{D}/core/split.py", 211, 211, "def split_three_way"),
    ("core/split.py:584", "data", f"{D}/core/split.py", 584, 584, "def partition_and_assemble"),
    ("core/split.py:200-201", "data", f"{D}/core/split.py", 200, 201, "val_percent"),
    (":489-490 (after core/split.py)", "data", f"{D}/core/split.py", 489, 490, "1.0"),
    (":343 (after core/split.py)", "data", f"{D}/core/split.py", 343, 343, "def temporal_split_indices"),
    (":504-510 (after core/split.py)", "data", f"{D}/core/split.py", 504, 510, "n_test"),
    ("core/partition_params.py:81", "data", f"{D}/core/partition_params.py", 81, 81, "sizing_mode"),
    ("core/partition_params.py:110-111", "data", f"{D}/core/partition_params.py", 110, 111, "not available for this generator"),
    ("partition_params.py:110-111", "data", f"{D}/core/partition_params.py", 110, 111, "not available for this generator"),
    ("core/constants.py:92", "data", f"{D}/core/constants.py", 92, 92, "DEFAULT_GENERATOR_SEED"),
    ("core/artifacts.py:44-45", "data", f"{D}/core/artifacts.py", 44, 45, "sorted(arrays.keys())"),
    (":62-63 (after core/artifacts.py)", "data", f"{D}/core/artifacts.py", 62, 63, "arrays_to_bytes(arrays)"),
    ("core/dataset_id.py:57", "data", f"{D}/core/dataset_id.py", 57, 57, 'separators=(",", ":")'),
    ("core/dataset_id.py:54-55", "data", f"{D}/core/dataset_id.py", 54, 55, 'canonical_data["_nonce"]'),
    ("core/dataset_id.py:46-61", "data", f"{D}/core/dataset_id.py", 46, 61, "hash_digest[:DATASET_ID_HASH_PREFIX_LENGTH]"),
    ("core/dataset_id.py:47-57", "data", f"{D}/core/dataset_id.py", 47, 57, "canonical_data"),
    ("core/meta.py:80-86", "data", f"{D}/core/meta.py", 80, 86, "X_train"),
    (":164 (after core/meta.py)", "data", f"{D}/core/meta.py", 164, 164, "X_"),
    ("core/meta.py:172-229", "data", f"{D}/core/meta.py", 172, 229, "def pop_data_quality_meta"),
    ("core/meta.py:172", "data", f"{D}/core/meta.py", 172, 172, "def pop_scaling_meta"),
    ("external_partition.py:30", "data", f"{S}/external_partition.py", 30, 30, 'EXTERNAL_STORE_VERSION: str = "3.0.0"'),
    ("external_partition.py:45", "data", f"{S}/external_partition.py", 45, 45, "def validate_carve_ratios"),
    ("external_partition.py:66", "data", f"{S}/external_partition.py", 66, 66, "def carve_three_way"),
    ("external_partition.py:139", "data", f"{S}/external_partition.py", 139, 139, "_UNSHUFFLED_SEED_MARKER"),
    ("external_partition.py:140", "data", f"{S}/external_partition.py", 140, 140, 'return f"{prefix}-{generate_dataset_id('),
    ("hf_store.py:133", "data", f"{S}/hf_store.py", 133, 133, "ds = ds.shuffle(seed=seed)"),
    ("hf_store.py:157", "data", f"{S}/hf_store.py", 157, 157, "scale = float(x_train.max())"),
    ("hf_store.py:162", "data", f"{S}/hf_store.py", 162, 162, "params = {"),
    ("hf_store.py:176-178", "data", f"{S}/hf_store.py", 176, 178, 'config_suffix = f"-{config_name}"'),
    ("hf_store.py:199", "data", f"{S}/hf_store.py", 199, 199, "self._cache_store.save(dataset_id, meta, arrays)"),
    ("hf_store.py:282", "data", f"{S}/hf_store.py", 282, 282, "/ 255.0"),
    ("kaggle_store.py:195-199", "data", f"{S}/kaggle_store.py", 195, 199, "random.shuffle(data)"),
    ("kaggle_store.py:199", "data", f"{S}/kaggle_store.py", 199, 199, "random.shuffle(data)"),
    ("kaggle_store.py:245", "data", f"{S}/kaggle_store.py", 245, 245, 'arrays["X_train"].shape[0] > 0'),
    ("kaggle_store.py:256", "data", f"{S}/kaggle_store.py", 256, 256, "params = {"),
    ("kaggle_store.py:270", "data", f"{S}/kaggle_store.py", 270, 270, "dataset_ref.replace('/', '-')"),
    ("kaggle_store.py:288", "data", f"{S}/kaggle_store.py", 288, 288, "self._cache_store.save(dataset_id, meta, arrays)"),
    ("storage/cached.py:145", "data", f"{S}/cached.py", 145, 145, "np.load(io.BytesIO(artifact))"),
    ("storage/cached.py:150", "data", f"{S}/cached.py", 150, 150, "Failed to populate the cache"),
    # juniper-data: generators
    ("spiral/generator.py:45-52", "data", f"{G}/spiral/generator.py", 45, 52, "partition_and_assemble"),
    ("mnist/generator.py:94-96", "data", f"{G}/mnist/generator.py", 94, 96, "partition_and_assemble"),
    ("mnist/generator.py:115-116", "data", f"{G}/mnist/generator.py", 115, 116, "ds = ds.shuffle(seed=params.seed)"),
    ("mnist/generator.py:124", "data", f"{G}/mnist/generator.py", 124, 124, "/ 255.0"),
    ("csv_import/generator.py:63-64", "data", f"{G}/csv_import/generator.py", 63, 64, "partition_and_assemble"),
    ("csv_import/generator.py:95", "data", f"{G}/csv_import/generator.py", 95, 95, "fit_source = X_train if X_train.shape[0]"),
    ("arc_agi/generator.py:25", "data", f"{G}/arc_agi/generator.py", 25, 25, 'VERSION = "4.0.0"'),
    ("arc_agi/generator.py:106-124", "data", f"{G}/arc_agi/generator.py", 106, 124, 'extras={"task_ids": task_ids}'),
    ("arc_agi/generator.py:183-189", "data", f"{G}/arc_agi/generator.py", 183, 189, "rng.choice("),
    (":215-221 (after arc_agi/generator.py)", "data", f"{G}/arc_agi/generator.py", 215, 221, "rng.choice("),
    ("arc_agi/generator.py:237-257", "data", f"{G}/arc_agi/generator.py", 237, 257, 'task.get("train", [])'),
    ("arc_agi/generator.py:272", "data", f"{G}/arc_agi/generator.py", 272, 272, "ids = np.array([], dtype=np.str_)"),
    (":285 (after arc_agi/generator.py)", "data", f"{G}/arc_agi/generator.py", 285, 285, "dtype=np.str_)"),
    ("arc_agi/params.py:46", "data", f"{G}/arc_agi/params.py", 46, 46, "n_tasks: int | None"),
    ("equities/generator.py:315", "data", f"{G}/equities/generator.py", 315, 315, 'datetime.now(UTC).strftime("%Y-%m-%d")'),
    ("equities/generator.py:346-372", "data", f"{G}/equities/generator.py", 346, 372, "int(round(n_rows * params.train_ratio))"),
    (":395 (after equities/generator.py)", "data", f"{G}/equities/generator.py", 395, 395, "fit_frame = train if len(train) > 0 else full"),
    ("equities/generator.py:414", "data", f"{G}/equities/generator.py", 414, 414, 'arrays["ticker_vocab"] = np.array(vocab, dtype=np.str_)'),
    ("equities/params.py:47", "data", f"{G}/equities/params.py", 47, 47, "class EquitiesParams(BaseModel)"),
    ("equities/params.py:137", "data", f"{G}/equities/params.py", 137, 137, "Unused for the temporal split"),
    ("equities_seq/generator.py:194-206", "data", f"{G}/equities_seq/generator.py", 194, 206, "fit_frames = train_frames if train_frames else"),
    ("equities_seq/generator.py:224-234", "data", f"{G}/equities_seq/generator.py", 224, 234, "temporal_split_indices(n_rows, params.train_ratio, params.val_ratio)"),
    ("_sequence.py:71", "data", f"{G}/_sequence.py", 71, 71, "embargo: bool = False"),
    ("_sequence.py:125-133", "data", f"{G}/_sequence.py", 125, 133, "target"),
    ("_sequence.py:277", "data", f"{G}/_sequence.py", 277, 277, "temporal_split_indices"),
    (":376 (after _sequence.py)", "data", f"{G}/_sequence.py", 376, 376, "temporal_split_indices"),
    ("_synthetic.py:65", "data", f"{G}/_synthetic.py", 65, 65, "seed: int = Field(default=0"),
    ("_synthetic.py:66", "data", f"{G}/_synthetic.py", 66, 66, "The NPZ stays RAW either way"),
    ("_synthetic.py:90", "data", f"{G}/_synthetic.py", 90, 90, "def build_sequence_arrays"),
    (":100 (after _synthetic.py:90)", "data", f"{G}/_synthetic.py", 100, 100, "window_regular_series("),
    ("_synthetic.py:111-130", "data", f"{G}/_synthetic.py", 111, 130, "scaling"),
    ("irregular_sine/generator.py:57", "data", f"{G}/irregular_sine/generator.py", 57, 57, "window_timed_series"),
    ("delay_product/generator.py:71", "data", f"{G}/delay_product/generator.py", 71, 71, "window_timed_series"),
    # juniper-data: tests and packaging
    ("test_val_emission_guards.py:162-163", "data", f"{D}/tests/unit/test_val_emission_guards.py", 162, 163, "zero-row val partition must be PRESENT and empty"),
    ("test_val_emission_guards.py:241-244", "data", f"{D}/tests/unit/test_val_emission_guards.py", 241, 244, "Which shape a consumer sees is then decided by cache state"),
    (":288 (after test_val_emission_guards.py)", "data", f"{D}/tests/unit/test_val_emission_guards.py", 288, 288, 'int(version.split(".")[0]) < 3'),
    (":296 (after test_val_emission_guards.py)", "data", f"{D}/tests/unit/test_val_emission_guards.py", 296, 296, 'assert ahead == {"arc_agi": "4.0.0", "equities": "5.0.0", "equities_seq": "5.0.0"}'),
    ("test_normaliser_fit_scope.py:172", "data", f"{D}/tests/unit/test_normaliser_fit_scope.py", 172, 172, "falls_back"),
    ("pyproject.toml:123 (juniper-data)", "data", "pyproject.toml", 123, 123, "juniper-data-client"),
    # juniper-data-client
    ("juniper_data_client/contract.py:13", "client", f"{C}/contract.py", 13, 13, "untouched and returns immediately"),
    ("contract.py:74", "client", f"{C}/contract.py", 74, 74, "return CONTRACT_KIND_TABULAR"),
    ("juniper_data_client/client.py:679-680", "client", f"{C}/client.py", 679, 680, "np.load(io.BytesIO(content))"),
    ("juniper_data_client/__init__.py:9,16", "client", f"{C}/__init__.py", 9, 16, "validate_npz_contract"),
    ("exceptions.py:82", "client", f"{C}/exceptions.py", 82, 82, "class JuniperDataContractError(JuniperDataClientError, ValueError):"),
    ("juniper_data_client/exceptions.py:82", "client", f"{C}/exceptions.py", 82, 82, "class JuniperDataContractError"),
    ("juniper_data_client/constants.py:283-307", "client", f"{C}/constants.py", 283, 307, 'GENERATOR_DELAY_PRODUCT: str = "delay_product"'),
    ("testing/fake_client.py:417", "client", f"{C}/testing/fake_client.py", 417, 417, "dataset_id = str(uuid.uuid4())"),
    # juniper-cascor
    ("src/spiral_problem/data_provider.py:218", "cascor", "src/spiral_problem/data_provider.py", 218, 218, "Extra keys are ignored"),
    ("src/spiral_problem/data_provider.py:193", "cascor", "src/spiral_problem/data_provider.py", 193, 193, "download_artifact_npz"),
    (":196 (after data_provider.py)", "cascor", "src/spiral_problem/data_provider.py", 196, 196, "_convert_arrays_to_tensors"),
    ("src/api/lifecycle/manager.py:4068", "cascor", "src/api/lifecycle/manager.py", 4068, 4068, "def _artifact_to_tensors"),
    ("src/api/lifecycle/manager.py:4210", "cascor", "src/api/lifecycle/manager.py", 4210, 4210, "download_artifact_npz"),
    (":4239 (after manager.py)", "cascor", "src/api/lifecycle/manager.py", 4239, 4239, "_artifact_to_tensors"),
    (":2846 (after manager.py)", "cascor", "src/api/lifecycle/manager.py", 2846, 2846, "dataset_shortfall"),
    (":2868 (after manager.py)", "cascor", "src/api/lifecycle/manager.py", 2868, 2868, "current_dataset"),
    ("src/api/lifecycle/manager.py:3739", "cascor", "src/api/lifecycle/manager.py", 3739, 3739, "allow_missing_validation_split"),
    ("manager.py:3739", "cascor", "src/api/lifecycle/manager.py", 3739, 3739, "allow_missing_validation_split"),
    ("src/api/settings.py:557", "cascor", "src/api/settings.py", 557, 557, "allow_missing_validation_split: bool"),
    ("src/api/app.py:563", "cascor", "src/api/app.py", 563, 563, "download_artifact_npz"),
    (":603 (after app.py)", "cascor", "src/api/app.py", 603, 603, "_artifact_to_tensors"),
    ("src/snapshots/snapshot_common.py:292-303", "cascor", "src/snapshots/snapshot_common.py", 292, 303, "tobytes()"),
    ("juniper-cascor/pyproject.toml:118", "cascor", "pyproject.toml", 118, 118, "juniper-data-client>=0.3.0"),
    # juniper-canopy
    ("src/demo_mode.py:848", "canopy", "src/demo_mode.py", 848, 848, "_VALIDATED_PARTITIONS"),
    ("src/demo_mode.py:1123", "canopy", "src/demo_mode.py", 1123, 1123, "download_artifact_npz"),
    (":1131 (after demo_mode.py)", "canopy", "src/demo_mode.py", 1131, 1131, "_validate_npz_arrays(npz_data)"),
    ("src/demo_mode.py:2026", "canopy", "src/demo_mode.py", 2026, 2026, "download_artifact_npz"),
    (":2043 (after demo_mode.py)", "canopy", "src/demo_mode.py", 2043, 2043, "_advise_npz_contract"),
    (":2059 (after demo_mode.py)", "canopy", "src/demo_mode.py", 2059, 2059, "_install_sequence_dataset"),
    (":2061 (after demo_mode.py)", "canopy", "src/demo_mode.py", 2061, 2061, "_validate_npz_arrays(npz_data)"),
    ("juniper-canopy/pyproject.toml:192", "canopy", "pyproject.toml", 192, 192, "juniper-data-client"),
    # juniper-recurrence
    ("juniper_recurrence_model/data.py:109", "recurrence", "juniper-recurrence-model/juniper_recurrence_model/data.py", 109, 109, 'key.endswith(f"_{present[0]}")'),
    ("juniper_recurrence_model/data.py:53-59", "recurrence", "juniper-recurrence-model/juniper_recurrence_model/data.py", 53, 59, "def load_sequence_npz"),
    ("juniper-recurrence-model/pyproject.toml:31-37", "recurrence", "juniper-recurrence-model/pyproject.toml", 31, 37, "juniper-model-core"),
    ("juniper-recurrence/juniper_recurrence/data.py:76", "recurrence", "juniper-recurrence/juniper_recurrence/data.py", 76, 76, "download_artifact_npz"),
    (":77 (after recurrence data.py)", "recurrence", "juniper-recurrence/juniper_recurrence/data.py", 77, 77, "validate_npz_contract(arrays)"),
    (":78 (after recurrence data.py)", "recurrence", "juniper-recurrence/juniper_recurrence/data.py", 78, 78, "sequence_data_from_arrays(arrays, split)"),
    ("juniper-recurrence/pyproject.toml:54", "recurrence", "juniper-recurrence/pyproject.toml", 54, 54, "juniper-data-client"),
    (":267 (bench/datasets.py)", "recurrence", "bench/datasets.py", 267, 267, "EquitiesSeqGenerator.generate"),
    (":47 (bench/app_e2e.py)", "recurrence", "bench/app_e2e.py", 47, 47, "_FakeClient"),
    (":64 (bench/app_e2e.py)", "recurrence", "bench/app_e2e.py", 64, 64, "JuniperDataClient"),
    # juniper-ml
    ("util/snapshot_attribute.py:341", "ml", "util/snapshot_attribute.py", 341, 341, ".generate("),
    ("util/experiments/run_experiment.py:1230", "ml", "util/experiments/run_experiment.py", 1230, 1230, "/artifact"),
    (":1332 (after run_experiment.py)", "ml", "util/experiments/run_experiment.py", 1332, 1332, "/artifact"),
    ("util/experiments/plots_cascor.py:43", "ml", "util/experiments/plots_cascor.py", 43, 43, "def load_npz_bytes"),
    ("util/experiments/plots_recurrence.py:49", "ml", "util/experiments/plots_recurrence.py", 49, 49, "def load_npz_bytes"),
    ("util/release_train/propose.py:930", "ml", "util/release_train/propose.py", 930, 930, "ceiling"),
    ("pyproject.toml:67 (juniper-ml)", "ml", "pyproject.toml", 67, 67, "juniper-data-client>="),
    (":86 (after juniper-ml pyproject.toml:67)", "ml", "pyproject.toml", 86, 86, "juniper-data>="),
]


def blob(repo: str, path: str) -> list[str] | None:
    checkout, sha = PINS[repo]
    result = subprocess.run(["git", "-C", str(checkout), "show", f"{sha}:{path}"], capture_output=True, text=True, check=False)  # nosec B603 B607
    if result.returncode != 0:
        return None
    return result.stdout.splitlines()


def coverage(spec_text: str) -> list[str]:
    """Every `name.ext:NN` citation in the spec must be matched by a row whose citation starts with it."""
    cited = set(re.findall(r"([A-Za-z0-9_./-]+\.(?:py|toml)):(\d+(?:[-,]\d+)*)", spec_text))
    written = {row[0].split(" ")[0] for row in ROWS}
    missing = []
    for name, lines in sorted(cited):
        text = f"{name}:{lines}"
        if text not in written:
            missing.append(text)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dump", action="store_true", help="print the cited lines instead of verifying tokens")
    parser.add_argument("--ml-pin", default=None, help="override the juniper-ml sha (default: the spec's pin in PINS)")
    args = parser.parse_args()
    if args.ml_pin:
        PINS["ml"] = (PINS["ml"][0], args.ml_pin)

    failures = 0
    cache: dict[tuple[str, str], list[str] | None] = {}
    for citation, repo, path, first, last, token in ROWS:
        key = (repo, path)
        if key not in cache:
            cache[key] = blob(repo, path)
        lines = cache[key]
        if lines is None:
            print(f"FAIL {citation}: {repo}:{path} not found at {PINS[repo][1][:10]}")
            failures += 1
            continue
        window = lines[first - 1:last]
        if args.dump:
            print(f"--- {citation}  [{repo} {PINS[repo][1][:8]} {path}:{first}-{last}]")
            for number, text in enumerate(window, start=first):
                print(f"  {number}: {text[:170]}")
            continue
        if not any(token in text for text in window):
            print(f"FAIL {citation}: token {token!r} not in {path}:{first}-{last} at {PINS[repo][1][:10]}")
            for number, text in enumerate(window, start=first):
                print(f"    {number}: {text[:150]}")
            failures += 1
    if args.dump:
        return 0
    missing = coverage(SPEC.read_text(encoding="utf-8"))
    for text in missing:
        print(f"FAIL coverage: the spec cites {text}, and no row checks it")
    failures += len(missing)
    print(f"\n{len(ROWS)} rows checked at {', '.join(f'{k}={v[1][:8]}' for k, v in PINS.items())}; {failures} failure(s)")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
