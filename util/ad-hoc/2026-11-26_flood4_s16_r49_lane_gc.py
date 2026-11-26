"""
Summarize the long cyclic-GC passes the r49 plugin recorded in a juniper-canopy unit-lane run (R49_GC=1), by directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49; input from util/ad-hoc/2026-11-26_flood4_s16_r49_stall_plugin.py

Usage:
    python3 -I <this file> --jsonl <run>.r49.jsonl [--min-s 0.05]
Prints JSON: the number of passes at or above --min-s, their generations and threads, the passes inside
src/tests/regression/ (each with its test and seconds), the largest five, and whether any landed in
test_x7_loop_responsiveness.py.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", required=True)
    parser.add_argument("--min-s", type=float, default=0.05)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
    gcs = [r for r in rows if r["kind"] == "gc" and r["seconds"] >= args.min_s]
    regression = [{"test": r["test"], "seconds": r["seconds"], "generation": r["generation"], "thread": r["thread"]} for r in gcs if (r.get("test") or "").startswith("src/tests/regression/")]
    in_health_file = [r for r in gcs if "test_x7_loop_responsiveness.py" in (r.get("test") or "")]
    result = {
        "passes": len(gcs),
        "by_generation": dict(collections.Counter(str(r["generation"]) for r in gcs)),
        "by_thread": dict(collections.Counter(r["thread"] for r in gcs)),
        "regression_dir_passes": regression,
        "largest": sorted(({"test": r["test"], "seconds": r["seconds"], "generation": r["generation"]} for r in gcs), key=lambda r: -r["seconds"])[:5],
        "in_test_x7_loop_responsiveness": in_health_file,
    }
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
