#!/usr/bin/env python3
"""
Run juniper-canopy's pytest from a carrier worktree's src/ under JuniperCanopy1, with a chosen global git config.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy tests carrier (#794's fixture must not inherit the host's commit.gpgsign)

Usage:
  2026-11-07_flood4_canopy_run_pytest.py --src <worktree>/src --log <file> --git-global inherit|devnull|<config file>
      [--bsd-base64-dir <dir>] [--force-not-linux] -- <pytest args>

--git-global devnull sets GIT_CONFIG_GLOBAL=/dev/null (CI's keyless runner has no signing config);
a file path emulates a signing workstation without touching a hardware key (gpg.program=false).
--bsd-base64-dir prepends a directory holding a BSD-like base64 to PATH (see
2026-11-07_flood4_canopy_bsd_base64_sim.py). The import-origin plugin
(2026-11-07_flood4_canopy_import_origin.py) is always loaded, plus any -p in the pytest args.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
CONDA = "/opt/miniforge3/bin/conda"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--git-global", required=True)
    parser.add_argument("--bsd-base64-dir")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    pytest_args = [a for a in args.pytest_args if a != "--"]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ADHOC)
    if args.git_global == "devnull":
        env["GIT_CONFIG_GLOBAL"] = os.devnull
    elif args.git_global != "inherit":
        env["GIT_CONFIG_GLOBAL"] = str(Path(args.git_global).resolve())
    if args.bsd_base64_dir:
        env["PATH"] = str(Path(args.bsd_base64_dir).resolve()) + os.pathsep + env["PATH"]
    cmd = [CONDA, "run", "-n", "JuniperCanopy1", "python", "-m", "pytest", "-p", "2026-11-07_flood4_canopy_import_origin", "-p", "no:cacheprovider", *pytest_args]
    header = f"# cwd={args.src}\n# GIT_CONFIG_GLOBAL={env.get('GIT_CONFIG_GLOBAL', '<inherited>')}\n# PATH[0]={env['PATH'].split(os.pathsep)[0]}\n# cmd={' '.join(cmd)}\n"
    proc = subprocess.run(cmd, cwd=args.src, env=env, capture_output=True, text=True, check=False)
    Path(args.log).write_text(header + proc.stdout + proc.stderr + f"\n# exit={proc.returncode}\n", encoding="utf-8")
    tail = (proc.stdout + proc.stderr).splitlines()[-14:]
    print(header + "\n".join(tail) + f"\n# exit={proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
