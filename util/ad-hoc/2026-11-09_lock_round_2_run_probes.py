#!/usr/bin/env python3
"""Run the per-lock probe for each R-OBS-SC-2 lock-round consumer with its recorded invocation.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Why
---
The ``before`` baselines of 2026-11-09 (session ``b4208d23``) were run by hand, so their exact
invocations (interpreter, extras, suites, marker expression, CPU torch) survived only in each
run's ``install.log`` / ``pytest.log``. The ``after`` runs must repeat them exactly, or a
before/after difference could come from the invocation rather than the lock. This file is that
record, transcribed from those logs; it drives ``2026-11-09_lock_round_2_probe.py`` once per
consumer and writes the probe's printed summary to ``<runs-parent>/runs-<short>-<label>.out``.

The one deliberate difference from the hand runs: juniper-data's first ``before`` run passed
``-q``, which (with the ``-q`` in that repo's pytest ``addopts``) suppressed pytest's summary
line. The probe driver adds no ``-q`` now, and neither does this.

Usage:
    python3 util/ad-hoc/2026-11-09_lock_round_2_run_probes.py --label before \
        --src-root tmp/lr2/src --out tmp/lr2/runs [--repo juniper-data ...]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "2026-11-09_lock_round_2_probe.py"
PY314 = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14"
PY313 = "/opt/miniforge3/envs/JuniperCanopy1/bin/python3.13"
TORCH_CPU = "2.14.0+cpu"

# src / lock are relative to --src-root. Transcribed from the 2026-11-09 ``before`` run logs.
CONSUMERS: dict[str, dict[str, object]] = {
    "juniper-data": {
        "short": "data",
        "src": "juniper-data",
        "lock": "juniper-data/requirements.lock",
        "python": PY314,
        "extras": "test",
        "torch": "",
        "pytest_args": [],
        "suites": [
            "juniper_data/tests/unit/test_observability.py",
            "juniper_data/tests/unit/test_phase1d_security.py",
            "juniper_data/tests/unit/test_security.py",
            "juniper_data/tests/unit/test_auth_posture_boot_check.py",
            "juniper_data/tests/unit/test_middleware.py",
            "juniper_data/tests/unit/test_api_app.py",
            "juniper_data/tests/integration/test_security_integration.py",
        ],
    },
    "juniper-cascor": {
        "short": "cascor",
        "src": "juniper-cascor",
        "lock": "juniper-cascor/requirements-cpu.lock",
        "python": PY314,
        "extras": "test",
        "torch": TORCH_CPU,
        "pytest_args": ["-m", "unit and not slow"],
        "suites": [
            "src/tests/unit/test_api_observability.py",
            "src/tests/unit/test_cfg_02_sentry_sdk_optional.py",
            "src/tests/unit/test_cfg_03_sentry_dsn_resolution.py",
            "src/tests/unit/test_main_sentry_no_local_variables.py",
            "src/tests/unit/test_import_hygiene_568.py",
            "src/tests/unit/api/test_api_security.py",
            "src/tests/unit/api/test_phase1c_security.py",
            "src/tests/unit/api/test_auth_posture_boot_check.py",
            "src/tests/unit/api/test_api_middleware.py",
            "src/tests/unit/api/test_api_health.py",
            "src/tests/unit/api/test_api_app.py",
        ],
    },
    "juniper-canopy": {
        "short": "canopy",
        "src": "juniper-canopy",
        "lock": "juniper-canopy/requirements.lock",
        "python": PY314,
        "extras": "test",
        "torch": TORCH_CPU,
        "pytest_args": ["-m", "not requires_cascor and not requires_server and not slow"],
        "suites": [
            "src/tests/regression/test_auth_posture_boot_check.py",
            "src/tests/regression/test_blank_api_key_warning_boot.py",
            "src/tests/regression/test_dependency_floor_boot_check.py",
            "src/tests/unit/frontend/test_internal_api_key_rules.py",
            "src/tests/unit/test_browser_control_auth.py",
            "src/tests/unit/test_main_gate_coverage_ws_helpers.py",
            "src/tests/unit/test_metrics_auth_settings_integration.py",
            "src/tests/unit/test_middleware_coverage.py",
            "src/tests/unit/test_middleware.py",
            "src/tests/unit/test_observability_coverage.py",
            "src/tests/unit/test_observability.py",
            "src/tests/unit/test_phase0_security.py",
            "src/tests/unit/test_r2_1_5_wire_compat.py",
            "src/tests/unit/test_readonly_ws_browser_auth.py",
            "src/tests/unit/test_security.py",
            "src/tests/unit/test_security_validation.py",
        ],
    },
    "juniper-recurrence": {
        "short": "recurrence",
        "src": "juniper-recurrence/juniper-recurrence",
        "lock": "juniper-recurrence/juniper-recurrence/requirements.lock",
        "python": PY313,
        "extras": "test,observability",
        "torch": "",
        "pytest_args": [],
        "suites": ["tests"],
    },
}


def _argv(repo: str, label: str, src_root: Path, out: Path) -> list[str]:
    spec = CONSUMERS[repo]
    argv = [sys.executable, str(PROBE), "--repo", repo, "--label", label, "--src", str(src_root / str(spec["src"])), "--lock", str(src_root / str(spec["lock"])), "--python", str(spec["python"]), "--extras", str(spec["extras"]), "--out", str(out)]
    if spec["torch"]:
        argv += ["--torch-cpu", str(spec["torch"])]
    for arg in spec["pytest_args"]:  # type: ignore[union-attr]
        argv.append(f"--pytest-arg={arg}")
    for suite in spec["suites"]:  # type: ignore[union-attr]
        argv += ["--suite", str(suite)]
    return argv


def _verify(repo: str, runs: Path) -> list[str]:
    """Compare ``CONSUMERS[repo]`` with a prior run's logs under ``runs/<repo>-*/``; return the mismatches."""
    spec = CONSUMERS[repo]
    dirs = sorted(runs.glob(f"{repo}-*/summary.json"))
    if not dirs:
        return [f"no {repo}-* run under {runs}"]
    run_dir = dirs[0].parent
    problems = []
    summary = json.loads((run_dir / "summary.json").read_text())
    if summary.get("pytest", {}).get("suites") != spec["suites"]:
        problems.append("suites differ")
    install = (run_dir / "install.log").read_text()
    commands = [line for line in install.splitlines() if line.startswith("$ ")]
    cmd = next((line for line in (run_dir / "pytest.log").read_text().splitlines() if line.startswith("$ ")), "")
    if f"--python {spec['python']} " not in install:
        problems.append("interpreter differs")
    torch_steps = [line for line in commands if " torch==" in line]
    if [f" torch=={spec['torch']} " in line for line in torch_steps] != ([True] if spec["torch"] else []):
        problems.append("CPU torch differs")
    if f"[{spec['extras']}] " not in install:
        problems.append("extras differ")
    if f"/{spec['lock']}" not in install:
        problems.append("lock path differs")
    marker = spec["pytest_args"]
    if marker and f" -m {marker[1]} " not in cmd:  # type: ignore[index]
        problems.append("marker expression differs")
    if not marker and cmd.count(" -m ") != 1:  # only ``python -m pytest``
        problems.append("a marker expression was passed")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True)
    parser.add_argument("--src-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo", action="append", choices=sorted(CONSUMERS), help="limit to these repos (repeatable)")
    parser.add_argument("--print-only", action="store_true", help="print each argv and run nothing")
    parser.add_argument("--verify-against", type=Path, help="a prior runs directory: compare the recorded invocations with its logs, run nothing")
    args = parser.parse_args()
    if args.verify_against:
        bad = 0
        for repo in args.repo or list(CONSUMERS):
            problems = _verify(repo, args.verify_against)
            print(f"{repo}: {'MATCHES' if not problems else 'DIFFERS: ' + '; '.join(problems)}")
            bad += bool(problems)
        return 1 if bad else 0
    worst = 0
    for repo in args.repo or list(CONSUMERS):
        argv = _argv(repo, args.label, args.src_root, args.out)
        if args.print_only:
            print(" ".join(argv))
            continue
        proc = subprocess.run(argv, capture_output=True, text=True)  # nosec B603
        record = args.out.parent / f"runs-{CONSUMERS[repo]['short']}-{args.label}.out"
        record.write_text(proc.stdout + proc.stderr + f"exit {proc.returncode}\n")
        try:
            brief = json.loads(proc.stdout)
            line = f"{repo}-{args.label}: {brief['result']}; wire probe: {brief['wire_probe']['result']}; pytest: {brief['pytest']['summary']} (exit {brief['pytest']['exit']}); pin_drift: {brief['pin_drift'] or 'none'}"
        except (json.JSONDecodeError, KeyError, TypeError):
            line = f"{repo}-{args.label}: driver exit {proc.returncode}; see {record}"
        print(line, flush=True)
        worst = max(worst, proc.returncode)
    return worst


if __name__ == "__main__":
    sys.exit(main())
