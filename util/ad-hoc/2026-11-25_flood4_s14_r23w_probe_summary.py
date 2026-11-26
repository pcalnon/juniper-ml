"""
Summarise the r23w probe's uvicorn cells (one JSON per implementation x scenario) into one table per directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23w: ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-25_flood4_s14_r23w_probe.py; notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Usage: python <this file> DIR [DIR ...]
Reads DIR/uv_<scenario>_<impl>.json and prints, per cell, the code it measured (manager sha256 prefix) and the
fields that decide each gap. Writes DIR/matrix.json with the same rows.
"""

import json
import sys
from pathlib import Path

_SCENARIOS = ("late_pong", "late_command", "stall")
_IMPLS = ("websockets", "websockets-sansio", "wsproto")


def _row(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    res = data["results"]
    code = data["code"]
    row = {
        "cell": path.stem,
        "uvicorn": data["env"].get("uvicorn"),
        "websockets": data["env"].get("websockets"),
        "wsproto": data["env"].get("wsproto"),
        "python": data["env"]["python"],
        "manager_sha256": code["juniper_service_core.websocket.manager"]["sha256"][:12],
        "control_stream_sha256": code["juniper_service_core.websocket.control_stream"]["sha256"][:12],
    }
    if "stall" in path.stem:
        row.update(
            {
                "dropped": res.get("dropped"),
                "seconds_to_drop": res.get("seconds_to_drop"),
                "broadcasts_until_drop": res.get("broadcasts_until_drop"),
                "at_drop": res.get("at_drop"),
                "b_handshake": res.get("b_handshake"),
                "when_b_tried": res.get("when_b_tried"),
                "a_handler_outcome": res.get("a_handler_outcome"),
                "a_handler_outlived_drop_seconds": res.get("a_handler_outlived_drop_seconds"),
                "c_handshake_after_a_ended": res.get("c_handshake_after_a_ended"),
                "end_counts": res.get("end_counts"),
            }
        )
    else:
        row.update(
            {
                "server_close": res.get("server_close"),
                "frames_after_server_close": res.get("frames_after_server_close"),
                "handler_outcome": res.get("handler_outcome"),
                "executed": res.get("executed"),
                "asgi_exceptions_logged": res.get("asgi_exceptions_logged"),
                "handler_seconds_after_server_close": res.get("handler_seconds_after_server_close"),
            }
        )
    return row


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    for directory in map(Path, argv[1:]):
        rows = []
        for scenario in _SCENARIOS:
            for impl in _IMPLS:
                path = directory / f"uv_{scenario}_{impl}.json"
                if path.is_file():
                    rows.append(_row(path))
                else:
                    rows.append({"cell": path.stem, "missing": True})
        (directory / "matrix.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        print(f"== {directory}")
        for row in rows:
            print(json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
