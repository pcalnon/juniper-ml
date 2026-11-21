#!/usr/bin/env python3
"""
Compare, test by test, the suites that fail in the carrier with the same suites on a clean main.

"The suite fails on main too" is not enough: a suite can fail in both trees for different tests, and a carrier
defect would hide behind a failure the host already has. So the failing and erroring test ids of each suite are
read from both runs' logs (`unittest -v`: the `FAIL:` / `ERROR:` headings) and the two sets are compared.

Usage:
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_compare_failures.py --carrier-logs <dir> --main-logs <dir>
        --out <json> SUITE [SUITE ...]

A suite's log is the newest of `<suite with / as __>.alone.log` and `.parallel.log` in each directory.
Exit 0 when every suite fails with exactly the same test ids in both trees; 1 otherwise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_run_suites.py (which writes the logs)
"""

import argparse
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(FAIL|ERROR): (\S+) \(([^)]+)\)", re.M)


def _ids(logs: Path, suite: str) -> tuple:
    stem = suite.replace("/", "__")
    candidates = [path for path in (logs / f"{stem}.alone.log", logs / f"{stem}.parallel.log") if path.is_file()]
    if not candidates:
        raise SystemExit(f"no log for {suite} in {logs}")
    log = max(candidates, key=lambda path: path.stat().st_mtime)
    return sorted({f"{kind}: {name} ({where})" for kind, name, where in HEADING.findall(log.read_text(encoding="utf-8", errors="replace"))}), str(log)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carrier-logs", required=True)
    ap.add_argument("--main-logs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("suites", nargs="+")
    args = ap.parse_args()
    rows, same = [], True
    for suite in args.suites:
        carrier, carrier_log = _ids(Path(args.carrier_logs), suite)
        main_ids, main_log = _ids(Path(args.main_logs), suite)
        identical = carrier == main_ids and bool(carrier)
        same = same and identical
        rows.append({"suite": suite, "failing_ids": len(carrier), "identical_on_clean_main": identical, "only_in_carrier": sorted(set(carrier) - set(main_ids)), "only_on_main": sorted(set(main_ids) - set(carrier)), "ids": carrier, "carrier_log": carrier_log, "main_log": main_log})
        print(f"{suite}: {len(carrier)} failing ids in the carrier, {len(main_ids)} on clean main -> {'identical' if identical else 'DIFFERENT'}")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
