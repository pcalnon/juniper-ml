#!/usr/bin/env python3
"""Pre-flight juniper-ml's extras against REAL PyPI: resolve each extra's pins per Python version, install nothing.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-18
Status: ad-hoc — one-off (the W1.13 extras raise, util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: W1.13 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         ml#2190 (the W1.11 floor raise, pre-flighted the same way on another host with uv)

Why this exists
---------------
No CI job installs ``[servers]``, ``[recurrence]`` or ``[all]``, so a floor or ceiling that PyPI cannot
satisfy, or that conflicts with another extra's cap, would ship unnoticed. This reads the extras from
``pyproject.toml`` (expanding ``juniper-ml[...]`` self-references, as ``[all]`` uses), then asks pip's
resolver for each extra and each Python version: ``pip install --dry-run --report`` against Linux
x86_64 wheels (``--python-version`` + ``--platform`` + ``--only-binary=:all:``), so nothing is built or
installed. uv is not used because it could not reach PyPI from the host this was written on (turing).

Usage
-----
    python3 util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py --extra servers --extra recurrence --extra all \\
        [--python 3.12 --python 3.13 --python 3.14]

Exit status: 0 when every (extra, Python) pair resolves, 1 when any fails.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLATFORMS = ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64", "manylinux2014_x86_64", "manylinux_2_5_x86_64", "manylinux1_x86_64"]
_SELF = re.compile(r"^juniper-ml\[(?P<extras>[^\]]+)\]$")


def requirements(extras: dict[str, list[str]], name: str, seen: frozenset = frozenset()) -> list[str]:
    """The flat requirement list of one extra, with ``juniper-ml[a,b]`` self-references expanded."""
    if name in seen:
        raise SystemExit(f"ERROR: extra {name!r} refers to itself")
    out: list[str] = []
    for req in extras[name]:
        match = _SELF.match(req.strip())
        if match:
            for sub in match.group("extras").split(","):
                out += requirements(extras, sub.strip(), seen | {name})
        else:
            out.append(req)
    return sorted(set(out))


def resolve(reqs: list[str], python: str) -> tuple[bool, dict[str, str], str]:
    with tempfile.TemporaryDirectory(prefix="extras-preflight-") as tmp:
        report = Path(tmp) / "report.json"
        # --resume-retries: a wheel with no PEP 658 metadata is downloaded to read its metadata, and on a
        # slow link (torch, via [worker]) an interrupted download otherwise fails the resolution outright.
        cmd = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--quiet", "--disable-pip-version-check", "--resume-retries", "10", "--report", str(report), "--python-version", python, "--only-binary=:all:", "--target", str(Path(tmp) / "target")]
        for platform in _PLATFORMS:
            cmd += ["--platform", platform]
        proc = subprocess.run(cmd + reqs, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return False, {}, (proc.stderr or proc.stdout).strip().splitlines()[-1:][0] if (proc.stderr or proc.stdout).strip() else f"pip exit {proc.returncode}"
        data = json.loads(report.read_text(encoding="utf-8"))
        return True, {item["metadata"]["name"].lower().replace("_", "-"): item["metadata"]["version"] for item in data["install"]}, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--extra", action="append", required=True)
    ap.add_argument("--python", action="append", default=None)
    args = ap.parse_args()
    pythons = args.python or ["3.12", "3.13", "3.14"]
    extras = tomllib.loads((_REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["optional-dependencies"]

    failed = False
    for name in args.extra:
        reqs = requirements(extras, name)
        print(f"[{name}] {len(reqs)} requirement(s): {', '.join(reqs)}", flush=True)
        for python in pythons:
            ok, resolved, why = resolve(reqs, python)
            if not ok:
                failed = True
                print(f"  Python {python}: FAILED -- {why}", flush=True)
                continue
            juniper = ", ".join(f"{pkg} {ver}" for pkg, ver in sorted(resolved.items()) if pkg.startswith("juniper-"))
            print(f"  Python {python}: resolves in {len(resolved)} packages -- {juniper}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
