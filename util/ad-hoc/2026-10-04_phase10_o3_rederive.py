#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-04
# Status      : ad-hoc — investigation; RETAINED as provenance (owner policy 2026-08-25)
# ---------------------------------------------------------------------------
"""Re-derive the selection arc's O3 by EXECUTING canopy's partition extractor on the frames cascor sends.

O3 (``reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md`` § "Observations"):
``/api/set_params`` answered ``{"applied": ["cn_training_iterations"]}`` while canopy logged four keys
updated over ``/ws/control`` and one over REST.

The shapes, read from source at the pinned commits:

  cascor 95cdc562   ``update_params`` returns the params echo plus ``applied`` / ``skipped``; "the REST
                    route's ``data`` and the WS ack's ``result`` carry them through untouched"
                    (``manager.py``). ``create_control_ack_message`` puts that dict at ``result`` inside
                    the envelope's ``data`` (``websocket/messages.py``).
  cascor-client     ``CascorControlStream`` resolves ``set_params`` with the WHOLE frame
                    (``ws_client.py``: ``self._pending[cid].set_result(msg)``).
  canopy 1b2dd438   ``apply_params`` does ``result_data.update(ws_frame)`` then
                    ``result_data.update(rest_envelope)``, and ``_extract_cascor_partition`` scans the
                    top level and ``data`` only.

Arms: WS only, WS then REST (the A-N2 case), REST only (control), and a mutation that also scans
``data.result`` (shows the extractor's answer depends on where it looks, so a different answer was
possible).

Usage (canopy env, LIBTORCH cleared):
    env -u LD_LIBRARY_PATH -u LIBTORCH -u LIBTORCH_LIB /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-10-04_phase10_o3_rederive.py --canopy-src <canopy tree at 1b2dd438>/src
"""

from __future__ import annotations

import argparse
import sys


def update_params_result(applied: list, skipped: list) -> dict:
    """cascor's update_params success return: the params echo plus the C2a partition."""
    return {"params": {"max_iterations": 5, "output_epochs": 500}, "applied": applied, "skipped": skipped}


def ws_frame(result: dict) -> dict:
    """The command_response frame as create_control_ack_message builds it and the client resolves it."""
    return {"type": "command_response", "timestamp": 0.0, "data": {"command": "set_params", "status": "success", "command_id": "cid-1", "result": result}}


def rest_envelope(result: dict) -> dict:
    """PATCH /v1/training/params: success_response(updated)."""
    return {"status": "success", "data": result, "meta": {}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canopy-src", required=True)
    args = ap.parse_args()
    sys.path.insert(0, args.canopy_src)
    from backend.cascor_service_adapter import CascorServiceAdapter as A

    ws = ws_frame(update_params_result(["max_iterations", "max_hidden_units", "output_epochs"], [{"key": "epochs_max", "reason": "not-updatable"}]))
    rest = rest_envelope(update_params_result(["candidate_epochs"], []))

    def merged(*parts):
        out: dict = {}
        for p in parts:
            out.update(p)  # apply_params: result_data.update(ws_result); result_data.update(rest_result)
        return out

    def extract(data, also_scan_result=False):
        applied, skipped = A._extract_cascor_partition(A, data)
        if also_scan_result:
            inner = (data.get("data") or {}).get("result")
            if isinstance(inner, dict):
                a2, s2 = A._extract_cascor_partition(A, inner)
                applied += [k for k in a2 if k not in applied]
                skipped += [s for s in s2 if s not in skipped]
        return applied, skipped

    arms = [
        ("WS leg only", merged(ws), False),
        ("WS leg then REST leg (the A-N2 case)", merged(ws, rest), False),
        ("REST leg only (control)", merged(rest), False),
        ("MUTATION: WS only, extractor also scans data.result", merged(ws), True),
    ]
    for label, data, mutate in arms:
        applied, skipped = extract(data, mutate)
        print(f"{label:<55} applied={applied}  skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
