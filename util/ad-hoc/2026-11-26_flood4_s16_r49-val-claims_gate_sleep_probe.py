#!/usr/bin/env python3
"""
Does juniper-canopy's X7 structural gate refuse a `time.sleep` in an async handler? Drive its census() over synthetic code.

Loads src/tests/regression/test_x7_off_loop_discipline.py from a canopy tree by path and runs its census() over small
synthetic modules: an async handler calling time.sleep (bare and as a module attribute), one calling a module-level
sync helper that sleeps, and, as a positive control, one calling backend.get_status() inline. Prints each module's
buckets. A bucket list that is empty for the sleep handlers means the gate does not see them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 49)
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path

CASES = {
    "time_sleep_attribute": "import time\n\nasync def handler():\n    time.sleep(1.0)\n    return {}\n",
    "time_sleep_bare": "from time import sleep\n\nasync def handler():\n    sleep(1.0)\n    return {}\n",
    "sync_helper_that_sleeps": "import time\n\ndef _wait():\n    time.sleep(1.0)\n\nasync def handler():\n    _wait()\n    return {}\n",
    "control_backend_inline": "async def handler():\n    return backend.get_status()\n",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="drive canopy's X7 gate census over synthetic handlers")
    ap.add_argument("--tree", required=True, help="a juniper-canopy tree")
    ap.add_argument("--out", required=True, help="JSON report to write")
    args = ap.parse_args()
    path = Path(args.tree) / "src/tests/regression/test_x7_off_loop_discipline.py"
    spec = importlib.util.spec_from_file_location("x7_gate_under_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = {"gate_file": str(path)}
    for name, source in CASES.items():
        buckets = module.census(ast.parse(source))
        report[name] = {"buckets": buckets, "reported": sum(len(v) for v in buckets.values())}
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
