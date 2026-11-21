"""
Print selected rows of the lockfile-print validation harness result: main's and the carrier's output for named scenarios.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", required=True, type=Path)
    parser.add_argument("--shell", default="bash-e")
    parser.add_argument("--merged-only", action="store_true")
    parser.add_argument("scenarios", nargs="+")
    args = parser.parse_args()
    with open(args.harness, encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    for row in rows:
        if row["shell"] != args.shell or row["scenario"] not in args.scenarios:
            continue
        print(f"===== {row['scenario']} [{row['shell']}] gh_rc={row['gh_rc']} signal={row['gh_signal']!r}")
        if not args.merged_only:
            for variant in ("main", "fix"):
                run = row[variant]
                print(f"--- {variant}: rc={run['rc']} gh_called={run['gh_called']} token_printed={run['token_printed']}")
                print(f"    stdout={run['stdout']!r}")
                print(f"    stderr={run['stderr']!r}")
        print("--- main merged log (stdout+stderr in write order):")
        print(row["main_merged_log"], end="" if row["main_merged_log"].endswith("\n") else "\n")
        print("--- fix merged log (stdout+stderr in write order):")
        print(row["fix_merged_log"], end="" if row["fix_merged_log"].endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
