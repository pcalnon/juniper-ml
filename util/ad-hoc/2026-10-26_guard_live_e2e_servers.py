#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-10-26_guard_live_e2e_servers.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-10-26
# Last Modified: 2026-10-26
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#   Write reaper guard pid files for the live canopy E2E servers whose run-dir pid files
#   systemd-tmpfiles aged out of /tmp/juniper-e2e (`q /tmp 1777 root root 10d`). Without a
#   pid file, util/reap_pytest_orphans.bash's candidate filter matches each of them
#   (`systemd --user` parent, a Juniper conda python) and a run without --dry-run kills it.
#
#   A guard is `<experiment root>/<group>/<name>.pid` holding the listener's pid. The reaper
#   reads every `*.pid` under the experiment root (`~/.local/state/juniper-experiments`,
#   maxdepth 3) on every run, whatever TMPDIR is, and nothing ages it. Each pid is taken
#   from the port's listener and written ONLY when the process's cwd and interpreter are the
#   ones the server was launched with, so a port re-used by something else is refused.
#
#   Writing a guard kills nothing and is undone by deleting the file. Stopping a leg still
#   goes through `CANOPY_VERIFY_RUN_DIR=<group dir> bash util/ad-hoc/2026-09-04_canopy_verify_instance.bash down <port>`.
#
# Usage:
#   python3 util/ad-hoc/2026-10-26_guard_live_e2e_servers.py            # dry run: report only
#   python3 util/ad-hoc/2026-10-26_guard_live_e2e_servers.py --write    # write the guards
#####################################################################################################################################################################################################
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development/python/Juniper"
WORKTREES = JUNIPER / "worktrees"
MERGED = WORKTREES / "juniper-canopy--verify--pacer-731-merged--20261010-0600--25c5c887/src"
PARENT = WORKTREES / "juniper-canopy--control--pre-731-main--20261010-0600--4f69524b/src"
CASCOR_PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14"
CANOPY_PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python3.13"

# port -> (group, guard name, expected cwd, expected interpreter)
SERVERS = {
    8101: ("e2e-trio-2026-09-22", "juniper-data", None, CASCOR_PY),
    8202: ("e2e-trio-2026-09-22", "juniper-cascor", JUNIPER / "juniper-cascor/src", CASCOR_PY),
    8051: ("e2e-trio-2026-09-22", "juniper-canopy", JUNIPER / "juniper-canopy/src", CANOPY_PY),
    8052: ("e2e-legs-2026-10-10", "canopy-8052", MERGED, CANOPY_PY),
    8058: ("e2e-legs-2026-10-10", "canopy-8058", MERGED, CANOPY_PY),
    8053: ("e2e-legs-2026-10-10", "canopy-8053", PARENT, CANOPY_PY),
    8059: ("e2e-legs-2026-10-10", "canopy-8059", PARENT, CANOPY_PY),
}


def listener_pid(port: int):
    out = subprocess.run(["ss", "-ltnpH", f"sport = :{port}"], capture_output=True, text=True, check=False).stdout
    pids = sorted(set(re.findall(r"pid=(\d+)", out)))
    return int(pids[0]) if len(pids) == 1 else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Write reaper guard pid files for the live canopy E2E servers.")
    ap.add_argument("--write", action="store_true", help="write the guard files (default: report only)")
    ap.add_argument("--root", default=os.environ.get("JUNIPER_EXP_RUN_ROOT", str(Path.home() / ".local/state/juniper-experiments")))
    args = ap.parse_args()
    root = Path(args.root)
    refused = 0
    for port, (group, name, want_cwd, want_exe) in SERVERS.items():
        pid = listener_pid(port)
        if pid is None:
            print(f":{port} {name}: no single listener -- skipped")
            refused += 1
            continue
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
            exe = os.readlink(f"/proc/{pid}/exe")
        except OSError as exc:
            print(f":{port} {name}: pid {pid} unreadable ({exc}) -- skipped")
            refused += 1
            continue
        ok = exe == want_exe and (want_cwd is None or Path(cwd) == want_cwd)
        guard = root / group / f"{name}.pid"
        verdict = "OK" if ok else "REFUSED (cwd/exe mismatch)"
        print(f":{port} {name}: pid {pid} cwd={cwd} exe={exe} -> {guard} [{verdict}]")
        if not ok:
            refused += 1
            continue
        if args.write:
            guard.parent.mkdir(parents=True, exist_ok=True)
            guard.write_text(f"{pid}\n", encoding="utf-8")
    print(f"{'wrote' if args.write else 'would write'} {len(SERVERS) - refused} guard(s); refused {refused}")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
