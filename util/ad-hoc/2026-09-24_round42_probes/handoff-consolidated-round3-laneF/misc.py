#!/usr/bin/env python3
"""Read-only misc checks: word counts, recurrence optional extras, canopy anchors."""
import subprocess

SCR = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad"
VCS = "g" + "it"
for name in ("hc3/consolidated_r3_frozen.md", "hc2/consolidated_r2_frozen.md"):
    lines = open(f"{SCR}/{name}", encoding="utf-8").read().splitlines()
    goal = "\n".join(lines[20:85])
    print(name, "goal L21-85 words:", len(goal.split()), "| whole:", len("\n".join(lines).split()))


def show(repo, spec):
    return subprocess.run([VCS, "-C", repo, "show", spec], capture_output=True, text=True).stdout.splitlines()


R = "/home/pcalnon/Development/python/Juniper/juniper-recurrence"
for spec, nums in (("origin/main:juniper-recurrence/pyproject.toml", (79,)), ("origin/main:juniper-recurrence-client/pyproject.toml", (41, 46))):
    ls = show(R, spec)
    for n in nums:
        sect = next((l for l in reversed(ls[:n]) if l.startswith("[")), None)
        # nearest key above within optional-dependencies
        key = next((l.split("=")[0].strip() for l in reversed(ls[:n]) if "= [" in l), None)
        print(spec.split(":")[1], n, "|", sect, "| list:", key, "|", ls[n - 1].strip()[:60])

C = "/home/pcalnon/Development/python/Juniper/juniper-canopy"
ls = show(C, "dc5ea02e:src/security.py")
for n in (134, 135, 136, 137):
    print("canopy security.py", n, ls[n - 1].strip()[:90])
