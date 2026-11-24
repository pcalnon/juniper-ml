#!/usr/bin/env python3
"""
Check that a dependency-only venv holds what today's resolution of juniper-data's ``.[all]`` extras gives.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (may two venvs built on 2026-11-11 stand in for CI's install of main c68e6b4c?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_data-landing_make_venv.py (built the venvs this checks)

Usage:
    python3 <this> --pyproject <juniper-data tree>/pyproject.toml --out <dir> --venv <name>=<venv interpreter> [--venv ...]

ci.yml's unit and integration jobs run ``pip install ".[all]"``; ``all`` is the seven extras api, arc-agi, equities,
mnist, observability, dev and test. For each venv this resolves those extras from the given pyproject.toml for that
interpreter (``uv pip compile``: a resolution only, nothing is installed and no venv is touched), lists what the venv
holds (``uv pip freeze``), and reports every package whose resolved version differs from the installed one, and
every resolved package the venv lacks. Packages the venv holds beyond the resolution (juniper-ci-tools and its
dependencies, which CI installs in a later step) are listed separately. CI resolves with pip, not uv, and installs
juniper-data-client from that project's default branch rather than from PyPI; neither is reproduced here.
Exit 0 when no resolved package differs or is missing.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: uv resolving and listing; nothing is installed
import sys
from pathlib import Path

EXTRAS = ("api", "arc-agi", "equities", "mnist", "observability", "dev", "test")
PIN_RE = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)")


def _pins(text: str) -> dict[str, str]:
    pins = {}
    for line in text.splitlines():
        hit = PIN_RE.match(line.strip())
        if hit:
            pins[re.sub(r"[-_.]+", "-", hit.group(1)).lower()] = hit.group(2)
    return pins


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--pyproject", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--venv", action="append", required=True, help="<name>=<venv interpreter>")
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"pyproject": str(args.pyproject.resolve()), "extras": list(EXTRAS), "venvs": []}
    ok = True
    for item in args.venv:
        name, python = item.split("=", 1)
        compile_argv = ["uv", "pip", "compile", str(args.pyproject.resolve()), "--python", python, "--quiet", "--no-header", "--no-annotate"]
        for extra in EXTRAS:
            compile_argv += ["--extra", extra]
        resolved = subprocess.run(compile_argv, capture_output=True, text=True, check=False)  # nosec B603
        frozen = subprocess.run(["uv", "pip", "freeze", "--python", python], capture_output=True, text=True, check=False)  # nosec B603
        with open(out / f"venv_check_{name}.log", "w", encoding="utf-8") as fh:
            fh.write(f"$ {' '.join(compile_argv)}\n# exit={resolved.returncode}\n{resolved.stdout}\n--- stderr ---\n{resolved.stderr}\n\n$ uv pip freeze --python {python}\n# exit={frozen.returncode}\n{frozen.stdout}\n")
        want, have = _pins(resolved.stdout), _pins(frozen.stdout)
        differ = {pkg: {"resolved_today": ver, "in_venv": have[pkg]} for pkg, ver in sorted(want.items()) if pkg in have and have[pkg] != ver}
        missing = {pkg: ver for pkg, ver in sorted(want.items()) if pkg not in have}
        extra_in_venv = {pkg: ver for pkg, ver in sorted(have.items()) if pkg not in want}
        row = {"venv": name, "python": python, "compile_exit": resolved.returncode, "freeze_exit": frozen.returncode, "resolved_packages": len(want), "venv_packages": len(have), "differ": differ, "missing_from_venv": missing, "only_in_venv": extra_in_venv, "matches": resolved.returncode == 0 and frozen.returncode == 0 and bool(want) and not differ and not missing}
        report["venvs"].append(row)
        ok = ok and row["matches"]
        print(json.dumps({k: row[k] for k in ("venv", "compile_exit", "freeze_exit", "resolved_packages", "venv_packages", "differ", "missing_from_venv", "only_in_venv", "matches")}))
    with open(out / "venv_check.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(f"wrote {out / 'venv_check.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
