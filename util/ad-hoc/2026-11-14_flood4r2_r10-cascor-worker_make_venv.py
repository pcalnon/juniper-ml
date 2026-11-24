#!/usr/bin/env python3
"""
Build a venv the way juniper-cascor-worker's CI unit lane builds its environment, and report what it holds.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor-worker)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
juniper-cascor-worker's tests/conftest.py imports the package, so even its secret-scan test file needs the package and
its runtime dependencies, torch among them. CI's unit lane installs torch from the PyTorch CPU index, pinned to the
Dockerfile's ARG TORCH_VERSION, and then `pip install -e ".[test]"`; an unpinned install would pull the CUDA build from
PyPI. This makes a venv from the base interpreter given (never touching that interpreter's own environment), installs
the same two things into it with uv, and writes the venv's sys.version, sys.executable, sys.base_prefix and the
versions of the packages the lanes need to --json. The six Sentry DSN variables are set to the empty string in every
child. It prints no environment variable.

Usage:
    python3 <this> --tree <worker worktree> --venv <new dir under a repo tmp/> --python <base interpreter> \
        --torch 2.14.0 --uv <uv binary> --json <out file>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 - runs uv and the venv's own interpreter with fixed argv
import sys
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
CPU_INDEX = "https://download.pytorch.org/whl/cpu"
PROBE = """
import importlib.metadata as md, json, sys
names = sys.argv[1].split(",")
out = {"version": sys.version.split()[0], "executable": sys.executable, "base_prefix": sys.base_prefix, "prefix": sys.prefix, "dists": {}}
for name in names:
    try:
        out["dists"][name] = md.version(name)
    except md.PackageNotFoundError:
        out["dists"][name] = "MISSING"
print(json.dumps(out))
"""
DISTS = "torch,numpy,pytest,pytest-asyncio,pytest-timeout,pytest-cov,PyYAML,websockets,juniper-cascor-protocol,juniper-config-tools,juniper-cascor-model,juniper-cascor-worker"


def run(argv: list[str], env: dict[str, str], log: list[dict]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    log.append({"argv": argv, "exit": proc.returncode, "stderr_tail": proc.stderr.strip().splitlines()[-8:]})
    if proc.returncode != 0:
        raise SystemExit(f"{argv[0]} exited {proc.returncode}: {proc.stderr.strip()[-600:]}")
    return proc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--venv", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--torch", required=True, help="the Dockerfile's ARG TORCH_VERSION")
    ap.add_argument("--uv", required=True)
    ap.add_argument("--json", type=Path, required=True)
    args = ap.parse_args()
    if args.venv.exists():
        raise SystemExit(f"{args.venv} exists; give a new directory")
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    log: list[dict] = []
    run([args.uv, "venv", "--python", args.python, str(args.venv)], env, log)
    py = str(args.venv / "bin" / "python")
    run([args.uv, "pip", "install", "--python", py, f"torch=={args.torch}+cpu", "--index-url", CPU_INDEX], env, log)
    run([args.uv, "pip", "install", "--python", py, "-e", f"{args.tree}[test]"], env, log)
    probe = run([py, "-I", "-c", PROBE, DISTS], env, log)
    facts = json.loads(probe.stdout)
    facts["recipe"] = [f"uv venv --python {args.python}", f"torch=={args.torch}+cpu from {CPU_INDEX}", f"-e {args.tree}[test]"]
    facts["steps"] = log
    args.json.write_text(json.dumps(facts, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: facts[k] for k in ("version", "executable", "base_prefix", "dists")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
