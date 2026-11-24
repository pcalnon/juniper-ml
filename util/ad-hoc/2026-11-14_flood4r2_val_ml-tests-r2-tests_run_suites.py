"""
Run named unittest suites under a chosen interpreter, one process each, and count what ran (stdlib only).

Each suite runs as ``<python> -m unittest -v <suite>`` from --root, with the six Sentry DSN variables set to the
empty string, a dead session-bus address, and --path-prefix put first on PATH (so a child that runs ``python3``
gets the same interpreter). Per suite it records the exit status, ``Ran N``, the skipped count, the failing ids,
and the ``def test_`` count by ast, and --repeat runs the whole set N times (a flake shows as a status that differs
between rounds).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --root <tree> --python <interpreter> --out <json> --logs <dir> [--path-prefix DIR]
        [--repeat N] [--jobs 1..4] --suites tests/test_a.py ...
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
RAN_RE = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s", re.M)
ID_RE = re.compile(r"^(?P<kind>FAIL|ERROR): (?P<name>\S+) \((?P<where>[^)]*)\)", re.M)


def child_env(prefix):
    env = dict(os.environ)
    for name in SENTRY_DSN_NAMES:
        env[name] = ""
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if prefix:
        env["PATH"] = prefix + os.pathsep + env.get("PATH", "")
    return env


def def_tests(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    count = 0
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            count += sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"))
    return count


def run_one(root, python, prefix, logs, suite, tag, timeout):
    started = time.monotonic()
    try:
        proc = subprocess.run([python, "-m", "unittest", "-v", suite], cwd=str(root), capture_output=True, text=True, timeout=timeout, check=False, env=child_env(prefix))
        rc, text = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, text = 124, "TIMEOUT after %ss\n%s%s" % (timeout, exc.stdout or "", exc.stderr or "")
    (Path(logs) / ("%s.%s.log" % (suite.replace("/", "__"), tag))).write_text(text, encoding="utf-8")
    ran = RAN_RE.findall(text)
    return {
        "suite": suite,
        "rc": rc,
        "ran": int(ran[-1][0]) if ran else None,
        "skipped": len(re.findall(r"\.\.\. skipped", text)),
        "failing_ids": sorted({"%s %s (%s)" % (m.group("kind"), m.group("name"), m.group("where")) for m in ID_RE.finditer(text)}),
        "last_line": text.strip().splitlines()[-1] if text.strip() else "",
        "wall_secs": round(time.monotonic() - started, 2),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--path-prefix", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--logs", required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--suites", nargs="+", default=[])
    parser.add_argument("--glob", help="suites as a glob relative to --root (added to --suites, sorted)")
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 4:
        raise SystemExit("--jobs must be 1..4")
    if args.glob:
        args.suites = list(args.suites) + sorted(str(path.relative_to(args.root)) for path in Path(args.root).glob(args.glob))
    if not args.suites:
        raise SystemExit("no suites")

    Path(args.logs).mkdir(parents=True, exist_ok=True)
    probe = subprocess.run([args.python, "-c", "import sys; print(sys.version.split()[0], sys.executable, sys.base_prefix)"], capture_output=True, text=True, check=False, env=child_env(args.path_prefix))
    child_python3 = subprocess.run(["python3", "-c", "import sys; print(sys.version.split()[0], sys.executable)"], capture_output=True, text=True, check=False, env=child_env(args.path_prefix))
    rounds = []
    for number in range(1, args.repeat + 1):
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            rows = list(pool.map(lambda suite, n=number: run_one(args.root, args.python, args.path_prefix, args.logs, suite, "r%d" % n, args.timeout), args.suites))
        rounds.append(rows)
        print("round %d: %s" % (number, " ".join("%s=%s/%s" % (row["suite"].rsplit("/", 1)[-1], row["rc"], row["ran"]) for row in rows)), flush=True)
    summary = []
    for index, suite in enumerate(args.suites):
        statuses = [item[index]["rc"] for item in rounds]
        summary.append({"suite": suite, "def_test": def_tests(Path(args.root) / suite), "ran": [item[index]["ran"] for item in rounds], "rc": statuses, "skipped": [item[index]["skipped"] for item in rounds], "stable": len(set(statuses)) == 1, "wall_secs": [item[index]["wall_secs"] for item in rounds]})
    result = {"root": args.root, "python": probe.stdout.strip(), "child_python3": child_python3.stdout.strip(), "rounds": rounds, "summary": summary}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print("interpreter:", result["python"], "| child python3:", result["child_python3"])
    for row in summary:
        print("  %-58s def_test=%-3s ran=%s rc=%s skipped=%s stable=%s" % (row["suite"], row["def_test"], row["ran"], row["rc"], row["skipped"], row["stable"]))
    return 0 if all(all(rc == 0 for rc in row["rc"]) for row in summary) else 1


if __name__ == "__main__":
    sys.exit(main())
