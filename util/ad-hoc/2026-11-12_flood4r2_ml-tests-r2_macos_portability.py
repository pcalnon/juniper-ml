#!/usr/bin/env python3
"""
What can be shown, off a Mac, about running the agent guard's suites in ci.yml's host-tooling-macos job.

The job runs on macos-latest, where /bin/bash is 3.2 and /usr/bin/python3 is 3.9, and its steps run each suite
with the `python3` that `actions/setup-python` puts first on PATH. For each suite named on the command line this
script records four things on a Linux host:

  1. PARSE     -- the suite, and every first-party module it imports (tests/*.py, util/claude_agent_guard.py),
                  parses with `ast.parse(..., feature_version=(3, 9))`: no syntax newer than Python 3.9;
  2. RUN 3.9   -- `<python 3.9> -m unittest -v <suite>` passes, one process per suite, so the suite and the guard
                  it drives (`sys.executable -I util/claude_agent_guard.py`, or an in-process import) use no
                  library call newer than 3.9;
  3. EXECS     -- under `strace -f -e trace=execve`, every program the suite starts: a suite that starts only
                  the Python interpreter needs no bash at all (so bash 3.2 cannot matter), no git and no GnuPG;
  4. TIMING    -- the wall time of the 3.9 run, the slowest interpreter here, for suites with a time bound.

A control suite (--control) is run the same way and is expected to start /bin/bash: it shows the exec census
sees a shell when one is started.

Not shown by any of this, and only the pull request's own macOS job can show it: Apple's /usr/bin/python3 build,
temporary directories under /var (a symlink to /private/var), APFS, and the runner's speed.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_macos_portability.py --python39 <path> --out <dir>
        [--control tests/test_claude_agent_guard.py] SUITE [SUITE ...]

Exit 0 when every suite parses as 3.9, passes under 3.9 and starts nothing but a Python interpreter.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tests/test_ci_host_tooling_macos.py; .github/workflows/ci.yml (host-tooling-macos)
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
GUARD = "util/claude_agent_guard.py"
EXEC_OK = re.compile(r'execve(?:at)?\((?:AT_FDCWD, )?"([^"]+)".*\) = 0$')


def _env() -> dict:
    return {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "PYTHONDONTWRITEBYTECODE": "1"}


def _first_party(suite: str) -> list:
    """The suite, tests/*.py modules it imports (one level deep is all these suites use), and the guard."""
    seen, queue = [], [suite]
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.append(path)
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("tests."):
                queue.append(node.module.replace(".", "/") + ".py")
    return seen + [GUARD]


def _parse_39(paths: list) -> dict:
    out = {}
    for path in paths:
        try:
            ast.parse(Path(path).read_text(encoding="utf-8"), filename=path, feature_version=(3, 9))
            out[path] = "ok"
        except SyntaxError as exc:
            out[path] = f"SyntaxError line {exc.lineno}: {exc.msg}"
    return out


def _run(argv: list, log: Path) -> dict:
    started = time.monotonic()
    proc = subprocess.run(argv, capture_output=True, text=True, env=_env(), check=False, timeout=1800)
    text = proc.stdout + proc.stderr
    log.write_text(text, encoding="utf-8")
    ran = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s", text, re.M)
    skipped = re.search(r"skipped=(\d+)", text)
    return {"rc": proc.returncode, "ran": int(ran[-1][0]) if ran else None, "unittest_secs": float(ran[-1][1]) if ran else None, "skipped": int(skipped.group(1)) if skipped else 0, "wall_secs": round(time.monotonic() - started, 1), "log": str(log)}


def _execs(suite: str, out: Path, stem: str) -> dict:
    trace = out / f"{stem}.strace"
    run = _run(["strace", "-f", "-qq", "-e", "trace=execve,execveat", "-o", str(trace), sys.executable, "-m", "unittest", "-v", suite], out / f"{stem}.strace_run.log")
    programs = {}
    for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
        match = EXEC_OK.search(line)
        if match:
            programs[match.group(1)] = programs.get(match.group(1), 0) + 1
    interpreters = {os.path.realpath(sys.executable), sys.executable}
    other = {program: count for program, count in programs.items() if os.path.realpath(program) not in interpreters and program not in interpreters}
    return {"rc": run["rc"], "ran": run["ran"], "programs": programs, "not_the_interpreter": other, "trace": str(trace)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--python39", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--control", default="")
    ap.add_argument("suites", nargs="+")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([args.python39, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    if not version.startswith("Python 3.9."):
        raise SystemExit(f"--python39 is {version}")
    rows, ok = [], True
    for suite in args.suites + ([args.control] if args.control else []):
        stem = Path(suite).stem
        row = {"suite": suite, "control": suite == args.control}
        row["parse_3_9"] = _parse_39(_first_party(suite))
        row["run_3_9"] = _run([args.python39, "-m", "unittest", "-v", suite], out / f"{stem}.py39.log")
        row["run_here"] = _run([sys.executable, "-m", "unittest", "-v", suite], out / f"{stem}.here.log")
        row["execs"] = _execs(suite, out, stem)
        good = all(v == "ok" for v in row["parse_3_9"].values()) and row["run_3_9"]["rc"] == 0 and row["run_here"]["rc"] == 0 and row["execs"]["rc"] == 0
        if not row["control"]:
            good = good and not row["execs"]["not_the_interpreter"]
            ok = ok and good
        row["verdict"] = "ok" if good else "NOT OK"
        rows.append(row)
        started = sorted(row["execs"]["not_the_interpreter"]) or "nothing but the interpreter"
        print(f"{'CONTROL ' if row['control'] else ''}{suite}: parse 3.9 {'ok' if all(v == 'ok' for v in row['parse_3_9'].values()) else 'FAIL'}; " f"3.9 run rc={row['run_3_9']['rc']} ran={row['run_3_9']['ran']} skipped={row['run_3_9']['skipped']} ({row['run_3_9']['wall_secs']}s); " f"here rc={row['run_here']['rc']} ran={row['run_here']['ran']}; starts: {started}")
    report = {"python39": version, "interpreter_here": f"{sys.executable} ({sys.version.split()[0]})", "suites": rows, "all_ok": ok}
    with open(out / "macos_portability.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
