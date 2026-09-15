#!/usr/bin/env python
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc probe
#
# Author:        Paul Calnon
# Version:       0.1.0
# File Name:     2026-09-15_split_field_form_leak_census.py
# File Path:     ${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/
#
# Date Created:  2026-09-15
#
# License:       MIT License
# Copyright:     Copyright (c) 2024,2025,2026 Paul Calnon
#
# Description:
#     Census for the canopy form-rendering leak recorded in §12.9.3 of
#     notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md:
#     the three-partition split plumbing (sizing_mode / val_percent / test_percent /
#     val_ratio) is claimed to render as generator CONTENT params on every generator,
#     because canopy's INFRASTRUCTURE_FIELDS predates those four fields.
#
#     Runs canopy's REAL parse_schema_fields against juniper-data's REAL generator
#     schemas, so the answer is measured rather than inferred from the constant.
#
#     Also reports the input_type each leaked field renders as -- the free-text
#     ``sizing_mode`` is the second half of the same finding.
#
# Usage:
#     /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-15_split_field_form_leak_census.py
#
#####################################################################################################################################################################################################
"""Measure which juniper-data generators leak split plumbing into canopy's rendered form."""

from __future__ import annotations

import sys

DATA_ROOT = "/home/pcalnon/Development/python/Juniper/juniper-data"
CANOPY_SRC = "/home/pcalnon/Development/python/Juniper/juniper-canopy/src"

SPLIT_FIELDS = {"sizing_mode", "val_percent", "test_percent", "val_ratio"}


def main() -> int:
    sys.path.insert(0, DATA_ROOT)
    sys.path.insert(0, CANOPY_SRC)

    from juniper_data.api.routes.generators import GENERATOR_REGISTRY  # noqa: E402

    from dataset_schema import form_excluded_fields, parse_schema_fields  # noqa: E402

    total = len(GENERATOR_REGISTRY)
    print(f"{total} generators in juniper-data's GENERATOR_REGISTRY\n")

    leaking: list[tuple[str, list[str]]] = []
    clean: list[str] = []
    types_seen: dict[str, set[str]] = {}

    for name, info in sorted(GENERATOR_REGISTRY.items()):
        schema = info["params_class"].model_json_schema()
        # Use the PER-GENERATOR exclusion that shipped in canopy#625, so this measures the
        # leak as it stands on main today -- not against the pre-fix universal set.
        fields = parse_schema_fields(schema, exclude=form_excluded_fields(name))
        by_name = {f.name: f for f in fields}
        leaked = sorted(SPLIT_FIELDS & set(by_name))
        if leaked:
            leaking.append((name, leaked))
            for field_name in leaked:
                types_seen.setdefault(field_name, set()).add(by_name[field_name].input_type)
        else:
            clean.append(name)

    print(f"LEAKING split plumbing into the content form: {len(leaking)}/{total}")
    for name, leaked in leaking:
        print(f"  {name:16s} {leaked}")
    if clean:
        print(f"\nNOT leaking ({len(clean)}): {clean}")

    print("\nRendered control type per leaked field:")
    for field_name in sorted(types_seen):
        print(f"  {field_name:16s} -> {sorted(types_seen[field_name])}")

    print("\nsizing_mode detail (the free-text half):")
    for name, info in sorted(GENERATOR_REGISTRY.items()):
        props = info["params_class"].model_json_schema().get("properties", {})
        if "sizing_mode" in props:
            prop = props["sizing_mode"]
            print(f"  {name:16s} type={prop.get('type')!r} enum={prop.get('enum')!r} default={prop.get('default')!r}")
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
