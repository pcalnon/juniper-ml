"""List pytest processes whose cwd is inside my canopy worktree, with elapsed/CPU time. Read-only. Scratch only."""

import os
import subprocess

MINE = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f"
pids = subprocess.run(["pgrep", "-f", "pytest tests/unit/ tests/regression/"], capture_output=True, text=True).stdout.split()
for pid in pids:
    try:
        cwd = os.readlink(f"/proc/{pid}/cwd")
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            cmd = fh.read().split(b"\0")[0].decode()
    except OSError:
        continue
    if cwd.startswith(MINE) and cmd.endswith("python"):
        info = subprocess.run(["ps", "-o", "pid,etime,time,stat", "-p", pid], capture_output=True, text=True).stdout.strip().splitlines()[-1]
        print("MINE:", info, cwd)
    else:
        print("other:", pid, cwd.replace("/home/pcalnon/Development/python/Juniper/", "") or "?")
