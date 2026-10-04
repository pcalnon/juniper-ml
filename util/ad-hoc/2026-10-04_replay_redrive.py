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
"""Live re-drive of the CAN-015 replay player against a WRITABLE cascor (still-owed item 16).

Verifies, in one browser session on the throwaway stack that
``util/ad-hoc/2026-10-04_replay_redrive_stack.bash`` brings up (data 8113 / cascor 8214 / canopy 8063):

  F-CANOPY-059  a replay started from the Snapshots tab renders the player's ACTIVE view
                (canopy#694): before, ``render_session`` raised ``KeyError: 0``.
  F-CANOPY-015  the weights badge, range and speed are read from ``data.session`` (canopy#532).
  F-CANOPY-056  play / seek / speed / range results reach the player, and Stop ends the session
                (canopy#696).
  echo loop     an idle player, and each single control, send no further ``/replay/control``
                requests (canopy#697; the ``can015-replay-player-control-loop`` exemption).
  range end     the sliders stop at the last frame (``length - 1``) and a narrowed range
                round-trips through cascor's exclusive end (canopy#697).
  after         Start works after the replay ended.

Requests are counted in CASCOR's uvicorn access log, so they are what reached cascor, not what the
page meant to send. Slider values are read from the Radix thumb's ``aria-valuenow`` /
``aria-valuemax``; readouts from the DOM text, polled to a deadline (one sample after a sleep is not
a settled reading).

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-10-04_replay_redrive.py --run-dir <stack run dir> --out <evidence dir>
"""

import argparse
import json
import pathlib
import re
import time
from typing import Any, Callable

import requests

DATA = "http://127.0.0.1:8113"
CASCOR = "http://127.0.0.1:8214"
CANOPY = "http://127.0.0.1:8063"
CID = "replay-player-panel"

# A short fit: enough epochs for a replayable history, small enough to finish in a minute or two.
# max_epochs and output_epochs are set together (AGENTS.md hazard).
CASCOR_CAPS = {"nn_max_iterations": 12, "nn_output_epochs": 40, "nn_max_total_epochs": 40, "cn_training_iterations": 20, "nn_max_hidden_units": 32}

CONTROL_RE = re.compile(r'"POST /v1/snapshots/[^/\s]+/replay/control HTTP/1\.1" (\d{3})')


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Evidence:
    def __init__(self, out: pathlib.Path) -> None:
        self.out = out
        out.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = []
        self.notes: dict[str, Any] = {"started": utc_now()}

    def row(self, name: str, verdict: str, detail: Any) -> None:
        self.rows.append({"check": name, "verdict": verdict, "detail": detail, "at": utc_now()})
        print(f"[{verdict}] {name}: {detail}", flush=True)

    def save(self) -> None:
        self.notes["finished"] = utc_now()
        (self.out / "verdicts.json").write_text(json.dumps({"notes": self.notes, "rows": self.rows}, indent=2, default=str) + "\n")


def control_requests(log: pathlib.Path) -> list[str]:
    """Every /replay/control status code cascor logged, in order."""
    with open(log, encoding="utf-8", errors="replace") as fh:
        return CONTROL_RE.findall(fh.read())


def poll(fn: Callable[[], Any], ok: Callable[[Any], bool], deadline_s: float, step_s: float = 0.25) -> tuple[bool, Any]:
    end = time.time() + deadline_s
    value = None
    while True:
        try:
            value = fn()
        except Exception as exc:  # noqa: BLE001 -- a read that fails is a reading, not a crash
            value = f"<error {exc!r}>"
        if ok(value):
            return True, value
        if time.time() > end:
            return False, value
        time.sleep(step_s)


# ---------------------------------------------------------------------------
# API setup: a fit that leaves snapshots
# ---------------------------------------------------------------------------


def api_session() -> tuple[requests.Session, dict[str, str]]:
    s = requests.Session()
    csrf = s.get(f"{CANOPY}/api/csrf", timeout=30).json()
    return s, {"Origin": CANOPY, "X-CSRF-Token": csrf.get("csrf_token", "")}


def train_for_snapshots(ev: Evidence) -> None:
    s, h = api_session()
    calls: dict[str, Any] = {"select": s.post(f"{CANOPY}/api/model/select", json={"nn_model": "cascor"}, headers=h, timeout=120).status_code}
    calls["caps"] = s.post(f"{CANOPY}/api/set_params", json={"nn_model": "cascor", **CASCOR_CAPS}, headers=h, timeout=120).status_code
    state = s.get(f"{CANOPY}/api/state", headers=h, timeout=30).json()
    stage = {"nn_dataset_type": "spirals", "nn_model": "cascor"}
    for key in ("nn_dataset_elements", "nn_dataset_noise", "nn_spiral_rotations", "nn_spiral_number"):
        if state.get(key) is not None:
            stage[key] = state[key]
    calls["stage"] = s.post(f"{CANOPY}/api/stage_dataset", json=stage, headers=h, timeout=180).status_code
    calls["start"] = s.post(f"{CANOPY}/api/train/start", headers=h, timeout=180).status_code
    seen = {"running": False}

    def status() -> dict[str, Any]:
        st = s.get(f"{CANOPY}/api/train/status", headers=h, timeout=30).json()
        seen["running"] = seen["running"] or bool(st.get("is_running") or st.get("is_training"))
        return st

    done, last = poll(status, lambda st: isinstance(st, dict) and seen["running"] and not (st.get("is_running") or st.get("is_training")), 600, 2.0)
    calls["fit_terminal"] = done
    calls["fit_last_status"] = {k: last.get(k) for k in ("fsm_status", "completed", "failed", "current_epoch", "hidden_units")} if isinstance(last, dict) else last
    ev.notes["fit"] = calls
    print(f"fit: {calls}", flush=True)


def newest_snapshot() -> dict[str, Any] | None:
    body = requests.get(f"{CANOPY}/api/v1/snapshots", params={"limit": 5}, timeout=30).json()
    items = body.get("snapshots") or []
    return items[0] if items else None


# ---------------------------------------------------------------------------
# Browser drive
# ---------------------------------------------------------------------------


def drive(ev: Evidence, cascor_log: pathlib.Path, snapshot_id: str) -> bool:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        page.goto(CANOPY, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#visualization-tabs", timeout=60000)
        welcome = page.locator("#welcome-modal-close")
        if welcome.count() and welcome.first.is_visible():
            welcome.first.click(force=True)

        def text(sel: str) -> str:
            loc = page.locator(sel)
            return loc.first.inner_text(timeout=2000) if loc.count() else ""

        def displayed(sel: str) -> bool:
            return bool(page.eval_on_selector(sel, "e => getComputedStyle(e).display !== 'none'"))

        def thumbs(slider: str) -> list[dict[str, Any]]:
            return page.eval_on_selector_all(f"#{CID}-{slider} [role=slider]", "els => els.map(e => ({now: e.getAttribute('aria-valuenow'), min: e.getAttribute('aria-valuemin'), max: e.getAttribute('aria-valuemax')}))")

        def controls() -> list[str]:
            return control_requests(cascor_log)

        # --- start the replay from the Snapshots tab ---
        # A click before dash-renderer is ready is dropped: re-click until the tab reports active.
        def tab_active() -> bool:
            page.locator("#visualization-tabs a[role=tab]", has_text="Snapshots").first.click(force=True)
            time.sleep(1.0)
            return page.locator("#visualization-tabs .active").all_inner_texts() == ["Snapshots"]

        ok, _ = poll(tab_active, bool, 60, 0.5)
        if not ok:
            ev.row("setup: Snapshots tab activates", "BLOCKED", page.locator("#visualization-tabs .active").all_inner_texts())
            return False
        op_sel = f"[id*='\"op\":\"replay\"'][id*='{snapshot_id}']"
        found, _ = poll(lambda: page.locator(op_sel).count(), lambda n: isinstance(n, int) and n > 0, 60, 1.0)
        if not found:
            ev.row("setup: replay button for the snapshot", "BLOCKED", f"no element matching {op_sel}")
            return False
        # The op is a dbc.DropdownMenuItem under the row's "Load ▼" toggle: open the menu first.
        item = page.locator(op_sel).first
        toggle = item.locator("xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' dropdown ')][1]").locator(".dropdown-toggle").first

        def menu_open() -> bool:
            if item.is_visible():
                return True
            toggle.evaluate("e => e.scrollIntoView({block: 'center'})")
            toggle.click(force=True)
            time.sleep(1.0)
            return item.is_visible()

        ok, _ = poll(menu_open, bool, 30, 0.5)
        if not ok:
            ev.row("setup: Load menu opens", "BLOCKED", "the replay item never became visible")
            return False
        item.click(force=True)
        ok, _ = poll(lambda: page.locator("#hdf5-snapshots-panel-restore-confirm").is_visible(), bool, 20)
        if not ok:
            ev.row("setup: confirm modal", "BLOCKED", "confirm button never visible")
            return False
        before_start = len(controls())
        page.locator("#hdf5-snapshots-panel-restore-confirm").click(force=True)

        # --- F-CANOPY-059: the active view renders ---
        ok, _ = poll(lambda: displayed(f"#{CID}-active"), bool, 30)
        idle_shown = displayed(f"#{CID}-idle")
        ev.row("F-CANOPY-059 active view renders for a cascor session", "PASS" if ok and not idle_shown else "FAIL", {"active_displayed": ok, "idle_displayed": idle_shown, "snapshot_id_text": text(f"#{CID}-snapshot-id")})
        if not ok:
            return False
        cascor_status = requests.get(f"{CASCOR}/v1/training/status", timeout=30).json().get("data", {})
        ev.notes["cascor_fsm_after_replay_start"] = (cascor_status.get("state_machine") or {}).get("status")

        # --- F-CANOPY-015 and the window end ---
        scrub = thumbs("scrubber")
        rng = thumbs("range")
        readouts = {"fsm": text(f"#{CID}-fsm-badge"), "weights": text(f"#{CID}-weights-badge"), "epoch": text(f"#{CID}-epoch-readout"), "range": text(f"#{CID}-range-readout"), "speed": text(f"#{CID}-speed-readout")}
        ev.notes["initial_readouts"] = readouts
        ev.notes["initial_thumbs"] = {"scrubber": scrub, "range": rng}
        ev.row("F-CANOPY-015 nested summary read (badge, range, speed)", "PASS" if readouts["weights"] and readouts["range"].startswith("[") and readouts["speed"] else "FAIL", readouts)
        # cascor's replay length is in its log line "Snapshot replay started: <id> (length=N)".
        with open(cascor_log, encoding="utf-8", errors="replace") as fh:
            lengths = re.findall(r"Snapshot replay started: \S+ \(length=(\d+)\)", fh.read())
        length = int(lengths[-1]) if lengths else None
        last_index = scrub[0]["max"] if scrub else None
        expected_max = str(length - 1) if length else None
        ok_window = bool(scrub and rng) and last_index == expected_max and rng[-1]["max"] == expected_max and rng[-1]["now"] == expected_max and readouts["range"] == f"[0, {expected_max}]"
        ev.row("window end: sliders stop at the last frame (length - 1)", "PASS" if ok_window else "FAIL", {"cascor_length": length, "scrubber_max": last_index, "range_thumbs": rng, "range_readout": readouts["range"]})

        # --- echo loop: idle ---
        settle = len(controls())
        time.sleep(15)
        idle_after = len(controls())
        ev.row("echo loop: an idle player sends no control requests", "PASS" if idle_after == settle else "FAIL", {"control_requests_at_start_of_window": settle - before_start, "during_15s_idle": idle_after - settle})

        def act(name: str, do: Callable[[], None], expect: Callable[[], bool], max_requests: int) -> None:
            c0 = len(controls())
            do()
            ok_, _ = poll(lambda: expect(), bool, 15)
            time.sleep(6)  # let any echo arrive
            sent = controls()[c0:]
            verdict = "PASS" if ok_ and 1 <= len(sent) <= max_requests and all(code == "200" for code in sent) else "FAIL"
            ev.row(name, verdict, {"observed": ok_, "control_requests": sent, "status": text(f"#{CID}-status"), "epoch": text(f"#{CID}-epoch-readout"), "range": text(f"#{CID}-range-readout"), "speed": text(f"#{CID}-speed-readout")})

        # --- F-CANOPY-056: controls ---
        act("F-CANOPY-056 play reaches cascor and the status", lambda: page.locator(f"#{CID}-play-btn").click(force=True), lambda: "Playing" in text(f"#{CID}-status"), 1)
        act("F-CANOPY-056 pause", lambda: page.locator(f"#{CID}-pause-btn").click(force=True), lambda: "Paused" in text(f"#{CID}-status"), 1)

        def press(slider: str, idx: int, key: str, n: int) -> Callable[[], None]:
            def _do() -> None:
                thumb = page.locator(f"#{CID}-{slider} [role=slider]").nth(idx)
                for _ in range(n):
                    thumb.press(key)
                    time.sleep(0.4)

            return _do

        # Seek 3 positions from wherever play/pause left the scrubber, in whichever direction has room.
        s_now, s_max = int(thumbs("scrubber")[0]["now"]), int(thumbs("scrubber")[0]["max"])
        if s_max >= 3:
            step_key, seek_to = ("ArrowRight", s_now + 3) if s_now + 3 <= s_max else ("ArrowLeft", s_now - 3)
            act(f"F-CANOPY-056 seek: scrubber {s_now} -> {seek_to} reaches the readout", press("scrubber", 0, step_key, 3), lambda: text(f"#{CID}-epoch-readout").startswith(f"{seek_to} /"), 3)
        else:
            ev.row("F-CANOPY-056 seek", "BLOCKED", f"replay too short to seek 3 (scrubber max {s_max})")
        speed_before = text(f"#{CID}-speed-readout")
        act("F-CANOPY-056 speed change reaches the readout", press("speed", 0, "ArrowRight", 1), lambda: text(f"#{CID}-speed-readout") not in ("", speed_before), 1)
        if last_index is not None and int(last_index) >= 3:
            target = f"[0, {int(last_index) - 2}]"
            act("range end: upper thumb -2 round-trips through cascor's exclusive end", press("range", 1, "ArrowLeft", 2), lambda: text(f"#{CID}-range-readout") == target, 2)
            ev.notes["range_after"] = {"readout": text(f"#{CID}-range-readout"), "thumbs": thumbs("range"), "target": target}

        # --- F-CANOPY-056: Stop ends the session ---
        c0 = len(controls())
        page.locator(f"#{CID}-stop-btn").click(force=True)
        ok, _ = poll(lambda: displayed(f"#{CID}-idle") and not displayed(f"#{CID}-active"), bool, 20)
        time.sleep(6)
        sent = controls()[c0:]
        cascor_status = requests.get(f"{CASCOR}/v1/training/status", timeout=30).json().get("data", {})
        canopy_status = requests.get(f"{CANOPY}/api/status", timeout=30).json()
        ev.row("F-CANOPY-056 Stop returns the player to idle", "PASS" if ok and sent == ["200"] else "FAIL", {"idle_shown": ok, "control_requests": sent, "cascor_fsm": (cascor_status.get("state_machine") or {}).get("status"), "canopy_fsm": canopy_status.get("fsm_status")})
        browser.close()
        return True


def start_after(ev: Evidence) -> None:
    s, h = api_session()
    r = s.post(f"{CANOPY}/api/train/start", headers=h, timeout=180)
    ok, st = poll(lambda: s.get(f"{CANOPY}/api/train/status", headers=h, timeout=30).json(), lambda v: isinstance(v, dict) and bool(v.get("is_running") or v.get("is_training") or v.get("completed")), 60, 1.0)
    ev.row("after: Start works once the replay has ended", "PASS" if r.status_code < 300 and ok else "FAIL", {"start_status": r.status_code, "start_body": r.text[:300], "observed_running_or_completed": ok})
    s.post(f"{CANOPY}/api/train/stop", headers=h, timeout=60)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run-dir", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--skip-train", action="store_true")
    ap.add_argument("--snapshot", help="replay this snapshot id instead of the newest")
    args = ap.parse_args()
    ev = Evidence(args.out)
    ev.notes["health"] = {name: requests.get(f"{url}/v1/health", timeout=30).json() for name, url in (("data", DATA), ("cascor", CASCOR), ("canopy", CANOPY))}
    try:
        if not args.skip_train:
            train_for_snapshots(ev)
        if args.snapshot:
            snap = {"id": args.snapshot}
        else:
            # cascor's automatic per-output-pass snapshots carry NO training history
            # (cascade_correlation.py saves them without include_training_state), so a replay
            # of one has length 0 and nothing to seek. The explicit save (POST /v1/snapshots,
            # manager.save_snapshot) includes it.
            saved = requests.post(f"{CASCOR}/v1/snapshots", json={"description": "replay re-drive"}, timeout=120).json().get("data") or {}
            snap = {"id": saved.get("id"), "explicit_save": saved}
        ev.notes["snapshot"] = snap
        if not snap:
            ev.row("setup: a snapshot exists", "BLOCKED", "no snapshot listed after the fit")
            return 1
        if drive(ev, args.run_dir / "logs" / "juniper-cascor.log", snap.get("id") or snap.get("snapshot_id") or snap.get("name")):
            start_after(ev)
    finally:
        ev.save()
    return 0 if all(r["verdict"] == "PASS" for r in ev.rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
