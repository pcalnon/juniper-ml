#!/usr/bin/env python3
"""
Compare two JUnit XML results of canopy's unit-lane selection: clean main vs the flood-4 tests carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; flood-4 validation brief (CI-parity lens)

Prints per-run totals, the failing/erroring test ids of each run (with the first line of each message),
whether the two failure sets are identical, and which test ids exist only in the carrier run (they should
be exactly the carried files' tests) or only in main's run (they should be none).

    python3 2026-11-07_flood4_val_canopy_lane_compare.py <main junit xml> <carrier junit xml>
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET  # nosec B405 - parsing our own pytest output


def load(path: str) -> tuple[dict[str, str], dict[str, str]]:
    root = ET.parse(path).getroot()  # nosec B314 - our own pytest junit file
    outcomes: dict[str, str] = {}
    messages: dict[str, str] = {}
    for case in root.iter("testcase"):
        tid = f"{case.get('classname')}::{case.get('name')}"
        status = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                status = child.tag
                messages[tid] = (child.get("message") or "").splitlines()[0][:200] if child.get("message") else ""
            elif child.tag == "skipped":
                status = "skipped"
        outcomes[tid] = status
    return outcomes, messages


def main() -> int:
    main_out, main_msg = load(sys.argv[1])
    car_out, car_msg = load(sys.argv[2])
    for label, out in (("main", main_out), ("carrier", car_out)):
        counts: dict[str, int] = {}
        for status in out.values():
            counts[status] = counts.get(status, 0) + 1
        print(f"{label}: {len(out)} cases {counts}")
    bad_main = {t for t, s in main_out.items() if s in ("failure", "error")}
    bad_car = {t for t, s in car_out.items() if s in ("failure", "error")}
    print("main failures:")
    for tid in sorted(bad_main):
        print(f"    {tid}: {main_msg.get(tid, '')}")
    print("carrier failures:")
    for tid in sorted(bad_car):
        print(f"    {tid}: {car_msg.get(tid, '')}")
    print(f"failure sets identical: {bad_main == bad_car}")
    only_car = sorted(set(car_out) - set(main_out))
    only_main = sorted(set(main_out) - set(car_out))
    modules = sorted({tid.split("::")[0] for tid in only_car})
    print(f"ids only in carrier: {len(only_car)} from {modules}; statuses {sorted({car_out[t] for t in only_car})}")
    print(f"ids only in main: {len(only_main)} {only_main[:5]}")
    changed = sorted(t for t in set(main_out) & set(car_out) if main_out[t] != car_out[t])
    print(f"shared ids whose outcome differs: {len(changed)} {changed[:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
