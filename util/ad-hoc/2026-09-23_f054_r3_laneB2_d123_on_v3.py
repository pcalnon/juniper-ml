#!/usr/bin/env python
"""F-CANOPY-054 round 3, Lane B2: the round-2 sequences D1, D2, D3 on v2 (85415f3c) and v3 (a967a5bd), under node.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation (independent-agent consensus, round 3, Lane B2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-23_f054_r2_laneB2_node_repro.py (driver), ..._r2_laneB2_fix_check.py (sequences)

Same sequences as round 2's fix check, now on the frozen v3 commit instead of a textual patch of v2:
  D1 a tick run applies the pause from its count, then the click's own request runs -> must stay paused
  D2 another run applies a step from its count, then the step's own request runs  -> one row, not two
  D3 a tick run applies a lost seek to 40 (row 1 of 3), then the seek's own trigger carries the value
     written back (33.33...) -> must stay on row 1 (v2 re-reads it as row 0)
plus the four intents v2 was built for (lost pause applies, merged steps apply twice, one click once,
a user seek applies).
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("fc", str(HERE / "2026-09-23_f054_r2_laneB2_fix_check.py"))
fc = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0]]
spec.loader.exec_module(fc)


def main():
    # reuse the fix check's sequences verbatim by capturing them from its main() inputs
    src = (HERE / "2026-09-23_f054_r2_laneB2_fix_check.py").read_text(encoding="utf-8")
    assert "seqs = {" in src
    builds = {"v2 85415f3c": fc.repro.load("85415f3c")[0], "v3 a967a5bd": fc.repro.load("a967a5bd")[0]}
    # rebuild the same sequence dict the fix check builds (copied, not re-derived)
    m50 = [{"epoch": i} for i in range(50)]
    m4 = [{"epoch": i} for i in range(4)]
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
            {"note": "tick", "triggered": ["replay-interval.n_intervals"], "n": 12, "clicks": {"replay-play": 1}},
            {"note": "own trigger", "triggered": ["replay-slider.value"], "n": 12, "clicks": {"replay-play": 1}}]},
        "keep: lost pause applies at the next run": {"state": playing, "slider": playing["slider_w"], "metrics": m50, "runs": [
            {"note": "tick", "triggered": ["replay-interval.n_intervals"], "n": 12, "clicks": {"replay-play": 2, "speed-4x": 1}}]},
        "keep: two merged step clicks step twice": {"state": paused, "slider": paused["slider_w"], "metrics": m50, "runs": [
            {"note": "merged", "triggered": ["replay-step-forward.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-forward": 2}}]},
        "keep: one click applies once": {"state": paused, "slider": paused["slider_w"], "metrics": m50, "runs": [
            {"note": "click", "triggered": ["replay-step-back.n_clicks"], "n": 11, "clicks": {"replay-play": 2, "replay-step-back": 1}}]},
        "keep: a user seek applies": {"state": paused, "slider": 50.0, "metrics": m50, "runs": [
            {"note": "seek to 50", "triggered": ["replay-slider.value"], "n": 11, "clicks": {"replay-play": 2}}]},
    }
    node = shutil.which("node")
    with tempfile.TemporaryDirectory() as d:
        sp = Path(d) / "s.json"
        sp.write_text(json.dumps(seqs), encoding="utf-8")
        drv = Path(d) / "d.js"
        drv.write_text(fc.repro.DRIVER, encoding="utf-8")
        for name, js in builds.items():
            res = json.loads(subprocess.run([node, str(drv), js, str(sp)], capture_output=True, text=True, check=True).stdout)
            print(f"== {name}")
            for sname, steps in res.items():
                last = steps[-1]
                print(f"   {sname:45s} -> mode={last['mode']:8s} index={last['index']}  (last run wrote label={last['label']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
