#!/usr/bin/env python3
"""Read-only: HEAD, branch and porcelain status (no optional locks) of the Appendix F worktrees."""
import subprocess

BASE = "/home/pcalnon/Development/python/Juniper/worktrees/"
WTS = [
    "juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2",
    "juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c",
    "juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac",
    "juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb",
    "juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480",
    "juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227",
    "juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2",
    "juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6",
    "juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6",
    "juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f",
]


def g(wt: str, *args: str) -> str:
    r = subprocess.run(["git", "--no-optional-locks", "-C", BASE + wt, *args], capture_output=True, text=True)
    return (r.stdout.strip() or r.stderr.strip())


for wt in WTS:
    head = g(wt, "rev-parse", "--short=8", "HEAD")
    br = g(wt, "rev-parse", "--abbrev-ref", "HEAD")
    st = g(wt, "status", "--porcelain")
    lines = [ln for ln in st.splitlines() if ln.strip()]
    print(f"{head} {br[:60]:60} dirty={len(lines)}  {wt[:70]}")
    for ln in lines[:6]:
        print(f"      {ln}")
