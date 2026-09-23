#!/usr/bin/env python
"""Re-score the coordinator's v1-vs-v2 clean room (2026-09-23_f054_pdup_cleanroom_v1_v2.json) for the
outcome its verdict rule cannot see: a pause that APPLIES and is then UNDONE with no new click.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 round 2 (Lane B); util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py

Its rule scores HELD when a 'paused' state appears within 8 s of the pause click. A double
application (the pause applied by COUNT in a queued tick run, then the click's own trigger toggling
back to 'playing') is also HELD under that rule. This reads each arm's raw ``state_log`` and flags,
per trial, a 'playing' state after the first 'paused' inside the trial's 8 s window. The harness
clicks nothing inside that window, so any such 'playing' is the callback's own doing.

Usage:
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_rescore_pdup.py <pdup json>
"""

import json
import sys


def main(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    tot = {"v1": [0, 0], "v2": [0, 0]}
    for name, arm in d["arms"].items():
        v = arm["summary"]["version"]
        slog = arm["state_log"]
        for t in arm["trials"]:
            if t.get("verdict") != "HELD":
                continue
            tc = t["t_click"]
            # CORRECTED WINDOW. The harness does not idle for 8 s: once 'paused' is seen it sleeps
            # 1.0 s and the NEXT trial clicks play. The first version of this re-score used the full
            # 8 s and flagged that next-trial play as an undo in 72 of 85 HELD trials (at K=0 too,
            # which is what exposed the error). The only click-free span after the pause is
            # (t_pause, t_pause + 1000 ms); a double application lands within milliseconds of the
            # first, so 900 ms is enough to see one.
            t_pause = tc + t["latency_ms"]
            win = [r for r in slog if tc <= r[0] <= t_pause + 900]
            first_p = next((i for i, r in enumerate(win) if r[1] == "paused"), None)
            undone = first_p is not None and any(r[1] == "playing" for r in win[first_p + 1 :])
            tot[v][0] += 1
            if undone:
                tot[v][1] += 1
                seq = [(r[0] - tc, r[1], r[2]) for r in win[: first_p + 4]]
                print(f"UNDONE {name} trial {t['trial']}: executed={t.get('click_executed')} recovered={t.get('recovered')} seq={seq}")
    for v, (held, und) in tot.items():
        print(f"{v}: HELD trials {held}, of which a pause applied then undone inside the window: {und}")


if __name__ == "__main__":
    main(sys.argv[1])
