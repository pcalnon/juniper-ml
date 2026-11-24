#!/usr/bin/env python3
"""
Compare two pytest JUnit files test by test: outcomes that changed, and tests only one side ran.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (Cursor flood-4 round 2, validator LN1, code lens on the r32 pause fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor carrier r32-pause-fix; the unit and integration lanes of a clean main and the fix

Usage:
  2026-11-15_flood4r2_val_r32-fix-code_junit_compare.py --main <main.xml> --fix <fix.xml> --out <json>
Exit: 0 when no shared test changed outcome; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses JUnit files this validator's own runs wrote
from pathlib import Path


def _outcomes(path: Path) -> dict:
    root = ET.parse(path).getroot()  # nosec B314 -- our own pytest output
    result = {}
    for case in root.iter("testcase"):
        test_id = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None:
            outcome = "failed"
        elif case.find("error") is not None:
            outcome = "error"
        elif case.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"
        result[test_id] = outcome
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--fix", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    main_outcomes = _outcomes(args.main)
    fix_outcomes = _outcomes(args.fix)
    shared = sorted(set(main_outcomes) & set(fix_outcomes))
    changed = [{"test": t, "main": main_outcomes[t], "fix": fix_outcomes[t]} for t in shared if main_outcomes[t] != fix_outcomes[t]]
    only_fix = sorted(set(fix_outcomes) - set(main_outcomes))
    only_main = sorted(set(main_outcomes) - set(fix_outcomes))
    report = {
        "main": str(args.main),
        "fix": str(args.fix),
        "shared": len(shared),
        "changed": changed,
        "only_in_fix": [{"test": t, "outcome": fix_outcomes[t]} for t in only_fix],
        "only_in_main": [{"test": t, "outcome": main_outcomes[t]} for t in only_main],
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"shared": len(shared), "changed": len(changed), "only_in_fix": len(only_fix), "only_in_main": len(only_main), "only_in_fix_outcomes": sorted({fix_outcomes[t] for t in only_fix})}))
    return 0 if not changed else 1


if __name__ == "__main__":
    sys.exit(main())
