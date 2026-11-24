#!/usr/bin/env python3
"""
Run every test of one pytest module in its own process, so no test's leftovers reach another's.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — one-off (Cursor flood-4 round 2: the r32 pause fix carrier's fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor src/tests/unit/api/test_lifecycle_pause_check_then_act.py

Collects the module's test ids in ``--tree`` (a juniper-cascor checkout or a hermetic copy of one),
then runs each id alone (``python -m pytest <id> -p no:cacheprovider -q``) from that tree's root with
``JUNIPER_CASCOR_LOG_DIR`` dropped, the six Sentry DSN variables set to the empty string, a dead
session bus and ``PYTHONDONTWRITEBYTECODE=1``. Records each id's exit code and the first ``E`` line
of its output, and the sha256 of the tree's ``src/api/lifecycle/manager.py`` and of the module.

Usage:
  2026-11-16_flood4r2_r32-cascor_each_test.py --tree <dir> --module <repo-relative path> --python <interpreter>
      --out <file.json> [--workers N (1-3)] [--logs <dir>]
Exit: 0 when every test passed; 1 when any failed; 2 when collection failed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 -- fixed-argv pytest runs
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
PER_TEST_TIMEOUT = 180


def _env() -> dict:
    env = {key: value for key, value in os.environ.items() if key != "JUNIPER_CASCOR_LOG_DIR"}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect(python: str, tree: Path, module: str) -> list:
    proc = subprocess.run([python, "-m", "pytest", module, "--collect-only", "-p", "no:cacheprovider"], cwd=tree, env=_env(), capture_output=True, text=True, check=False, timeout=PER_TEST_TIMEOUT)  # nosec B603 -- fixed argv
    return [line.strip() for line in proc.stdout.splitlines() if "::" in line and not line.startswith(" ")]


def _run_one(python: str, tree: Path, test_id: str, logs: Path, index: int) -> dict:
    try:
        proc = subprocess.run([python, "-m", "pytest", test_id, "-p", "no:cacheprovider", "-q"], cwd=tree, env=_env(), capture_output=True, text=True, check=False, timeout=PER_TEST_TIMEOUT)  # nosec B603 -- fixed argv
        output = proc.stdout + proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = f"TIMEOUT after {PER_TEST_TIMEOUT}s\n{exc.stdout or ''}"
        code = -1
    (logs / f"{index:03d}.log").write_text(f"{test_id}\n{output}", encoding="utf-8")
    first_error = next((line.strip() for line in output.splitlines() if line.startswith("E  ")), "")
    return {"id": test_id, "exit": code, "outcome": "passed" if code == 0 else "failed", "first_error": first_error[:300], "log": f"{index:03d}.log"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--module", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--logs", type=Path)
    args = parser.parse_args()
    workers = max(1, min(3, args.workers))
    logs = args.logs or args.out.with_suffix(".logs")
    logs.mkdir(parents=True, exist_ok=True)
    ids = _collect(args.python, args.tree, args.module)
    if not ids:
        print("collection found no test", file=sys.stderr)
        return 2
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda pair: _run_one(args.python, args.tree, pair[1], logs, pair[0]), enumerate(ids)))
    summary = {"passed": sum(r["outcome"] == "passed" for r in results), "failed": sum(r["outcome"] == "failed" for r in results), "total": len(results)}
    report = {
        "tree": str(args.tree),
        "module": args.module,
        "python": args.python,
        "manager_sha256": _sha256(args.tree / "src" / "api" / "lifecycle" / "manager.py"),
        "module_sha256": _sha256(args.tree / args.module),
        "workers": workers,
        "summary": summary,
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
