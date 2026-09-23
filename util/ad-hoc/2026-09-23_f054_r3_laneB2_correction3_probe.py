#!/usr/bin/env python
"""F-CANOPY-054 round 3, Lane B2: what does v3's correction (3) -- the widened "write nothing" return -- change?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation (independent-agent consensus, round 3, Lane B2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: canopy#670 v2 = 85415f3c, v3 = a967a5bd (REPLAY_CONTROLS_JS);
         util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py (the node driver reused here)

v3 changed the early return from ``tickSeen && ...`` to ``order.length > 0 && ...``. To isolate (3),
each scenario runs on three builds read from git OBJECTS: v2, v3, and "v3-minus-3" = v3 with that one
condition put back to ``order.indexOf("tick") >= 0`` (tickSeen's exact meaning). Scenarios, each the
renderer's delivery (triggered list + Inputs + State) of one reachable situation:
  S1  mount (triggered [], the layout's default state) -- must render.
  S2  tab rebuild, a pre-rebuild TICK request survives rDuplicates (:2992-2996 drops the initial call
      when not alone) -- what renders, against the layout defaults.
  S3  tab rebuild, a pre-rebuild PLAY click request survives -- fresh state, re-created button (count 0).
  S4  a skipped trigger after a refill grew the history (the thumb is stale) -- does anything re-render?
  S5  a user drag merged out-and-back to exactly slider_w: (a) playing at row 0 before any tick,
      (b) playing at row 37 of 100 (an integer slider_w), (c) stopped at the end (slider_w 100).
The layout defaults the page shows when nothing renders (metrics_panel.py @ a967a5bd): position spans
"0" / "0", play label "▶", slider value 0 max 100, interval disabled, metrics-store data [].
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("repro", str(HERE / "2026-09-23_f054_r2_laneB2_node_repro.py"))
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)

NEW_RET = "if (order.length > 0 && !controlFired && !ticked && !sliderReset) {"
OLD_RET = 'if (order.indexOf("tick") >= 0 && !controlFired && !ticked && !sliderReset) {'

DRIVER = r"""
globalThis.window = {dash_clientside: {no_update: {description: 'no_update'}}};
const NU = window.dash_clientside.no_update;
const fn = eval('(' + process.argv[2] + ')');
const cases = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const BUTTONS = ['replay-play','replay-step-back','replay-step-forward','replay-start','replay-end','speed-1x','speed-2x','speed-4x'];
const out = {};
for (const [name, c] of Object.entries(cases)) {
  const counts = BUTTONS.map(b => (c.clicks && b in c.clicks) ? c.clicks[b] : null);
  window.dash_clientside.callback_context = {triggered: c.triggered.map(p => ({prop_id: 'metrics-panel-' + p, value: null}))};
  const r = fn.apply(null, counts.concat([c.slider, c.n, JSON.parse(JSON.stringify(c.state)), c.metrics]));
  delete window.dash_clientside.callback_context;
  const all = r.every(v => v === NU);
  out[name] = all ? 'NO_UPDATE x8' : {mode: r[0] === NU ? 'nu' : r[0].mode, index: r[0] === NU ? 'nu' : r[0].current_index,
     disabled: r[1] === NU ? 'nu' : r[1], slider: r[3] === NU ? 'nu' : Math.round(r[3] * 1000) / 1000,
     pos: (r[5] === NU ? 'nu' : r[5]) + ' / ' + (r[6] === NU ? 'nu' : r[6]), label: r[7] === NU ? 'nu' : r[7]};
}
console.log(JSON.stringify(out));
"""


def cases():
    default = {"mode": "stopped", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": None}
    m50 = [{"epoch": i} for i in range(50)]
    m80 = [{"epoch": i} for i in range(80)]
    m101 = [{"epoch": i} for i in range(101)]
    paused20 = {"mode": "paused", "speed": 1.0, "current_index": 20, "start_index": 0, "end_index": 49, "tick_n": 4, "clicks": {"replay-play": 2, "replay-step-forward": 3}, "slider_w": 20 / 49 * 100}
    return {
        "S1 mount": {"triggered": [], "clicks": {}, "slider": 0, "n": 0, "state": default, "metrics": []},
        "S1b mount, history already filled": {"triggered": [], "clicks": {}, "slider": 0, "n": 0, "state": default, "metrics": m50},
        "S2 rebuild, stale tick survives": {"triggered": ["replay-interval.n_intervals"], "clicks": {}, "slider": 0, "n": 0, "state": default, "metrics": []},
        "S3 rebuild, stale play click survives": {"triggered": ["replay-play.n_clicks"], "clicks": {}, "slider": 0, "n": 0, "state": default, "metrics": []},
        "S4 skipped step trigger after refill 50->80": {"triggered": ["replay-step-forward.n_clicks"], "clicks": {"replay-play": 2, "replay-step-forward": 3}, "slider": paused20["slider_w"], "n": 4, "state": paused20, "metrics": m80},
        "S5a playing row 0, drag out-and-back to 0": {"triggered": ["replay-slider.value"], "clicks": {"replay-play": 1}, "slider": 0, "n": 9, "state": {"mode": "playing", "speed": 1.0, "current_index": 0, "start_index": 0, "end_index": 100, "tick_n": 9, "clicks": {"replay-play": 1}, "slider_w": 0}, "metrics": m101},
        "S5b playing row 37/100, drag back to 37": {"triggered": ["replay-slider.value"], "clicks": {"replay-play": 1}, "slider": 37, "n": 9, "state": {"mode": "playing", "speed": 1.0, "current_index": 37, "start_index": 0, "end_index": 100, "tick_n": 9, "clicks": {"replay-play": 1}, "slider_w": 37}, "metrics": m101},
        "S5c stopped at end, drag back to 100": {"triggered": ["replay-slider.value"], "clicks": {"replay-play": 1}, "slider": 100, "n": 9, "state": {"mode": "stopped", "speed": 1.0, "current_index": 100, "start_index": 0, "end_index": 100, "tick_n": 9, "clicks": {"replay-play": 1}, "slider_w": 100}, "metrics": m101},
    }


def main():
    v2, _ = repro.load("85415f3c")
    v3, _ = repro.load("a967a5bd")
    assert v3.count(NEW_RET) == 1, "v3 early return not found"
    builds = {"v2": v2, "v3": v3, "v3-minus-3": v3.replace(NEW_RET, OLD_RET)}
    node = shutil.which("node")
    with tempfile.TemporaryDirectory() as d:
        cp = Path(d) / "c.json"
        cp.write_text(json.dumps(cases()), encoding="utf-8")
        drv = Path(d) / "d.js"
        drv.write_text(DRIVER, encoding="utf-8")
        res = {b: json.loads(subprocess.run([node, str(drv), js, str(cp)], capture_output=True, text=True, check=True).stdout) for b, js in builds.items()}
    for name in cases():
        print(f"== {name}")
        for b in builds:
            print(f"   {b:11s} {res[b][name]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
