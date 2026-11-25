#!/usr/bin/env python3
"""Record every process whose working directory lies under a worktree root (flood-4 session 12, ruling 7's live check).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (ruling 7's read-only worktree inventory; tmp/flood4/session12/r7/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session12/briefs/R7_inventory.txt ("Live use"); util/ad-hoc/2026-11-23_r_obs_sc_2_housekeeping.bash
    (its holders() check, which the executing script must repeat at run time)

Reads /proc/<pid>/cwd (readlink) for every process, the superset of the brief's ``pgrep -f claude`` and any
python/pytest/node process, and keeps those under one of the three worktree roots. Also records, for each such process,
the worktree it is in (the first path component below its root) and its command line, cut to 200 characters.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s12_r7_live.py --out FILE.tsv
It changes nothing and writes only FILE.tsv.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ROOTS = [str(JUNIPER / "worktrees") + "/", str(JUNIPER / "juniper-ml" / ".claude" / "worktrees") + "/", str(JUNIPER / "juniper-canopy" / ".claude" / "worktrees") + "/"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = []
    for entry in os.listdir("/proc"):
        if not entry.isdecimal():
            continue
        try:
            cwd = os.readlink(f"/proc/{entry}/cwd")
        except OSError:
            continue
        root = next((r for r in ROOTS if cwd.startswith(r)), None)
        if root is None:
            continue
        worktree = root + cwd[len(root):].split("/", 1)[0]
        try:
            with open(f"/proc/{entry}/cmdline", "rb") as fh:
                cmd = fh.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
        except OSError:
            cmd = ""
        rows.append((int(entry), worktree, cwd, cmd[:200].replace("\t", " ")))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with a.out.open("w", encoding="utf-8") as fh:
        fh.write(f"# captured {now}; {len(rows)} processes under the worktree roots\n")
        fh.write("pid\tworktree\tcwd\tcmdline\n")
        for pid, wt, cwd, cmd in sorted(rows):
            fh.write(f"{pid}\t{wt}\t{cwd}\t{cmd}\n")
    counts: dict[str, int] = {}
    for _, wt, _, _ in rows:
        counts[wt] = counts.get(wt, 0) + 1
    print(f"captured {now}: {len(rows)} processes in {len(counts)} worktrees")
    for wt, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {wt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
