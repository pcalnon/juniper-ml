#!/usr/bin/env python3
"""
Print what each named interpreter really starts (version, executable, base prefix, pyvenv.cfg) and whether the test
dependencies import from it, because the host's python3 link moved to the system CPython on 2026-11-14.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: finishing the d2-unrun-tests validation after VF was cut off)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session8/BRIEF_S8_ADDENDUM.txt (section 2: a venv may now start the system interpreter)

Usage: 2026-11-14_flood4r2_val_d2-data_venv_probe.py --out <json> <interpreter> [<interpreter> ...]
Each interpreter is run with -I (isolated: no user site, no script directory) and -B (writes no bytecode, so a venv
that lives inside another tree is not written to).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROBE = (
    "import json, sys, importlib.util\n"
    "mods = ['pytest', 'pytest_cov', 'numpy', 'fastapi', 'httpx', 'pydantic', 'juniper_data']\n"
    "found = {m: (importlib.util.find_spec(m).origin if importlib.util.find_spec(m) else None) for m in mods}\n"
    "print(json.dumps({'version': sys.version, 'executable': sys.executable, 'base_prefix': sys.base_prefix, 'prefix': sys.prefix, 'imports': found}))\n"
)


def probe(interpreter: str) -> dict:
    path = Path(interpreter)
    cfg = path.parent.parent / "pyvenv.cfg"
    row: dict = {"interpreter": interpreter, "resolves_to": str(path.resolve()), "pyvenv_cfg": cfg.read_text(encoding="utf-8").splitlines() if cfg.is_file() else None}
    done = subprocess.run([interpreter, "-I", "-B", "-c", PROBE], capture_output=True, text=True, check=False, timeout=120)
    row["exit"] = done.returncode
    if done.returncode == 0:
        row.update(json.loads(done.stdout))
    else:
        row["stderr_tail"] = done.stderr[-800:]
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", required=True)
    parser.add_argument("interpreters", nargs="+")
    ns = parser.parse_args()
    rows = [probe(interpreter) for interpreter in ns.interpreters]
    for row in rows:
        version = row.get("version", "?").split()[0]
        missing = [name for name, origin in row.get("imports", {}).items() if origin is None]
        print(f"{row['interpreter']}\n   -> {row['resolves_to']} | exit {row['exit']} | {version} | executable {row.get('executable')} | base_prefix {row.get('base_prefix')} | missing {missing}")
        print(f"   juniper_data from: {row.get('imports', {}).get('juniper_data')}")
    Path(ns.out).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
