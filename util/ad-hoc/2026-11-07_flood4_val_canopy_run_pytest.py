#!/usr/bin/env python3
"""
Run canopy's pytest in JuniperCanopy1 against a VALIDATION worktree, with a controlled git config and plugins.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; flood-4 validation brief (CI-parity lens)

    python3 2026-11-07_flood4_val_canopy_run_pytest.py --root <worktree> --cwd root|src \
        --git-global devnull|inherit|<file> --log <file> [--env K=V ...] [--plugin <module> ...] -- <pytest args>

Runs `/opt/miniforge3/bin/conda run -n JuniperCanopy1 --no-capture-output python -m pytest -p no:cacheprovider
-p 2026-11-07_flood4_val_canopy_origin_plugin [-p <plugin> ...] <pytest args>` from the worktree root (as CI's
unit lane does) or from its src/, with this directory on PYTHONPATH and CI's unit-lane env
(CASCOR_BACKEND_AVAILABLE=0 RUN_SERVER_TESTS=0 ENABLE_SLOW_TESTS=0). The import-origin record lands in
<log>.origin.txt. Prints the pytest summary line and the exit status; exits with pytest's status.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
CONDA = "/opt/miniforge3/bin/conda"


def main() -> int:
    argv = sys.argv[1:]
    split = argv.index("--") if "--" in argv else len(argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--cwd", choices=("root", "src"), default="root")
    parser.add_argument("--git-global", default="devnull")
    parser.add_argument("--log", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--plugin", action="append", default=[])
    parser.add_argument("--interp", default=None, help="run `<interp> -s -m pytest` instead of conda run in JuniperCanopy1")
    opts = parser.parse_args(argv[:split])
    pytest_args = argv[split + 1 :]
    root = Path(opts.root).resolve()
    env = dict(os.environ)
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"):
        env.pop(name, None)
    env["PYTHONPATH"] = str(ADHOC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["VAL_ROOT"] = str(root) + "/"
    origin = Path(opts.log + ".origin.txt")
    origin.unlink(missing_ok=True)
    env["VAL_ORIGIN_FILE"] = str(origin)
    env.update({"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0"})
    if opts.git_global == "devnull":
        env["GIT_CONFIG_GLOBAL"] = os.devnull
    elif opts.git_global != "inherit":
        env["GIT_CONFIG_GLOBAL"] = opts.git_global
    for pair in opts.env:
        key, _, value = pair.partition("=")
        env[key] = value
    plugins = ["-p", "no:cacheprovider", "-p", "2026-11-07_flood4_val_canopy_origin_plugin"]
    for plugin in opts.plugin:
        plugins += ["-p", plugin]
    if opts.interp:
        cmd = [opts.interp, "-s", "-m", "pytest", *plugins, *pytest_args]
    else:
        cmd = [CONDA, "run", "-n", "JuniperCanopy1", "--no-capture-output", "python", "-m", "pytest", *plugins, *pytest_args]
    cwd = root if opts.cwd == "root" else root / "src"
    with open(opts.log, "w", encoding="utf-8") as handle:
        handle.write(f"CMD: {' '.join(cmd)}\nCWD: {cwd}\nGIT_CONFIG_GLOBAL={env.get('GIT_CONFIG_GLOBAL', '(inherited/unset)')}\n")
        handle.write("VAL env: " + " ".join(f"{k}={v}" for k, v in sorted(env.items()) if k.startswith("VAL_")) + "\n\n")
        handle.flush()
        proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)
        handle.write(f"\nEXIT: {proc.returncode}\n")
    lines = Path(opts.log).read_text(encoding="utf-8", errors="replace").splitlines()
    summary = [line for line in lines if (" passed" in line or " failed" in line or " error" in line) and line.strip().startswith(("=", "1", "2", "3", "4", "5", "6", "7", "8", "9"))]
    print(f"log={opts.log}")
    print("summary:", summary[-1] if summary else "(none)")
    print("exit:", proc.returncode)
    if origin.is_file():
        for line in origin.read_text(encoding="utf-8").splitlines():
            if line.startswith(("modules-from", "KEY settings", "KEY config_manager", "KEY backend", "exitstatus")):
                print("origin:", line)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
