"""
Run the flood-4 round-2 canopy-tests carrier's two new test files N times, each in a fresh fenced process.

Validator helper (tests/code/CI lens): a flakiness check. Odd runs list the files in reverse order (and with
main's drift module between them), so module import order varies across runs; there is no randomizing plugin in
the environment. Each run goes through the fenced runner with LD_LIBRARY_PATH / LIBTORCH emptied at the
child's start.

Usage:
  python3 <this file> <python> <canopy worktree> <out dir> <N>

Writes <out dir>/repeat_summary.json; exit 0 when every run passed with zero fence refusals, else 1.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-canopy#800, #801 (flood-4 round 2), canopy-tests carrier validation
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RUNNER = Path(__file__).resolve().parent / "2026-11-08_flood4r2_val_canopy-tests_fenced_pytest.py"
FLAT = "src/tests/unit/backend/test_apply_partition_flat_legs.py"
NESTED = "src/tests/unit/test_schema_drift_nested_equality.py"
MAIN_DRIFT = "src/tests/unit/test_check_juniper_data_generator_schemas.py"


def main() -> int:
    python, wt, out, count = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), int(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "LD_LIBRARY_PATH": "", "LIBTORCH": ""}
    runs = []
    for index in range(count):
        files = [FLAT, NESTED] if index % 2 == 0 else [NESTED, MAIN_DRIFT, FLAT]
        fence = out / f"repeat_fence_{index:02d}.json"
        command = [python, "-I", str(RUNNER), "--wt", str(wt), "--out", str(fence), "--", "-m", "not requires_cascor and not requires_server and not slow", "--timeout=60", "-p", "no:cacheprovider", "-q", *files]
        started = time.monotonic()
        proc = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
        elapsed = round(time.monotonic() - started, 2)
        tail = [line for line in proc.stdout.splitlines() if re.search(r"\b(passed|failed|error)\b", line)]
        record = json.loads(fence.read_text(encoding="utf-8")) if fence.is_file() else {}
        runs.append({"run": index, "files": files, "exit": proc.returncode, "seconds": elapsed, "result": tail[-1] if tail else None, "fence_refusals": len(record.get("fence_refusals", [])), "imported_outside_wt": record.get("imported_outside_wt")})
        print(f"run {index:02d}: exit={proc.returncode} {tail[-1] if tail else '?'} refusals={runs[-1]['fence_refusals']} ({elapsed}s)")
    ok = all(run["exit"] == 0 and run["fence_refusals"] == 0 and not run["imported_outside_wt"] for run in runs)
    (out / "repeat_summary.json").write_text(json.dumps({"python": python, "worktree": str(wt), "count": count, "all_passed_unfenced": ok, "runs": runs}, indent=1), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
