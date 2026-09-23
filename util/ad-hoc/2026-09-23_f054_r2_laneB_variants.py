#!/usr/bin/env python
"""canopy#670 round 2 (Lane B): run v2's replay tests against variants of metrics_panel.py, on a COPY
of the v2 tree materialised from git objects (never the fix worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy canopy#670 (F-CANOPY-054); util/ad-hoc/2026-09-23_f054_r2_laneB_extract.py

Variants:
  parent        main 0fca86e9's metrics_panel.py (falsification of ALL v2 tests, incl. the 2 added
                after the coordinator's 54-test falsification run)
  fix_idempotent  v2 with a triggered button applied only when its count shows it pending
                (``times = pending``; a button event with times 0 is skipped). The minimal fix for
                the double-application race. Reports which v2 tests fail (they pin the old rule).

Usage:
    python3 util/ad-hoc/2026-09-23_f054_r2_laneB_variants.py --objects <canopy .git/objects> --tree <v2 tree dir>
"""

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gitobj", HERE / "2026-09-23_f054_r2_laneB_gitobj.py")
gitobj = importlib.util.module_from_spec(_spec)
sys.modules["gitobj"] = gitobj
_spec.loader.exec_module(gitobj)

PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
MP = "src/frontend/components/metrics_panel.py"
TESTS = ["tests/unit/frontend/test_f054_replay_block_clientside.py", "tests/unit/frontend/test_f048_replay_cycle.py"]

OLD = 'var times = (ev === "replay-slider") ? 1 : Math.max(pending[ev], inTriggers[ev] ? 1 : 0);'
NEW = 'var times = (ev === "replay-slider") ? 1 : pending[ev];\n        if (times <= 0) { continue; }  // already applied (by count, in an earlier run)'


def run(tree: Path):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", LIBTORCH="", LD_LIBRARY_PATH="")
    p = subprocess.run([PY, "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider", "--no-header", "-rf"], cwd=tree / "src", env=env, capture_output=True, text=True, timeout=900, check=False)
    failed = [ln.split(" - ")[0].replace("FAILED ", "") for ln in p.stdout.splitlines() if ln.startswith("FAILED")]
    summ = [ln for ln in p.stdout.splitlines() if re.search(r"\d+ (passed|failed)", ln)]
    return (summ[-1] if summ else p.stdout[-300:]).strip(), failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objects", required=True)
    ap.add_argument("--tree", required=True)
    a = ap.parse_args()
    st = gitobj.Store(a.objects)
    tree = Path(a.tree)
    target = tree / MP
    v2_text = target.read_text(encoding="utf-8")
    try:
        # parent
        target.write_bytes(st.blob_at(st.resolve("0fca86e9"), MP)[1])
        summ, failed = run(tree)
        f054 = [f for f in failed if "test_f054" in f]
        f048 = [f for f in failed if "test_f048" in f]
        print(f"parent 0fca86e9: {summ}  | failed f054={len(f054)} f048={len(f048)}")
        for f in f048:
            print("   f048 failed:", f.split("::", 1)[1])
        # fix
        assert v2_text.count(OLD) == 1, "search text not unique"
        target.write_text(v2_text.replace(OLD, NEW), encoding="utf-8")
        summ, failed = run(tree)
        print(f"v2 + fix_idempotent: {summ}")
        for f in failed:
            print("   failed:", f.split("::", 1)[1])
    finally:
        target.write_text(v2_text, encoding="utf-8")
    print("tree restored:", target.read_text(encoding="utf-8") == v2_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
