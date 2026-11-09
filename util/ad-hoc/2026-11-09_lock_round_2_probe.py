#!/usr/bin/env python3
"""The per-lock probe of R-OBS-SC-2's second lock round: build a venv from one consumer lock and probe it.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

What it is, and what it is not
------------------------------
The consolidated plan's Security step 4 asks each image lock PR to carry "S0.11's relay run".
S0.11's relay tests (a planted fake data key driven through every relay) do not exist for
juniper-data, -cascor or -canopy: A1's F-S10 rulings are open. On 2026-11-09 the owner chose this
per-lock probe instead (AskUserQuestion, "Per-lock probe (Recommended)"). Each PR body says it
is NOT S0.11's relay run.

Steps (each consumer lock, ``--label`` names the run, e.g. ``before`` / ``after``):

1. a fresh venv (``uv venv``) at ``<out>/<repo>-<label>/venv``; optional CPU torch first (cascor's
   image lock leaves torch to the Dockerfile), held to the lock by ``--constraint``;
2. ``uv pip install -r <lock>``, then the consumer itself with ``--extras`` under
   ``--constraint <lock>``, so every lock pin is held; the freeze is compared with the lock and
   any pin that differs is reported (``PIN-DRIFT``) and fails the run;
3. ``2026-11-09_lock_round_2_env_record.py`` (FastAPI's native-telemetry setting, OpenTelemetry
   distributions and provider, the DSN variables) -> ``record.json``;
4. ``2026-11-08_p3_07_sentry_wire_probe.py`` (P3-07's wire probe: the installed
   ``configure_sentry`` into a capturing transport; exit 0 CLEAN, 1 LEAK, 2 VACUOUS) when
   sentry-sdk is installed; otherwise recorded as not applicable;
5. the consumer's Sentry and security suites (``--suite``, repeatable) with pytest.

Every subprocess runs with the six Sentry DSN variables of plan H-14 set to ``""`` (never unset:
``load_dotenv`` re-injects them), and without ``LD_LIBRARY_PATH`` (this host's conda value breaks
torch) or ``JUNIPER_CASCOR_LOG_DIR`` (six cascor tests assert its unset fallback).

Output: ``<out>/<repo>-<label>/`` holds ``install.log``, ``freeze.txt``, ``record.json``,
``wire_probe.log``, ``pytest.log`` and ``summary.json``. Exit 0 when every step ran and the probe
and the suites passed (or the probe is not applicable), 1 otherwise.

Usage:
    python3 util/ad-hoc/2026-11-09_lock_round_2_probe.py --repo juniper-data --label before \
        --src tmp/lr2/src/juniper-data --lock tmp/lr2/src/juniper-data/requirements.lock \
        --python /opt/miniforge3/envs/JuniperCascor1/bin/python3.14 --extras test \
        --suite juniper_data/tests/unit/test_observability.py [--suite ...] \
        [--torch-cpu 2.14.0+cpu] [--pytest-arg=-m --pytest-arg="not slow"] --out tmp/lr2/runs
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
UV = shutil.which("uv") or "/opt/miniforge3/envs/JuniperCascor1/bin/uv"
SIX_DSNS = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
CPU_INDEX = "https://download.pytorch.org/whl/cpu"
# pytest's last line: ``==== 12 passed in 1.0s ====`` at verbosity 0, bare at -q (several repos' addopts
# carry -q, so this driver adds no -q of its own: -qq would suppress the line).
SUMMARY = re.compile(r"^=*\s*(\d+ (passed|failed|errors?|skipped|deselected|xfailed|xpassed)\b.*|no tests ran.*)\s*=*$")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    for name in SIX_DSNS:
        env[name] = ""
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("JUNIPER_CASCOR_LOG_DIR", None)
    env.pop("VIRTUAL_ENV", None)
    return env


def _run(argv: list[str], log: Path, cwd: Path | None = None) -> int:
    with log.open("a") as handle:
        handle.write(f"\n$ {' '.join(argv)}\n")
        handle.flush()
        proc = subprocess.run(argv, cwd=cwd, env=_env(), stdout=handle, stderr=subprocess.STDOUT)  # nosec B603
        handle.write(f"[exit {proc.returncode}]\n")
    return proc.returncode


def _pins(lock: Path) -> dict[str, str]:
    pins = {}
    for line in lock.read_text().splitlines():
        if line and not line.startswith((" ", "\t", "#")) and "==" in line:
            name, version = line.split(";")[0].strip().split("==", 1)
            pins[re.sub(r"[-_.]+", "-", name.strip().lower())] = version.strip()
    return pins


def _freeze(python: Path, out: Path) -> dict[str, str]:
    proc = subprocess.run([UV, "pip", "freeze", "--python", str(python)], capture_output=True, text=True, env=_env())  # nosec B603
    out.write_text(proc.stdout)
    installed = {}
    for line in proc.stdout.splitlines():
        if "==" in line:
            name, version = line.split("==", 1)
            installed[re.sub(r"[-_.]+", "-", name.strip().lower())] = version.strip()
        elif " @ " in line:
            installed[re.sub(r"[-_.]+", "-", line.split(" @ ")[0].strip().lower())] = "(direct)"
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--src", required=True, type=Path, help="the package directory (holds pyproject.toml)")
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--extras", default="")
    parser.add_argument("--suite", action="append", default=[])
    parser.add_argument("--pytest-arg", action="append", default=[])
    parser.add_argument("--torch-cpu", default="")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    run_dir = (args.out / f"{args.repo}-{args.label}").resolve()
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    src = args.src.resolve()
    lock = args.lock.resolve()
    venv = run_dir / "venv"
    python = venv / "bin" / "python"
    install_log = run_dir / "install.log"
    summary: dict[str, object] = {"repo": args.repo, "label": args.label, "lock": str(lock), "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    steps = [[UV, "venv", "--python", args.python, str(venv)]]
    if args.torch_cpu:
        steps.append([UV, "pip", "install", "--python", str(python), f"torch=={args.torch_cpu}", "--index-strategy", "unsafe-best-match", "--extra-index-url", CPU_INDEX, "--constraint", str(lock)])
    steps.append([UV, "pip", "install", "--python", str(python), "-r", str(lock)])
    target = f"{src}[{args.extras}]" if args.extras else str(src)
    steps.append([UV, "pip", "install", "--python", str(python), "-e", target, "--constraint", str(lock)])
    for argv in steps:
        if _run(argv, install_log) != 0:
            summary["result"] = f"INSTALL-FAILED at: {' '.join(argv[:4])}"
            (run_dir / "summary.json").write_text(json.dumps(summary, indent=1))
            print(json.dumps(summary, indent=1))
            return 1

    lock_pins = _pins(lock)
    installed = _freeze(python, run_dir / "freeze.txt")
    drift = {name: (version, installed.get(name)) for name, version in lock_pins.items() if installed.get(name) not in (version, "(direct)")}
    summary["lock_pins"] = len(lock_pins)
    summary["pin_drift"] = drift

    record = subprocess.run([str(python), "-I", str(HERE / "2026-11-09_lock_round_2_env_record.py")], capture_output=True, text=True, env=_env())  # nosec B603
    (run_dir / "record.json").write_text(record.stdout + record.stderr)
    try:
        summary["record"] = json.loads(record.stdout)
    except json.JSONDecodeError:
        summary["record"] = f"FAILED (exit {record.returncode}); see record.json"

    has_sentry = "sentry-sdk" in installed
    if has_sentry:
        probe_log = run_dir / "wire_probe.log"
        code = _run([str(python), "-I", str(HERE / "2026-11-08_p3_07_sentry_wire_probe.py")], probe_log)
        result_line = next((line for line in probe_log.read_text().splitlines() if line.startswith(("RESULT:", "VACUOUS:"))), "no RESULT line")
        summary["wire_probe"] = {"exit": code, "result": result_line}
    else:
        summary["wire_probe"] = {"exit": None, "result": "N/A: sentry-sdk is not installed from this lock"}

    if args.suite:
        pytest_log = run_dir / "pytest.log"
        argv = [str(python), "-m", "pytest", "-p", "no:cacheprovider", *args.pytest_arg, *args.suite]
        if "pytest-cov" in installed:
            argv.insert(3, "--no-cov")
        code = _run(argv, pytest_log, cwd=src)
        lines = [line for line in pytest_log.read_text().splitlines() if SUMMARY.match(line)]
        summary["pytest"] = {"exit": code, "summary": lines[-1] if lines else "no summary line", "suites": args.suite}
    else:
        summary["pytest"] = {"exit": None, "summary": "no suites requested"}

    probe_ok = summary["wire_probe"]["exit"] in (0, None)  # type: ignore[index]
    suites_ok = summary["pytest"]["exit"] in (0, None)  # type: ignore[index]
    summary["result"] = "PASS" if (probe_ok and suites_ok and not drift) else "FAIL"
    summary["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=repr))
    brief = {key: summary[key] for key in ("repo", "label", "result", "lock_pins", "pin_drift", "wire_probe", "pytest")}
    print(json.dumps(brief, indent=1, default=repr))
    return 0 if summary["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
