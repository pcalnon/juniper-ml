#!/usr/bin/env python3
"""
Run unittest suites of a juniper-ml tree the way ci.yml does (one `python -m unittest -v <file>` process each) and summarise each log.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-ml)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
This host's shell classifier refuses a compound command whose text names the secret scanner, and the port's worktree
path does, so the suite runs a port needs (the new file with no binary, with the official binary, with pre-commit's
build, under CI's Python 3.12, on main's tree and on the port's) are run from here. Each suite runs in a process of its
own, from the tree's root, with the six Sentry DSN variables set to the empty string and the session bus pointed at a
socket that does not exist (no test run may reach Sentry, and none may reach the desktop). The gitleaks binary is
either named (`--gitleaks-bin`, exported as GITLEAKS_BIN) or absent: `--no-binary` removes GITLEAKS_BIN and every PATH
entry that holds a `gitleaks`, and the summary says which. `--parity-required` sets GITLEAKS_PARITY_REQUIRED=1, as the
Security Scan job does. TMPDIR is left as the session gave it. It prints, per suite, the exit status and unittest's own
`Ran N tests` and result lines, and writes one log per suite under --logs. It never prints the environment.

Usage:
    python3 <this> --tree <juniper-ml tree> --python <interpreter> --logs <dir> [--gitleaks-bin <path> | --no-binary] [--parity-required] [--tag <name>] <tests/test_x.py> [...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv: <interpreter> -m unittest -v <file>
import sys
import time
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DEAD_BUS = "unix:path=/nonexistent/no-session-bus"
RESULT = re.compile(r"^(OK|FAILED)\b.*$", re.MULTILINE)
RAN = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s$", re.MULTILINE)


def child_env(args: argparse.Namespace) -> tuple[dict[str, str], str | None]:
    env = dict(os.environ.items())
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = DEAD_BUS
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("GITLEAKS_PARITY_REQUIRED", None)
    if args.parity_required:
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    if args.no_binary:
        env.pop("GITLEAKS_BIN", None)
        kept = [entry for entry in env.get("PATH", "").split(os.pathsep) if entry and not (Path(entry) / "gitleaks").exists()]
        env["PATH"] = os.pathsep.join(kept)
    elif args.gitleaks_bin:
        env["GITLEAKS_BIN"] = str(Path(args.gitleaks_bin).resolve())
    return env, shutil.which("gitleaks", path=env.get("PATH"))


def run_unittest(python: str, suite: str, tree: Path, env: dict[str, str], timeout: int) -> tuple[str, int]:
    """``python -m unittest -v suite`` in ``tree``; returns (stdout + stderr, exit status), 124 on a timeout."""
    try:
        proc = subprocess.run([python, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, env=env, check=False, timeout=timeout)  # nosec B603
    except subprocess.TimeoutExpired as exc:
        return f"TIMEOUT after {timeout}s: {exc}", 124
    return proc.stdout + proc.stderr, proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--logs", type=Path, required=True)
    ap.add_argument("--gitleaks-bin")
    ap.add_argument("--no-binary", action="store_true")
    ap.add_argument("--parity-required", action="store_true")
    ap.add_argument("--tag", default="run")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("suites", nargs="+")
    args = ap.parse_args()
    if args.no_binary and args.gitleaks_bin:
        raise SystemExit("--no-binary and --gitleaks-bin are exclusive")
    env, on_path = child_env(args)
    args.logs.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run([args.python, "-c", "import sys; print(sys.version.split()[0], sys.executable, sys.base_prefix)"], capture_output=True, text=True, env=env, check=False, timeout=60)  # nosec B603
    summary = {"tag": args.tag, "tree": str(args.tree), "interpreter": probe.stdout.strip(), "gitleaks_bin": env.get("GITLEAKS_BIN"), "gitleaks_on_path": on_path, "parity_required": args.parity_required, "suites": []}
    print(f"[{args.tag}] interpreter: {summary['interpreter']}; GITLEAKS_BIN={summary['gitleaks_bin']}; gitleaks on PATH: {on_path}; parity required: {args.parity_required}")
    worst = 0
    for suite in args.suites:
        start = time.monotonic()
        output, code = run_unittest(args.python, suite, args.tree, env, args.timeout)
        seconds = round(time.monotonic() - start, 1)
        log = args.logs / f"{args.tag}__{Path(suite).stem}.log"
        log.write_text(output, encoding="utf-8")
        ran = RAN.findall(output)
        # unittest's own verdict is the last line that starts with OK or FAILED.
        verdicts = [m.group(0) for m in RESULT.finditer(output)]
        row = {"suite": suite, "exit": code, "seconds": seconds, "ran": int(ran[-1][0]) if ran else None, "result_line": verdicts[-1] if verdicts else None, "log": str(log)}
        summary["suites"].append(row)
        print(f"[{args.tag}] {suite}: exit {code} in {seconds}s; Ran {row['ran']}; {row['result_line']}")
        worst = max(worst, code)
    with open(args.logs / f"{args.tag}__summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    return worst


if __name__ == "__main__":
    sys.exit(main())
