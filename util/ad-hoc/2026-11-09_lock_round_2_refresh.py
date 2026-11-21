#!/usr/bin/env python3
"""Refresh, or replay the freshness gate of, each R-OBS-SC-2 lock-round consumer lock by its recorded recipe.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Why
---
Five image locks move ``juniper-observability`` 0.4.1 -> 0.4.2 and ``juniper-service-core``
0.7.1 -> 0.7.2, and nothing else. Each has its own recipe, and getting one wrong shows up as
collateral pin moves (refused) or as a lock CI's freshness gate rejects. The recipes below were
read from each repo's ``main`` on 2026-11-09 (data ``4f04fc8d``, cascor ``f3dfee8c``, canopy
``63a2f3d7``, recurrence ``3529dfd9``):

* data, cascor ``requirements.lock``, canopy: the extras of CI's ``Lockfile Freshness`` step
  (data ``ci.yml:686``, cascor ``:776``, canopy ``:738``), Python 3.14, which that job and
  ``lockfile-update.yml`` set up, with ``uv==0.11.8`` in both CI and here;
* cascor ``requirements-cpu.lock``: its 35-line header's regeneration command (CPU torch
  override, the PyTorch CPU index, ``--constraint requirements.lock``), so it runs AFTER the GPU
  lock; CI itself only checks that every image dependency is named in it;
* recurrence ``juniper-recurrence/requirements.lock``: its header's command, Python 3.13 (the
  image is ``python:3.13-slim``), from inside ``juniper-recurrence/``; no CI gate.

``refresh`` runs ``2026-10-10_targeted_lock_refresh.py refresh`` with ``--upgrade-package`` for
the two packages (it compiles onto a copy of the lock, refuses any collateral move and restores
the hand-written header); ``check`` runs its ``check`` (CI's constraint-mode replay). The CPU
torch override file is written to ``<tree>/tmp/torch-cpu-override``, the path the header names.

Usage:
    python3 util/ad-hoc/2026-11-09_lock_round_2_refresh.py {refresh,check} --src-root tmp/lr2/src \
        [--repo juniper-data ...]
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "2026-10-10_targeted_lock_refresh.py"
PACKAGES = ("juniper-observability", "juniper-service-core")
CPU_TORCH = "torch==2.14.0+cpu"
CASCOR_EXTRAS = "--extra ml --extra api --extra observability --extra juniper-data --index-strategy unsafe-best-match"

# Per consumer, its locks in refresh order: (project dir under --src-root, lock, uv args, Python).
RECIPES: dict[str, list[tuple[str, str, str, str]]] = {
    "juniper-data": [("juniper-data", "requirements.lock", "--extra api --extra observability --extra mnist --extra equities", "3.14")],
    "juniper-cascor": [
        ("juniper-cascor", "requirements.lock", f"{CASCOR_EXTRAS} --no-emit-package torch", "3.14"),
        ("juniper-cascor", "requirements-cpu.lock", f"{CASCOR_EXTRAS} --extra-index-url https://download.pytorch.org/whl/cpu --no-emit-package torch --override tmp/torch-cpu-override --constraint requirements.lock", "3.14"),
    ],
    "juniper-canopy": [("juniper-canopy", "requirements.lock", "--extra juniper-data --extra juniper-cascor --extra observability", "3.14")],
    "juniper-recurrence": [("juniper-recurrence/juniper-recurrence", "requirements.lock", "--extra observability", "3.13")],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("refresh", "check"))
    parser.add_argument("--src-root", required=True, type=Path)
    parser.add_argument("--repo", action="append", choices=sorted(RECIPES), help="limit to these repos (repeatable)")
    args = parser.parse_args()
    worst = 0
    for repo in args.repo or list(RECIPES):
        for project, lock, uv_args, python in RECIPES[repo]:
            project_dir = args.src_root / project
            if "--override tmp/torch-cpu-override" in uv_args:
                (project_dir / "tmp").mkdir(exist_ok=True)
                (project_dir / "tmp" / "torch-cpu-override").write_text(CPU_TORCH + "\n")
            argv = [sys.executable, str(TOOL), args.mode, "--project-dir", str(project_dir), "--lock", lock, "--uv-args", uv_args, "--python-version", python]
            if args.mode == "refresh":
                for package in PACKAGES:
                    argv += ["--upgrade-package", package]
            print(f"== {repo} {lock} ({args.mode})", flush=True)
            code = subprocess.run(argv).returncode  # nosec B603
            print(f"== {repo} {lock}: exit {code}", flush=True)
            worst = max(worst, code)
            if code != 0 and args.mode == "refresh":
                return code  # never refresh a lock after one that failed (cascor's CPU lock reads the GPU lock)
    return worst


if __name__ == "__main__":
    sys.exit(main())
