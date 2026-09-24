"""Lane B, T1: what the gate does when a sibling checkout is missing, and the pre-#660 control.

Scenarios (each in its own scratch ecosystem, JUNIPER_DRIFT_TEST_FORCE_LOCAL=1, GITHUB_ACTIONS unset):
  A. all present (control)                     -> expect OK
  B. canopy checkout missing (failed clone)    -> the PR says FAIL (file-existence test)
  C. juniper-data checkout missing             -> no root; everything skips?
  D. juniper-cascor checkout missing           -> no root; everything skips?
  E. canopy at pre-#660 48074653               -> the PR says two subtests fail
Also: the same run with GITHUB_ACTIONS=true instead of FORCE_LOCAL (docs-full-check's condition).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
ECO = LANE / "eco"
WORK = LANE / "t1_clone"
PRE660 = LANE / "canopy-hist" / "security_48074653.py"


def build(name: str, omit: str | None = None, canopy_src: Path | None = None) -> Path:
    eco = WORK / name
    for repo in ("juniper-data", "juniper-cascor", "juniper-canopy"):
        if repo == omit:
            continue
        shutil.copytree(ECO / repo, eco / repo, symlinks=True)
    shutil.copytree(ECO / "juniper-ml" / "tests", eco / "juniper-ml" / "tests")
    shutil.copytree(ECO / "juniper-ml" / "juniper-service-core", eco / "juniper-ml" / "juniper-service-core")
    if canopy_src is not None:
        shutil.copy2(canopy_src, eco / "juniper-canopy" / "src" / "security.py")
    return eco / "juniper-ml"


def run(cwd: Path, gha: bool) -> str:
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL")}
    if gha:
        env["GITHUB_ACTIONS"] = "true"
    else:
        env["JUNIPER_DRIFT_TEST_FORCE_LOCAL"] = "1"
    r = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests/test_service_fork_drift.py"], cwd=cwd, env=env, capture_output=True, text=True, check=False)
    lines = r.stderr.strip().splitlines()
    keep = [ln for ln in lines if ln.startswith(("FAIL:", "ERROR:", "Ran ", "OK", "FAILED")) or "skipped '" in ln]
    return f"exit={r.returncode}\n    " + "\n    ".join(keep)


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    scenarios = [
        ("A_all_present", None, None),
        ("B_canopy_missing", "juniper-canopy", None),
        ("C_data_missing", "juniper-data", None),
        ("D_cascor_missing", "juniper-cascor", None),
        ("E_canopy_pre660", None, PRE660),
    ]
    for name, omit, src in scenarios:
        root = build(name, omit, src)
        for gha in (False, True):
            print(f"== {name} ({'GITHUB_ACTIONS=true' if gha else 'FORCE_LOCAL=1'}): {run(root, gha)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
