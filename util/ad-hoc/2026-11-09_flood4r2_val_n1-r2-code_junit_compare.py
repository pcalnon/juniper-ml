"""
Compare two pytest JUnit XML files: per-outcome counts, tests only in one, and outcome changes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, n1 r2 code lens)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 11, cascor paused-fit wedge)

Usage: python3 <this> BASE.xml HEAD.xml

A testcase's outcome is failed / error / skipped / passed from its child elements. Prints the
counts for each file, the tests present in only one, and every test whose outcome differs.
"""

import collections
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses the validator's own pytest output


def _outcomes(path: str) -> dict:
    root = ET.parse(path).getroot()  # nosec B314 - the validator's own pytest output
    result = {}
    for case in root.iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag for child in case}
        outcome = "failed" if "failure" in tags else "error" if "error" in tags else "skipped" if "skipped" in tags else "passed"
        result[key] = outcome
    return result


def main() -> int:
    base, head = _outcomes(sys.argv[1]), _outcomes(sys.argv[2])
    for label, data in (("base", base), ("head", head)):
        print(f"{label}: {len(data)} testcases {dict(collections.Counter(data.values()))}")
    only_head = sorted(set(head) - set(base))
    only_base = sorted(set(base) - set(head))
    changed = sorted(k for k in set(base) & set(head) if base[k] != head[k])
    print(f"only in head: {len(only_head)} {dict(collections.Counter(head[k] for k in only_head))}")
    for k in only_head:
        print(f"  + {head[k]:7s} {k}")
    print(f"only in base: {len(only_base)}")
    for k in only_base:
        print(f"  - {base[k]:7s} {k}")
    print(f"outcome changes: {len(changed)}")
    for k in changed:
        print(f"  ~ {base[k]} -> {head[k]} {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
