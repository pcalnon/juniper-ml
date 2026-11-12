#!/usr/bin/env python3
"""
Run juniper-service-core's suite with ci-service-core.yml's pytest command and coverage gate, per tree and interpreter.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (verification evidence for the N-4 fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         .github/workflows/ci-service-core.yml (the test job's two commands)

Each job is ``<tag>=<tree root>=<python>``. From the tree root it runs CI's command,
``pytest juniper-service-core/tests/ -v --cov=juniper_service_core --cov-report=term-missing
--cov-report=json:<out>/coverage-<tag>.json --cov-fail-under=80``, plus ``-p no:cacheprovider`` and a
``--basetemp`` under ``<out>`` so nothing is written into the tree, with PYTHONPATH = the tree's
``juniper-service-core`` and ``juniper-model-core`` (nothing installed), then
``juniper-coverage-gap-map --coverage-json <that json> --enforce`` as CI does. At most four jobs run
at once. Usage::

    python3 <this file> --out <dir> <tag>=<tree>=<python> [...]

Prints one JSON object: per job, both exit statuses, the pytest summary line and the TOTAL line.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def _run_job(spec: str, out: Path) -> dict:
    tag, tree, python = spec.split("=", 2)
    root = Path(tree).resolve()
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(root / "juniper-service-core"), str(root / "juniper-model-core")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["COVERAGE_FILE"] = str(out / f".coverage-{tag}")
    cov_json = out / f"coverage-{tag}.json"
    pytest_cmd = [python, "-m", "pytest", "juniper-service-core/tests/", "-v", "--cov=juniper_service_core", "--cov-report=term-missing", f"--cov-report=json:{cov_json}", "--cov-fail-under=80", "-p", "no:cacheprovider", f"--basetemp={out / ('bt-' + tag)}"]
    log = out / f"suite-{tag}.log"
    with log.open("w", encoding="utf-8") as handle:
        pytest_rc = subprocess.run(pytest_cmd, cwd=root, env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=1800, check=False).returncode
    text = log.read_text(encoding="utf-8")
    summary = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed)", line)]
    total = [line for line in text.splitlines() if line.startswith("TOTAL")]
    gate_log = out / f"gate-{tag}.log"
    with gate_log.open("w", encoding="utf-8") as handle:
        gate_rc = subprocess.run(["juniper-coverage-gap-map", "--coverage-json", str(cov_json), "--enforce"], cwd=root, stdout=handle, stderr=subprocess.STDOUT, timeout=300, check=False).returncode
    return {"tag": tag, "tree": str(root), "python": python, "pytest_exit": pytest_rc, "summary": summary[-1:] if summary else [], "total": total, "gate_exit": gate_rc, "log": str(log), "gate_log": str(gate_log), "command": " ".join(pytest_cmd)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("jobs", nargs="+")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda spec: _run_job(spec, out), args.jobs))
    print(json.dumps(results, indent=1))
    return 0 if all(r["pytest_exit"] == 0 and r["gate_exit"] == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
