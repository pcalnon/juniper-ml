#!/usr/bin/env python3
"""Put a throwaway cascor into ``Investigating`` with a small trained network: train a spiral, snapshot it, restore it.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc)
Application:  canopy E2E validation arc -- item 30 (the Network Editor rows need a writable cascor in Investigating)
Author:       Paul Calnon
Created:      2026-10-20
Status:       ad-hoc -- investigation
Retire when:  RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:      util/ad-hoc/2026-10-20_turing_cascor_leg.bash (the leg); util/ad-hoc/e2e_p1wave_redrive.py --step f011 (the
              W5-07 UI path, restore from the Snapshots tab, which the Linux-host drives used);
              notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 13, item 30)
License:      MIT License

The entry condition for M-NETWORK-EDITOR-09/-13/-17 is a cascor whose FSM is Investigating with a network that has
hidden units and MORE THAN ONE OUTPUT (the spiral has two), so that the manual's semicolon and newline forms for
``output_weights`` meet the shape check F-CANOPY-012's residue describes. This script reaches it through cascor's
own API, never through the trio: POST /v1/training/start with the in-process spiral fallback and a small budget,
wait for the run to end, POST /v1/snapshots, POST /v1/snapshots/{id}/restore. Every response is printed and the
run is recorded as JSON so the drive's provenance (snapshot id, topology) is on file.

Usage:
    python3 -I util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py --cascor http://127.0.0.1:8222 \\
        --out reports/e2e-canopy-2026-09-02/item30-turing/cascor_8222_prepare.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def http(base: str, method: str, path: str, body=None, timeout: float = 60.0):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 -- loopback test leg
            raw = r.read().decode() or "null"
            try:
                return r.status, json.loads(raw)
            except ValueError:
                return r.status, raw[:500]
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw[:500]


def data_of(payload):
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cascor", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-hidden-units", type=int, default=3)
    ap.add_argument("--max-iterations", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--wait-seconds", type=float, default=600.0)
    ap.add_argument("--skip-train", action="store_true", help="snapshot + restore the network that is already there")
    args = ap.parse_args()
    base = args.cascor.rstrip("/")
    rec: dict = {"cascor": base, "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    rec["health"] = http(base, "GET", "/v1/health")
    print("health", rec["health"])
    if not args.skip_train:
        body = {
            "dataset": {"generator": "spiral", "params": {"n_points_per_spiral": 60, "n_rotations": 1.0, "noise": 0.0, "seed": 7}},
            "params": {"max_hidden_units": args.max_hidden_units, "max_iterations": args.max_iterations, "output_epochs": args.epochs, "candidate_epochs": args.epochs, "max_epochs": args.epochs, "patience": 25, "candidate_patience": 25},
            "start_fresh": True,
        }
        rec["start_body"] = body
        rec["start"] = http(base, "POST", "/v1/training/start", body)
        print("start", json.dumps(rec["start"])[:600])
        t0 = time.time()
        last = None
        while time.time() - t0 < args.wait_seconds:
            code, st = http(base, "GET", "/v1/training/status")
            d = data_of(st) if code == 200 else {}
            active = d.get("training_active") if isinstance(d, dict) else None
            sm = (d.get("state_machine") or {}) if isinstance(d, dict) else {}
            key = (active, sm.get("status") or sm.get("state"))
            if key != last:
                print(f"  +{round(time.time() - t0, 1)}s training_active={active} state={sm.get('status') or sm.get('state')} hidden={(d.get('training_state') or {}).get('hidden_units') if isinstance(d, dict) else None}")
                last = key
            if active is False and last[0] is False and time.time() - t0 > 5:
                break
            time.sleep(2)
        rec["status_after_training"] = http(base, "GET", "/v1/training/status")
    rec["topology_before"] = http(base, "GET", "/v1/network/topology")
    print("topology", json.dumps(rec["topology_before"])[:400])
    rec["snapshot"] = http(base, "POST", "/v1/snapshots", {"description": "item 30 re-drive entry network (turing, 2026-10-20)"})
    print("snapshot", json.dumps(rec["snapshot"])[:500])
    snap = data_of(rec["snapshot"][1]) if rec["snapshot"][0] in (200, 201) else {}
    sid = (snap.get("snapshot_id") or snap.get("id") or snap.get("snapshot", {}).get("id")) if isinstance(snap, dict) else None
    rec["snapshot_id"] = sid
    if not sid:
        print("no snapshot id; stopping", file=sys.stderr)
        rec["ok"] = False
    else:
        rec["restore"] = http(base, "POST", f"/v1/snapshots/{sid}/restore")
        print("restore", json.dumps(rec["restore"])[:500])
        rec["status_after_restore"] = http(base, "GET", "/v1/training/status")
        d = data_of(rec["status_after_restore"][1])
        sm = (d.get("state_machine") or {}) if isinstance(d, dict) else {}
        rec["fsm_after_restore"] = sm.get("status") or sm.get("state")
        rec["topology_after"] = http(base, "GET", "/v1/network/topology")
        print("fsm after restore:", rec["fsm_after_restore"], "topology:", json.dumps(rec["topology_after"])[:300])
        rec["ok"] = str(rec["fsm_after_restore"]).lower().startswith("investigat")
    rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, default=str)
    print("OK" if rec.get("ok") else "NOT OK", "->", args.out)
    return 0 if rec.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
