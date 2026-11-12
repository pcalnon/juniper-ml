"""
Run one JuniperCascor1 python invocation (pytest, coverage, a script) in a juniper-cascor tree, logged, with cascor's test hygiene.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge)

Usage: python3 <this> <log> --cwd <tree> [--switchinterval S] [--taskset CPU] [--fresh-coverage] -- <python args ...>

Runs ``/opt/miniforge3/envs/JuniperCascor1/bin/python <python args>`` with cwd=<tree>:
- JUNIPER_CASCOR_LOG_DIR is removed (cascor's AGENTS.md: six tests assert its unset fallback);
- TMPDIR is left exactly as the session set it (pointing it at a worktree makes CPython's
  multiprocessing fall back to the system temp directory); only its length is logged;
- PYTHONDONTWRITEBYTECODE=1, so no stale .pyc answers for an edited source;
- PYTHONPATH is a temporary directory holding two pytest plugins written by this script:
  ``n1r3_provenance`` (printed at session end: the file each lifecycle module was imported from,
  and the GIL switch interval in effect) and ``n1r3_switch`` (sets ``sys.setswitchinterval(S)``).
  For a ``-m pytest`` run, ``-p n1r3_provenance`` is appended, and ``-p n1r3_switch`` with
  --switchinterval;
- --taskset pins the process to one CPU (``taskset -c CPU``);
- --fresh-coverage deletes src/tests/reports/.coverage and .coverage.* first (CI starts empty);
- CI's directories (logs, src/logs, reports/junit, reports/htmlcov, src/tests/reports) are made.
The log gets the command, start/end UTC, the load average, the exit status read from the child
itself (never through a pipe), and that status is returned. No environment variable is printed.
"""

import argparse
import datetime
import os
import subprocess  # nosec B404 -- fixed interpreter, operator-supplied argv
import sys
import tempfile
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
PROVENANCE = '''import sys

_MODULES = ("api.lifecycle.manager", "api.lifecycle.state_machine")


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    lines = [f"PROVENANCE {name} -> {getattr(sys.modules.get(name), '__file__', None)}" for name in _MODULES]
    lines.append(f"PROVENANCE switchinterval -> {sys.getswitchinterval()}")
    for line in lines:
        if reporter is not None:
            reporter.write_line(line)
        else:
            print(line)
'''
SWITCH = '''import sys


def pytest_configure(config):
    sys.setswitchinterval({interval!r})
'''


def _utc() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load() -> str:
    with open("/proc/loadavg", encoding="ascii") as fh:
        return " ".join(fh.read().split()[:3])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--switchinterval", type=float)
    parser.add_argument("--taskset")
    parser.add_argument("--fresh-coverage", action="store_true")
    argv_in = sys.argv[1:]
    if "--" not in argv_in:
        parser.error("the python arguments follow a '--'")
    split = argv_in.index("--")
    args = parser.parse_args(argv_in[:split])
    rest = argv_in[split + 1 :]
    cwd = Path(args.cwd).resolve()
    log_path = Path(args.log).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    for rel in ("logs", "src/logs", "reports/junit", "reports/htmlcov", "src/tests/reports"):
        (cwd / rel).mkdir(parents=True, exist_ok=True)
    if args.fresh_coverage:
        for stale in (cwd / "src" / "tests" / "reports").glob(".coverage*"):
            stale.unlink()

    with tempfile.TemporaryDirectory(prefix="n1r3-plugins-") as plugins:
        (Path(plugins) / "n1r3_provenance.py").write_text(PROVENANCE, encoding="utf-8")
        argv = [PYTHON, *rest]
        if rest[:2] == ["-m", "pytest"]:
            argv += ["-p", "n1r3_provenance"]
            if args.switchinterval is not None:
                (Path(plugins) / "n1r3_switch.py").write_text(SWITCH.format(interval=args.switchinterval), encoding="utf-8")
                argv += ["-p", "n1r3_switch"]
        if args.taskset is not None:
            argv = ["taskset", "-c", args.taskset, *argv]
        env = {key: value for key, value in os.environ.items() if key != "JUNIPER_CASCOR_LOG_DIR"}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = plugins
        with open(log_path, "w", encoding="utf-8") as log:
            log.write(f"$ (cwd={cwd}) {' '.join(argv)}\n")
            log.write(f"# start {_utc()}; load {_load()}; JUNIPER_CASCOR_LOG_DIR unset; TMPDIR length {len(env.get('TMPDIR', ''))} (untouched); PYTHONDONTWRITEBYTECODE=1\n")
            log.flush()
            proc = subprocess.run(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)  # nosec B603
            log.write(f"\n# end {_utc()}; load {_load()}; exit status {proc.returncode}\n")
    print(f"{log_path.name}: exit status {proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
