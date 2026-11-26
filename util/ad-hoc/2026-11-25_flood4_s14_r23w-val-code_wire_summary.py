"""
Summarise the r23w code lens's wire-probe cells into one line per cell and a main-vs-fix verdict per scenario.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

Usage:
  python -I <this file> WIRE_DIR --out SUMMARY.json [--txt SUMMARY.txt]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def line(d: dict) -> dict:
    s = d.get("scenario", "")
    out = {"impl": d.get("impl"), "uvicorn": d.get("uvicorn"), "websockets": d.get("websockets"), "port_ephemeral": d.get("port_ephemeral"), "manager_sha": d.get("modules", {}).get("juniper_service_core.websocket.manager", {}).get("sha256"), "control_sha": d.get("modules", {}).get("juniper_service_core.websocket.control_stream", {}).get("sha256")}
    out["asgi_exceptions"] = d.get("asgi_exceptions")
    out["handlers"] = [h.get("outcome") for h in d.get("handlers", [])]
    if s == "a_unsendable":
        out["client_closes"] = [c["closes"] for c in d["clients"]]
        out["client_seqs"] = [c["seqs"] for c in d["clients"]]
        out["resume_from_1"] = d["resume_from_1"]
        out["final_seq"] = d["steps"][-1]["current_seq"]
        out["unserializable"] = d["steps"][-1]["unserializable"]
    elif s == "a_deliverable":
        out["frames_normalised_sha256"] = d["frames_normalised_sha256"]
        out["seqs"] = d["seqs"]
        out["closes"] = d["closes"]
        out["chunk_groups"] = d["chunk_groups"]
        out["stats"] = d["stats"]
    elif s.startswith("b_"):
        for k in ("http_status", "server_close", "frames_after_server_close", "executed", "handler_end_after_server_close_s", "info_logs"):
            out[k] = d.get(k)
        out["error_logs"] = [e["msg"][:160] for e in d.get("error_logs", [])]
    elif s.startswith("c_"):
        for k in ("drop", "a_close", "b_status_while_a_open", "b_connection_established_connections", "with_b", "hold_s", "a_handler_end_after_drop_s", "c_status_after_hold", "at_c", "after_all_gone"):
            if k in d:
                out[k] = d[k]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("wire", type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--txt", type=pathlib.Path)
    args = parser.parse_args()
    cells = {}
    missing = []
    for path in sorted(args.wire.rglob("*.json")):
        rel = path.relative_to(args.wire)
        try:
            with path.open(encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            missing.append(str(rel))
            continue
        cells[str(rel)] = line(d)
    args.out.write_text(json.dumps({"cells": cells, "unreadable": missing}, indent=1) + "\n")
    if args.txt:
        with args.txt.open("w", encoding="utf-8") as fh:
            for rel, c in cells.items():
                fh.write(f"{rel}: {json.dumps(c, ensure_ascii=False)}\n")
    print(f"cells={len(cells)} unreadable={len(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
