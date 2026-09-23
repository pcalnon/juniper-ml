#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Grow the arc's cascor fixture by one window, the arc's own way, and snapshot it.

WHY THIS EXISTS. A resumed snapshot restores the NETWORK, not the metrics buffer:
cascor's ``/v1/metrics/history`` reads the lifecycle monitor, which is empty in a fresh
process. Every "66 metrics rows (output 54 / candidate 12)" figure in the 2026-09-10
handoff described rows accumulated by three growth windows inside ONE long-lived
cascor process. That process stopped on 2026-09-19. So a relaunched stack serves the
52-unit network with an EMPTY history, and every row that reads the store (the
candidate loss figure, the replay block, the F-CANOPY-038 identity guard, the
full-history mode) is untestable until a window runs.

THE RECIPE, from the ledger (Phase 5, "the fixture: restored with its identity"):
re-stage the dataset (``spirals/1000/0.25/1.5/2``, canopy's defaults), PATCH the
cap, start, and snapshot after. NEVER ``POST /v1/network`` -- that mints a new uuid
and the fixture's identity is lost.

Usage:
    python3 util/ad-hoc/2026-09-22_fixture_grow.py --to 54 \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-22_fixture_grow_54.json
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

CASCOR = os.environ.get("JUNIPER_E2E_CASCOR_URL", "http://127.0.0.1:8202")
TERMINAL = {"COMPLETED", "FAILED", "STOPPED", "ERROR"}


def _req(method: str, path: str, body: dict | None = None, timeout: float = 60.0) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(CASCOR + path, data=data, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 -- loopback only
            return {"http": r.status, "body": json.loads(r.read().decode() or "null")}
    except urllib.error.HTTPError as e:
        return {"http": e.code, "body": e.read().decode()[:600]}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"http": None, "body": f"{type(e).__name__}: {e}"}


def _data(resp: dict) -> dict:
    body = resp.get("body")
    return (body.get("data") or {}) if isinstance(body, dict) else {}


def _sample() -> dict:
    status = _data(_req("GET", "/v1/training/status", timeout=10))
    net = _data(_req("GET", "/v1/network", timeout=10))
    sm = status.get("state_machine") or {}
    mon = status.get("monitor") or {}
    return {
        "fsm": sm.get("status"),
        "phase": sm.get("phase"),
        "hidden_units": net.get("hidden_units"),
        "uuid": net.get("uuid"),
        "total_metrics": mon.get("total_metrics"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", type=int, required=True, help="the new max_hidden_units cap")
    ap.add_argument("--timeout", type=float, default=600.0, help="seconds to wait for a terminal FSM state")
    ap.add_argument("--no-stage", action="store_true", help="skip re-staging the dataset (it is already staged)")
    ap.add_argument("--no-snapshot", action="store_true", help="do not save a snapshot after the window")
    ap.add_argument("--out", required=True, help="where to write the JSON record")
    args = ap.parse_args()

    t0 = time.monotonic()
    rec: dict = {"cascor": CASCOR, "health": _data(_req("GET", "/v1/health")) or _req("GET", "/v1/health").get("body"), "samples": []}
    rec["before"] = _sample()
    print(f"before: {rec['before']}", flush=True)
    if not rec["before"].get("uuid"):
        print("REFUSED: cascor holds no network -- resume the fixture snapshot first", file=sys.stderr)
        return 2

    if not args.no_stage:
        rec["stage"] = _req("POST", "/v1/training/dataset", {"dataset_type": "spirals", "n_samples": 1000, "noise": 0.25, "rotations": 1.5, "n_spirals": 2})
        print(f"stage: http {rec['stage']['http']}", flush=True)
    rec["patch"] = _req("PATCH", "/v1/training/params", {"max_hidden_units": args.to})
    print(f"patch max_hidden_units={args.to}: http {rec['patch']['http']}", flush=True)
    rec["start"] = _req("POST", "/v1/training/start", {})
    print(f"start: http {rec['start']['http']} {str(rec['start']['body'])[:200]}", flush=True)
    if rec["start"]["http"] != 200:
        rec["verdict"] = "START-REFUSED"
        _write(args.out, rec)
        return 1

    last = None
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        s = _sample()
        s["t"] = round(time.monotonic() - t0, 1)
        rec["samples"].append(s)
        key = (s["fsm"], s["phase"], s["hidden_units"])
        if key != last:
            print(f"[t={s['t']:6.1f}] fsm={s['fsm']} phase={s['phase']} hidden={s['hidden_units']} metrics={s['total_metrics']}", flush=True)
            last = key
        if (s["fsm"] or "").upper() in TERMINAL:
            break
        time.sleep(1.0)

    rec["after"] = _sample()
    print(f"after: {rec['after']}", flush=True)
    fsm = (rec["after"].get("fsm") or "").upper()
    rec["verdict"] = "COMPLETED" if fsm == "COMPLETED" else f"NOT-COMPLETED ({fsm or 'unknown'})"
    if rec["after"].get("uuid") != rec["before"].get("uuid"):
        rec["verdict"] += " -- UUID CHANGED, the fixture identity is lost"

    if not args.no_snapshot and fsm == "COMPLETED":
        rec["snapshot"] = _req("POST", "/v1/snapshots", {})
        print(f"snapshot: http {rec['snapshot']['http']} {str(rec['snapshot']['body'])[:300]}", flush=True)

    _write(args.out, rec)
    print(f"=> {rec['verdict']}  (record -> {args.out})", flush=True)
    return 0 if fsm == "COMPLETED" else 1


def _write(path: str, rec: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2, default=str)


if __name__ == "__main__":
    sys.exit(main())
