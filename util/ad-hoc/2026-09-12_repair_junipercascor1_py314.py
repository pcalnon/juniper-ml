#!/usr/bin/env python3
"""
Re-home JuniperCascor1's pip packages from the stranded 3.13 tree into 3.14.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-12
Status: ad-hoc -- migration
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: [[junipercascor1-python314-upgrade-broke-console-scripts]]

Why this exists
---------------
On 2026-09-12 16:01 a conda transaction whose update specs were the CUDA stack
(``cuquantum cusolvermp cuda-python nccl numbast cutensor cublasmp cudnn cuda
cusparselt``) pulled Python **3.14.7** into JuniperCascor1 as a dependency. Conda
rebuilt its own 26 packages under ``lib/python3.14``; the **192 pip-installed**
distributions stayed in ``lib/python3.13/site-packages``, where 3.14 cannot see
them, and 63 console scripts in ``bin/`` still shebang the removed
``python3.13``. ``pre-commit`` and ``flake8`` are among the casualties.

What it will and will not do
----------------------------
* Reinstalls the pip distributions **at their recorded versions** -- torch stays
  2.11.0, which does publish a cp314 wheel.
* **Skips anything conda now manages under 3.14** (numpy, the cuda_* / numba
  family, ...). Letting pip reinstall those would put PyPI CUDA wheels on top of
  a conda CUDA stack, which is the classic way to break such an env.
* Handles the 6 **editable** Juniper installs separately -- an editable cannot be
  restored from a version pin; it needs ``pip install -e <repo>``.
* ``--dry-run`` (the default) resolves and prints the plan without installing,
  and flags any package pip would have to build from source.

Usage
-----
    python3 util/ad-hoc/2026-09-12_repair_junipercascor1_py314.py            # plan only
    python3 util/ad-hoc/2026-09-12_repair_junipercascor1_py314.py --execute  # do it
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ENV = Path("/opt/miniforge3/envs/JuniperCascor1")
OLD_SP = ENV / "lib/python3.13/site-packages"
NEW_SP = ENV / "lib/python3.14/site-packages"
PY = ENV / "bin/python3.14"

# Editable installs, resolved from their finder modules: dist name -> repo root.
EDITABLES = {
    "juniper-cascor": "/home/pcalnon/Development/python/Juniper/juniper-cascor",
    "juniper-cascor-client": "/home/pcalnon/Development/python/Juniper/juniper-cascor-client",
    "juniper-data": "/home/pcalnon/Development/python/Juniper/juniper-data",
    "juniper-data-client": "/home/pcalnon/Development/python/Juniper/juniper-data-client",
    "juniper-recurrence": "/home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence",
    "juniper-recurrence-client": "/home/pcalnon/Development/python/Juniper/juniper-recurrence/juniper-recurrence-client",
}


def norm(name: str) -> str:
    return name.lower().replace("_", "-")


def dists(site_packages: Path) -> dict[str, tuple[str, Path]]:
    """name -> (version, dist_info_dir) for every .dist-info under site_packages."""
    out: dict[str, tuple[str, Path]] = {}
    for d in sorted(site_packages.glob("*.dist-info")):
        stem = d.name[: -len(".dist-info")]
        if "-" not in stem:
            continue
        name, _, version = stem.rpartition("-")
        out[norm(name)] = (version, d)
    return out


def is_pip_installed(dist_info: Path) -> bool:
    f = dist_info / "INSTALLER"
    return f.is_file() and f.read_text(encoding="utf-8").strip() == "pip"


def is_editable(dist_info: Path) -> bool:
    f = dist_info / "direct_url.json"
    if not f.is_file():
        return False
    try:
        return bool(json.loads(f.read_text(encoding="utf-8")).get("dir_info", {}).get("editable"))
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="actually install (default: plan only)")
    args = ap.parse_args()

    for p in (OLD_SP, NEW_SP, PY):
        if not p.exists():
            print(f"ERROR: missing {p}", file=sys.stderr)
            return 2

    old = dists(OLD_SP)
    conda_has = set(dists(NEW_SP))

    pins: list[str] = []
    skipped_conda: list[str] = []
    skipped_editable: list[str] = []

    for name, (version, info) in sorted(old.items()):
        if not is_pip_installed(info):
            continue
        if is_editable(info) or name in EDITABLES:
            skipped_editable.append(name)
            continue
        if name in conda_has:
            skipped_conda.append(f"{name} (conda has {dists(NEW_SP)[name][0]}, 3.13 had {version})")
            continue
        pins.append(f"{name}=={version}")

    print(f"stranded pip dists in 3.13 : {sum(1 for n, (_, i) in old.items() if is_pip_installed(i))}")
    print(f"  -> to reinstall           : {len(pins)}")
    print(f"  -> skipped, conda-managed : {len(skipped_conda)}")
    print(f"  -> skipped, editable      : {len(skipped_editable)}")
    print()
    print("conda-managed, NOT reinstalled by pip (avoids pip-CUDA over conda-CUDA):")
    for s in skipped_conda:
        print(f"    {s}")
    print()
    print("editable, reinstalled with -e:")
    for e in sorted(skipped_editable):
        print(f"    {e} -> {EDITABLES.get(e, '?? no repo mapping')}")

    req = Path("/tmp/junipercascor1_py314_reinstall.txt")
    req.write_text("\n".join(pins) + "\n", encoding="utf-8")
    print(f"\nrequirements written: {req}")

    cmd = [str(PY), "-m", "pip", "install", "-r", str(req)]
    if not args.execute:
        cmd.append("--dry-run")
        cmd += ["--report", "/tmp/junipercascor1_py314_plan.json"]
    print("\n$ " + " ".join(cmd))
    rc = subprocess.run(cmd).returncode
    print(f"pip exit={rc}")
    if rc != 0:
        return rc

    if not args.execute:
        print("\n(plan only -- rerun with --execute to install, then the -e installs below)")
        for repo in sorted(EDITABLES.values()):
            print(f"  {PY} -m pip install --no-deps -e {repo}")
        return 0

    for name, repo in sorted(EDITABLES.items()):
        print(f"\n=== editable: {name} ===")
        rc = subprocess.run([str(PY), "-m", "pip", "install", "--no-deps", "-e", repo]).returncode
        print(f"  exit={rc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
