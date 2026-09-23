#!/usr/bin/env python
"""F-CANOPY-054 round 2, Lane B2: logic-level reproductions against canopy#670 v2 (85415f3c), under node.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation (independent-agent consensus, round 2, Lane B2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy fix/f054-replay-block-clientside (canopy#670) v2 = local commit 85415f3c;
         util/ad-hoc/2026-09-23_f054_r2_laneB2_double_apply_cleanroom.py (the live-renderer half)

Reads REPLAY_CONTROLS_JS from a git OBJECT (default 85415f3c), injects the prefix and control list
exactly as register_callbacks does, and calls it under node with the arguments the renderer delivers
in each sequence below. Each case states the input sequence; the output is what v2 writes.

  D1  double application: run A is a tick request that executes AFTER the click's setProps (so it
      reads the new n_clicks) but before the click's own request runs; run B is the click's own
      request (triggered = the button). v2 applies the click in A (by count) and again in B
      (``times = max(pending, triggered ? 1 : 0)`` = 1 with pending 0).
  D2  the same for step-forward: one click, two steps.
  D3  slider: a lost seek applied by count in A, then its own trigger in B reads the value A wrote
      back; trunc() of the round trip idx/max*100/100*max can land one index low.
  D4  the one-toggle rule versus a repeat click whose first click was already recovered by a tick.

Usage:
    python util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py [--ref 85415f3c]
"""

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CANOPY = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--f054-replay-block-clientside--20260923-0036--2f973ca2"
MP_PATH = "src/frontend/components/metrics_panel.py"
P = "metrics-panel-"


def load(ref):
    src = subprocess.run(["git", "-C", CANOPY, "show", f"{ref}:{MP_PATH}"], capture_output=True, text=True, check=True).stdout
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) == "REPLAY_CONTROLS_JS":
            out["js"] = ast.literal_eval(node.value)
        if isinstance(node, ast.ClassDef) and node.name == "MetricsPanel":
            for b in node.body:
                if isinstance(b, ast.AnnAssign) and getattr(b.target, "id", None) == "REPLAY_CONTROL_IDS":
                    out["ids"] = ast.literal_eval(b.value)
    return out["js"].replace("__PREFIX__", json.dumps(P)).replace("__CONTROLS__", json.dumps(list(out["ids"]))), out["ids"]


DRIVER = r"""
globalThis.window = {dash_clientside: {no_update: {description: 'no_update'}}};
const NU = window.dash_clientside.no_update;
const fn = eval('(' + process.argv[2] + ')');
const seqs = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const BUTTONS = ['replay-play','replay-step-back','replay-step-forward','replay-start','replay-end','speed-1x','speed-2x','speed-4x'];
const out = {};
for (const [name, seq] of Object.entries(seqs)) {
  let state = JSON.parse(JSON.stringify(seq.state));
  let slider = seq.slider;
  const steps = [];
  for (const run of seq.runs) {
    const counts = BUTTONS.map(b => (run.clicks && b in run.clicks) ? run.clicks[b] : 0);
    const s = ('slider' in run) ? run.slider : slider;
    window.dash_clientside.callback_context = {triggered: run.triggered.map(p => ({prop_id: 'metrics-panel-' + p, value: null}))};
    const r = fn.apply(null, counts.concat([s, run.n, JSON.parse(JSON.stringify(state)), seq.metrics]));
    delete window.dash_clientside.callback_context;
    if (r[0] !== NU) { state = r[0]; }
    if (r[3] !== NU) { slider = r[3]; }
    steps.push({note: run.note, triggered: run.triggered, mode: state.mode, index: state.current_index, clicks: state.clicks, slider_written: r[3] === NU ? 'no_update' : r[3], label: r[7] === NU ? 'no_update' : r[7]});
  }
  out[name] = steps;
}
console.log(JSON.stringify(out));
"""


def seqs():
    m50 = [{"epoch": i} for i in range(50)]
    playing = {"mode": "playing", "speed": 4.0, "current_index": 20, "start_index": 0, "end_index": None, "tick_n": 11, "clicks": {"replay-play": 1, "speed-4x": 1}, "slider_w": 20 / 49 * 100}
    paused = {"mode": "paused", "speed": 1.0, "current_index": 20, "start_index": 0, "end_index": 49, "tick_n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 0}, "slider_w": 20 / 49 * 100}
    out = {
        "D1_pause_applied_twice": {
            "state": playing, "slider": playing["slider_w"], "metrics": m50,
            "runs": [
                {"note": "A: a tick request that was waiting in `prioritized` executes after the pause click's setProps (n_clicks 1->2); the click's own request is still in `requested`", "triggered": ["replay-interval.n_intervals"], "n": 12, "clicks": {"replay-play": 2, "speed-4x": 1}},
                {"note": "B: the pause click's OWN request runs next (triggered = play), same n_clicks", "triggered": ["replay-play.n_clicks"], "n": 12, "clicks": {"replay-play": 2, "speed-4x": 1}},
            ],
        },
        "D2_one_step_forward_click_moves_two": {
            "state": paused, "slider": paused["slider_w"], "metrics": m50,
            "runs": [
                {"note": "A: another request of the callback (e.g. a speed click's) runs after the step click's setProps: step is pending by count", "triggered": ["speed-2x.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 1, "speed-2x": 1}},
                {"note": "B: the step click's own request runs", "triggered": ["replay-step-forward.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 1, "speed-2x": 1}},
            ],
        },
    }
    return out


def slider_round_trip_census():
    js = r"""
let bad = 0, total = 0, ex = [];
for (let max = 1; max <= 2000; max++) {
  for (let idx = 0; idx <= max; idx++) {
    total++;
    const q = idx / max * 100;               // what v2 writes to the slider and to slider_w
    const back = Math.trunc((q / 100) * max); // what a slider trigger carrying q seeks to
    if (back !== idx) { bad++; if (ex.length < 6) ex.push([idx, max, q, back]); }
  }
}
console.log(JSON.stringify({bad, total, examples: ex}));
"""
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="85415f3c")
    args = ap.parse_args()
    node = shutil.which("node")
    assert node, "node is required"
    js, ids = load(args.ref)
    assert "state.clicks = seen;" in js, "not the v2 source"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "seqs.json"
        p.write_text(json.dumps(seqs()), encoding="utf-8")
        drv = Path(d) / "drv.js"
        drv.write_text(DRIVER, encoding="utf-8")
        res = json.loads(subprocess.run([node, str(drv), js, str(p)], capture_output=True, text=True, check=True).stdout)
    print(f"source: {args.ref}:{MP_PATH}")
    for name, steps in res.items():
        print(f"== {name}")
        for s in steps:
            print(f"   {s['note']}")
            print(f"      -> mode={s['mode']} index={s['index']} clicks={s['clicks']} label={s['label']}")
    census = slider_round_trip_census()
    print("== D3 slider round trip: a slider TRIGGER carrying the value v2 itself wrote seeks to trunc(q/100*max)")
    print(f"   (idx, max) pairs, max 1..2000: {census['bad']} of {census['total']} land one index low; e.g. [idx, max, q, seek] {census['examples']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
