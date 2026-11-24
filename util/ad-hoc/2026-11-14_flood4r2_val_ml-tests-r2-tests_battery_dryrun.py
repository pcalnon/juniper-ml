"""
Execute main-verify.yml's "Run Python regression battery" script with a stub python3, to show which lines it reaches.

The step's own ``run:`` text is extracted from --tree's workflow and executed the way a GitHub-hosted runner runs a
step with no ``shell:`` key (``bash -e <file>``), with a stub ``python3`` first on PATH that records its argv and
exits 0 -- or 1 for the suite named by --fail. The recorded suites are compared, in order, with the battery list
parsed from the same text: a line the script never reaches, or a failure that does not fail the step, shows here.
Nothing is imported or run from the tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_val_ml-tests-r2-tests_battery_check.py (the order check)

Usage:
    python3 <this file> --tree <landed tree> --work <scratch dir> --out <json> [--fail tests/test_x.py]
"""

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import yaml

LINE_RE = re.compile(r"^\s*python3 -m unittest(?: -[A-Za-z]+)* (?P<suite>\S+)\s*$")
STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$BATTERY_DRYRUN_LOG"
last=""
for arg in "$@"; do last="$arg"; done
if [ -n "$BATTERY_DRYRUN_FAIL" ] && [ "$last" = "$BATTERY_DRYRUN_FAIL" ]; then exit 1; fi
exit 0
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--work", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--fail", default="")
    args = parser.parse_args(argv)

    workflow = yaml.safe_load((Path(args.tree) / ".github" / "workflows" / "main-verify.yml").read_text(encoding="utf-8"))
    steps = [item for item in workflow["jobs"]["battery"]["steps"] if item.get("name") == "Run Python regression battery"]
    if len(steps) != 1 or "shell" in steps[0]:
        raise SystemExit("expected one battery step with no shell key, found %d" % len(steps))
    script = steps[0]["run"]
    expected = [m.group("suite") for m in (LINE_RE.match(line) for line in script.splitlines()) if m]

    work = Path(args.work)
    (work / "bin").mkdir(parents=True, exist_ok=True)
    stub = work / "bin" / "python3"
    stub.write_text(STUB, encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    step_file = work / "battery_step.sh"
    step_file.write_text(script, encoding="utf-8")
    log = work / ("calls%s.log" % ("_fail" if args.fail else ""))
    log.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env.update({"PATH": str(work / "bin") + os.pathsep + env.get("PATH", ""), "BATTERY_DRYRUN_LOG": str(log), "BATTERY_DRYRUN_FAIL": args.fail})
    done = subprocess.run(["bash", "-e", str(step_file)], cwd=str(args.tree), env=env, capture_output=True, text=True, check=False)
    calls = [line.split()[-1] for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    flags_ok = all(line.startswith("-m unittest -v ") for line in log.read_text(encoding="utf-8").splitlines() if line.strip())
    if args.fail:
        stop = expected.index(args.fail) + 1 if args.fail in expected else None
        reached_as_expected = stop is not None and calls == expected[:stop]
    else:
        reached_as_expected = calls == expected
    result = {"tree": args.tree, "fail": args.fail or None, "step_exit": done.returncode, "expected_lines": len(expected), "calls": len(calls), "calls_in_order_as_expected": reached_as_expected, "argv_shape_ok": flags_ok, "stderr_tail": done.stderr.strip().splitlines()[-3:]}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
