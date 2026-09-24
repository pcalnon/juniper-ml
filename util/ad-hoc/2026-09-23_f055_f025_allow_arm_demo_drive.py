#!/usr/bin/env python
"""F-CANOPY-055's fix, driven through F-CANOPY-025's allow arm: does the Live Dataset Switch enable? Demo legs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 8, F-CANOPY-055's fix
         direction: "plus a Live Switch allow-arm drive on a leg whose training may be started"; F-CANOPY-025's
         closure block, run 20260825T041134Z); util/ad-hoc/2026-09-23_status_bar_apply_census.py

WHY DEMO LEGS. The allow arm needs a running training, and the arc's trio (cascor :8202, fixture 2/68/2) must not
be touched. A demo-mode canopy runs its own simulated training (``DemoBackend.initialize`` auto-starts it) and keeps
the experimental-functions flag in process, so a leg can hold "flag on + run live" with no cascor at all. Launch
each leg with ``CANOPY_VERIFY_DEMO_MODE=1`` and a cascor URL that points at nothing:

    CANOPY_VERIFY_DEMO_MODE=1 JUNIPER_CANOPY_CASCOR_SERVICE_URL=http://127.0.0.1:9 \\
        bash util/ad-hoc/2026-09-04_canopy_verify_instance.bash up <worktree>/src 8058

THE GATE. ``live-dataset-switch-button`` ships ``disabled=True``. Its only writer is ``update_unified_status_bar``,
which computes ``not (flags.experimental_functions and status.is_running)`` from each of its responses
(``_gate_live_switch_button_handler``). So the button can enable only when a status-bar response APPLIES while the
flag is on and the run is live. F-CANOPY-055: on the shared 1 Hz lane no response applied at all.

PROCEDURE, per leg, one fresh browser each:
  1. POST /api/admin/experimental_functions {"enabled": true}, and read it back.
  2. Confirm /api/status reports is_running (the demo auto-start). If it does not, POST /api/train/start.
  3. Open the dashboard; the fresh mount reads the flag. Sample once a second for --allow-seconds: the button's
     ``disabled`` (DOM), the bar's status and step text (DOM), and the server's is_running and flag.
  4. POST /api/train/stop. Sample for --deny-seconds.
  5. Cleanup: the flag goes back off. The demo run stays stopped.

VERDICT RULE -- FIXED BEFORE THE FIRST RUN.
  ALLOW  LANDS  the button is enabled at any sample at which the server reports is_running and the flag on.
         NEVER  it stays disabled for the whole window, with both true at every sample.
         VOID   anything else (the run or the flag was not held, so there is nothing to judge).
  DENY   RETURNS  after the stop, the button is disabled again at some sample within --deny-seconds.
         STUCK    it stays enabled for the whole window.
         N/A      ALLOW did not land.
  BAR    APPLIES  the bar's status text differs from its layout default ("Stopped") at any sample at which the
                  server reports is_running.
         FROZEN   otherwise.

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (two demo legs, nothing else driving them):
  the fix leg (the F-CANOPY-055 head): ALLOW LANDS within 30 s of the page load; DENY RETURNS; BAR APPLIES.
  the parent leg (``main`` with the idle cuts): ALLOW NEVER and BAR FROZEN, if the demo page's delivery latency
  exceeds the 1 s tick as the trio legs' did. A demo page may run faster than a service page. If its latency
  stays under 1 s, the parent can land too, and then this drive does not discriminate; the census on the trio
  legs remains the discriminating test.

Usage:
    JUNIPER_E2E_BROWSER_GPU=1 LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py --leg fix=http://127.0.0.1:8058 \\
        --leg parent=http://127.0.0.1:8059 \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f055_f025_allow_arm_demo_drive.json
"""

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BUTTON = "live-dataset-switch-button"
STATUS = "top-status-display"
STEP = "top-epoch-display"
STATUS_DEFAULT = "Stopped"

PROBE = """(ids) => { const out = {};
  for (const id of ids) { const el = document.getElementById(id);
    out[id] = el ? {text: (el.innerText || '').trim().slice(0, 80), disabled: el.disabled === true || el.getAttribute('disabled') !== null} : null; }
  return out; }"""


def _http(base: str, method: str, path: str, body=None, timeout: float = 10.0):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310 - loopback test leg
            raw = r.read().decode() or "null"
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:  # noqa: BLE001 - recorded, never raised from a probe
        return None, f"{type(e).__name__}: {e}"[:300]


def _server(base: str) -> dict:
    _c1, st = _http(base, "GET", "/api/status")
    _c2, fl = _http(base, "GET", "/api/admin/experimental_functions")
    st = st if isinstance(st, dict) else {}
    fl = fl if isinstance(fl, dict) else {}
    return {"is_running": bool(st.get("is_running")), "flag": bool((fl.get("data") or {}).get("enabled")), "phase": st.get("phase"), "epoch": st.get("current_epoch")}


def _sample(page, base: str, t0: float) -> dict:
    dom = page.evaluate(PROBE, [BUTTON, STATUS, STEP])
    return {
        "t_s": round(time.time() - t0, 1),
        "button_disabled": (dom.get(BUTTON) or {}).get("disabled"),
        "status_text": (dom.get(STATUS) or {}).get("text"),
        "step_text": (dom.get(STEP) or {}).get("text"),
        **_server(base),
    }


def _verdicts(allow: list, deny: list) -> dict:
    live = [s for s in allow if s["is_running"] and s["flag"]]
    landed = [s for s in live if s["button_disabled"] is False]
    if landed:
        allow_v = "LANDS"
    elif live and len(live) == len(allow):
        allow_v = "NEVER"
    else:
        allow_v = "VOID"
    if allow_v != "LANDS":
        deny_v = "N/A"
    else:
        deny_v = "RETURNS" if any(s["button_disabled"] is True for s in deny) else "STUCK"
    running = [s for s in allow if s["is_running"]]
    bar_v = "APPLIES" if any(s["status_text"] not in (STATUS_DEFAULT, None) for s in running) else "FROZEN"
    return {
        "ALLOW": allow_v,
        "allow_first_enabled_t_s": landed[0]["t_s"] if landed else None,
        "DENY": deny_v,
        "deny_first_disabled_t_s": next((s["t_s"] for s in deny if s["button_disabled"] is True), None),
        "BAR": bar_v,
        "bar_texts_seen": sorted({s["status_text"] for s in allow + deny if s["status_text"] is not None}),
        "step_texts_last": [s["step_text"] for s in allow[-3:]],
    }


def drive(pw, label: str, base: str, args, w3, f027) -> dict:
    os.environ["JUNIPER_E2E_CANOPY_URL"] = base
    w3.CANOPY = base  # open_dashboard navigates to the module-level CANOPY
    log = w3.log
    rec = {"label": label, "base": base, "serving": w3.serving_commit()}
    rec["flag_on"] = _http(base, "POST", "/api/admin/experimental_functions", {"enabled": True})
    srv = _server(base)
    if not srv["is_running"]:
        rec["start"] = _http(base, "POST", "/api/train/start")
        t = time.time()
        while time.time() - t < 15 and not _server(base)["is_running"]:
            time.sleep(0.5)
    rec["server_before_page"] = _server(base)
    log(f"  {label}: server before page {json.dumps(rec['server_before_page'])}")
    browser, _ctx, page = w3.open_dashboard(pw, [])
    errors = []
    page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
    allow, deny = [], []
    try:
        f027.ensure_no_modal(page)
        t0 = time.time()
        while time.time() - t0 < args.allow_seconds:
            allow.append(_sample(page, base, t0))
            page.wait_for_timeout(1000)
        rec["stop"] = _http(base, "POST", "/api/train/stop")
        t1 = time.time()
        while time.time() - t1 < args.deny_seconds:
            deny.append(_sample(page, base, t1))
            page.wait_for_timeout(1000)
    finally:
        browser.close()
        rec["flag_off"] = _http(base, "POST", "/api/admin/experimental_functions", {"enabled": False})
    rec["allow_samples"] = allow
    rec["deny_samples"] = deny
    rec["console_errors"] = errors[:20]
    rec["verdicts"] = _verdicts(allow, deny)
    log(f"  {label} {base} sha={(rec['serving'] or {}).get('git_sha', '')[:8]} => {json.dumps(rec['verdicts'])}")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leg", action="append", required=True, metavar="LABEL=URL", help="repeatable; driven in the order given")
    ap.add_argument("--allow-seconds", type=float, default=60.0)
    ap.add_argument("--deny-seconds", type=float, default=45.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    w3 = _load("_w3drv", "e2e_w3_params_driver.py")
    f027 = _load("_f027drv", "e2e_f027_redrive.py")

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "allow_seconds": args.allow_seconds, "deny_seconds": args.deny_seconds, "legs": []}
    with sync_playwright() as pw:
        for spec in args.leg:
            label, _, base = spec.partition("=")
            res["legs"].append(drive(pw, label, base, args, w3, f027))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    w3.log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
