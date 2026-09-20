#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : juniper-canopy#631 -- packaging fix trial
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Try candidate ``pyproject.toml`` packaging configs and BUILD each one.

canopy's layout has two roots -- ``juniper_canopy/`` at the repo root and
``backend/ communication/ frontend/ logger/`` under ``src/`` -- held together by
``[tool.setuptools.packages.find] where = [".", "src"]``. ``py-modules`` does not read
``where``; it resolves against ``package-dir``, which this project does not set. So
"just add py-modules" is a hypothesis about setuptools, not a fix, and the only way to
know which config produces a wheel carrying ``canopy_constants.py`` is to build each one
and look inside.

Each trial runs in its own copy of the tree, so a config that corrupts the build cannot
affect the next trial or the checkout. Reports, per config: did the build succeed, how
many of the 19 wanted modules landed, and are the four packages still present (a
``package-dir`` that fixes the modules can silently drop the packages -- the failure this
is most likely to introduce).

Usage:
  python util/ad-hoc/2026-09-15_canopy_py_modules_build_trial.py --tree /tmp/.../canopy-build
"""

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

WANTED = [
    "audit_log", "canopy_constants", "config_manager", "csrf", "dataset_import",
    "dataset_schema", "demo_mode", "discovery", "health", "main", "middleware",
    "model_registry", "observability", "provenance", "secrets_util", "security",
    "settings", "validation_gate", "ws_security",
]
PACKAGES = ("backend", "communication", "frontend", "logger", "juniper_canopy")

FIND_BLOCK = re.compile(
    r"\[tool\.setuptools\.packages\.find\]\n"
    r"where = \[\".\", \"src\"\]\n"
    r"include = \[[^\]]*\]\n",
    re.M,
)


def config_a(text: str) -> str:
    """py-modules alone, no package-dir -- the issue's suggestion, verbatim."""
    block = FIND_BLOCK.search(text).group(0)
    mods = ",\n    ".join(f'"{m}"' for m in WANTED)
    return text.replace(block, block + f"\n[tool.setuptools]\npy-modules = [\n    {mods},\n]\n", 1)


def config_b(text: str) -> str:
    """py-modules plus an explicit empty-string package-dir pointing at src/."""
    block = FIND_BLOCK.search(text).group(0)
    mods = ",\n    ".join(f'"{m}"' for m in WANTED)
    add = (f"\n[tool.setuptools]\npy-modules = [\n    {mods},\n]\n\n"
           f'[tool.setuptools.package-dir]\n"" = "src"\n')
    return text.replace(block, block + add, 1)


def config_c(text: str) -> str:
    """package-dir mapping BOTH roots: "" -> src for the modules, juniper_canopy -> itself.

    setuptools accepts per-package entries alongside the empty-string default, which is the
    only shape that can express canopy's two roots without moving anything.
    """
    block = FIND_BLOCK.search(text).group(0)
    mods = ",\n    ".join(f'"{m}"' for m in WANTED)
    add = (f"\n[tool.setuptools]\npy-modules = [\n    {mods},\n]\n\n"
           f'[tool.setuptools.package-dir]\n"" = "src"\njuniper_canopy = "juniper_canopy"\n')
    return text.replace(block, block + add, 1)


def config_d(text: str) -> str:
    """As C, but also narrow packages.find to src/ since package-dir now supplies the root."""
    block = FIND_BLOCK.search(text).group(0)
    mods = ",\n    ".join(f'"{m}"' for m in WANTED)
    repl = (
        '[tool.setuptools.packages.find]\n'
        'where = [".", "src"]\n'
        'include = ["juniper_canopy*", "backend*", "communication*", "frontend*", "logger*"]\n'
        f"\n[tool.setuptools]\npy-modules = [\n    {mods},\n]\n\n"
        '[tool.setuptools.package-dir]\njuniper_canopy = "juniper_canopy"\nbackend = "src/backend"\n'
        'communication = "src/communication"\nfrontend = "src/frontend"\nlogger = "src/logger"\n'
        '"" = "src"\n'
    )
    return text.replace(block, repl, 1)


CONFIGS = {
    "A: py-modules only": config_a,
    "B: py-modules + package-dir": config_b,
    "C: package-dir both roots": config_c,
    "D: C + explicit per-package dirs": config_d,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tree", required=True, help="a pristine copy of the canopy tree")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()
    base = Path(args.tree).resolve()

    for label, fn in CONFIGS.items():
        work = base.parent / f"trial-{label[0]}"
        shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(base, work, symlinks=True,
                        ignore=shutil.ignore_patterns("dist", "build", "*.egg-info", "__pycache__"))
        pp = work / "pyproject.toml"
        text = pp.read_text(encoding="utf-8")
        if FIND_BLOCK.search(text) is None:
            print(f"{label}: packages.find block not matched -- pyproject has drifted", file=sys.stderr)
            return 2
        pp.write_text(fn(text), encoding="utf-8")

        r = subprocess.run([args.python, "-m", "build", "--wheel"],
                           cwd=work, capture_output=True, text=True)
        print(f"\n=== {label} ===")
        if r.returncode != 0:
            tail = [ln for ln in r.stderr.strip().splitlines() if ln.strip()][-3:]
            print(f"  BUILD FAILED (exit {r.returncode})")
            for ln in tail:
                print(f"    {ln[:150]}")
            continue
        whl = sorted((work / "dist").glob("*.whl"))
        if not whl:
            print("  build reported success but produced no wheel")
            continue
        names = zipfile.ZipFile(whl[-1]).namelist()
        top_mods = {n[:-3] for n in names if n.endswith(".py") and "/" not in n}
        got = [m for m in WANTED if m in top_mods]
        lost = [p for p in PACKAGES if not any(n.startswith(p + "/") for n in names)]
        print(f"  wheel: {whl[-1].name}  ({len(names)} members)")
        print(f"  wanted modules present: {len(got)}/{len(WANTED)}")
        if len(got) != len(WANTED):
            print(f"  missing: {[m for m in WANTED if m not in top_mods]}")
        print(f"  packages still shipped: {[p for p in PACKAGES if p not in lost]}")
        if lost:
            print(f"  *** PACKAGES LOST: {lost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
