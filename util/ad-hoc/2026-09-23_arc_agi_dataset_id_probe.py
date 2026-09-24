#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-09-23_arc_agi_dataset_id_probe.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-09-23
# Last Modified: 2026-09-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Derive the dataset_id juniper-data's POST /v1/datasets would mint for an
#    arc_agi request, the way the route does it: ArcAgiParams(**request.params),
#    then the generator's bind_deployment_defaults hook if it has one, then
#    generate_dataset_id("arc_agi", VERSION, params.model_dump()).
#
#    Why: juniper-data#427. #402 changed arc_agi's metadata without bumping its
#    VERSION, so the id -- and a cached artifact's stale metadata -- survived the
#    fix. The bump to 4.0.0 is only a fix if the ids actually move. This prints
#    the ids for the two requests the issue measured in the published 0.14.0 and
#    0.15.0 images (a default request, and seed 7), so a run against an
#    UNMODIFIED tree must reproduce the issue's values (the check that the
#    derivation matches the route), and a run against the fixed tree must not.
#
#    Imports juniper_data from --data-root (put first on sys.path), so it measures
#    the tree you name rather than whatever is installed.
#
# Usage:
#    env -u JUNIPER_DATA_DEFAULT_GENERATOR_SEED \
#      /opt/miniforge3/envs/JuniperData/bin/python \
#      util/ad-hoc/2026-09-23_arc_agi_dataset_id_probe.py --data-root <juniper-data tree>
#####################################################################################################################################################################################################

from __future__ import annotations

import argparse
import sys

# The ids juniper-data#427 measured inside ghcr.io/pcalnon/juniper-data:0.14.0 and :0.15.0.
ISSUE_427_IDS = {
    "default": "arc_agi-3.0.0-5cbabfa9a9026f82",
    "seed=7": "arc_agi-3.0.0-a7cf193634254e5e",
}
REQUESTS = {"default": {}, "seed=7": {"seed": 7}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, help="a juniper-data tree (checkout or tarball extract)")
    args = parser.parse_args()
    sys.path.insert(0, args.data_root)

    import juniper_data  # noqa: PLC0415 -- must follow the sys.path insert
    from juniper_data.core.dataset_id import generate_dataset_id  # noqa: PLC0415
    from juniper_data.generators.arc_agi import VERSION, ArcAgiGenerator, ArcAgiParams  # noqa: PLC0415

    print(f"juniper_data imported from {juniper_data.__file__}")
    print(f"arc_agi VERSION = {VERSION}")
    binder = getattr(ArcAgiGenerator, "bind_deployment_defaults", None)
    status = 0
    for label, request_params in REQUESTS.items():
        params = ArcAgiParams(**request_params)
        if callable(binder):
            params = binder(params)
        dataset_id = generate_dataset_id(generator="arc_agi", version=VERSION, params=params.model_dump())
        issue_id = ISSUE_427_IDS[label]
        if VERSION == "3.0.0":
            verdict = "MATCHES #427's measurement" if dataset_id == issue_id else "DIFFERS from #427's measurement -- the derivation is not the route's"
            status = status or (0 if dataset_id == issue_id else 1)
        else:
            verdict = "a NEW id, so no 3.0.0 cache entry can answer it" if dataset_id != issue_id else "STILL the 3.0.0 id -- the bump did not move it"
            status = status or (0 if dataset_id != issue_id else 1)
        print(f"{label:8} seed={params.seed!r:5} -> {dataset_id}  ({verdict})")
    print(f"exit={status}")
    return status


if __name__ == "__main__":
    sys.exit(main())
