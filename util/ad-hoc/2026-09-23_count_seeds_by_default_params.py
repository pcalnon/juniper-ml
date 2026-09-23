"""
Count canopy's seeded datasets by compatible model and by whether their ``default_params`` are empty.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: canopy ``src/tests/regression/test_dataset_generator_contract.py::test_an_unseeded_dataset_is_unchanged``,
         whose comment says "the seven cascor-compatible seeds that carry {}".

Usage:
    /opt/miniforge3/envs/JuniperCanopy1/bin/python util/ad-hoc/2026-09-23_count_seeds_by_default_params.py <canopy-checkout>
"""

import sys
from pathlib import Path

src = Path(sys.argv[1]).resolve() / "src"
sys.path.insert(0, str(src))

import model_registry  # noqa: E402

print(f"model_registry from {model_registry.__file__}")
for model in model_registry.MODELS:
    compatible = model_registry.compatible_datasets(model)
    empty = [spec.value for spec in compatible if not model_registry.dataset_default_params(spec.value)]
    seeded = {spec.value: dict(model_registry.dataset_default_params(spec.value)) for spec in compatible if model_registry.dataset_default_params(spec.value)}
    print(f"{model.key}: {len(compatible)} compatible; {len(empty)} carry {{}}: {empty}")
    print(f"    with params: {sorted(seeded)}")
