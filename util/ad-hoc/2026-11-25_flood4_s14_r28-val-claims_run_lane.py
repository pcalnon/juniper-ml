"""
Run juniper-canopy pytest (ci.yml's unit-lane step, or a subset) in a CI-like child environment and record the result.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r28 (juniper-canopy's load-sensitive relay test). Modelled on
    util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py, without its connect census.

Usage (run under bash tmp/flood4/session14/runenv.bash):
    python3 -I <this file> --python <venv python> --tree <canopy tree> --out <dir> --label <name> [--lane] [-- <pytest args>]

--lane runs ci.yml's unit-lane pytest command verbatim (juniper-canopy .github/workflows/ci.yml, unit-tests job):
-m "not requires_cascor and not requires_server and not slow" src/tests/unit/ src/tests/regression/ src/tests/contract/
src/tests/performance/ --verbose --timeout=60 --maxfail=5 --junitxml=... --cov=src --cov-report=term-missing
--cov-report=xml:... --cov-report=json:... --cov-report=html:... --cov-fail-under=80, with any args after -- appended.
Without --lane, the args after -- are the whole pytest argument list.

The child environment: every JUNIPER_*, CASCOR_* and CANOPY_* variable dropped, except names containing SENTRY, which
are kept and set EMPTY; LD_LIBRARY_PATH and PYTHONPATH dropped (this host's LD_LIBRARY_PATH names a foreign libtorch);
LIBTORCH set empty; the CI step's CASCOR_BACKEND_AVAILABLE=0, RUN_SERVER_TESTS=0, ENABLE_SLOW_TESTS=0 set. Only the
names set are recorded, never values. Outputs in --out: <label>.log, <label>.run.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - runs pytest under a chosen interpreter, list argv
import sys
import time
from pathlib import Path

CI_STEP = {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"}
LANE = [
    "-m",
    "not requires_cascor and not requires_server and not slow",
    "src/tests/unit/",
    "src/tests/regression/",
    "src/tests/contract/",
    "src/tests/performance/",
    "--verbose",
    "--timeout=60",
    "--maxfail=5",
    "--junitxml=reports/junit/junit-unit.xml",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=xml:reports/coverage.xml",
    "--cov-report=json:reports/coverage.json",
    "--cov-report=html:reports/htmlcov",
    "--cov-fail-under=80",
]


def child_env() -> tuple[dict, list[str]]:
    env = {}
    for k, v in os.environ.items():
        if k in ("LD_LIBRARY_PATH", "PYTHONPATH"):
            continue
        if k.startswith(("JUNIPER_", "CASCOR_", "CANOPY_")):
            if "SENTRY" in k:
                env[k] = ""
            continue
        env[k] = v
    env["LIBTORCH"] = ""
    env.update(CI_STEP)
    return env, sorted(set(CI_STEP) | {"LIBTORCH"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--lane", action="store_true")
    ap.add_argument("--timeout", type=int, default=3000)
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    rest = args.rest[1:] if args.rest and args.rest[0] == "--" else args.rest
    tree = Path(args.tree)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for d in ("logs", "src/logs", "reports/junit", "reports/coverage", "reports/htmlcov"):
        (tree / d).mkdir(parents=True, exist_ok=True)
    argv = [args.python, "-m", "pytest", *(LANE if args.lane else []), *rest]
    env, names = child_env()
    log = out / f"{args.label}.log"
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as fh:
        cp = subprocess.run(argv, cwd=tree, env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=args.timeout, check=False)  # nosec B603
    secs = round(time.time() - t0, 1)
    text = log.read_text(encoding="utf-8", errors="replace")
    summary = [ln for ln in text.splitlines() if re.match(r"^=+ .*(passed|failed|error|no tests ran|deselected|selected).* =+$", ln)]
    collected = [ln for ln in text.splitlines() if re.search(r"\d+(/\d+)? tests? collected|tests? collected", ln)]
    rec = {"label": args.label, "argv": argv[1:], "cwd": str(tree), "exit": cp.returncode, "seconds": secs, "summary": summary[-1:] if summary else [], "collected_lines": collected[-2:], "env_names_set": names, "python": args.python}
    (out / f"{args.label}.run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
