"""
Probe how /ws/training answers the resume frames that round 3 of the N-3 fix changes or documents, on a chosen tree.

Each raw frame goes through the real training_stream_handler and WebSocketManager (the carrier test file's FakeWS and
helpers), in two buffer states: nothing broadcast yet, and seqs 1-5 buffered. One broadcast follows each handshake, so
the record shows whether the socket ended up in the live fan-out. The frames:

  * a negative last_seq (-1, -5), beside 0 for comparison   -> the code lens's F4
  * `data` that is null, a list, a string, a number, absent -> the code lens's F5
  * a last_seq of 4,301 digits, which Python's json refuses  -> the row the API reference gains

Usage: python <this> --out <json>   (PROBE_SRC=<a src/ tree> to probe other code; default: the carrier's src/)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses;
         tmp/flood4r2-val/n3-r2-code-lens/findings.json F4, F5
"""

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path

CARRIER = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
SRC = Path(os.environ.get("PROBE_SRC", str(CARRIER / "src")))
sys.path.insert(0, str(SRC))
_SPEC = importlib.util.spec_from_file_location("resume_tests", CARRIER / "src" / "tests" / "unit" / "api" / "test_websocket_resume_continuity.py")
t = importlib.util.module_from_spec(_SPEC)
sys.modules["resume_tests"] = t
_SPEC.loader.exec_module(t)

logging.disable(logging.CRITICAL)


def frames(server_instance_id: str) -> dict:
    """Label -> raw frame text. Raw, because json.dumps cannot write some of these."""
    sid = json.dumps(server_instance_id)
    out = {}
    for label, raw in (("last_seq -1", "-1"), ("last_seq -5", "-5"), ("last_seq 0", "0"), ("last_seq of 4301 digits", "9" * 4301)):
        out[label] = '{"type": "resume", "data": {"last_seq": ' + raw + ', "server_instance_id": ' + sid + "}}"
    for label, raw in (("data null", "null"), ("data list", "[]"), ("data string", '"last_seq"'), ("data number", "7")):
        out[label] = '{"type": "resume", "data": ' + raw + "}"
    out["data absent"] = '{"type": "resume"}'
    return out


async def probe(label: str, buffered: int) -> dict:
    mgr = t._manager()
    await t._observer(mgr)
    for i in range(buffered):
        await mgr.broadcast(t._metrics(i))
    ws = t.FakeWS(app=t._app(mgr), incoming=[frames(mgr.server_instance_id)[label]])
    task = asyncio.create_task(t.training_stream_handler(ws))
    await t._settle(task, ws)
    await mgr.broadcast(t._metrics("live"))
    await t._finish(task, ws)
    types = ws.types()
    if "resume_ok" in types:
        reply = "resume_ok replayed_count=" + str(ws.frame("resume_ok")["data"]["replayed_count"])
    elif "resume_failed" in types:
        reply = "resume_failed " + ws.frame("resume_failed")["data"]["reason"]
    else:
        reply = "no resume reply (fresh connect)"
    return {"frame": label, "buffered_seqs": buffered, "reply": reply, "seqs_received": ws.seqs(), "closed": ws.closed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = []
    for buffered in (0, 5):
        for label in frames("x"):
            rows.append(asyncio.run(probe(label, buffered)))
    result = {"code_under_test": sys.modules["api.websocket.training_stream"].__file__, "int_max_str_digits": sys.get_int_max_str_digits(), "rows": rows}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")
    print("code under test:", result["code_under_test"])
    for row in rows:
        print(f"  buffered {row['buffered_seqs']} | {row['frame']:<24} -> {row['reply']:<36} seqs {row['seqs_received']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
