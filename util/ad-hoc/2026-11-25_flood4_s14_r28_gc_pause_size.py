"""
Measure how long one full (generation-2) cyclic-GC pass holds the interpreter for a heap of N tracked objects.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Usage:
    python <this file> [--millions 1,2,4,8]
Prints, per heap size, gc.get_count-independent timings of gc.collect() (three passes each) and the number of
objects the collector tracks (len(gc.get_objects())).
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--millions", default="1,2,4,8")
    args = parser.parse_args()
    print(json.dumps({"python": sys.version.split()[0], "executable": sys.executable}))
    keep = []
    for millions in [float(m) for m in args.millions.split(",")]:
        target = int(millions * 1_000_000)
        while len(keep) < target:
            keep.append([len(keep)])
        tracked = len(gc.get_objects())
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            gc.collect()
            timings.append(round((time.perf_counter() - start) * 1000, 1))
        print(json.dumps({"retained_lists_millions": millions, "gc_tracked_objects": tracked, "full_collect_ms": timings}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
