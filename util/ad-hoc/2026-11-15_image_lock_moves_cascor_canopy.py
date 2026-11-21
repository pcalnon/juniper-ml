#!/usr/bin/env python3
"""List what moved in the lock each image installs, between juniper-cascor v0.13.0 -> v0.14.0 and juniper-canopy v0.9.0 -> v0.10.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the lock half of the juniper-deploy pin PR's CHANGELOG entry)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-deploy#266 (the precedent's entry lists cascor 0.13.0's lock moves);
         util/ad-hoc/2026-11-15_deploy_pin_cascor_0_14_0_canopy_0_10_0.py (the pin edits)

Why
---
A pin PR moves every package an image installs, not only the one it names, so its entry says what else moved. Each
lock is read at the two Release tags through the contents API (cascor's image installs ``requirements-cpu.lock``,
canopy's ``requirements.lock``), and the ``name==version`` lines are compared.

Usage
-----
    python3 util/ad-hoc/2026-11-15_image_lock_moves_cascor_canopy.py

It needs ``gh`` (authenticated); it writes nothing.
"""

from __future__ import annotations

import re
import subprocess
import sys

PAIRS = (
    ("juniper-cascor", "v0.13.0", "v0.14.0", "requirements-cpu.lock"),
    ("juniper-canopy", "v0.9.0", "v0.10.0", "requirements.lock"),
)
_PIN = re.compile(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?==([^\s;\\]+)")


def lock(repo: str, ref: str, path: str) -> dict[str, str]:
    raw = subprocess.run(
        ["gh", "api", f"repos/pcalnon/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    out: dict[str, str] = {}
    for line in raw.splitlines():
        m = _PIN.match(line.strip())
        if m:
            out[m.group(1).lower().replace("_", "-")] = m.group(2)
    return out


def main() -> int:
    for repo, old, new, path in PAIRS:
        a, b = lock(repo, old, path), lock(repo, new, path)
        moved = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
        print(f"== {repo} {path}: {old} -> {new}: {len(a)} -> {len(b)} pins, {len(moved)} moved")
        print(f"   added {sorted(b.keys() - a.keys())}; removed {sorted(a.keys() - b.keys())}")
        for k in moved:
            print(f"   {k} {a[k]} -> {b[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
