"""
JUnit XML helper for the r27-val-code2 lens: per-file test time sums, and the failed/errored test ids of a run.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2

Usage:
    python <this file> times <junit.xml> <file listing repo-relative test files, one per line>
    python <this file> failed <junit.xml>          prints one JSON object: {"failed": [...], "errors": [...], counts}
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses junit files this lens's own runs wrote


def cases(path: str):
    root = ET.parse(path).getroot()  # nosec B314 - local files written by pytest runs of this lens
    for case in root.iter("testcase"):
        classname = case.get("classname", "")
        yield case, classname, case.get("name", ""), float(case.get("time", "0") or 0)


def file_of(classname: str) -> str:
    parts = classname.split(".")
    for end in range(len(parts), 0, -1):
        candidate = "/".join(parts[:end]) + ".py"
        if parts[end - 1].startswith("test_"):
            return candidate
    return classname


def main() -> int:
    mode, junit = sys.argv[1], sys.argv[2]
    if mode == "times":
        with open(sys.argv[3], encoding="utf-8") as handle:
            wanted = {line.strip() for line in handle if line.strip()}
        total, count, per = 0.0, 0, {}
        for _case, classname, _name, seconds in cases(junit):
            name = file_of(classname)
            if name in wanted:
                total += seconds
                count += 1
                per[name] = per.get(name, 0.0) + seconds
        print(json.dumps({"tests": count, "seconds": round(total, 1), "top": sorted(((round(v, 1), k) for k, v in per.items()), reverse=True)[:12]}, indent=1))
        return 0
    failed, errors, total = [], [], 0
    for case, classname, name, _seconds in cases(junit):
        total += 1
        ident = f"{file_of(classname)}::{classname.split('.')[-1] if not classname.split('.')[-1].startswith('test_') else ''}::{name}".replace("::::", "::")
        if case.find("failure") is not None:
            failed.append(ident)
        elif case.find("error") is not None:
            errors.append(ident)
    print(json.dumps({"tests": total, "failed_count": len(failed), "error_count": len(errors), "failed": failed, "errors": errors}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
