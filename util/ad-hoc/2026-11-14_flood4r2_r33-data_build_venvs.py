#!/usr/bin/env python3
"""
Build fresh, dependency-only virtual environments for juniper-data's scheduled test lane (its `[all]` extra, every
extra named one by one, WITHOUT juniper-data itself), one per named interpreter, and record what each one really is.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, juniper-data benchmark smoke run)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: the Overtoad's ruling of 2026-11-14, a daily smoke run of the 41 benchmarks)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_val_d2-data_venv_probe.py (the interpreter probe this reuses in spirit)

WHY THIS EXISTS
The host's `python3` link moved to the system CPython on 2026-11-14, and a conda environment must never receive an
install. So each venv is made by `uv venv --python <explicit interpreter>` under the caller's scratch directory, and
filled by `uv pip install -r <tree>/pyproject.toml --extra api --extra arc-agi ...`: the dependencies that
`pip install -e ".[all]"` (what scheduled-tests.yml runs) installs, minus juniper-data itself. The tests import
juniper_data from the checkout through pytest's `pythonpath = ["."]`. The extras are named one by one because `all`
is a self-reference (`juniper-data[api,...]`) that a resolver could satisfy from PyPI's juniper-data wheel instead.

It refuses an existing venv directory (fresh means fresh). After the install it proves the venv holds no juniper-data
distribution and that juniper_data does not import from a neutral directory, and records sys.version,
sys.executable and sys.base_prefix, the versions of pytest, pytest-benchmark and numpy, and the full freeze.

Usage:
    python3 <this> --tree <juniper-data tree> --out-dir <scratch> --uv <uv binary> LABEL=INTERPRETER [LABEL=INTERPRETER ...]
Exit 0 = every venv built and checked; 1 = a build or a check failed (see <out-dir>/venv_<label>.json).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 - fixed argv: uv and the venvs' own interpreters
import sys
import time
from pathlib import Path

EXTRAS = ("api", "arc-agi", "equities", "mnist", "observability", "dev", "test")
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
PROBE = (
    "import json, sys, importlib.util, importlib.metadata as md\n"
    "def ver(name):\n"
    "    try:\n"
    "        return md.version(name)\n"
    "    except md.PackageNotFoundError:\n"
    "        return None\n"
    "spec = importlib.util.find_spec('juniper_data')\n"
    "print(json.dumps({'version': sys.version, 'executable': sys.executable, 'base_prefix': sys.base_prefix, 'prefix': sys.prefix,\n"
    "    'juniper_data_importable_from_neutral_cwd': spec is not None, 'juniper_data_distribution': ver('juniper-data'),\n"
    "    'pytest': ver('pytest'), 'pytest-benchmark': ver('pytest-benchmark'), 'numpy': ver('numpy'), 'pytest-timeout': ver('pytest-timeout'),\n"
    "    'juniper-data-client': ver('juniper-data-client'), 'PyYAML': ver('PyYAML')}))\n"
)


def child_env() -> dict[str, str]:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    env.pop("VIRTUAL_ENV", None)
    return env


def run(argv: list[str], log: Path, cwd: Path | None = None, timeout: int = 1800) -> int:
    started = time.monotonic()
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"$ {' '.join(argv)}\n")
        handle.flush()
        done = subprocess.run(argv, cwd=cwd, env=child_env(), stdout=handle, stderr=subprocess.STDOUT, check=False, timeout=timeout)  # nosec B603
        handle.write(f"[exit {done.returncode} after {time.monotonic() - started:.1f}s]\n")
    return done.returncode


def build(label: str, interpreter: str, tree: Path, out_dir: Path, uv: str) -> dict:
    venv = out_dir / "venvs" / label
    log = out_dir / f"venv_{label}.log"
    row: dict = {"label": label, "interpreter": interpreter, "venv": str(venv), "log": str(log), "extras": list(EXTRAS)}
    if venv.exists():
        row["error"] = "venv directory already exists: refused (fresh means fresh)"
        return row
    venv.parent.mkdir(parents=True, exist_ok=True)
    row["uv_venv_exit"] = run([uv, "venv", "--python", interpreter, str(venv)], log)
    if row["uv_venv_exit"] != 0:
        return row
    python = venv / "bin" / "python"
    argv = [uv, "pip", "install", "--python", str(python), "-r", str(tree / "pyproject.toml")]
    for extra in EXTRAS:
        argv += ["--extra", extra]
    row["uv_pip_install_exit"] = run(argv, log, timeout=3000)
    if row["uv_pip_install_exit"] != 0:
        return row
    neutral = out_dir / "venvs"
    probe = subprocess.run([str(python), "-I", "-B", "-c", PROBE], cwd=neutral, env=child_env(), capture_output=True, text=True, check=False, timeout=120)  # nosec B603
    row["probe_exit"] = probe.returncode
    if probe.returncode == 0:
        row.update(json.loads(probe.stdout))
    else:
        row["probe_stderr_tail"] = probe.stderr[-800:]
    freeze = subprocess.run([uv, "pip", "freeze", "--python", str(python)], env=child_env(), capture_output=True, text=True, check=False, timeout=120)  # nosec B603
    (out_dir / f"venv_{label}_freeze.txt").write_text(freeze.stdout, encoding="utf-8")
    row["freeze"] = str(out_dir / f"venv_{label}_freeze.txt")
    row["freeze_names_juniper_data"] = any(line.lower().startswith(("juniper-data==", "juniper_data==", "juniper-data @", "-e ")) for line in freeze.stdout.splitlines())
    row["ok"] = bool(probe.returncode == 0 and row.get("juniper_data_distribution") is None and not row.get("juniper_data_importable_from_neutral_cwd") and not row["freeze_names_juniper_data"] and row.get("pytest-benchmark"))
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--uv", required=True)
    parser.add_argument("pairs", nargs="+", help="LABEL=INTERPRETER")
    ns = parser.parse_args()
    status = 0
    for pair in ns.pairs:
        label, _, interpreter = pair.partition("=")
        row = build(label, interpreter, ns.tree.resolve(), ns.out_dir.resolve(), ns.uv)
        (ns.out_dir / f"venv_{label}.json").write_text(json.dumps(row, indent=1) + "\n", encoding="utf-8")
        print(f"{label}: ok={row.get('ok')} version={str(row.get('version', '?')).split()[0]} executable={row.get('executable')} base_prefix={row.get('base_prefix')} pytest={row.get('pytest')} pytest-benchmark={row.get('pytest-benchmark')} juniper-data dist={row.get('juniper_data_distribution')} error={row.get('error')}")
        if not row.get("ok"):
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
