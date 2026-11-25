"""
Print a compact per-row table of one or two r23l probe JSON files (main and fix side by side).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, builder r23l)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-25_flood4_s14_r23l_probe.py; notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Usage: python3 <this file> PROBE.json [PROBE2.json]
"""

import json
import sys

KEYS = (
    "op_outcome",
    "after_op",
    "after_the_stopped_fit_ended",
    "op_once_the_stopped_fit_ended",
    "leave_outcome",
    "after_leaving",
    "session_survived",
    "start_after_leaving",
    "replay_stop_outcome",
    "after_replay_stop",
    "stop_event_set_after_replay_stop",
    "run_fit_alive_after_replay_stop",
    "second_start",
    "second_start_accepted_beside_the_running_fit",
    "stop_replay_outcome",
    "before",
    "after",
    "seek_outcome",
    "fsm_during",
    "replay_frames_in_the_live_sink",
    "load_status",
    "load_detail",
    "after_load",
    "replay",
    "retrain",
    "start",
    "replay_stop_status",
    "replay_stop_body",
    "status_after_replay_stop",
    "run_fit_alive",
    "second_start_status",
    "second_start_detail",
    "ws_unknown_commands",
    "ws_start_ack",
    "http_replay_stop_status",
    "fsm_after_replay_stop",
    "ws_second_start_ack",
    "peak_fits_at_once",
    "setup_error",
)


def _short(value):
    if isinstance(value, dict):
        if "fsm" in value:
            parts = [f"{value.get('fsm')}/{value.get('monitor')}"]
            if "history" in value:
                parts.append(f"h{value['history']}")
            if value.get("error"):
                parts.append(f"err={value['error']}")
            if value.get("replay_session"):
                parts.append("session")
            return " ".join(parts)
        return json.dumps(value, sort_keys=True)
    return str(value)


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    docs = [_load(p) for p in argv[1:]]
    for doc in docs:
        h = doc["header"]
        print(f"# {h['label']}: python {h['python'].split()[0]}, manager {h['manager_sha256'][:12]} ({h['manager_py']})")
    for i, row in enumerate(docs[0]["rows"]):
        others = [d["rows"][i] for d in docs[1:]]
        print(f"\n== {row['row']}")
        for key in KEYS:
            if key not in row and not any(key in o for o in others):
                continue
            vals = [_short(row.get(key))] + [_short(o.get(key)) for o in others]
            print(f"   {key}: " + "  ||  ".join(vals))
        print("   defect_seen: " + "  ||  ".join(str(r.get("defect_seen")) for r in [row] + others))
    for doc in docs:
        rows = doc["rows"]
        print(f"\nTOTAL {doc['header']['label']}: {len(rows)} rows, defect_seen {sum(1 for r in rows if r.get('defect_seen'))}, setup errors {sum(1 for r in rows if 'setup_error' in r)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
