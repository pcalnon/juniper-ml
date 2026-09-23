#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""The §3.1 replay block, M-METRICS-11..16 and -18, re-driven on a COMPLETED fixture.

WHY. Segment 15 (2026-08-20) scored the seven replay-transport rows BLOCKED: the
controls revealed at COMPLETED but ``metrics-panel-replay-position`` stayed ``0 / 0``,
so ``max_index = 0`` clamped every index transition and none had an observable.
M-METRICS-13 -- the play toggle -- was named the discriminator because its
observable is DATA-INDEPENDENT (the icon flips to ⏸ and ``replay-interval`` is
enabled whatever the store holds), and it too failed then, with zero wire output
across 196 responses. Whether that was a third face of F-CANOPY-027 (the pre-Stage-2
poller starvation, since fixed) or its own defect was left open.

WHAT THE SOURCE SAYS, read 2026-09-08 (``metrics_panel.py:982-1099``): all three
replay callbacks -- ``handle_replay_controls``, ``replay_tick``, ``update_replay_ui``
-- compute ``max_index = len(metrics_data) - 1 if metrics_data else 0`` from
``State(metrics-panel-metrics-store)``. So the index rows are downstream of the
F-CANOPY-035 store (empty -> every transition clamps to 0), while the play toggle
(``mode`` flip -> ``update_play_button`` -> ⏸, and ``replay-interval.disabled``)
and the speed buttons (``interval = 1000/speed``) are not.

WHAT THIS DRIVES, on the Training Metrics tab with training COMPLETED:

  M-METRICS-13  click ▶: play button text ▶ -> ⏸, ``replay-interval.disabled`` -> false,
                ``replay-state.mode`` -> playing; click again -> back. Wire: a
                ``/_dash-update-component`` response naming ``replay-state``.
  M-METRICS-16  click 2x / 4x / 1x: ``replay-interval.interval`` -> 500 / 250 / 1000.
  M-METRICS-11/-12/-14/-15/-18
                ⏮ / ◀ / step-forward / ⏭ / slider: ``current_index`` and the position
                text. With ``max_index`` 0 these are expected to CLAMP; the row is
                then scored BLOCKED with the blocker named (F-035), not FAIL -- the
                callback ran and did what its code says for an empty store.

Every prop is read off dash-renderer's layout through ``paths.strs`` (the arc's
store reader), never guessed from the DOM.

Usage:
    JUNIPER_E2E_CANOPY_URL=http://127.0.0.1:8052 \\
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        util/ad-hoc/2026-09-08_replay_block_redrive.py
"""

import argparse
import importlib.util
import json
import os
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
_seg17 = _load("_seg17drv", "e2e_seg17_topology_driver.py")
_f039 = _load("_f039supt", "e2e_f039_supersession_test.py")
SETPROPS = _f039.SETPROPS

log = _w3.log
CANOPY = _w3.CANOPY
serving_commit = _w3.serving_commit
open_dashboard = _seg17.open_dashboard
_store = _seg17._store
open_tab = _f027.open_tab
ensure_no_modal = _f027.ensure_no_modal
vis = _f027.vis
shot = _f027.shot

MP = "metrics-panel"
OUT = os.environ.get("REPLAY_RESULTS", "/tmp/juniper-e2e/replay_block.json")


def _prop(page, comp_id: str, prop: str):
    return page.evaluate(
        """(a) => { const [id, prop] = a;
             const st = window.store && window.store.getState ? window.store.getState() : null;
             if (!st || !st.layout) return null;
             const strs = st.paths && st.paths.strs ? st.paths.strs : null;
             if (!strs || !strs[id]) return null;
             let node = st.layout;
             for (const key of strs[id]) { if (node == null) break; node = node[key]; }
             if (!node || !node.props) return null;
             return node.props[prop] === undefined ? null : node.props[prop]; }""",
        [comp_id, prop],
    )


def _snap(page) -> dict:
    ms = (_store(page, f"{MP}-metrics-store") or {}).get("value")
    rs = (_store(page, f"{MP}-replay-state") or {}).get("value")
    return {
        "metrics_store_len": len(ms) if isinstance(ms, list) else None,
        "replay_state": rs if isinstance(rs, dict) else rs,
        "position": (vis(page, f"{MP}-replay-position") or {}).get("text"),
        "play_text": (vis(page, f"{MP}-replay-play") or {}).get("text"),
        "interval_disabled": _prop(page, f"{MP}-replay-interval", "disabled"),
        "interval_ms": _prop(page, f"{MP}-replay-interval", "interval"),
        "slider_value": _prop(page, f"{MP}-replay-slider", "value"),
        "controls": {k: v for k, v in (vis(page, f"{MP}-replay-controls") or {}).items() if k in ("present", "display", "h")},
    }


def _click(page, comp_id: str) -> bool:
    return page.evaluate(
        """(id) => { const el = document.getElementById(id); if (!el) return false; el.click(); return true; }""",
        comp_id,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settle", type=float, default=4.0, help="seconds to wait after each click")
    ap.add_argument("--fill-budget", type=float, default=45.0, help="seconds to wait for the metrics store to fill before driving")
    ap.add_argument("--park-metrics-poll", action="store_true",
                    help="after the fill, set metrics-store-interval.interval to 1e9 ms (NOT disabled -- the CAN-000 gate and the "
                         "#614 strand watchdog both write disabled) so update_metrics_store stops cycling, then drive. "
                         "One variable: tests the claimed-Input promotion block hypothesis for F-CANOPY-048.")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    capture: list = []
    res: dict = {"canopy": CANOPY, "serving": serving_commit(), "steps": []}
    log(f"serving: {json.dumps(res['serving'])}")

    # 2026-09-22 (still-owed item 2a): the SERVER's side of every replay-state write.
    # "the controls never apply" has three branches -- the handler never ran, it ran
    # and returned an unchanged state, or it returned the new state and the renderer
    # discarded it -- and only the response bodies separate them.
    replay_resp: list = []

    def on_response(resp):
        if "_dash-update-component" not in resp.url:
            return
        try:
            out_ids = {t.split("@", 1)[0] for t in str((resp.request.post_data_json or {}).get("output") or "").strip(".").split("...") if t}
        except Exception:  # noqa: BLE001
            return
        if f"{MP}-replay-state.data" not in out_ids:
            return
        try:
            rmap = (json.loads(resp.text()) or {}).get("response") or {}
        except Exception:  # noqa: BLE001
            replay_resp.append({"t": time.time(), "unparsed": True})
            return
        data = (rmap.get(f"{MP}-replay-state") or {}).get("data") if f"{MP}-replay-state" in rmap else None
        replay_resp.append({"t": time.time(), "carried": f"{MP}-replay-state" in rmap,
                            "mode": data.get("mode") if isinstance(data, dict) else None,
                            "current_index": data.get("current_index") if isinstance(data, dict) else None})

    def step(page, label: str, comp: str | None, expect: str):
        before = _snap(page)
        r0 = len(replay_resp)
        n0 = len(capture)
        clicked = _click(page, f"{MP}-{comp}") if comp else None
        page.wait_for_timeout(int(args.settle * 1000))
        after = _snap(page)
        reqs = [c for c in capture[n0:] if "_dash-update-component" in (c.get("url") or "")]
        naming = [c for c in reqs if "replay" in (c.get("body") or "")]
        rec = {"label": label, "component": comp, "clicked": clicked, "expect": expect, "before": before, "after": after, "requests": len(reqs), "requests_naming_replay": len(naming),
               "replay_state_responses": replay_resp[r0:]}
        res["steps"].append(rec)
        log(f"  {label}: clicked={clicked} play={before['play_text']!r}->{after['play_text']!r} pos={before['position']!r}->{after['position']!r} "
            f"disabled={before['interval_disabled']}->{after['interval_disabled']} interval={before['interval_ms']}->{after['interval_ms']} "
            f"mode={(before['replay_state'] or {}).get('mode') if isinstance(before['replay_state'], dict) else before['replay_state']}->"
            f"{(after['replay_state'] or {}).get('mode') if isinstance(after['replay_state'], dict) else after['replay_state']} "
            f"idx={(after['replay_state'] or {}).get('current_index') if isinstance(after['replay_state'], dict) else None} reqs={len(reqs)}/{len(naming)}")
        return rec

    with sync_playwright() as pw:
        browser, _ctx, page = open_dashboard(pw, capture)
        page.on("response", on_response)
        try:
            ensure_no_modal(page)
            open_tab(page, "Training Metrics")
            page.wait_for_timeout(6000)
            # 2026-09-22: WAIT FOR THE FILL before driving. On a leg carrying the
            # F-CANOPY-035 fix (canopy#613) the store fills DURING page load -- 7-12 s
            # after the observer, and later under load -- so the 09-11 run read it EMPTY
            # here, filled to 66 mid-run, and scored every index row against the stale
            # empty read (re-attributing them to a finding that no longer blocked them).
            t_fill = time.time()
            while (_snap(page).get("metrics_store_len") or 0) == 0 and time.time() - t_fill < args.fill_budget:
                page.wait_for_timeout(1000)
            res["fill"] = {"waited_s": round(time.time() - t_fill, 1), "len_after_wait": _snap(page).get("metrics_store_len")}
            log(f"  fill wait: {res['fill']}")
            if args.park_metrics_poll:
                park = {"setprops": page.evaluate(SETPROPS, {"id": "metrics-store-interval", "payload": {"interval": 1_000_000_000}})}
                page.wait_for_timeout(12000)  # let any in-flight poll cycle finish and apply
                park["interval_prop"] = _prop(page, "metrics-store-interval", "interval")
                park["n0"] = _prop(page, "metrics-store-interval", "n_intervals")
                page.wait_for_timeout(8000)
                park["n1"] = _prop(page, "metrics-store-interval", "n_intervals")
                park["stopped"] = park["n0"] == park["n1"] and park["interval_prop"] == 1_000_000_000
                res["park_metrics_poll"] = park
                log(f"  park metrics poll: {park}")
            res["initial"] = _snap(page)
            log(f"  initial: {json.dumps(res['initial'])[:400]}")
            shot(page, "REPLAY__initial.png")

            s13a = step(page, "M-METRICS-13 play", "replay-play", "play text -> ⏸, interval enabled, mode playing")
            s13b = step(page, "M-METRICS-13 pause", "replay-play", "play text -> ▶, interval disabled, mode paused")
            s16_2 = step(page, "M-METRICS-16 2x", "speed-2x", "interval -> 500")
            s16_4 = step(page, "M-METRICS-16 4x", "speed-4x", "interval -> 250")
            s16_1 = step(page, "M-METRICS-16 1x", "speed-1x", "interval -> 1000")
            s14 = step(page, "M-METRICS-14 step-forward", "replay-step-forward", "index +1 capped at max_index")
            s12 = step(page, "M-METRICS-12 step-back", "replay-step-back", "index -1 floored at 0")
            s15 = step(page, "M-METRICS-15 end", "replay-end", "index -> end_index")
            s11 = step(page, "M-METRICS-11 start", "replay-start", "index -> start_index (0)")
            # M-METRICS-18: the slider. Drive its value through the component (Radix-free:
            # dcc.Slider) via setProps on the rendered handle is unreliable; use the
            # keyboard on the focused handle, which plotly-dash's rc-slider honours.
            before18 = _snap(page)
            r18 = len(replay_resp)
            n0 = len(capture)
            moved = page.evaluate(
                f"""() => {{ const el = document.getElementById('{MP}-replay-slider');
                       if (!el) return false;
                       const h = el.querySelector('[role=slider]') || el.querySelector('.rc-slider-handle');
                       if (!h) return false; h.focus();
                       return true; }}"""
            )
            if moved:
                for _ in range(10):
                    page.keyboard.press("ArrowRight")
                    page.wait_for_timeout(120)
            page.wait_for_timeout(int(args.settle * 1000))
            after18 = _snap(page)
            reqs18 = [c for c in capture[n0:] if "_dash-update-component" in (c.get("url") or "") and "replay" in (c.get("body") or "")]
            res["steps"].append({"label": "M-METRICS-18 slider", "component": "replay-slider", "clicked": moved, "expect": "value maps to index, mode paused", "before": before18, "after": after18, "requests_naming_replay": len(reqs18),
                                 "replay_state_responses": replay_resp[r18:]})
            log(f"  M-METRICS-18 slider: handle focused={moved} value={before18['slider_value']}->{after18['slider_value']} pos={before18['position']!r}->{after18['position']!r} reqs naming replay={len(reqs18)}")
            shot(page, "REPLAY__after_drive.png")
            res["final"] = _snap(page)
        finally:
            browser.close()

    # --- verdicts, from the rules in the docstring ---
    def mode(s):
        rs = s.get("replay_state")
        return rs.get("mode") if isinstance(rs, dict) else None

    def idx(s):
        rs = s.get("replay_state")
        return rs.get("current_index") if isinstance(rs, dict) else None

    v: dict = {}

    # 2026-09-22: every index row is scored on the store length ITS OWN step saw
    # before its click -- never on the one ``initial`` read, which went stale on the
    # 09-11 run when the store filled mid-drive (0 -> 66).
    def mx(s):
        return max(0, (s["before"].get("metrics_store_len") or 0) - 1)

    def blocked(s):
        return (f"BLOCKED-BY-F-035 (metrics store len {s['before'].get('metrics_store_len')} at this step -> max_index {mx(s)}; "
                "every index transition clamps to 0 in the three replay callbacks' len-1 bound)")

    toggled_on = s13a["after"]["play_text"] == "⏸" and s13a["after"]["interval_disabled"] is False and mode(s13a["after"]) == "playing"
    toggled_off = s13b["after"]["play_text"] == "▶" and s13b["after"]["interval_disabled"] is True and mode(s13b["after"]) == "paused"
    v["M-METRICS-13"] = "PASS" if (toggled_on and toggled_off) else ("FAIL" if s13a["clicked"] else "BLOCKED (button absent)")
    v["M-METRICS-16"] = "PASS" if (s16_2["after"]["interval_ms"] == 500 and s16_4["after"]["interval_ms"] == 250 and s16_1["after"]["interval_ms"] == 1000) else "FAIL"
    # 2026-09-22: NO VACUOUS PASSES. On 09-22 step-back and start "passed" by expecting
    # index 0 from an index that had never left 0, and the slider "passed" because the
    # rc-slider moved its OWN value while the replay state never followed. A row whose
    # expected end state equals its start state proves nothing; it needs the transition.
    # Step targets are RELATIVE to the index the step started from. The first 2026-09-22 repair
    # hard-coded step-forward's target as 1, which is right only from index 0. On a live block,
    # a replay tick can advance the index first, and the run on canopy#658's leg scored a correct
    # 1 -> 2 step as FAIL. Fixed before a fresh run; that run was not re-scored.
    for row, s, want in (("M-METRICS-14", s14, lambda s: min(mx(s), (idx(s["before"]) or 0) + 1)),
                         ("M-METRICS-12", s12, lambda s: max(0, (idx(s["before"]) or 0) - 1)),
                         ("M-METRICS-15", s15, mx), ("M-METRICS-11", s11, lambda s: 0)):
        if mx(s) > 0:
            start = idx(s["before"])
            target = want(s)
            if start is not None and start == target:
                # The index cannot move, so it cannot be the observable. Every one of
                # these controls ALSO writes ``mode = "paused"`` (metrics_panel.py
                # ``handle_replay_controls``), which IS observable from any index.
                if mode(s["after"]) == "paused" and idx(s["after"]) == target:
                    v[row] = f"PASS (index already {start}; the click's paused-mode write applied)"
                else:
                    v[row] = f"FAIL (index already {start}, and the click's write never applied: mode {mode(s['before'])} -> {mode(s['after'])})"
            else:
                v[row] = "PASS" if idx(s["after"]) == target else "FAIL"
        else:
            ran = s["requests_naming_replay"] > 0 and mode(s["after"]) == "paused"
            v[row] = blocked(s) if ran else "FAIL (the click produced no replay-state write)"
    s18 = res["steps"][-1]
    if mx(s18) > 0:
        # The slider must move the REPLAY STATE, not only its own value.
        moved_state = idx(s18["after"]) not in (None, idx(s18["before"])) or s18["after"]["position"] != s18["before"]["position"]
        v["M-METRICS-18"] = "PASS" if moved_state else f"FAIL (slider value {s18['before']['slider_value']} -> {s18['after']['slider_value']} but the replay state/position never followed)"
    else:
        v["M-METRICS-18"] = blocked(s18) if s18["requests_naming_replay"] > 0 or s18["clicked"] else "BLOCKED (slider handle not focusable)"
    res["verdicts"] = v
    # Which branch of "never applies": per step, did the server's response CARRY a
    # replay-state write, and with what mode?
    res["server_side_by_step"] = {
        s["label"]: {"responses": len(s.get("replay_state_responses") or []),
                     "carried": sum(1 for r in (s.get("replay_state_responses") or []) if r.get("carried")),
                     "modes": [r.get("mode") for r in (s.get("replay_state_responses") or []) if r.get("carried")]}
        for s in res["steps"]}
    for lab, ss in res["server_side_by_step"].items():
        log(f"  server side  {lab:28s}: responses={ss['responses']} carried={ss['carried']} modes={ss['modes']}")
    res["max_index_by_step"] = {s["label"]: mx(s) for s in res["steps"]}
    res["max_index"] = mx(res["steps"][0])
    log("")
    for k, val in v.items():
        log(f"  => {k}: {val}")
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    log(f"results -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
