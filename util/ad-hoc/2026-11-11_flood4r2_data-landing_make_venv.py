#!/usr/bin/env python3
"""
Build a dependency-only uv venv that holds what juniper-data's CI unit lane installs (``.[all]`` minus the package).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (the JuniperData conda env is a free-threaded build that lags main's floors)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt; notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --pyproject <juniper-data checkout>/pyproject.toml --python <base interpreter> --venv <new dir> --log <file>

ci.yml's ``unit-tests`` job runs ``pip install ".[all]"``. ``all`` is a self-reference
(``juniper-data[api,arc-agi,equities,mnist,observability,dev,test]``), so this installs those seven extras from the
checkout's own ``pyproject.toml`` with ``uv pip install -r pyproject.toml --extra ...``: the dependencies only. The
package is NOT installed, so ``python -m pytest`` run from a worktree root imports that worktree's ``juniper_data``
and nothing else can shadow it. ``juniper-ci-tools>=0.9.0,<0.10.0`` is added for the per-file coverage gate, as the
job's own step installs it. Nothing is installed into a conda env, and TMPDIR is left as the session gave it.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - fixed argv: uv building a venv under the caller's scratch directory
import sys
from pathlib import Path

EXTRAS = ("api", "arc-agi", "equities", "mnist", "observability", "dev", "test")


def _run(argv: list[str], log) -> int:
    log.write(f"$ {' '.join(argv)}\n")
    log.flush()
    proc = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
    log.write(f"[exit {proc.returncode}]\n")
    log.flush()
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--pyproject", type=Path, required=True)
    ap.add_argument("--python", required=True, help="base interpreter for the venv")
    ap.add_argument("--venv", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    args = ap.parse_args()
    venv = args.venv.resolve()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with open(args.log, "w", encoding="utf-8") as log:
        rc = _run(["uv", "venv", "--python", args.python, str(venv)], log)
        if rc != 0:
            return rc
        vpy = str(venv / "bin" / "python")
        install = ["uv", "pip", "install", "--python", vpy, "-r", str(args.pyproject.resolve())]
        for extra in EXTRAS:
            install += ["--extra", extra]
        install.append("juniper-ci-tools>=0.9.0,<0.10.0")
        rc = _run(install, log)
        if rc != 0:
            return rc
        rc = _run(["uv", "pip", "list", "--python", vpy], log)
        probe = "import importlib.util as u, sys; print(sys.version); print('juniper_data spec outside a checkout:', u.find_spec('juniper_data'))"
        rc = rc or _run([vpy, "-I", "-c", probe], log)
    print(f"exit={rc} venv={venv} log={args.log}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
