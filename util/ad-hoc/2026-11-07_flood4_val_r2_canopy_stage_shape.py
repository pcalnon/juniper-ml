#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Round-2 probe of POST /api/stage_dataset's documented response and 422 row.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#802 docs carrier, validation round 2, correction D-F3 (findings: tmp/flood4/canopy/val-round2/)

Run with the canopy env's python from <canopy tree>/src, PYTHONDONTWRITEBYTECODE=1:
  1. shape_stage_payload for an mnist body, then CascorServiceAdapter's key map, gives the
     body cascor would record (the doc's example `config`).
  2. FastAPI's handling of a non-integer nn_dataset_elements on canopy's real `app`
     (TestClient; the route body never runs on a validation failure, so no backend is called).
Read-only: writes nothing.
"""
import json
import os
import sys

sys.path.insert(0, os.getcwd())


def main() -> int:
    out = {}
    from backend import recurrence_request  # noqa: E402
    from backend.cascor_service_adapter import CascorServiceAdapter  # noqa: E402

    for body in ({"nn_dataset_type": "mnist"}, {"nn_dataset_type": "mnist", "nn_dataset_elements": 500, "nn_dataset_noise": 0.2}):
        stage = recurrence_request.shape_stage_payload(dict(body))
        mapped = {CascorServiceAdapter._DATASET_PARAM_MAP[k]: v for k, v in stage.payload.items() if k in CascorServiceAdapter._DATASET_PARAM_MAP and v is not None}
        out[json.dumps(body)] = {"shaped": stage.payload, "forwarded_to_cascor": mapped}
    # 2. The route's request model alone (no app import, so no startup side effects):
    #    FastAPI answers a body that fails this model with its default 422 handler.
    from pydantic import BaseModel, ValidationError  # noqa: E402
    from typing import Any, Optional  # noqa: E402

    class StageDatasetRequest(BaseModel):  # copied field-for-field from main.py:4535-4558
        nn_dataset_type: Optional[str] = None
        nn_dataset_elements: Optional[int] = None
        nn_dataset_noise: Optional[float] = None
        nn_spiral_rotations: Optional[float] = None
        nn_spiral_number: Optional[int] = None
        nn_dataset_params: Optional[dict[str, Any]] = None
        nn_model: Optional[str] = None

    try:
        StageDatasetRequest(nn_dataset_type="mnist", nn_dataset_elements="abc")
        out["non_integer_elements"] = "ACCEPTED"
    except ValidationError as exc:
        out["non_integer_elements"] = [e["type"] for e in exc.errors()]
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
