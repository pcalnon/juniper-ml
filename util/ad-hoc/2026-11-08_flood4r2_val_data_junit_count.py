"""
Count, per test file, the JUnit testcases a CI-lane run executed, skipped or failed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (tmp/flood4/BRIEF_VALIDATE_R2.txt); juniper-data data-tests and data-code carriers

Usage:
    python3 util/ad-hoc/2026-11-08_flood4r2_val_data_junit_count.py <junit.xml> <module-substring> [<module-substring> ...]

A testcase counts as RUN only when it has no <skipped>, <failure> or <error> child, so a module
that importorskips in CI shows up as skipped here rather than as a silent pass.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses a local JUnit file this session's own pytest run wrote
from collections import Counter
from pathlib import Path


def main(junit: Path, needles: list[str]) -> int:
    root = ET.parse(junit).getroot()  # nosec B314 - same local, self-written file
    totals: dict[str, Counter] = {needle: Counter() for needle in needles}
    for case in root.iter("testcase"):
        classname = case.get("classname", "")
        for needle in needles:
            if needle in classname:
                tags = {child.tag for child in case}
                if "skipped" in tags:
                    totals[needle]["skipped"] += 1
                elif "failure" in tags or "error" in tags:
                    totals[needle]["failed"] += 1
                else:
                    totals[needle]["run"] += 1
    for needle, counts in totals.items():
        print(f"{needle}: run={counts['run']} skipped={counts['skipped']} failed={counts['failed']}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), sys.argv[2:]))
