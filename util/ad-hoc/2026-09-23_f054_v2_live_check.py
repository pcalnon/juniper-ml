#!/usr/bin/env python
"""F-CANOPY-054 v2 on a LIVE leg: clicks DURING PLAYBACK at 1x and 4x, with the renderer queue instrumented.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 8);
         util/ad-hoc/2026-09-23_f054_live_pause_check.py (v1's live check: 3 pauses, 1x, no queue instrument);
         util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py (the controlled-contention discrimination)

WHY A SECOND LIVE CHECK. Round 1 found the v1 live evidence thin: only 4 clicks were made during playback,
all of them pauses at 1x, and every other control was driven while paused, so none was exposed to the
slot contention that drops a queued click (Lane B2). Nothing recorded the pool at the click (Lane B). And
tick counting was never exercised, because every live step was +1 (Lane B2). This check drives every
click DURING PLAYBACK and records, per click:
  * the pool at the click (``executing`` + ``watched``);
  * whether the controls callback's request carrying the click was seen in ``prioritized``, and whether a
    run carrying it was ever seen executing (``executing``/``watched``). A click that applies with no such
    run is RECOVERED: it came from the count, not the trigger.
It is not a discrimination test between v1 and v2 -- the clean room is. It shows whether v2 behaves on
the real page, and whether the real page produces the replacement at all.

PROTOCOL (one browser, GPU, one page load, Training Metrics, after the metrics store fills):
  speed-1x, then 5 PAUSE trials; speed-4x, then 5 PAUSE trials, 2 STEP trials (step-forward during
  playback) and 2 SEEK trials (the slider set to 30% and to 70% during playback, through setProps -- the
  component's own path). Each trial: play, wait for a ``playing`` state (30 s), 2-4 s of playback, the
  click, then a 16 s watch (F-CANOPY-004's interaction contract). Every control used here pauses the
  replay (``REPLAY_CONTROLS_JS``: step, start, end and a seek all set ``paused``).

VERDICT RULE, per trial -- FIXED BEFORE THE FIRST RUN:
  APPLIED     a ``paused`` state applied within 16 s of the click, no ``playing`` state after it within the
              watch, and the final mode not ``playing``. For SEEK, in addition: the paused index equals
              trunc(pct / 100 * max_index). For STEP, in addition: the paused index is above the index
              held just before the click.
  UNDONE      ``paused`` applied, then ``playing`` again (F-CANOPY-054's own signature).
  DROPPED     no ``paused`` within 16 s, and the index advanced after the click.
  STARVED     no ``paused`` within 16 s, and the index did not advance.
  WRONG       paused, but at the wrong index (SEEK/STEP only).
  VOID        play never applied within 30 s; the trial is not driven.
Overall: PASS if every non-VOID trial is APPLIED and at least 10 trials are non-VOID; else FAIL.

PREDICTIONS -- FIXED BEFORE THE FIRST RUN (:8055 serving 85415f3c, the trio 2/68/2, idle, one browser):
  * PASS, 14 of 14 APPLIED.
  * the pause median latency below 3 s (v1 measured 1.42-2.35 s at 1x);
  * the pool at the click at or above 1 in most trials (the page is saturated, Phase 7);
  * RECOVERED in 0-3 trials. If 0, the live page did not produce the replacement in this sample, and the
    clean room stays the only evidence for the recovery path. That is not a failure;
  * tick counting exercised: some 4x trial shows a single ``playing`` write advancing the index by >= 2;
  * the DOM label and position agree with the store at the end of every trial.

RUN LOG (2026-09-23, ``…_f054_v2_live_check_8055.json``, :8055 serving 85415f3c):
  PASS, 14 of 14 APPLIED. Pause median 1979.5 ms (max 2406 ms). Pool at the click 5-11 in 14 of 14, never 12;
  RECOVERED 0; the DOM agreed with the store in 14 of 14. Scored against the predictions: PASS held;
  median below 3 s held; pool >= 1 held; RECOVERED 0 lies in the predicted 0-3 range, so the live page did
  not produce the replacement; tick counting exercised MISSED, with every 4x write advancing by one row;
  DOM agreement held. That run's ``console_errors`` field is WRONG: it filtered ``capture``, which holds
  request records, and so kept 3 POSTs whose output names contain "error". The run's log shows 0
  ``CONSOLE[error]`` lines. Fixed afterwards: console errors now come from ``page.on("console")``.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8055 JUNIPER_E2E_BROWSER_GPU=1 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-23_f054_v2_live_check.py \\
        --out reports/e2e-canopy-2026-09-02/transcripts/2026-09-23_f054_v2_live_check_8055.json
"""

import argparse
import importlib.util
import json
import random
import statistics
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
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")

log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
open_dashboard = _w3.open_dashboard
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal
SETPROPS = _f039.SETPROPS

MP = "metrics-panel"
PLAY_BUDGET_S = 30.0
WATCH_S = 16.0

WATCH = """
() => {
  const st = window.store;
  if (!st || typeof st.getState !== 'function') return {found: false};
  const CTL = 'metrics-panel-replay-state.data';
  const isCtl = cb => { const o = cb && cb.callback && cb.callback.output; return typeof o === 'string' && o.indexOf(CTL) >= 0; };
  const at = (s, id, prop) => {
    const path = s.paths && s.paths.strs ? s.paths.strs[id] : null;
    if (!path) return undefined;
    let node = s.layout;
    for (const key of path) { if (node == null) return undefined; node = node[key]; }
    return node && node.props ? node.props[prop] : undefined;
  };
  window.__v2 = {state: [], q: [], pool: [], n: 0};
  let lastS = null, lastQ = null, lastP = null;
  const sample = () => {
    const s = st.getState(); const now = Date.now(); window.__v2.n += 1;
    const rs = at(s, 'metrics-panel-replay-state', 'data');
    const ks = rs ? (rs.mode + '|' + rs.current_index + '|' + rs.speed) : 'null';
    if (ks !== lastS) { lastS = ks; window.__v2.state.push([now, rs ? rs.mode : null, rs ? rs.current_index : null, rs ? rs.speed : null]); }
    const cbs = s.callbacks || {};
    const pool = (cbs.executing || []).length + (cbs.watched || []).length;
    if (pool !== lastP) { lastP = pool; window.__v2.pool.push([now, pool]); }
    const snap = {};
    for (const q of ['requested', 'prioritized', 'blocked', 'executing', 'watched']) {
      const arr = (cbs[q] || []).filter(isCtl).map(cb => Object.keys(cb.changedPropIds || {}).map(x => x.replace('metrics-panel-', '')).join('+'));
      if (arr.length) snap[q] = arr;
    }
    const kq = JSON.stringify(snap);
    if (kq !== lastQ) { lastQ = kq; window.__v2.q.push([now, pool, snap]); }
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


def _dom(page) -> dict:
    return page.evaluate(
        f"() => ({{label: (document.getElementById('{MP}-replay-play') || {{}}).textContent || null, position: (document.getElementById('{MP}-replay-position') || {{}}).textContent || null}})"
    )


def _last_state(page):
    return page.evaluate("() => { const r = window.__v2.state; return r[r.length - 1] || null; }")


def _wait_mode(page, mode: str, since: int, budget_s: float):
    t_end = time.time() + budget_s
    while time.time() < t_end:
        hit = page.evaluate(f"() => window.__v2.state.find(r => r[0] >= {since} && r[1] === '{mode}') || null")
        if hit:
            return hit
        page.wait_for_timeout(50)
    return None


def _settle_paused(page) -> bool:
    for _ in range(4):
        cur = _last_state(page)
        if cur and cur[1] != "playing":
            return True
        t = page.evaluate("Date.now()")
        _click(page, f"{MP}-replay-play")
        if _wait_mode(page, "paused", t, 16):
            return True
    return False


def _trial(page, kind: str, pct: int, max_index: int) -> dict:
    rec = {"kind": kind, "pct": pct}
    if not _settle_paused(page):
        rec.update(verdict="VOID", why="could not settle to a non-playing mode")
        return rec
    t_play = page.evaluate("Date.now()")
    _click(page, f"{MP}-replay-play")
    if not _wait_mode(page, "playing", t_play, PLAY_BUDGET_S):
        rec.update(verdict="VOID", why="play never applied")
        return rec
    page.wait_for_timeout(int(random.uniform(2.0, 4.0) * 1000))
    before = _last_state(page)
    t_click = page.evaluate("Date.now()")
    if kind == "pause":
        _click(page, f"{MP}-replay-play")
    elif kind == "step":
        _click(page, f"{MP}-replay-step-forward")
    else:
        rec["setprops"] = page.evaluate(SETPROPS, {"id": f"{MP}-replay-slider", "payload": {"value": pct}})
    page.wait_for_timeout(int(WATCH_S * 1000))
    win = int(WATCH_S * 1000)
    after = page.evaluate(f"() => window.__v2.state.filter(r => r[0] >= {t_click} && r[0] <= {t_click} + {win})")
    first_paused = next((r for r in after if r[1] == "paused"), None)
    replayed = first_paused is not None and any(r[1] == "playing" and r[0] > first_paused[0] for r in after)
    final = _last_state(page)
    rec.update(t_click=t_click, index_before=before[2] if before else None, final=final)
    if first_paused is None:
        advanced = before is not None and any(r[2] is not None and r[2] > before[2] for r in after)
        rec["verdict"] = "DROPPED" if advanced else "STARVED"
    elif replayed or (final and final[1] == "playing"):
        rec["verdict"] = "UNDONE"
    else:
        rec["latency_ms"] = first_paused[0] - t_click
        rec["paused_index"] = first_paused[2]
        ok = True
        if kind == "seek":
            rec["expected_index"] = int(pct / 100 * max_index)
            ok = first_paused[2] == rec["expected_index"]
        elif kind == "step":
            ok = before is not None and first_paused[2] > before[2]
        rec["verdict"] = "APPLIED" if ok else "WRONG"
    # the queue around the click: seen waiting, seen running, recovered
    q = page.evaluate(f"() => window.__v2.q.filter(r => r[0] >= {t_click} - 50 && r[0] <= {t_click} + {win})")
    tag = {"pause": "replay-play", "step": "replay-step-forward", "seek": "replay-slider"}[kind]
    in_prio = [r for r in q if any(tag in x for x in r[2].get("prioritized", []))]
    ran = [r for r in q if any(tag in x for x in r[2].get("executing", []) + r[2].get("watched", []))]
    pools = page.evaluate(f"() => window.__v2.pool.filter(r => r[0] <= {t_click}).slice(-1)")
    rec.update(pool_at_click=pools[0][1] if pools else None, click_seen_in_prioritized=bool(in_prio), click_executed=bool(ran), recovered=rec["verdict"] == "APPLIED" and bool(in_prio) and not ran)
    # tick counting: the largest single-write advance while playing, between play and the click
    play_writes = page.evaluate(f"() => window.__v2.state.filter(r => r[0] >= {t_play} && r[0] < {t_click})")
    steps = [b[2] - a[2] for a, b in zip(play_writes, play_writes[1:]) if a[2] is not None and b[2] is not None and b[1] == "playing" and b[2] > a[2]]
    rec["max_step_while_playing"] = max(steps) if steps else 0
    rec["steps_while_playing"] = len(steps)
    dom = _dom(page)
    exp_label = "▶" if final and final[1] != "playing" else "⏸"
    rec["dom"] = dom
    rec["dom_agrees"] = bool(final) and dom.get("label") == exp_label and (dom.get("position") or "").split(" / ")[0].strip() == str(final[2])
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    random.seed(args.seed)

    from playwright.sync_api import sync_playwright

    res = {"probe": Path(__file__).name, "canopy": CANOPY, "serving": serving_commit(), "trials": []}
    log(f"canopy {CANOPY} serving {json.dumps(res['serving'])}")
    plan = [("speed", "speed-1x")] + [("pause", 0)] * 5 + [("speed", "speed-4x")] + [("pause", 0)] * 5 + [("step", 0)] * 2 + [("seek", 30), ("seek", 70)]
    capture: list = []
    console_errors: list = []
    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        page.on("console", lambda m: console_errors.append(m.text[:300]) if m.type == "error" else None)
        try:
            ensure_no_modal(page)
            open_tab(page, "Training Metrics")
            t_fill = time.time()
            while (page.evaluate(STORE_LEN) or 0) == 0 and time.time() - t_fill < 90:
                page.wait_for_timeout(500)
            rows = page.evaluate(STORE_LEN) or 0
            res["store_len"] = rows
            res["fill_wait_s"] = round(time.time() - t_fill, 1)
            res["watch"] = page.evaluate(WATCH)
            if not res["watch"].get("found") or rows == 0:
                log("!! store not reachable or empty")
                return 2
            max_index = rows - 1
            for kind, arg in plan:
                if kind == "speed":
                    _settle_paused(page)
                    _click(page, f"{MP}-{arg}")
                    page.wait_for_timeout(3000)
                    log(f"  speed -> {arg}: state {json.dumps(_last_state(page))}")
                    continue
                rec = _trial(page, kind, arg, max_index)
                rec["speed_state"] = (rec.get("final") or [None, None, None, None])[3]
                res["trials"].append(rec)
                log(f"  {kind}{('@' + str(arg)) if kind == 'seek' else ''}: {rec['verdict']} lat={rec.get('latency_ms')} pool={rec.get('pool_at_click')} prio={rec.get('click_seen_in_prioritized')} exec={rec.get('click_executed')} recovered={rec.get('recovered')} maxstep={rec.get('max_step_while_playing')} dom_ok={rec.get('dom_agrees')}")
            # ``capture`` holds REQUEST records only; console messages arrive through page.on("console").
            res["console_errors"] = console_errors[:50]
            res["console_error_count"] = len(console_errors)
        finally:
            browser.close()
    scored = [t for t in res["trials"] if t["verdict"] != "VOID"]
    lat = [t["latency_ms"] for t in scored if t["kind"] == "pause" and t.get("latency_ms") is not None]
    res["summary"] = {
        "non_void": len(scored),
        "verdicts": {v: sum(1 for t in res["trials"] if t["verdict"] == v) for v in sorted({t["verdict"] for t in res["trials"]})},
        "pause_latency_ms_median": statistics.median(lat) if lat else None,
        "pause_latency_ms_max": max(lat) if lat else None,
        "pool_ge_1_at_click": sum(1 for t in scored if (t.get("pool_at_click") or 0) >= 1),
        "recovered": sum(1 for t in scored if t.get("recovered")),
        "max_step_while_playing_4x": max((t.get("max_step_while_playing") or 0) for t in scored if t.get("speed_state") == 4.0) if any(t.get("speed_state") == 4.0 for t in scored) else None,
        "dom_agrees": sum(1 for t in scored if t.get("dom_agrees")),
    }
    res["overall"] = "PASS" if len(scored) >= 10 and all(t["verdict"] == "APPLIED" for t in scored) else "FAIL"
    log(f"SUMMARY {json.dumps(res['summary'])}")
    log(f"=> OVERALL: {res['overall']}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
