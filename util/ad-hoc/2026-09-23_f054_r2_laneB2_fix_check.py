#!/usr/bin/env python
"""F-CANOPY-054 round 2, Lane B2: the proposed minimal change to canopy#670 v2, checked under node.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation (independent-agent consensus, round 2, Lane B2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: canopy#670 v2 = local commit 85415f3c; util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py

THE CHANGE (two statements in REPLAY_CONTROLS_JS, applied textually to the git object's source):
  1. ``times = max(pending, triggered ? 1 : 0)`` -> ``times = pending`` for a button, and an event whose
     count was already applied is SKIPPED. A trigger only orders events; the count decides them.
  2. a slider trigger is a seek only if its value differs from ``slider_w`` (or none was written yet):
     the value this callback wrote itself, arriving late as a trigger, is not the user's.
Checks, each a sequence of runs with the renderer's delivery (triggered list + current Inputs):
  D1  tick run consumes the pause by count, then the click's own trigger run  -> must stay paused
  D2  another run consumes the step by count, then the step's own trigger     -> one step, not two
  D3  a tick run applies a lost seek, then the seek's own trigger (value = the one written) -> no drift
  and v2's own intent, re-run on the changed code: a lost pause applies at the next tick; two merged
  step clicks step twice; a single click of each control still applies; a triggered click with a count
  increment applies exactly once.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("repro", str(Path(__file__).parent / "2026-09-23_f054_r2_laneB2_node_repro.py"))
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)

OLD_TIMES = 'var times = (ev === "replay-slider") ? 1 : Math.max(pending[ev], inTriggers[ev] ? 1 : 0);'
NEW_TIMES = ('var times = (ev === "replay-slider") ? 1 : pending[ev];\n'
             '        if (ev !== "replay-slider" && times <= 0) { continue; }  // already applied by count in an earlier run\n'
             '        if (ev === "replay-slider" && typeof state.slider_w === "number" && sliderValue === state.slider_w) { continue; }  // our own write, late')


def main():
    js_v2, _ids = repro.load("85415f3c")
    assert js_v2.count(OLD_TIMES) == 1, "anchor not found"
    variants = {"v2": js_v2, "v2+fix": js_v2.replace(OLD_TIMES, NEW_TIMES)}
    m50 = [{"epoch": i} for i in range(50)]
    m4 = [{"epoch": i} for i in range(4)]  # max index 3: (idx 1, max 3) is in the drift census
    playing = {"mode": "playing", "speed": 4.0, "current_index": 20, "start_index": 0, "end_index": None, "tick_n": 11, "clicks": {"replay-play": 1, "speed-4x": 1}, "slider_w": 20 / 49 * 100}
    paused = {"mode": "paused", "speed": 1.0, "current_index": 20, "start_index": 0, "end_index": 49, "tick_n": 11, "clicks": {"replay-play": 2}, "slider_w": 20 / 49 * 100}
    playing4 = {"mode": "playing", "speed": 4.0, "current_index": 0, "start_index": 0, "end_index": None, "tick_n": 11, "clicks": {"replay-play": 1}, "slider_w": 0.0}
    seqs = {
        "D1 pause by count, then its own trigger": {"state": playing, "slider": playing["slider_w"], "metrics": m50, "runs": [
            {"note": "tick", "triggered": ["replay-interval.n_intervals"], "n": 12, "clicks": {"replay-play": 2, "speed-4x": 1}},
            {"note": "own trigger", "triggered": ["replay-play.n_clicks"], "n": 12, "clicks": {"replay-play": 2, "speed-4x": 1}}]},
        "D2 step by count, then its own trigger": {"state": paused, "slider": paused["slider_w"], "metrics": m50, "runs": [
            {"note": "speed run", "triggered": ["speed-2x.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 1, "speed-2x": 1}},
            {"note": "own trigger", "triggered": ["replay-step-forward.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 1, "speed-2x": 1}}]},
        "D3 lost seek, then its own trigger": {"state": playing4, "slider": 40.0, "metrics": m4, "runs": [
            {"note": "tick (slider moved to 40 by the user: index trunc(1.2) = 1)", "triggered": ["replay-interval.n_intervals"], "n": 12, "clicks": {"replay-play": 1}},
            {"note": "own trigger, carrying the value the tick run wrote", "triggered": ["replay-slider.value"], "n": 12, "clicks": {"replay-play": 1}}]},
        "keep: lost pause applies at the next tick": {"state": playing, "slider": playing["slider_w"], "metrics": m50, "runs": [
            {"note": "tick", "triggered": ["replay-interval.n_intervals"], "n": 12, "clicks": {"replay-play": 2, "speed-4x": 1}}]},
        "keep: two merged step clicks step twice": {"state": paused, "slider": paused["slider_w"], "metrics": m50, "runs": [
            {"note": "merged", "triggered": ["replay-step-forward.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 2}}]},
        "keep: one click, triggered, applies once": {"state": paused, "slider": paused["slider_w"], "metrics": m50, "runs": [
            {"note": "click", "triggered": ["replay-step-back.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-back": 1}}]},
        "keep: a user seek applies": {"state": paused, "slider": 50.0, "metrics": m50, "runs": [
            {"note": "seek to 50", "triggered": ["replay-slider.value"], "n": 11, "clicks": {"replay-play": 2}}]},
    }
    node = shutil.which("node")
    with tempfile.TemporaryDirectory() as d:
        sp = Path(d) / "s.json"
        sp.write_text(json.dumps(seqs), encoding="utf-8")
        drv = Path(d) / "d.js"
        drv.write_text(repro.DRIVER, encoding="utf-8")
        for name, js in variants.items():
            res = json.loads(subprocess.run([node, str(drv), js, str(sp)], capture_output=True, text=True, check=True).stdout)
            print(f"== {name}")
            for sname, steps in res.items():
                last = steps[-1]
                print(f"   {sname:45s} -> mode={last['mode']:8s} index={last['index']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
