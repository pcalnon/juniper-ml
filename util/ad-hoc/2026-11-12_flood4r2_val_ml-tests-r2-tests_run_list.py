"""
Re-derive CI's regression list from a tree's ci.yml and run it, one process per suite, for the tests-lens validator.

The list is read from the workflow itself (job `tests`, step "Run Python regression tests"): every line of that
step's script that starts a `python3 -m unittest` process, in order, duplicates reported. Each suite then runs as
its own `<interpreter> -m unittest -v <suite>` process from the tree's root, at most --jobs at a time. A suite that
fails in the parallel pass is run again alone. The failing test ids of every failure are parsed from the output.

Every child gets the six Sentry DSN variables set to the empty string and a dead session-bus address, so no run can
reach Sentry or send a desktop notification.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --root <tree> --list-only --out <json>
    python3 <this file> --root <tree> --out <json> --logs <dir> [--jobs 4] [--only SUITE ...] [--repeat N]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DEAD_BUS = "unix:path=/nonexistent/no-session-bus"
STEP_NAME = "Run Python regression tests"
LINE_RE = re.compile(r"^\s*python3 -m unittest(?P<flags>(?: -[A-Za-z]+)*) (?P<suite>\S+)\s*$")
ID_RE = re.compile(r"^(?P<kind>FAIL|ERROR): (?P<name>\S+) \((?P<where>[^)]*)\)", re.M)
RAN_RE = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s", re.M)


def child_env():
    env = dict(os.environ)
    for name in SENTRY_DSN_NAMES:
        env[name] = ""
    env["DBUS_SESSION_BUS_ADDRESS"] = DEAD_BUS
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def regression_list(root):
    """The suites of the regression step, in order, with every non-comment line that is not a suite line."""
    with open(Path(root) / ".github" / "workflows" / "ci.yml", encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    steps = workflow["jobs"]["tests"]["steps"]
    matches = [step for step in steps if step.get("name") == STEP_NAME]
    if len(matches) != 1:
        raise SystemExit("expected one step named %r, found %d" % (STEP_NAME, len(matches)))
    suites, other = [], []
    for line in matches[0]["run"].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        found = LINE_RE.match(line)
        if found:
            suites.append({"suite": found.group("suite"), "flags": found.group("flags").strip()})
        else:
            other.append(stripped)
    return suites, other


def run_one(root, logs, suite, timeout, tag):
    started = time.monotonic()
    argv = [sys.executable, "-m", "unittest", "-v", suite]
    try:
        proc = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, timeout=timeout, check=False, env=child_env())
        rc, out = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = "TIMEOUT after %ss\n%s%s" % (timeout, exc.stdout or "", exc.stderr or "")
    log = Path(logs) / (suite.replace("/", "__") + "." + tag + ".log")
    log.write_text(out if isinstance(out, str) else str(out), encoding="utf-8")
    ran = RAN_RE.findall(out)
    ids = sorted({"%s %s (%s)" % (m.group("kind"), m.group("name"), m.group("where")) for m in ID_RE.finditer(out)})
    last = out.strip().splitlines()[-1] if out.strip() else ""
    return {
        "suite": suite,
        "rc": rc,
        "ok": rc == 0,
        "ran": int(ran[-1][0]) if ran else None,
        "unittest_secs": float(ran[-1][1]) if ran else None,
        "wall_secs": round(time.monotonic() - started, 2),
        "last_line": last,
        "failing_ids": ids,
        "log": str(log),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--logs")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--list-only", action="store_true")
    parser.add_argument("--tag", default="run")
    args = parser.parse_args(argv)
    if args.jobs > 4:
        raise SystemExit("at most 4 workers")

    root = Path(args.root).resolve()
    listed, other = regression_list(root)
    names = [row["suite"] for row in listed]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    missing = [name for name in names if not (root / name).is_file()]
    summary = {
        "root": str(root),
        "interpreter": "%s (%s)" % (sys.executable, sys.version.split()[0]),
        "suite_lines": len(names),
        "distinct_suites": len(set(names)),
        "duplicates": duplicates,
        "missing_files": missing,
        "flags_seen": sorted({row["flags"] for row in listed}),
        "non_suite_lines": other,
        "order": names,
    }
    if args.list_only:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=1)
            fh.write("\n")
        print("suite_lines=%d distinct=%d duplicates=%s missing=%s flags=%s non_suite_lines=%d" % (len(names), len(set(names)), duplicates, missing, summary["flags_seen"], len(other)))
        return 0

    logs = Path(args.logs)
    logs.mkdir(parents=True, exist_ok=True)
    suites = list(dict.fromkeys(args.only)) if args.only else list(dict.fromkeys(names))
    started = time.monotonic()
    rounds = []
    for number in range(1, args.repeat + 1):
        tag = "%s%d" % (args.tag, number)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            first = list(pool.map(lambda name, tag=tag: run_one(root, logs, name, args.timeout, tag + ".parallel"), suites))
        alone = []
        for row in first:
            if not row["ok"]:
                alone.append(run_one(root, logs, row["suite"], args.timeout, tag + ".alone"))
        rounds.append({"round": number, "parallel": first, "alone": alone})
        failed_parallel = [row["suite"] for row in first if not row["ok"]]
        failed_alone = [row["suite"] for row in alone if not row["ok"]]
        print("round %d: %d suites, %d tests, parallel failures %s, failing alone %s (%.0fs so far)" % (number, len(first), sum(row["ran"] or 0 for row in first), failed_parallel, failed_alone, time.monotonic() - started), flush=True)
    summary["rounds"] = rounds
    summary["suites_run"] = suites
    summary["total_wall_secs"] = round(time.monotonic() - started, 1)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    any_alone = any(row for item in rounds for row in item["alone"] if not row["ok"])
    return 1 if any_alone else 0


if __name__ == "__main__":
    sys.exit(main())
