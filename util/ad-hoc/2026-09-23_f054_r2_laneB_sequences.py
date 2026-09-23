#!/usr/bin/env python
"""canopy#670 round 2 (Lane B): run v1 and v2 replay JavaScript (from git OBJECTS) under node over
multi-run SEQUENCES -- each run is fed the state the previous run wrote -- to find what the v2
corrections broke at the logic level.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 (F-CANOPY-054); util/ad-hoc/2026-09-23_f054_r2_laneB_cleanroom.py

A RUN is one execution of the controls callback: (triggered prop ids, n_clicks per button, slider
value, n_intervals, state, metrics). The renderer decides which runs happen; this harness only asks
what the JavaScript does with each sequence of runs. Whether the renderer can produce a sequence is
shown separately, in the browser clean room.

Usage:
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_sequences.py --objects <canopy .git/objects>
"""

import argparse
import ast
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gitobj", HERE / "2026-09-23_f054_r2_laneB_gitobj.py")
gitobj = importlib.util.module_from_spec(_spec)
sys.modules["gitobj"] = gitobj
_spec.loader.exec_module(gitobj)

P = "metrics-panel-"
BUTTONS = ["replay-play", "replay-step-back", "replay-step-forward", "replay-start", "replay-end", "speed-1x", "speed-2x", "speed-4x"]
TICK = P + "replay-interval.n_intervals"
M50 = [{"e": i} for i in range(50)]


def trig(*names):
    return [TICK if n == "tick" else (P + n + (".value" if n == "replay-slider" else ".n_clicks")) for n in names]


def load(store, ref):
    body = store.blob_at(store.resolve(ref), "src/frontend/components/metrics_panel.py")[1].decode()
    tree = ast.parse(body)
    js = ids = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "REPLAY_CONTROLS_JS":
            js = ast.literal_eval(node.value)
        if isinstance(node, ast.ClassDef) and node.name == "MetricsPanel":
            for b in node.body:
                if isinstance(b, ast.AnnAssign) and getattr(b.target, "id", None) == "REPLAY_CONTROL_IDS":
                    ids = ast.literal_eval(b.value)
    return js.replace("__PREFIX__", json.dumps(P)).replace("__CONTROLS__", json.dumps(list(ids)))


def run_seq(node, js, runs):
    """runs: list of dicts {trig, clicks{button:n}, slider, n, metrics, state?}. state None => carry
    the previous run's written state (or the initial layout state)."""
    driver = (
        "globalThis.window = {dash_clientside: {}};\n"
        "const NU = {nu: 1}; window.dash_clientside.no_update = NU;\n"
        f"const fn = ({js});\n"
        "const runs = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));\n"
        "let state = {mode: 'stopped', speed: 1.0, current_index: 0, start_index: 0, end_index: null};\n"
        "const BUT = " + json.dumps(BUTTONS) + ";\n"
        "const out = [];\n"
        "for (const r of runs) {\n"
        "  if (r.state) state = r.state;\n"
        "  window.dash_clientside.callback_context = {triggered: r.trig.map(p => ({prop_id: p, value: null}))};\n"
        "  const args = BUT.map(b => (r.clicks && b in r.clicks) ? r.clicks[b] : null).concat([r.slider === 'NaN' ? NaN : r.slider, r.n, JSON.parse(JSON.stringify(state)), r.metrics]);\n"
        "  const res = fn.apply(null, args);\n"
        "  const wrote = res[0] !== NU;\n"
        "  if (wrote) state = res[0];\n"
        "  out.push({wrote, mode: state.mode, index: state.current_index, clicks: state.clicks || null, slider_w: state.slider_w, slider_out: res[3] === NU ? 'NU' : res[3], label: res[res.length - 1] === NU ? 'NU' : res[res.length - 1], disabled: res[1] === NU ? 'NU' : res[1]});\n"
        "}\n"
        "console.log(JSON.stringify(out));\n"
    )
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "d.js").write_text(driver, encoding="utf-8")
        (Path(d) / "r.json").write_text(json.dumps(runs), encoding="utf-8")
        p = subprocess.run([node, str(Path(d) / "d.js"), str(Path(d) / "r.json")], capture_output=True, text=True, timeout=60)
        if p.returncode:
            raise RuntimeError(p.stderr)
        return json.loads(p.stdout)


def sequences():
    """Each: (name, description, intent, runs)."""
    S = []
    # the state a playing replay has after one play click at n_intervals 10, slider at index 7 of 49
    playing = {"mode": "playing", "speed": 1.0, "current_index": 7, "start_index": 0, "end_index": 49, "tick_n": 10, "clicks": {b: 0 for b in BUTTONS} | {"replay-play": 1}, "slider_w": 7 / 49 * 100}
    paused = dict(playing, mode="paused")
    S.append(("double_pause", "Pause clicked (play n_clicks 1->2). A queued TICK request runs first (the renderer freed a slot before processing the click's request): it sees the count and applies the pause. Then the click's OWN request runs, triggered by replay-play, count unchanged.", "paused",
              [{"state": playing, "trig": trig("tick"), "clicks": {"replay-play": 2}, "slider": 7 / 49 * 100, "n": 11, "metrics": M50},
               {"trig": trig("replay-play"), "clicks": {"replay-play": 2}, "slider": "carry", "n": 11, "metrics": M50}]))
    S.append(("double_step", "Paused at 7. step-forward clicked once (0->1). A queued speed-1x request runs first and applies the step by count; the click's own request runs after.", "index 8",
              [{"state": paused, "trig": trig("speed-1x"), "clicks": {"replay-play": 1, "speed-1x": 1, "replay-step-forward": 1}, "slider": 7 / 49 * 100, "n": 11, "metrics": M50},
               {"trig": trig("replay-step-forward"), "clicks": {"replay-play": 1, "speed-1x": 1, "replay-step-forward": 1}, "slider": "carry", "n": 11, "metrics": M50}]))
    S.append(("pause_then_resume_lost", "Playing. The user pauses, then resumes (play 1->3); both triggers lost to a tick request.", "playing (last click = resume)",
              [{"state": playing, "trig": trig("tick"), "clicks": {"replay-play": 3}, "slider": 7 / 49 * 100, "n": 11, "metrics": M50}]))
    S.append(("step_then_play_lost", "Playing. The user steps forward (pauses) then presses play to resume; both triggers lost to a tick request.", "playing, index 8",
              [{"state": playing, "trig": trig("tick"), "clicks": {"replay-play": 2, "replay-step-forward": 1}, "slider": 7 / 49 * 100, "n": 11, "metrics": M50}]))
    S.append(("play_then_stepback_lost_while_paused", "Paused. The user presses play, then step-back (pauses again); both lost to a later click's request of speed-2x.", "paused, index 6",
              [{"state": paused, "trig": trig("speed-2x"), "clicks": {"replay-play": 2, "replay-step-back": 1, "speed-2x": 1}, "slider": 7 / 49 * 100, "n": 11, "metrics": M50}]))
    S.append(("state_without_new_keys", "A state lacking clicks/slider_w (the layout default, or a pre-v2 state) while the buttons already carry counts (play 3, step-forward 2); a tick runs.", "no spurious action",
              [{"state": {"mode": "playing", "speed": 1.0, "current_index": 7, "start_index": 0, "end_index": 49, "tick_n": 10}, "trig": trig("tick"), "clicks": {"replay-play": 3, "replay-step-forward": 2}, "slider": 7 / 49 * 100, "n": 11, "metrics": M50}]))
    S.append(("mount_none_counts", "Mount: n_clicks None everywhere, state without new keys, no trigger.", "renders, records clicks 0 and slider_w",
              [{"state": {"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None}, "trig": [], "clicks": {}, "slider": 0, "n": 0, "metrics": M50}]))
    S.append(("shrunk_store_tick", "Playing at 30 with end_index latched at 49; the store shrinks to 20 rows. Two ticks.", "a slider value > 100 is written and recorded",
              [{"state": dict(playing, current_index=30, slider_w=30 / 49 * 100), "trig": trig("tick"), "clicks": {"replay-play": 1}, "slider": 30 / 49 * 100, "n": 11, "metrics": M50[:20]},
               {"trig": trig("tick"), "clicks": {"replay-play": 1}, "slider": "carry", "n": 12, "metrics": M50[:20]}]))
    S.append(("clamped_echo", "Same, but the slider component echoes a CLAMPED 100 (only if dcc.Slider clamps and re-emits; the browser arm decides whether it does).", "not a seek",
              [{"state": dict(playing, current_index=31, slider_w=31 / 19 * 100), "trig": trig("replay-slider"), "clicks": {"replay-play": 1}, "slider": 100, "n": 12, "metrics": M50[:20]}]))
    S.append(("nan_then_tick", "Cleared number box (NaN) whose trigger is LOST to a tick request.", "no NaN in the state; slider restored",
              [{"state": paused, "trig": trig("tick"), "clicks": {"replay-play": 1}, "slider": "NaN", "n": 11, "metrics": M50}]))
    S.append(("end_with_lost_pause", "Playing at 48 (end 49). The pause's trigger is lost to the tick that would reach the end.", "paused at 48",
              [{"state": dict(playing, current_index=48, slider_w=48 / 49 * 100), "trig": trig("tick"), "clicks": {"replay-play": 2}, "slider": 48 / 49 * 100, "n": 11, "metrics": M50}]))
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", required=True)
    a = ap.parse_args()
    node = shutil.which("node")
    store = gitobj.Store(a.objects)
    builds = {"v1": load(store, "c0530279"), "v2": load(store, "85415f3c")}
    for name, desc, intent, runs in sequences():
        print(f"\n== {name}: {desc}\n   intent: {intent}")
        for v, js in builds.items():
            # 'carry' slider: feed the previous run's written slider value
            rr, prev = [], None
            res = []
            for r in runs:
                r = dict(r)
                if r["slider"] == "carry":
                    r["slider"] = prev if isinstance(prev, (int, float)) else 0
                out = run_seq(node, js, rr + [r])
                prev = out[-1]["slider_out"] if out[-1]["slider_out"] != "NU" else r["slider"]
                rr.append(dict(r, state=None) if rr else r)
                res = out
            print(f"   {v}: " + " -> ".join(f"[{o['mode']} idx={o['index']} wrote={o['wrote']} slider={round(o['slider_out'], 2) if isinstance(o['slider_out'], (int, float)) else o['slider_out']} label={o['label']}]" for o in res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
