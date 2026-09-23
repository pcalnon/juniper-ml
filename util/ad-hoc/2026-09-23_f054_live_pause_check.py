#!/usr/bin/env python
"""F-CANOPY-054 on a LIVE canopy leg: does a pause hold? Every replay-state write, read off the store.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (F-CANOPY-054, Phase 8);
         util/ad-hoc/2026-09-23_f054_replay_tick_cleanroom.py (the same rule, no canopy)

WHY NOT THE REPLAY PROBE. ``2026-09-08_replay_block_redrive.py`` reads the state once, ``settle``
seconds after each click. F-CANOPY-054 is a SEQUENCE -- a ``paused`` write, then a late ``playing``
write -- and the probe's 2026-09-22 run 2 ended ``paused`` after exactly that sequence. So this check
subscribes to dash-renderer's Redux store and records every change of the replay state's
``(mode, current_index)`` and of ``replay-interval.disabled``, stamped, for the whole run. The path
is resolved through ``paths.strs`` at each change (a lookup, not a layout walk: the page's main
thread is ~0.1% idle, and a walk per store change would perturb what it measures).

ONE RUN: a fresh browser context; the Training Metrics tab; wait until the metrics store holds
rows; click play and wait until a ``playing`` state is applied (PLAY_BUDGET_S); wait PLAY_S; click
play again (the pause); watch SETTLE_S, F-CANOPY-004's 16 s interaction contract.

VERDICT RULE, per run -- FIXED BEFORE THE FIRST RUN (the clean room's, plus one category):

  PLAY-NEVER-APPLIED  no 'playing' state within PLAY_BUDGET_S of the play click; the pause is not
                      driven and the run is not scored.
  PAUSE-HELD          a 'paused' state applied after the pause click, no 'playing' state applied
                      after it, the final mode is not 'playing', and the index did not change in the
                      last 8 s.
  F054-UNDONE         a 'paused' state applied after the click, and a 'playing' state after that.
  CLICK-DROPPED       no 'paused' state applied within the settle.
  OTHER               anything else.

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (3 runs a leg, GPU browser, trio 2/68/2, uuid 1cd15120):

  :8056 serving canopy main 2f973ca2 (the parent; negative control): F054-UNDONE in at least 2 of 3.
  :8055 serving the fix: PAUSE-HELD in 3/3; the pause applied within 2 s of the click in 3/3; the
       index advanced during play in 3/3; the DOM label and position agree with the store at the
       end in 3/3.

If the negative control does not show F054-UNDONE, the live check does not discriminate and the
fix leg's result is recorded as consistent with the fix, not as evidence for it.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8055 JUNIPER_E2E_BROWSER_GPU=1 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_live_pause_check.py --runs 3 \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_live_pause_8055.json
"""

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_w3 = _load("_w3drv", "e2e_w3_params_driver.py")
_f027 = _load("_f027drv", "e2e_f027_redrive.py")

log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal

MP = "metrics-panel"
PLAY_BUDGET_S = 30.0
PLAY_S = 10.0
SETTLE_S = 16.0

WATCH = """
() => {
  const st = window.store;
  if (!st || typeof st.getState !== 'function') return {found: false};
  const at = (id, prop) => {
    const s = st.getState();
    const path = s.paths && s.paths.strs ? s.paths.strs[id] : null;
    if (!path) return undefined;
    let node = s.layout;
    for (const key of path) { if (node == null) return undefined; node = node[key]; }
    return node && node.props ? node.props[prop] : undefined;
  };
  window.__f054 = {series: [], disabled: [], n: 0};
  let last = null, lastDis = null;
  const sample = () => {
    window.__f054.n += 1;
    const rs = at('metrics-panel-replay-state', 'data');
    const key = rs ? (rs.mode + '|' + rs.current_index) : 'null';
    if (key !== last) { last = key; window.__f054.series.push([Date.now(), rs ? rs.mode : null, rs ? rs.current_index : null]); }
    const d = at('metrics-panel-replay-interval', 'disabled');
    if (d !== lastDis) { lastDis = d; window.__f054.disabled.push([Date.now(), d]); }
  };
  sample();
  st.subscribe(sample);
  return {found: true};
}
"""

STORE_LEN = """() => { const st = window.store; if (!st) return null; const s = st.getState();
  const path = s.paths && s.paths.strs ? s.paths.strs['metrics-panel-metrics-store'] : null; if (!path) return null;
  let node = s.layout; for (const key of path) { if (node == null) return null; node = node[key]; }
  const d = node && node.props ? node.props.data : null; return Array.isArray(d) ? d.length : null; }"""


def _click(page, comp_id: str) -> bool:
    return page.evaluate("(id) => { const el = document.getElementById(id); if (!el) return false; el.click(); return true; }", comp_id)


def _dom(page) -> list:
    return page.evaluate(
        f"() => [Date.now(), (document.getElementById('{MP}-replay-play') || {{}}).textContent || null, (document.getElementById('{MP}-replay-position') || {{}}).textContent || null]"
    )


def _one_run(pw) -> dict:
    capture: list = []
    obs: dict = {"serving": serving_commit()}
    browser, _ctx, page = open_dashboard(pw, capture)
    try:
        ensure_no_modal(page)
        open_tab(page, "Training Metrics")
        t_fill = time.time()
        while (page.evaluate(STORE_LEN) or 0) == 0 and time.time() - t_fill < 60:
            page.wait_for_timeout(1000)
        obs["store_len"] = page.evaluate(STORE_LEN)
        obs["fill_wait_s"] = round(time.time() - t_fill, 1)
        obs["watch"] = page.evaluate(WATCH)
        if not obs["watch"].get("found"):
            return {**obs, "verdict": "OTHER", "why": "redux store not reachable"}
        page.wait_for_timeout(2000)
        obs["dom_before"] = _dom(page)

        obs["t_play"] = page.evaluate("Date.now()")
        obs["play_clicked"] = _click(page, f"{MP}-replay-play")
        t0 = time.time()
        while time.time() - t0 < PLAY_BUDGET_S:
            series = page.evaluate("window.__f054.series")
            if any(r[1] == "playing" and r[0] >= obs["t_play"] for r in series):
                break
            page.wait_for_timeout(250)
        series = page.evaluate("window.__f054.series")
        playing = [r for r in series if r[1] == "playing" and r[0] >= obs["t_play"]]
        if not playing:
            rec = page.evaluate("window.__f054")
            return {**obs, "series": rec["series"], "disabled": rec["disabled"], "verdict": "PLAY-NEVER-APPLIED"}
        obs["play_latency_ms"] = playing[0][0] - obs["t_play"]
        page.wait_for_timeout(int(PLAY_S * 1000))

        obs["t_pause"] = page.evaluate("Date.now()")
        obs["pause_clicked"] = _click(page, f"{MP}-replay-play")
        dom = []
        t_end = time.time() + SETTLE_S
        while time.time() < t_end:
            dom.append(_dom(page))
            page.wait_for_timeout(250)
        obs["dom"] = dom
        rec = page.evaluate("window.__f054")
        obs["series"], obs["disabled"], obs["store_changes"] = rec["series"], rec["disabled"], rec["n"]
    finally:
        browser.close()

    series = obs["series"]
    t_pause, t_end_ms = obs["t_pause"], obs["t_pause"] + SETTLE_S * 1000
    at_pause = [r for r in series if r[0] < t_pause]
    i_at_pause = at_pause[-1][2] if at_pause else None
    i_play = next((r[2] for r in series if r[0] >= obs["t_play"] and r[1] == "playing"), None)
    after = [r for r in series if r[0] >= t_pause]
    paused_at = next((r for r in after if r[1] == "paused"), None)
    playing_after = [r for r in after if paused_at and r[0] > paused_at[0] and r[1] == "playing"]
    final = series[-1]
    last8 = [r for r in series if r[0] >= t_end_ms - 8000]
    if paused_at and playing_after:
        verdict = "F054-UNDONE"
    elif paused_at is None:
        verdict = "CLICK-DROPPED"
    elif final[1] != "playing" and len({r[2] for r in last8}) <= 1:
        verdict = "PAUSE-HELD"
    else:
        verdict = "OTHER"
    dom_last = obs["dom"][-1] if obs["dom"] else [None, None, None]
    exp_label = "⏸" if final[1] == "playing" else "▶"
    obs.update(
        {
            "verdict": verdict,
            "pause_latency_ms": (paused_at[0] - t_pause) if paused_at else None,
            "steps_during_play": (i_at_pause - i_play) if (i_at_pause is not None and i_play is not None) else None,
            "final_mode": final[1],
            "final_index": final[2],
            "final_interval_disabled": obs["disabled"][-1][1] if obs["disabled"] else None,
            "dom_last": dom_last[1:],
            "dom_label_agrees": dom_last[1] == exp_label,
            "dom_position_index_agrees": isinstance(dom_last[2], str) and dom_last[2].split(" / ")[0] == str(final[2]),
            "writes_after_pause": [[r[0] - t_pause, r[1], r[2]] for r in after],
        }
    )
    return obs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": serving_commit(), "play_s": PLAY_S, "settle_s": SETTLE_S, "runs": []}
    log(f"canopy {CANOPY} serving {json.dumps(res['serving'])}")
    with sync_playwright() as pw:
        for i in range(args.runs):
            r = _one_run(pw)
            res["runs"].append(r)
            log(
                f"  run {i + 1}: {r['verdict']:18s} play_lat={r.get('play_latency_ms')} pause_lat={r.get('pause_latency_ms')} steps_play={r.get('steps_during_play')} "
                f"final={r.get('final_mode')}/{r.get('final_index')} disabled={r.get('final_interval_disabled')} dom={r.get('dom_last')} "
                f"label_ok={r.get('dom_label_agrees')} pos_ok={r.get('dom_position_index_agrees')} after_pause={r.get('writes_after_pause')}"
            )
    res["verdicts"] = [r["verdict"] for r in res["runs"]]
    log(f"=> verdicts: {res['verdicts']}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
