#!/usr/bin/env python3
"""
Sample /proc/loadavg on an interval into a TSV, so a timing measurement carries its host condition.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — investigation (perf lane P2 item 2.1 probe; reusable for any host-bound run)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md

WHY THIS EXISTS

`run_experiment.py` records nproc, platform and the thread env in a run's manifest but NOT the
load average, and the headroom sweep (§8.2 of the 2026-09-02 instrument-resolution note) had to
record `/proc/loadavg` per block itself for the same reason. A calibration figure taken while a
peer session's stack was training is a figure for a different condition; without the trace there
is no way to tell afterwards. This writes one row per interval:

    utc_iso    epoch_s    load_1m    load_5m    load_15m    running/total

Run it in the background for the life of the measurement, then kill it:

    python3 util/ad-hoc/2026-09-08_loadavg_sampler.py --out PATH.tsv --interval 10 &
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_STOP = False


def _stop(signum, frame):  # noqa: ARG001 - signal handler signature
    global _STOP
    _STOP = True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=10.0)
    args = parser.parse_args(argv)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fresh = not args.out.exists()
    with args.out.open("a", encoding="utf-8") as out:
        if fresh:
            out.write("utc_iso\tepoch_s\tload_1m\tload_5m\tload_15m\trunning_total\n")
        while not _STOP:
            fields = Path("/proc/loadavg").read_text(encoding="utf-8").split()
            now = time.time()
            out.write(f"{datetime.fromtimestamp(now, timezone.utc).isoformat()}\t{now:.0f}\t{fields[0]}\t{fields[1]}\t{fields[2]}\t{fields[3]}\n")
            out.flush()
            time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
