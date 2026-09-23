#!/usr/bin/env python
"""F-CANOPY-054 round 2, Lane B2: re-score a pdup_cleanroom_v1_v2 transcript for UNDONE pauses.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation (independent-agent consensus, round 2, Lane B2)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-23_f054_pdup_cleanroom_v1_v2.py (the transcript's producer)

WHY. The producer scores HELD on the FIRST ``paused`` record after the pause click and reads the
state log at that moment, so a pause that is applied and then undone (a ``playing`` record after it,
with no new click) scores HELD; its ``settle_not_playing`` then re-pauses silently before the next
trial. canopy#670 v2 can apply one click twice (by count, then by its own trigger), and for the play
button the second application is a toggle back to ``playing``.

RULE (fixed before reading the transcript). For every HELD trial with pause record t_p:
  UNDONE-CERTAIN   a ``playing`` record in (t_p, t_p + 1000 ms]. The producer sleeps 1.0 s after its
                   verdict (taken <= 50 ms after t_p) and only then clicks play for the next trial,
                   so no harness click can explain it.
  UNDONE-PROBABLE  otherwise, two or more ``paused`` records between t_p and the next trial's pause
                   click minus 2 s: the extra one is settle_not_playing re-pausing an undone replay.
Usage:
    python util/ad-hoc/2026-09-23_f054_r2_laneB2_rescore_undone.py <transcript.json>
"""

import json
import sys


def main(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    total = {}
    for name, arm in d["arms"].items():
        slog = arm["state_log"]
        trials = arm["trials"]
        clicks = [t.get("t_click") for t in trials]
        cert, prob, held = [], [], 0
        for i, t in enumerate(trials):
            if t.get("verdict") != "HELD":
                continue
            held += 1
            tc = t["t_click"]
            p = next((r for r in slog if r[0] >= tc and r[1] == "paused"), None)
            if not p:
                continue
            tp = p[0]
            if any(r[1] == "playing" for r in slog if tp < r[0] <= tp + 1000):
                cert.append((t["trial"], next(r[0] - tp for r in slog if tp < r[0] <= tp + 1000 and r[1] == "playing")))
                continue
            nxt = clicks[i + 1] if i + 1 < len(clicks) and clicks[i + 1] else None
            hi = (nxt - 2000) if nxt else tp + 30000
            pauses = [r for r in slog if tp <= r[0] <= hi and r[1] == "paused"]
            if len(pauses) >= 2:
                prob.append(t["trial"])
        s = arm["summary"]
        key = (s["version"], s["K"], s["speed"])
        total[key] = (held, cert, prob, s.get("recovered"))
        print(f"{name:14s} HELD={held:2d} recovered={s.get('recovered')} UNDONE-CERTAIN={len(cert)} {cert} UNDONE-PROBABLE={len(prob)} {prob}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
