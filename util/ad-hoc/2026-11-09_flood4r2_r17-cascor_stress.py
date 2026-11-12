#!/usr/bin/env python3
"""
Repeat juniper-cascor's stop-then-start tests many times, optionally with a forced GIL switch interval.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#753's determinism runs (``--count=60`` at the default and a 1 µs switch interval)

Runs ``-m "unit and not slow" <tests> --count=<N>`` (pytest-repeat) from the checkout root, with a
one-function plugin that sets ``sys.setswitchinterval(<interval>)`` at configure time (when given)
and prints the interval in force and the ``__file__`` of ``api.lifecycle.manager`` at session end,
so the log proves both. ``JUNIPER_CASCOR_LOG_DIR`` is dropped from the environment.

Usage:
  2026-11-09_flood4r2_r17-cascor_stress.py --tree <checkout> --test <path> --count N --label <name> --out <dir> [--switch-interval 1e-6]
Exit: the pytest exit code.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 -- fixed-argv pytest run
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses the JUnit file this run just wrote
from pathlib import Path

PLUGIN_NAME = "_r17_stress_switch"
PLUGIN_TEMPLATE = """import sys

_INTERVAL = {interval!r}


def pytest_configure(config):
    if _INTERVAL is not None:
        sys.setswitchinterval(_INTERVAL)


def pytest_sessionfinish(session, exitstatus):
    module = sys.modules.get("api.lifecycle.manager")
    print("\\nSWITCH_INTERVAL " + repr(sys.getswitchinterval()))
    print("PROVENANCE " + str(getattr(module, "__file__", None)))
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--test", required=True, help="checkout-relative test file")
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--switch-interval", type=float, default=None)
    args = parser.parse_args()
    tree = args.tree.resolve()
    out = args.out.resolve()
    plugin_dir = out / f"_plugins_{args.label}"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / f"{PLUGIN_NAME}.py").write_text(PLUGIN_TEMPLATE.format(interval=args.switch_interval), encoding="utf-8")
    junit = out / f"stress-{args.label}.xml"
    argv = [sys.executable, "-m", "pytest", "-m", "unit and not slow", args.test, f"--count={args.count}", "-p", "no:cacheprovider", "-p", PLUGIN_NAME, "--timeout=120", "-q", f"--junitxml={junit}"]
    env = {k: v for k, v in os.environ.items() if k != "JUNIPER_CASCOR_LOG_DIR"}
    env["PYTHONPATH"] = str(plugin_dir)
    log = out / f"stress-{args.label}.log"
    with log.open("w", encoding="utf-8") as handle:
        handle.write(f"$ (cwd {tree}) {' '.join(argv)}\n")
        handle.flush()
        proc = subprocess.run(argv, cwd=tree, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)  # nosec B603 -- fixed argv
        handle.write(f"\n[pytest exit {proc.returncode}]\n")
    text = log.read_text(encoding="utf-8", errors="replace")
    root = ET.parse(junit).getroot() if junit.exists() else None  # nosec B314 -- our own pytest output
    cases = list(root.iter("testcase")) if root is not None else []
    failed = [c.get("name") for c in cases if c.find("failure") is not None or c.find("error") is not None]
    result = {
        "label": args.label,
        "exit": proc.returncode,
        "requested_interval": args.switch_interval,
        "reported_interval": [line.split(" ", 1)[1] for line in text.splitlines() if line.startswith("SWITCH_INTERVAL ")],
        "provenance": [line.split(" ", 1)[1] for line in text.splitlines() if line.startswith("PROVENANCE ")],
        "tests": len(cases),
        "failed": failed,
    }
    (out / f"stress-{args.label}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
